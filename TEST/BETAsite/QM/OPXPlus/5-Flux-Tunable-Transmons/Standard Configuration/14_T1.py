"""
        T1 MEASUREMENT
The sequence consists in putting the qubit in the excited stated by playing the x180 pulse and measuring the resonator
after a varying time. The qubit T1 is extracted by fitting the exponential decay of the measured quadratures.

Prerequisites:
    - Having found the resonance frequency of the resonator coupled to the qubit under study (resonator_spectroscopy).
    - Having calibrated qubit pi pulse (x180) by running qubit, spectroscopy, rabi_chevron, power_rabi and updated the config.
    - (optional) Having calibrated the readout (readout_frequency, amplitude, duration_optimization IQ_blobs) for better SNR.
    - Set the desired flux bias.

Next steps before going to the next node:
    - Update the qubit T1 (qubit_T1) in the configuration.
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
n_avg = 100000
tau_min = 4  # in clock cycles
tau_max = 24_000  # in clock cycles
d_tau = 140  # in clock cycles
t_delay = np.arange(tau_min, tau_max + 0.1, d_tau)  # Linear sweep
# t_delay = np.logspace(np.log10(tau_min), np.log10(tau_max), 29)  # Log sweep


# QUA program
with program() as T1:
    I, I_st, Q, Q_st, n, n_st = qua_declaration(nb_of_qubits=5)
    t = declare(int)  # QUA variable for the wait time

    with for_(n, 0, n < n_avg, n + 1):
        with for_(*from_array(t, t_delay)):
            # qubit 1
            play("x180", "q1_xy")
            wait(t, "q1_xy")
            # qubit 2
            play("x180", "q2_xy")
            wait(t, "q2_xy")
            # qubit 3
            play("x180", "q3_xy")
            wait(t, "q3_xy")
            # qubit 4
            play("x180", "q4_xy")
            wait(t, "q4_xy")
            # qubit 5
            play("x180", "q5_xy")
            wait(t, "q5_xy")

            # Align the elements to measure after having waited a time "tau" after the qubit pulses.
            align()
            # Measure the state of the resonators
            multiplexed_readout(I, I_st, Q, Q_st, resonators=[1, 2, 3, 4, 5], weights="rotated_")
            # Wait for the qubit to decay to the ground state
            wait(thermalization_time * u.ns)
        # Save the averaging iteration to get the progress bar
        save(n, n_st)

    with stream_processing():
        n_st.save("n")
        # resonator 1
        I_st[0].buffer(len(t_delay)).average().save("I1")
        Q_st[0].buffer(len(t_delay)).average().save("Q1")
        # resonator 2
        I_st[1].buffer(len(t_delay)).average().save("I2")
        Q_st[1].buffer(len(t_delay)).average().save("Q2")
        # resonator 3
        I_st[2].buffer(len(t_delay)).average().save("I3")
        Q_st[2].buffer(len(t_delay)).average().save("Q3")
        # resonator 4
        I_st[3].buffer(len(t_delay)).average().save("I4")
        Q_st[3].buffer(len(t_delay)).average().save("Q4")
        # resonator 5
        I_st[4].buffer(len(t_delay)).average().save("I5")
        Q_st[4].buffer(len(t_delay)).average().save("Q5")


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
    job = qmm.simulate(config, T1, simulation_config)
    job.get_simulated_samples().con1.plot()
    plt.show()
else:
    # Open the quantum machine
    qm = qmm.open_qm(config)
    # Send the QUA program to the OPX, which compiles and executes it
    job = qm.execute(T1)
    # Prepare the figure for live plotting
    fig = plt.figure()
    interrupt_on_close(fig, job)
    # Tool to easily fetch results from the OPX (results_handle used in it)
    results = fetching_tool(job, ["n", "I1", "Q1", "I2", "Q2", "I3", "Q3", "I4", "Q4", "I5", "Q5"], mode="live")
    # Live plotting
    while results.is_processing():
        # Fetch results
        n, I1, Q1, I2, Q2, I3, Q3, I4, Q4, I5, Q5 = results.fetch_all()
        # Convert the results into Volts
        I1, Q1 = u.demod2volts(I1, readout_len), u.demod2volts(Q1, readout_len)
        I2, Q2 = u.demod2volts(I2, readout_len), u.demod2volts(Q2, readout_len)
        I3, Q3 = u.demod2volts(I3, readout_len), u.demod2volts(Q3, readout_len)
        I4, Q4 = u.demod2volts(I4, readout_len), u.demod2volts(Q4, readout_len)
        I5, Q5 = u.demod2volts(I5, readout_len), u.demod2volts(Q5, readout_len)
        # Progress bar
        progress_counter(n, n_avg, start_time=results.start_time)
        # Plot
        plt.suptitle("T1 measurement (%s/%s)" %(n,n_avg))
        # q1:
        plt.subplot(2,5,1)
        plt.cla()
        plt.plot(4 * t_delay, I1)
        plt.ylabel("I quadrature [V]")
        plt.title("Qubit 1")
        plt.subplot(2,5,6)
        plt.cla()
        plt.plot(4 * t_delay, Q1)
        plt.ylabel("Q quadrature [V]")
        plt.xlabel("Wait time (ns)")
        # q2:
        plt.subplot(2,5,2)
        plt.cla()
        plt.plot(4 * t_delay, I2)
        plt.title("Qubit 2")
        plt.subplot(2,5,7)
        plt.cla()
        plt.plot(4 * t_delay, Q2)
        plt.title("Q2")
        plt.xlabel("Wait time (ns)")
        # q3:
        plt.subplot(2,5,3)
        plt.cla()
        plt.plot(4 * t_delay, I3)
        plt.title("Qubit 3")
        plt.subplot(2,5,8)
        plt.cla()
        plt.plot(4 * t_delay, Q3)
        plt.title("Q3")
        plt.xlabel("Wait time (ns)")
        # q4:
        plt.subplot(2,5,4)
        plt.cla()
        plt.plot(4 * t_delay, I4)
        plt.title("Qubit 4")
        plt.subplot(2,5,9)
        plt.cla()
        plt.plot(4 * t_delay, Q4)
        plt.title("Q4")
        plt.xlabel("Wait time (ns)")
        # q5:
        plt.subplot(2,5,5)
        plt.cla()
        plt.plot(4 * t_delay, I5)
        plt.title("Qubit 5")
        plt.subplot(2,5,10)
        plt.cla()
        plt.plot(4 * t_delay, Q5)
        plt.title("Q5")
        plt.xlabel("Wait time (ns)")

        plt.tight_layout()
        plt.pause(0.1)
    # Close the quantum machines at the end in order to put all flux biases to 0 so that the fridge doesn't heat-up
    qm.close()

    # Fit the results to extract the qubit decay time T1
    try:
        from qualang_tools.plot.fitting import Fit

        fit = Fit()
        plt.figure()
        plt.suptitle("T1 measurement")
        
        # q1:
        plt.subplot(1,5,1)
        decay_fit = fit.T1(4 * t_delay, I1, plot=True)
        qubit_T1 = np.round(np.abs(decay_fit["T1"][0]) / 4) * 4
        plt.xlabel("Delay [ns]")
        plt.ylabel("I quadrature [V]")
        print(f"Qubit decay time to update in the config: qubit_T1 = {qubit_T1:.0f} ns")
        plt.legend((f"T1={qubit_T1:.0f}ns",))
        plt.title("Qubit 1")
        # q2:
        plt.subplot(1,5,2)
        decay_fit = fit.T1(4 * t_delay, I2, plot=True)
        qubit_T1 = np.round(np.abs(decay_fit["T1"][0]) / 4) * 4
        plt.xlabel("Delay [ns]")
        plt.ylabel("I quadrature [V]")
        print(f"Qubit decay time to update in the config: qubit_T1 = {qubit_T1:.0f} ns")
        plt.legend((f"T1={qubit_T1:.0f}ns",))
        plt.title("Qubit 2")
        # q3:
        plt.subplot(1,5,3)
        decay_fit = fit.T1(4 * t_delay, I3, plot=True)
        qubit_T1 = np.round(np.abs(decay_fit["T1"][0]) / 4) * 4
        plt.xlabel("Delay [ns]")
        plt.ylabel("I quadrature [V]")
        print(f"Qubit decay time to update in the config: qubit_T1 = {qubit_T1:.0f} ns")
        plt.legend((f"T1={qubit_T1:.0f}ns",))
        plt.title("Qubit 3")
        # q4:
        plt.subplot(1,5,4)
        decay_fit = fit.T1(4 * t_delay, I4, plot=True)
        qubit_T1 = np.round(np.abs(decay_fit["T1"][0]) / 4) * 4
        plt.xlabel("Delay [ns]")
        plt.ylabel("I quadrature [V]")
        print(f"Qubit decay time to update in the config: qubit_T1 = {qubit_T1:.0f} ns")
        plt.legend((f"T1={qubit_T1:.0f}ns",))
        plt.title("Qubit 4")
        # q5:
        plt.subplot(1,5,5)
        decay_fit = fit.T1(4 * t_delay, I5, plot=True)
        qubit_T1 = np.round(np.abs(decay_fit["T1"][0]) / 4) * 4
        plt.xlabel("Delay [ns]")
        plt.ylabel("I quadrature [V]")
        print(f"Qubit decay time to update in the config: qubit_T1 = {qubit_T1:.0f} ns")
        plt.legend((f"T1={qubit_T1:.0f}ns",))
        plt.title("Qubit 5")

        plt.tight_layout()
        plt.show()
    except (Exception,):
        pass
