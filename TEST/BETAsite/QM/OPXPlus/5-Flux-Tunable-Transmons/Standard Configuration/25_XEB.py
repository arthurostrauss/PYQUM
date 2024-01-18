from qm import QuantumMachinesManager
from qm.qua import *
from configuration import *
from qm.simulate import SimulationConfig
from matplotlib import pyplot as plt
import pprint
from macros import multiplexed_readout, qua_declaration, cz_gate
from qualang_tools.results import progress_counter
import time
import random
# qmm = QuantumMachinesManager(host=qop_ip, cluster_name=cluster_name)
qmm = QuantumMachinesManager(host=qop_ip, port=qop_port, cluster_name=cluster_name, octave=octave_config)

qubits = [4,5]
multiplexed = [4,5,1,2,3]
cz_type = "const_wf"
simulate = False

random_gates = 3
seqs = 97
depth = 5
avgs = 101
depths = np.arange(depth)

filename = f"XEB_q{qubits[0]}_{qubits[1]}_seqs({seqs})_depth({depth})_avgs({avgs})_random_gates({random_gates})"
# filename = "XEB_test"

with program() as xeb:

  I, I_st, Q, Q_st, n, n_st = qua_declaration(nb_of_qubits=len(multiplexed))
  state = [declare(bool) for _ in range(len(multiplexed))]
  state_st = [declare_stream() for _ in range(len(multiplexed))]
  d = declare(int)
  d_ = declare(int)
  _d = declare(int)
  _d_ = declare(int)
  s = declare(int)
  s_st = declare_stream()
  g1 = declare(int, size=depths[-1]) # single qubit gate q1
  g2 = declare(int, size=depths[-1]) # single qubit gate q1
  g1_st = declare_stream()
  g2_st = declare_stream()
  r = Random(); r.set_seed(12321)
  a1_00 = declare(fixed, size=depths[-1]) # amplitude matrix argument q1
  a1_01 = declare(fixed, size=depths[-1]) # amplitude matrix argument q1
  a1_10 = declare(fixed, size=depths[-1]) # amplitude matrix argument q1
  a1_11 = declare(fixed, size=depths[-1]) # amplitude matrix argument q1
  a2_00 = declare(fixed, size=depths[-1]) # amplitude matrix argument q2
  a2_01 = declare(fixed, size=depths[-1]) # amplitude matrix argument q2
  a2_10 = declare(fixed, size=depths[-1]) # amplitude matrix argument q2
  a2_11 = declare(fixed, size=depths[-1]) # amplitude matrix argument q2 
  tot_state_ = declare(int)
  state00 = declare(int)
  state01 = declare(int)
  state10 = declare(int)
  state11 = declare(int)
  state00_st = declare_stream()
  state01_st = declare_stream()
  state10_st = declare_stream()
  state11_st = declare_stream()

  if simulate:
    a1_00_st = declare_stream()
    a1_01_st = declare_stream()
    a1_10_st = declare_stream()
    a1_11_st = declare_stream()
    a2_00_st = declare_stream()
    a2_01_st = declare_stream()
    a2_10_st = declare_stream()
    a2_11_st = declare_stream()

    update_frequency(f"q{qubits[0]}_xy", 0)
    update_frequency(f"q{qubits[1]}_xy", 0)

  with for_(s, 0, s<seqs, s+1):

      with for_each_(d, depths): 

        # randomize the sequence
        if True:
          """
          an index between 0-2 will be randomized for each qubit per iteration and will determine the sequence
          """
          # assign(g1[0], r.rand_int(3))
          # assign(g2[0], r.rand_int(3))
          # save(g1[0], g1_st)
          # save(g2[0], g2_st)
          # with for_(d_, 1, d_ < d, d_ + 1):
          #   assign(g1[d_], r.rand_int(3))
          #   with while_(g1[d_] == g1[d_ - 1]):
          #     assign(g1[d_], r.rand_int(3))
          #   assign(g2[d_], r.rand_int(3))
          #   with while_(g2[d_] == g2[d_ - 1]):
          #     assign(g2[d_], r.rand_int(3))
          #   save(g1[d_], g1_st)
          #   save(g2[d_], g2_st)

          with for_(d_, 0, d_<d, d_+1):
            assign(g1[d_], r.rand_int(3))
            assign(g2[d_], r.rand_int(3))
            save(g1[d_], g1_st)
            save(g2[d_], g2_st)
        
        # map sequence indices into amplitude matrix arguments (the blankers)
        if True:
          with for_(_d, 0, _d<d, _d+1):
            """
            0 => x90, [1,0,0,1]
            1 => y90, [0,1,-1,0]
            2 => x90 + y90, [1, 1, -1, 1] * 0.70710678
            """
            with switch_(g1[_d]):
              with case_(0):
                assign(a1_00[_d], 1); assign(a1_01[_d], 0)
                assign(a1_10[_d], 0); assign(a1_11[_d], 1)
              with case_(1):
                assign(a1_00[_d], 0); assign(a1_01[_d], 1)
                assign(a1_10[_d], -1); assign(a1_11[_d], 0)
              with case_(2):
                assign(a1_00[_d], +0.70710678); assign(a1_01[_d], +0.70710678)
                assign(a1_10[_d], -0.70710678); assign(a1_11[_d], +0.70710678)
            
            with switch_(g2[_d]):
              with case_(0):
                assign(a2_00[_d], 1); assign(a2_01[_d], 0)
                assign(a2_10[_d], 0); assign(a2_11[_d], 1)
              with case_(1):
                assign(a2_00[_d], 0); assign(a2_01[_d], 1)
                assign(a2_10[_d], -1); assign(a2_11[_d], 0)
              with case_(2):
                assign(a2_00[_d], +0.70710678); assign(a2_01[_d], +0.70710678)
                assign(a2_10[_d], -0.70710678); assign(a2_11[_d], +0.70710678)

            if simulate:
              save(a1_00[_d], a1_00_st)
              save(a1_01[_d], a1_01_st)
              save(a1_10[_d], a1_10_st)
              save(a1_11[_d], a1_11_st)
              save(a2_00[_d], a2_00_st)
              save(a2_01[_d], a2_01_st)
              save(a2_10[_d], a2_10_st)
              save(a2_11[_d], a2_11_st)

        assign(state00, 0)
        assign(state01, 0)
        assign(state10, 0)
        assign(state11, 0)
        
        with for_(n, 0, n< avgs, n+1):
            
            # play sequence s at depth d
            if True:
              if simulate:
                wait(25, f"q{qubits[0]}_xy", f"q{qubits[1]}_xy")
              else:
                wait(1* thermalization_time * u.ns, f"q{qubits[0]}_xy", f"q{qubits[1]}_xy")
              with for_(_d_, 0, _d_ < d, _d_ + 1):
                play("x90"*amp(a1_00[_d_], a1_01[_d_], a1_10[_d_], a1_11[_d_]), f"q{qubits[0]}_xy")
                play("x90"*amp(a2_00[_d_], a2_01[_d_], a2_10[_d_], a2_11[_d_]), f"q{qubits[1]}_xy")
                
                # align()
                # play("cz", "q1_z")
                # frame_rotation_2pi(0, f"q{qubits[0]}_xy")

                # align()
                # cz_gate(2, 1, cz_type)
                # frame_rotation_2pi(eval(f"cz{1}_{2}_2pi_dev"), "q2_xy")
                # frame_rotation_2pi(eval(f"cz{2}_{1}_2pi_dev"), "q1_xy")
                # align()

                # align()
                # cz_gate(3, 2, cz_type)
                # frame_rotation_2pi(eval(f"cz{2}_{3}_2pi_dev"), "q3_xy")
                # frame_rotation_2pi(eval(f"cz{3}_{2}_2pi_dev"), "q2_xy")
                # align()

                # align()
                # cz_gate(3, 4, cz_type)
                # frame_rotation_2pi(eval(f"cz{4}_{3}_2pi_dev"), "q4_xy")
                # frame_rotation_2pi(eval(f"cz{3}_{4}_2pi_dev"), "q3_xy")
                # align()

                align()
                cz_gate(4, 5, cz_type)
                frame_rotation_2pi(eval(f"cz{5}_{4}_2pi_dev"), "q5_xy")
                frame_rotation_2pi(eval(f"cz{4}_{5}_2pi_dev"), "q4_xy")
                align()

              # multiplexed_readout(I, I_st, Q, Q_st, resonators=multiplexed)
              multiplexed_readout(I, I_st, Q, Q_st, resonators=multiplexed, weights="rotated_")

              # State discrimination
              assign(state[0], I[0] > eval(f"ge_threshold_q{qubits[0]}"))
              assign(state[1], I[1] > eval(f"ge_threshold_q{qubits[1]}"))
              save(state[0], state_st[0])
              save(state[1], state_st[1])

              assign(tot_state_, Cast.to_int(state[0]) + 2 * Cast.to_int(state[1]) )
              with switch_(tot_state_):
                with case_(0):
                  assign(state00, state00+1)
                with case_(1):
                  assign(state01, state01+1)
                with case_(2):
                  assign(state10, state10+1)
                with case_(3):
                  assign(state11, state11+1)

        save(state00, state00_st)
        save(state01, state01_st)
        save(state10, state10_st)
        save(state11, state11_st)

        # Save the sequence iteration to get the progress bar
        save(s, s_st)

  with stream_processing():
     s_st.save("s")
     g1_st.save_all('g1')
     g2_st.save_all('g2')
     I_st[0].buffer(avgs).map(FUNCTIONS.average()).buffer(len(depths)).save_all("I1")
     Q_st[0].buffer(avgs).map(FUNCTIONS.average()).buffer(len(depths)).save_all("Q1")
     I_st[1].buffer(avgs).map(FUNCTIONS.average()).buffer(len(depths)).save_all("I2")
     Q_st[1].buffer(avgs).map(FUNCTIONS.average()).buffer(len(depths)).save_all("Q2")
     state_st[0].boolean_to_int().buffer(avgs).map(FUNCTIONS.average()).buffer(len(depths)).save_all("state1")
     state_st[1].boolean_to_int().buffer(avgs).map(FUNCTIONS.average()).buffer(len(depths)).save_all("state2")
     state00_st.buffer(len(depths)).save_all("state00")
     state01_st.buffer(len(depths)).save_all("state01")
     state10_st.buffer(len(depths)).save_all("state10")
     state11_st.buffer(len(depths)).save_all("state11")

     if simulate:
        a1_00_st.save_all('a1_00')
        a1_01_st.save_all('a1_01')
        a1_10_st.save_all('a1_10')
        a1_11_st.save_all('a1_11')
        a2_00_st.save_all('a2_00')
        a2_01_st.save_all('a2_01')
        a2_10_st.save_all('a2_10')
        a2_11_st.save_all('a2_11')


if simulate:
  job = qmm.simulate(config, xeb, SimulationConfig(50000))
  job.result_handles.wait_for_all_values()
  g1 = job.result_handles.get("g1").fetch_all()['value'].flatten()
  g2 = job.result_handles.get("g2").fetch_all()['value'].flatten()
  a1_00 = job.result_handles.get("a1_00").fetch_all()['value'].flatten()
  a1_01 = job.result_handles.get("a1_01").fetch_all()['value'].flatten()
  a1_10 = job.result_handles.get("a1_10").fetch_all()['value'].flatten()
  a1_11 = job.result_handles.get("a1_11").fetch_all()['value'].flatten()
  a2_00 = job.result_handles.get("a2_00").fetch_all()['value'].flatten()
  a2_01 = job.result_handles.get("a2_01").fetch_all()['value'].flatten()
  a2_10 = job.result_handles.get("a2_10").fetch_all()['value'].flatten()
  a2_11 = job.result_handles.get("a2_11").fetch_all()['value'].flatten()
  gates = list(zip(g1,g2))
  replacement_dict = {0: 'x', 1: 'y', 2: 'w'}
  gates = [(replacement_dict[item[0]], replacement_dict[item[1]]) for item in gates]

  # printing the randomized gates
  if True: 
    idx = 0
    for i in range(seqs):
      print(f"\nseq{i+1}:")
      for j in depths:
        print(f"depth = {j}")
        k=0
        while k<j:
          pprint.pprint(gates[idx])
          if simulate:
            print(f"g1 = [{a1_00[idx]},{a1_01[idx]},{a1_10[idx]},{a1_11[idx]}]")
            print(f"g2 = [{a2_00[idx]},{a2_01[idx]},{a2_10[idx]},{a2_11[idx]}]")
          k+=1; idx+=1

  job.get_simulated_samples().con1.plot()
  plt.show()

else:
  qm = qmm.open_qm(config)
  job = qm.execute(xeb)
  job.result_handles.wait_for_all_values()
  g1 = job.result_handles.get("g1").fetch_all()['value'].flatten()
  g2 = job.result_handles.get("g2").fetch_all()['value'].flatten()
  I1 = job.result_handles.get("I1").fetch_all()['value']
  I2 = job.result_handles.get("I2").fetch_all()['value']
  Q1 = job.result_handles.get("Q1").fetch_all()['value']
  Q2 = job.result_handles.get("Q2").fetch_all()['value']
  state1 = job.result_handles.get('state1').fetch_all()['value']
  state2 = job.result_handles.get('state2').fetch_all()['value']
  state00 = job.result_handles.get('state00').fetch_all()['value']
  state01 = job.result_handles.get('state01').fetch_all()['value']
  state10 = job.result_handles.get('state10').fetch_all()['value']
  state11 = job.result_handles.get('state11').fetch_all()['value']
  S1 = I1 + 1J*Q1
  S2 = I2 + 1J*Q2

  # Close the quantum machines at the end in order to put all flux biases to 0 so that the fridge doesn't heat-up
  qm.close()

  save = True
  if save:
      np.savez(save_dir/filename, g1=g1, g2=g2, I1=I1, I2=I2, Q1=Q1, Q2=Q2, seqs=seqs, depth=depth, avgs=avgs, random_gates=random_gates, 
               state1=state1, state2=state2, state00=state00, state01=state01, state10=state10, state11=state11)
      print("Data saved as %s.npz" %filename)

  # Create a pcolor plot
  plt.suptitle(f"XEB for q{qubits[0]}-q{qubits[1]}, inner-average: {avgs}, random-gates: {random_gates}")
  plt.subplot(241)
  plt.pcolor(np.abs(S1))
  ax = plt.gca()
  ax.set_title('q1 measured')
  # ax.set_xlabel('Circuit depth')
  ax.set_ylabel('Sequences')
  ax.set_xticks(np.array(depths))
  ax.set_yticks(np.arange(1, seqs+1))
  plt.colorbar()

  plt.subplot(242)
  plt.pcolor(np.abs(S2))
  ax = plt.gca()
  ax.set_title('q2 measured')
  # ax.set_xlabel('Circuit depth')
  ax.set_ylabel('Sequences')
  ax.set_xticks(np.array(depths))
  ax.set_yticks(np.arange(1, seqs+1))
  plt.colorbar()

  plt.subplot(245)
  plt.pcolor(I1)
  ax = plt.gca()
  ax.set_title(f'q{qubits[0]}-I')
  ax.set_xlabel('Circuit depth')
  ax.set_ylabel('Sequences')
  ax.set_xticks(np.array(depths))
  ax.set_yticks(np.arange(1, seqs+1))
  plt.colorbar()

  plt.subplot(246)
  plt.pcolor(I2)
  ax = plt.gca()
  ax.set_title(f'q{qubits[1]}-I')
  ax.set_xlabel('Circuit depth')
  ax.set_ylabel('Sequences')
  ax.set_xticks(np.array(depths))
  ax.set_yticks(np.arange(1, seqs+1))
  plt.colorbar()

  plt.subplot(243)
  plt.pcolor(state00)
  ax = plt.gca()
  ax.set_title('state00')
  # ax.set_xlabel('Circuit depth')
  ax.set_ylabel('Sequences')
  ax.set_xticks(np.array(depths))
  ax.set_yticks(np.arange(1, seqs+1))
  plt.colorbar()

  plt.subplot(244)
  plt.pcolor(state11)
  ax = plt.gca()
  ax.set_title('state11')
  # ax.set_xlabel('Circuit depth')
  ax.set_ylabel('Sequences')
  ax.set_xticks(np.array(depths))
  ax.set_yticks(np.arange(1, seqs+1))
  plt.colorbar()

  plt.subplot(247)
  plt.pcolor(state01)
  ax = plt.gca()
  ax.set_title('state01')
  ax.set_xlabel('Circuit depth')
  ax.set_ylabel('Sequences')
  ax.set_xticks(np.array(depths))
  ax.set_yticks(np.arange(1, seqs+1))
  plt.colorbar()

  plt.subplot(248)
  plt.pcolor(state10)
  ax = plt.gca()
  ax.set_title('state10')
  ax.set_xlabel('Circuit depth')
  ax.set_ylabel('Sequences')
  ax.set_xticks(np.array(depths))
  ax.set_yticks(np.arange(1, seqs+1))
  plt.colorbar()

  plt.show()

  
