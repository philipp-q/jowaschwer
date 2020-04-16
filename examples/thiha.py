import tequila as tq
import numpy

# initialize Hamiltonian from file
with open("thiha.txt", "r") as f:
    string = f.read()

H = tq.QubitHamiltonian.init_from_string(string=string)

# in case you want to diagonalize brut force (works here since its a small system)
eigenValues, eigenVectors = numpy.linalg.eigh(H.to_matrix())
true_wfn = tq.QubitWaveFunction.from_array(eigenVectors[:,0])
print("True Ground State Energy = ", eigenValues[0])
print("True Ground State Wfn    = ", true_wfn)
print("--------------------------\n")

# An example of how to build a circuit and optimize itL Should be replaced by an ansatz that actually can solve the thing
U = tq.gates.Ry(angle="a", target=0)
U += tq.gates.Ry(angle="b", target=1)
U += tq.gates.Ry(angle="c", target=1)
U += tq.gates.Ry(angle="d", target=1)
U += tq.gates.X(target=0, control=1)
U += tq.gates.X(target=1, control=2)
U += tq.gates.X(target=2, control=3)

print("Circuit Ansatz is:")
tq.draw(U)

# build an objective/expectationvalue
E = tq.ExpectationValue(H=H, U=U)

# simulate the wavefunction or the full expectationvalue for a given set of parameters/variables
# Just to play around, not necessary
variables = {"a": 1.0, "b": 2.0, "c": 3.0, "d": 4.0} # just a random example
wfn = tq.simulate(U, variables=variables)
energy = tq.simulate(E, variables=variables)
print("Test ansatz for variables: ", variables)
print("wfn    = ", wfn)
print("energy = ", energy)

# optimize the current ansatz
result = tq.optimizer_scipy.minimize(E, method="bfgs")

# print the results and do some analysis
print("\n------------------------")
print("final energy: ", result.energy)
print("final angles:\n", result.angles)
wfn = tq.simulate(U, variables=result.angles) # wavefunction from the ansatz with optimized angles
print("final wfn: ", )
print("fidelity with true groundstate: ", numpy.abs(wfn.inner(true_wfn))**2)

result.history.plot("energies", filename=None) # need to plot to file when run on orquestra

