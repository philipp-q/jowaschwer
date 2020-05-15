import tequila as tq
import numpy as np
import pickle
# import qepsi4

def run(basis_set, geometry, active_orbitals=None):
    molecule = tq.chemistry.Molecule(basis_set=basis_set, geometry=geometry, active_orbitals=active_orbitals)
    
    H = molecule.make_hamiltonian()

    cc2 = molecule.compute_amplitudes("cc2")
    energy_hf = molecule.energies["hf"]
    energy_cc2 = molecule.energies["cc2"]
    energy_mp2 = molecule.compute_energy("mp2")
    energy_ccsd = molecule.compute_energy("ccsd")
    energy_fci = molecule.compute_energy("fci")

    # sort CC2 amplitudes
    tcc2 = dict(sorted(cc2.make_parameter_dictionary().items(), key=lambda x: x[1]))
    print("Sorted CC2 Amplitudes\n", tcc2)
    
    # get the circuit for the HF reference
    U = molecule.prepare_reference()
    
    # create UCCSD circuit with CC2 ordering
    # first form all generators
    generators = {}
    for k,v in tcc2.items():
        if len(k) == 2:
            # spatial in spin indices
            # could combine variables in principle
            idx = [(2*k[0], 2*k[1])]
            aa = molecule.make_excitation_generator(indices=idx)
            generators[tuple(idx)] = aa
            idx = [(2*k[0]+1, 2*k[1]+1)]
            bb = molecule.make_excitation_generator(indices=idx)
            generators[tuple(idx)] = bb
        if len(k) == 4:
            a,i,b,j = k
            idx = [(2*a+1, 2*i+1),(2*b, 2*j)]
            bbaa = molecule.make_excitation_generator(indices=idx)
            generators[tuple(idx)] = bbaa

            if not(a!=b and i!=j):
                idx = [(2 * a, 2 * i), (2 * b + 1, 2 * j + 1)]
                aabb = molecule.make_excitation_generator(indices=idx)
                generators[tuple(idx)] = aabb

            if a!=b and i!=j:
                idx = [(2*k[0], 2*k[1]), (2*k[2], 2*k[3])]
                generator = molecule.make_excitation_generator(indices=idx)
                generators[tuple(idx)] = generator

                idx = [(2*k[0]+1, 2*k[1]+1), (2*k[2]+1, 2*k[3]+1)]
                generator = molecule.make_excitation_generator(indices=idx)
                generators[tuple(idx)] = generator

    # now form the circuit
    for k, v in generators.items():
        U += tq.gates.Trotterized(angles=[tuple(k)], generators=[v], steps=1)
    
    # get the objective
    E = tq.ExpectationValue(H=H, U=U)

    # start with all angles zero
    variables = {k:0.0 for k in E.extract_variables()}

    method="bfgs"
    if len(variables)>20:
        method="cobyla"

    result = tq.optimizer_scipy.minimize(E, method=method, initial_values=variables)
    history = result.history

    # print("Computations Ended:")
    # print("RHF  energy = {:8.5f} ", energy_hf)
    # print("MP2  energy = {:8.5f} ", energy_mp2)
    # print("MP2  energy = {:8.5f} ", energy_cc2)
    # print("CCSD energy = {:8.5f} ", energy_ccsd)
    # print("FCI  energy = {:8.5f} ", energy_fci)
    # print("VQE  energy = {:8.5f} ",  result.energy)

    with open("history.pickle", "wb") as f:
        pickle.dump(result.history, f, pickle.HIGHEST_PROTOCOL)

    baselines = {"HF":energy_hf, "MP2":energy_mp2, "CCSD": energy_ccsd}
    #history.plot("energies", filename="energies.pdf", baselines=baselines)
    #history.plot("gradients", filename="gradients.pdf")
    #history.plot("angles", filename="angles.pdf")

    energies = history.extract_energies()
    #import matplotlib.pyplot as plt
    #plt.figure()
    #plt.yscale("log")
    #plt.plot([-(energy_fci-e) for e in energies.values()], label="|FCI-VQE|", marker="o", linestyle="--")
    #plt.legend()
    #plt.show()

    print({'energies': energies}

    return {"energies": energies}


