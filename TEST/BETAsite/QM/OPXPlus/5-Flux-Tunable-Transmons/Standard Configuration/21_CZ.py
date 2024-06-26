"""
        CZ CHEVRON - 4ns granularity
The goal of this protocol is to find the parameters of the CZ gate between two flux-tunable qubits.
The protocol consists in flux tuning one qubit to bring the |11> state on resonance with |20>.
The two qubits must start in their excited states so that, when |11> and |20> are on resonance, the state |11> will
start acquiring a global phase when varying the flux pulse duration.

By scanning the flux pulse amplitude and duration, the CZ chevron can be obtained and post-processed to extract the
CZ gate parameters corresponding to a single oscillation period such that |11> pick up an overall phase of pi (flux
pulse amplitude and interation time).

This version sweeps the flux pulse duration using real-time QUA, which means that the flux pulse can be arbitrarily long
but the step must be larger than 1 clock cycle (4ns) and the minimum pulse duration is 4 clock cycles (16ns).

Prerequisites:
    - Having found the resonance frequency of the resonator coupled to the qubit under study (resonator_spectroscopy).
    - Having found the qubits maximum frequency point (qubit_spectroscopy_vs_flux).
    - Having calibrated qubit gates (x180) by running qubit spectroscopy, rabi_chevron, power_rabi, Ramsey and updated the configuration.
    - (Optional) having corrected the flux line distortions by running the Cryoscope protocol and updating the filter taps in the configuration.

Next steps before going to the next node:
    - Update the CZ gate parameters in the configuration.
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
import numpy as np
from macros import qua_declaration, multiplexed_readout
import warnings

warnings.filterwarnings("ignore")

simulate = False
indicate_config = 1
linewidth = 0.73

####################
# Define variables #
####################

# Qubit to flux-tune to reach some distance of Ec with another qubit, Qubit to meet with:
# 5,4  4,3  2,3  1,2
qubit_to_flux_tune,qubit_to_meet_with = 5,4 

starting_point = eval(f"idle_q{qubit_to_flux_tune}")
if indicate_config:
    cz_point = starting_point + eval(f"cz{qubit_to_flux_tune}_{qubit_to_meet_with}_amp")
    cz_duration = eval(f"cz{qubit_to_flux_tune}_{qubit_to_meet_with}_len")
multiplexed = [1,2,3,4,5]

# Pulse waveforms to choose from:
scale_reference = const_flux_amp # for const
# scale_reference = cz_point_1_2_q2-idle_q2 # for gaussian-like cz

# Flux offset (at idle-point) 
flux_offset = config["controllers"]["con2"]["analog_outputs"][
    config["elements"][f"q{qubit_to_flux_tune}_z"]["singleInput"]["port"][1]
]["offset"]
print("flux_offset for q%s: %s" %(qubit_to_flux_tune, flux_offset))

n_avg = 130000  # The number of averages
ts = np.arange(4, 30, 1)  # The flux pulse durations in clock cycles (4ns) - Must be larger than 4 clock cycles.

# First guess:
amps = (np.arange(starting_point-0.35, starting_point+0.35, 0.0005) - flux_offset) / scale_reference

# Zoom in:
# amps = (np.arange(0.225, 0.255, 0.0001) - flux_offset) / scale_reference
# amps = (np.arange(0.18, 0.21, 0.0001) - flux_offset) / scale_reference

# calibrated:
# q2->q1
# amps = (np.arange(-0.135, -0.115, 0.0002) - flux_offset) / scale_reference  

# q1->q2 
# amps = (np.arange(-0.20, -0.10, 0.00005) - flux_offset) / scale_reference

# q3->q2
# amps = (np.arange(0.0, 0.033, 0.00002) - flux_offset) / scale_reference 

# q2->q3
# amps = (np.arange(0.16, 0.18, 0.00002) - flux_offset) / scale_reference
# amps = (np.arange(0.19, 0.22, 0.00002) - flux_offset) / scale_reference
# amps = (np.arange(0.265, 0.285, 0.00002) - flux_offset) / scale_reference 

# q4->q3
# amps = (np.arange(0.15, 0.18, 0.00005) - flux_offset) / scale_reference 

# q5->q4:
amps = (np.arange(0.185, 0.207, 0.00002) - flux_offset) / scale_reference


# gaussian-like:
# amps = (np.arange(0.125, 0.145, 0.0001) - flux_offset) / scale_reference

###################
# The QUA program #
###################

with program() as cz:
    I, I_st, Q, Q_st, n, n_st = qua_declaration(nb_of_qubits=len(multiplexed))
    t = declare(int)  # QUA variable for the flux pulse duration
    a = declare(fixed)  # QUA variable for the flux pulse amplitude pre-factor.

    with for_(n, 0, n < n_avg, n + 1):
        # set_dc_offset("q1_z", "single", 0.15)
        with for_(*from_array(t, ts)):
            with for_(*from_array(a, amps)):
                # Put the two qubits in their excited states
                play("x180", f"q{qubit_to_flux_tune}_xy")
                play("x180", f"q{qubit_to_meet_with}_xy")
                
                align()
                wait(flux_settle_time * u.ns)

                # Play a flux pulse on the qubit with the highest frequency to bring it close to the excited qubit while
                # varying its amplitude and duration in order to observe the SWAP chevron.
                play("const" * amp(a), f"q{qubit_to_flux_tune}_z", duration=t)
                # NOTE: optional: play another pulse on the "qubit_to_meet_with"
                # play("const" * amp(0.3125), f"q{qubit_to_meet_with}_z", duration=t)
                
                align()
                
                wait(flux_settle_time * u.ns)
                align()

                multiplexed_readout(I, I_st, Q, Q_st, resonators=multiplexed, weights="rotated_")
                wait(thermalization_time * u.ns)
        # Save the averaging iteration to get the progress bar
        save(n, n_st)

    with stream_processing():
        # for the progress counter
        n_st.save("n")
        # resonator 1
        I_st[multiplexed.index(qubit_to_flux_tune)].buffer(len(amps)).buffer(len(ts)).average().save("I1")
        Q_st[multiplexed.index(qubit_to_flux_tune)].buffer(len(amps)).buffer(len(ts)).average().save("Q1")
        # resonator 2
        I_st[multiplexed.index(qubit_to_meet_with)].buffer(len(amps)).buffer(len(ts)).average().save("I2")
        Q_st[multiplexed.index(qubit_to_meet_with)].buffer(len(amps)).buffer(len(ts)).average().save("Q2")

#####################################
#  Open Communication with the QOP  #
#####################################

qmm = QuantumMachinesManager(host=qop_ip, port=qop_port, cluster_name=cluster_name, octave=octave_config)

###########################
# Run or Simulate Program #
###########################
if simulate:
    # Simulates the QUA program for the specified duration
    simulation_config = SimulationConfig(duration=10_000)  # In clock cycles = 4ns
    job = qmm.simulate(config, cz, simulation_config)
    job.get_simulated_samples().con1.plot()
else:
    # Open the quantum machine
    qm = qmm.open_qm(config)
    # Send the QUA program to the OPX, which compiles and executes it
    job = qm.execute(cz)
    # Prepare the figure for live plotting
    fig = plt.figure()
    interrupt_on_close(fig, job)
    # Tool to easily fetch results from the OPX (results_handle used in it)
    results = fetching_tool(job, ["n", "I1", "Q1", "I2", "Q2"], mode="live")
    # Live plotting
    while results.is_processing():
        # Fetch results
        n, I1, Q1, I2, Q2 = results.fetch_all()
        # Convert the results into Volts
        I1, Q1 = u.demod2volts(I1, readout_len), u.demod2volts(Q1, readout_len)
        I2, Q2 = u.demod2volts(I2, readout_len), u.demod2volts(Q2, readout_len)
        # Progress bar
        progress_counter(n, n_avg, start_time=results.start_time)
        # Plot
        plt.suptitle(f"CZ chevron sweeping the flux on qubit {qubit_to_flux_tune}")
        plt.subplot(221)
        plt.cla()
        plt.pcolor(amps * scale_reference + flux_offset, 4 * ts, I1)
        plt.title(f"q{qubit_to_flux_tune} - I [V]")
        plt.ylabel("Interaction time (ns)")
        if indicate_config:
            plt.axhline(cz_duration, color="r", linewidth=linewidth)
            plt.axvline(cz_point, color="r", linewidth=linewidth)
        plt.subplot(223)
        plt.cla()
        plt.pcolor(amps * scale_reference + flux_offset, 4 * ts, Q1)
        plt.title(f"q{qubit_to_flux_tune} - Q [V]")
        plt.xlabel("Flux amplitude (V)")
        plt.ylabel("Interaction time (ns)")
        if indicate_config:
            plt.axhline(cz_duration, color="r", linewidth=linewidth)
            plt.axvline(cz_point, color="r", linewidth=linewidth)
        plt.subplot(222)
        plt.cla()
        plt.pcolor(amps * scale_reference + flux_offset, 4 * ts, I2)
        plt.title(f"q{qubit_to_meet_with} - I [V]")
        if indicate_config:
            plt.axhline(cz_duration, color="r", linewidth=linewidth)
            plt.axvline(cz_point, color="r", linewidth=linewidth)
        plt.subplot(224)
        plt.cla()
        plt.pcolor(amps * scale_reference + flux_offset, 4 * ts, Q2)
        plt.title(f"q{qubit_to_meet_with} - Q [V]")
        plt.xlabel("Flux amplitude (V)")
        if indicate_config:
            plt.axhline(cz_duration, color="r", linewidth=linewidth)
            plt.axvline(cz_point, color="r", linewidth=linewidth)

        plt.tight_layout()
        plt.pause(0.1)
    
    # Close the quantum machines at the end in order to put all flux biases to 0 so that the fridge doesn't heat-up
    qm.close()
    plt.show()

    # np.savez(save_dir/'cz', I1=I1, Q1=Q1, I2=I2, Q2=Q2, ts=ts, amps=amps)

