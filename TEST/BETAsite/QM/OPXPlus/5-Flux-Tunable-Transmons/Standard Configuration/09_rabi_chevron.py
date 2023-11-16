"""
        RABI CHEVRON (AMPLITUDE VS FREQUENCY)
This sequence involves executing the qubit pulse and measuring the state
of the resonator across various qubit intermediate frequencies and pulse amplitudes.
By analyzing the results, one can determine the qubit and estimate the x180 pulse amplitude for a specified duration.

Prerequisites:
    - Determination of the resonator's resonance frequency when coupled to the qubit of interest (referred to as "resonator_spectroscopy").
    - Calibration of the IQ mixer connected to the qubit drive line (be it an external mixer or an Octave port).
    - Identification of the approximate qubit frequency (referred to as "qubit_spectroscopy").
    - Configuration of the qubit frequency and the desired pi pulse duration (labeled as "pi_len_q").
    - Set the desired flux bias

Before proceeding to the next node:
    - Adjust the qubit frequency setting, labeled as "qubit_IF_q", in the configuration.
    - Modify the qubit pulse amplitude setting, labeled as "pi_amp_q", in the configuration.
"""

from qm.QuantumMachinesManager import QuantumMachinesManager
from qm.qua import *
from qm import SimulationConfig
from configuration import *
import matplotlib.pyplot as plt
from qualang_tools.loops import from_array
from qualang_tools.results import fetching_tool
from qualang_tools.plot import interrupt_on_close
from qualang_tools.results import progress_counter
from macros import qua_declaration, multiplexed_readout
import warnings

warnings.filterwarnings("ignore")

###################
# The QUA program #
###################
n_avg = 100000  # The number of averages
test_qubits = [1,2,3,4,5]

# Qubit detuning sweep with respect to qubit_IF
dfs = np.arange(-100e6, +100e6, 1e6)
# Qubit pulse amplitude sweep (as a pre-factor of the qubit pulse amplitude) - must be within [-2; 2)
amps = np.arange(0.0, 1.98, 0.01)

print("plotting %s X %s points" %(len(test_qubits),len(dfs)*len(amps)))

with program() as rabi_chevron:
    I, I_st, Q, Q_st, n, n_st = qua_declaration(nb_of_qubits=5)
    df = declare(int)  # QUA variable for the qubit detuning
    a = declare(fixed)  # QUA variable for the qubit pulse amplitude pre-factor

    with for_(n, 0, n < n_avg, n + 1):
        with for_(*from_array(df, dfs)):
            update_frequency("q1_xy", df + qubit_IF_q1)
            update_frequency("q2_xy", df + qubit_IF_q2)
            update_frequency("q3_xy", df + qubit_IF_q3)
            update_frequency("q4_xy", df + qubit_IF_q4)
            update_frequency("q5_xy", df + qubit_IF_q5)

            with for_(*from_array(a, amps)):
                if 1 in test_qubits: play("x180" * amp(a), "q1_xy")
                if 2 in test_qubits: play("x180" * amp(a), "q2_xy")
                if 3 in test_qubits: play("x180" * amp(a), "q3_xy")
                if 4 in test_qubits: play("x180" * amp(a), "q4_xy")
                if 5 in test_qubits: play("x180" * amp(a), "q5_xy")
                # Measure after the qubit pulses
                align()
                # Multiplexed readout, also saves the measurement outcomes
                multiplexed_readout(I, I_st, Q, Q_st, resonators=[1, 2, 3, 4, 5], weights="rotated_", amplitude=0.99)
                # Wait for the qubit to decay to the ground state
                wait(thermalization_time * u.ns)
        # Save the averaging iteration to get the progress bar
        save(n, n_st)

    with stream_processing():
        n_st.save("n")
        # resonator 1
        I_st[0].buffer(len(amps)).buffer(len(dfs)).average().save("I1")
        Q_st[0].buffer(len(amps)).buffer(len(dfs)).average().save("Q1")
        # resonator 2
        I_st[1].buffer(len(amps)).buffer(len(dfs)).average().save("I2")
        Q_st[1].buffer(len(amps)).buffer(len(dfs)).average().save("Q2")
        # resonator 3
        I_st[2].buffer(len(amps)).buffer(len(dfs)).average().save("I3")
        Q_st[2].buffer(len(amps)).buffer(len(dfs)).average().save("Q3")
        # resonator 4
        I_st[3].buffer(len(amps)).buffer(len(dfs)).average().save("I4")
        Q_st[3].buffer(len(amps)).buffer(len(dfs)).average().save("Q4")
        # resonator 5
        I_st[4].buffer(len(amps)).buffer(len(dfs)).average().save("I5")
        Q_st[4].buffer(len(amps)).buffer(len(dfs)).average().save("Q5")


#####################################
#  Open Communication with the QOP  #
#####################################
qmm = QuantumMachinesManager(host=qop_ip, port=qop_port, cluster_name=cluster_name, octave=octave_config)

###########################
# Run or Simulate Program #
###########################

simulate = False

if simulate:
    # Simulates the QUA program for the specified duration
    simulation_config = SimulationConfig(duration=10_000)  # In clock cycles = 4ns
    job = qmm.simulate(config, rabi_chevron, simulation_config)
    job.get_simulated_samples().con1.plot()
    plt.show()
else:
    # Open the quantum machine
    qm = qmm.open_qm(config)
    # Send the QUA program to the OPX, which compiles and executes it
    job = qm.execute(rabi_chevron)
    # Prepare the figure for live plotting
    fig = plt.figure()
    interrupt_on_close(fig, job)
    # Tool to easily fetch results from the OPX (results_handle used in it)
    results = fetching_tool(job, ["n", "I1", "Q1", "I2", "Q2", "I3", "Q3", "I4", "Q4", "I5", "Q5"], mode="live")
    # Live plotting
    while results.is_processing():
        # Fetch results
        n, I1, Q1, I2, Q2, I3, Q3, I4, Q4, I5, Q5 = results.fetch_all()
        # Progress bar
        progress_counter(n, n_avg, start_time=results.start_time)
        # Convert the results into Volts
        I1, Q1 = u.demod2volts(I1, readout_len), u.demod2volts(Q1, readout_len)
        I2, Q2 = u.demod2volts(I2, readout_len), u.demod2volts(Q2, readout_len)
        I3, Q3 = u.demod2volts(I3, readout_len), u.demod2volts(Q3, readout_len)
        I4, Q4 = u.demod2volts(I4, readout_len), u.demod2volts(Q4, readout_len)
        I5, Q5 = u.demod2volts(I5, readout_len), u.demod2volts(Q5, readout_len)
        # Plots
        plt.suptitle("Rabi chevron (%s/%s)" %(n,n_avg))
        # q1:
        plt.subplot(2,5,1)
        plt.cla()
        plt.pcolor(amps * pi_amp_q1, dfs, I1)
        plt.xlabel("X-pulse amplitude [V]")
        plt.ylabel("q1 detuning [MHz]")
        plt.axvline(pi_amp_q1, color="k", linewidth=0.37)
        plt.axhline(0, color="k", linewidth=0.37)
        plt.title(f"q1 (f_res: {(qubit_LO_q1 + qubit_IF_q1) / u.MHz} MHz)")
        plt.subplot(2,5,6)
        plt.cla()
        plt.pcolor(amps * pi_amp_q1, dfs, Q1)
        plt.xlabel("X-pulse amplitude [V]")
        plt.ylabel("q1 detuning [MHz]")
        # q2:
        plt.subplot(2,5,2)
        plt.cla()
        plt.pcolor(amps * pi_amp_q2, dfs, I2)
        plt.title(f"q2 (f_res: {(qubit_LO_q2 + qubit_IF_q2) / u.MHz} MHz)")
        plt.xlabel("X-pulse amplitude [V]")
        plt.ylabel("q2 detuning [MHz]")
        plt.axvline(pi_amp_q2, color="k", linewidth=0.37)
        plt.axhline(0, color="k", linewidth=0.37)
        plt.subplot(2,5,7)
        plt.cla()
        plt.pcolor(amps * pi_amp_q2, dfs, Q2)
        plt.xlabel("X-pulse amplitude [V]")
        plt.ylabel("q2 detuning [MHz]")
        # q3:
        plt.subplot(2,5,3)
        plt.cla()
        plt.pcolor(amps * pi_amp_q3, dfs, I3)
        plt.title(f"q3 (f_res: {(qubit_LO_q3 + qubit_IF_q3) / u.MHz} MHz)")
        plt.xlabel("X-pulse amplitude [V]")
        plt.ylabel("q3 detuning [MHz]")
        plt.axvline(pi_amp_q3, color="k", linewidth=0.37)
        plt.axhline(0, color="k", linewidth=0.37)
        plt.subplot(2,5,8)
        plt.cla()
        plt.pcolor(amps * pi_amp_q3, dfs, Q3)
        plt.xlabel("X-pulse amplitude [V]")
        plt.ylabel("q3 detuning [MHz]")
        plt.tight_layout()
        plt.pause(0.1)
        # q4:
        plt.subplot(2,5,4)
        plt.cla()
        plt.pcolor(amps * pi_amp_q4, dfs, I4)
        plt.title(f"q4 (f_res: {(qubit_LO_q4 + qubit_IF_q4) / u.MHz} MHz)")
        plt.xlabel("X-pulse amplitude [V]")
        plt.ylabel("q4 detuning [MHz]")
        plt.axvline(pi_amp_q4, color="k", linewidth=0.37)
        plt.axhline(0, color="k", linewidth=0.37)
        plt.subplot(2,5,9)
        plt.cla()
        plt.pcolor(amps * pi_amp_q4, dfs, Q4)
        plt.xlabel("X-pulse amplitude [V]")
        plt.ylabel("q4 detuning [MHz]")
        # q5:
        plt.subplot(2,5,5)
        plt.cla()
        plt.pcolor(amps * pi_amp_q5, dfs, I5)
        plt.title(f"q5 (f_res: {(qubit_LO_q5 + qubit_IF_q5) / u.MHz} MHz)")
        plt.xlabel("X-pulse amplitude [V]")
        plt.ylabel("q5 detuning [MHz]")
        plt.axvline(pi_amp_q5, color="k", linewidth=0.37)
        plt.axhline(0, color="k", linewidth=0.37)
        plt.subplot(2,5,10)
        plt.cla()
        plt.pcolor(amps * pi_amp_q5, dfs, Q5)
        plt.xlabel("X-pulse amplitude [V]")
        plt.ylabel("q5 detuning [MHz]")

        plt.tight_layout()
        plt.pause(0.1)
    # Close the quantum machines at the end in order to put all flux biases to 0 so that the fridge doesn't heat-up
    qm.close()
