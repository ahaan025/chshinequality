import qiskit_ibm_runtime
import qiskit
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as tck
 
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter, QuantumCircuit
from qiskit.quantum_info import SparsePauliOp
from qiskit_ibm_runtime import QiskitRuntimeService
 
# from qiskit_ibm_runtime import EstimatorV2 as Estimator
from qiskit_ibm_runtime import QiskitRuntimeService
from qiskit_aer import Aer
from qiskit.primitives import StatevectorEstimator
from qiskit_aer import StatevectorSimulator
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
 
qiskit.version.get_version_info()
qiskit_ibm_runtime.version.get_version_info()
 
token = "761537a8f6ebedc09fa5123310731dad7a03509dcd31374fea4b9935fdcdfecf373b9153eddc6e3c257e6dca66968fbc5e52e1278aeeecf47d714a05cdf59e18"
 
service = QiskitRuntimeService(channel="ibm_quantum", token=token)
 
print(service.backends())
backendlist = service.backends()
backend = backendlist[2]  # TODO: review
print(backend)
 
theta = Parameter("$\\theta$")
 
chsh_circuit = QuantumCircuit(2)
chsh_circuit.h(0)
chsh_circuit.cx(0, 1)
chsh_circuit.ry(theta, 0)
chsh_circuit.draw(output="mpl", idle_wires=False, style="iqp")
 
number_of_phases = 21
phases = np.linspace(0, 2 * np.pi, number_of_phases)
# Phases need to be expressed as list of lists in order to work
individual_phases = [[ph] for ph in phases]
 
# <CHSH1> = <AB> - <Ab> + <aB> + <ab> -> <ZZ> - <ZX> + <XZ> + <XX>
observable1 = SparsePauliOp.from_list([("ZZ", 1), ("ZX", -1), ("XZ", 1), ("XX", 1)])
 
# <CHSH2> = <AB> + <Ab> - <aB> + <ab> -> <ZZ> + <ZX> - <XZ> + <XX>
observable2 = SparsePauliOp.from_list([("ZZ", 1), ("ZX", 1), ("XZ", -1), ("XX", 1)])
 
# Create a backend
backend = Aer.get_backend("qasm_simulator")
 
# Define the target
target = backend.target
 
# Generate the preset pass manager
pm = generate_preset_pass_manager(target=target, optimization_level=3)
 
# Run the circuit through the pass manager
chsh_isa_circuit = pm.run(chsh_circuit)
 
# Draw the optimized circuit
chsh_isa_circuit.draw(output="mpl", idle_wires=False, style="iqp")
 
isa_observable1 = observable1.apply_layout(layout=chsh_isa_circuit.layout)
isa_observable2 = observable2.apply_layout(layout=chsh_isa_circuit.layout)
 
# Initialize the simulator
simulator = StatevectorSimulator()
 
# Bind parameters before running the circuit
bound_circuits = [chsh_circuit.assign_parameters({theta: phase}) for phase in phases]
 
# Run the circuit
results = [simulator.run(bound_circuit).result() for bound_circuit in bound_circuits]
 
# Get the statevector
statevectors = [result.get_statevector() for result in results]
estimator = StatevectorEstimator()
 
pubs = [
    (
        chsh_isa_circuit,  # ISA circuit
        [[isa_observable1], [isa_observable2]],  # ISA Observables
        individual_phases,  # Parameter values
    )
]
 
job_result = estimator.run(pubs=pubs).result()
 
chsh1_est = job_result[0].data.evs[0]
chsh2_est = job_result[0].data.evs[1]
 
fig, ax = plt.subplots(figsize=(10, 6))
 
# results from hardware
ax.plot(phases / np.pi, chsh1_est, "o-", label="CHSH1", color="#1f77b4", zorder=3)
ax.plot(phases / np.pi, chsh2_est, "o-", label="CHSH2", color="#ff7f0e", zorder=3)
 
# classical bound +-2
ax.axhline(y=2, color="#7f7f7f", linestyle="--", linewidth=2)
ax.axhline(y=-2, color="#7f7f7f", linestyle="--", linewidth=2)
 
# quantum bound, +-2√2
ax.axhline(y=np.sqrt(2) * 2, color="#2ca02c", linestyle="-.", linewidth=2)
ax.axhline(y=-np.sqrt(2) * 2, color="#2ca02c", linestyle="-.", linewidth=2)
ax.fill_between(phases / np.pi, 2, 2 * np.sqrt(2), color="#2ca02c", alpha=0.3)
ax.fill_between(phases / np.pi, -2, -2 * np.sqrt(2), color="#2ca02c", alpha=0.3)
 
# set x tick labels to the unit of pi
ax.xaxis.set_major_formatter(tck.FormatStrFormatter("%g $\\pi$"))
ax.xaxis.set_major_locator(tck.MultipleLocator(base=0.5))
 
# set labels, and legend
plt.xlabel("Theta", fontsize=14)
plt.ylabel("CHSH witness", fontsize=14)
plt.title("Violation of Bell Inequality", fontsize=16)
plt.legend(fontsize=12)
 
# change the background color
ax.set_facecolor("#f0f0f0")
 
# change the grid style
ax.grid(color="#d0d0d0", linestyle="--", linewidth=1)
 
plt.show()