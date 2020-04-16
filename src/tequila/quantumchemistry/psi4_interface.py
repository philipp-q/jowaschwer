from tequila import TequilaException
from openfermion import MolecularData

from tequila.quantumchemistry.qc_base import ParametersQC, QuantumChemistryBase, ClosedShellAmplitudes, Amplitudes

import copy
import numpy
import typing

from dataclasses import dataclass

__HAS_PSI4_PYTHON__ = False
try:
    import psi4

    __HAS_PSI4_PYTHON__ = True
except ModuleNotFoundError:
    __HAS_PSI4_PYTHON__ = False


class TequilaPsi4Exception(TequilaException):
    pass


class OpenVQEEPySCFException(TequilaException):
    pass


@dataclass
class Psi4Results:
    variables: dict = None  # psi4 variables dictionary, storing all computed values
    filename: str = None  # psi4 output file
    wfn: typing.Union[
        psi4.core.Wavefunction, psi4.core.CCWavefunction, psi4.core.CIWavefunction] = None  # psi4 wavefunction
    mol: psi4.core.Molecule = None


class QuantumChemistryPsi4(QuantumChemistryBase):
    @dataclass
    class OrbitalData:
        irrep: str = None
        idx_irrep: int = None
        idx_total: int = None
        energy: float = None

        def __str__(self):
            return "{} : {}{} energy = {:+2.6f} ".format(self.idx_total, self.idx_irrep, self.irrep, self.energy)

    def _make_psi4_active_space_data(self, active_orbitals, reference=None):
        """
        Small helper function
        Internal use only
        Parameters
        ----------
        active_orbitals: dictionary :
            dictionary with irreps as keys and a list of integers as values
            i.e. occ = {"A1":[0,1], "A2":[0]}
            means the occupied active space is made up of spatial orbitals
            0A1, 1A1 and 0A2
            as list: Give a list of spatial orbital indices
            i.e. occ = [0,1,3] means that spatial orbital 0, 1 and 3 are used
        reference: (Default value=None)
            List of orbitals which form the reference
            Can be given in the same format as active_orbitals
            If given as None then the first N_electron/2 orbitals are taken
            and the corresponding active orbitals are removed

        Returns
        -------
        Dataclass with active indices and reference indices (in spatial notation)

        """

        if active_orbitals is None:
            return None

        @dataclass
        class ActiveSpaceData:
            active_orbitals: list  # active orbitals (spatial, c1)
            reference_orbitals: list  # reference orbitals (spatial, c1)
            frozen_docc: list = None  # frozen reference orbitals grouped by irrep (psi4 option, if None then the active space can not be represented by psi4)
            frozen_uocc: list = None  # frozen virtual orbtials grouped by irrep (psi4 option, if None then the active space can not be represented by psi4)

            def __str__(self):
                result = "Active Space Data:\n"
                result += "{key:15} : {value:15} \n".format(key="active_orbitals", value=str(self.active_orbitals))
                result += "{key:15} : {value:15} \n".format(key="reference_orbitals", value=str(self.reference_orbitals))
                result += "{key:15} : {value:15} \n".format(key="frozen_docc", value=str(self.frozen_docc))
                result += "{key:15} : {value:15} \n".format(key="frozen_uocc", value=str(self.frozen_uocc))
                return result


            @property
            def frozen_reference_orbitals(self):
                return [i for i in self.reference_orbitals if i not in self.active_orbitals]

            @property
            def psi4_representable(self):
                return self.frozen_docc is not None and self.frozen_uocc is not None

            @property
            def active_reference_orbitals(self):
                return [i for i in self.reference_orbitals if i in self.active_orbitals]

        # transform irrep notation to absolute ints
        active_idx = active_orbitals
        ref_idx = reference
        if isinstance(active_orbitals, dict):
            active_idx = []
            frozen_uocc = {}
            for key, value in active_orbitals.items():
                active_idx += [self.orbitals_by_irrep[key.upper()][i].idx_total for i in value]
        elif active_orbitals is None:
            active_idx = [i for i in range(self.n_orbitals)]

        standard_ref = sorted([i for i in range(self.n_electrons // 2)])
        if isinstance(reference, dict):
            ref_idx = []
            for key, value in reference.items():
                orbitals = [self.orbitals_by_irrep[key.upper()][i] for i in value]
                ref_idx += [x.idx_total for x in orbitals]
        elif reference is None:
            assert (self.n_electrons % 2 == 0)
            ref_idx = standard_ref

        # determine if the active space can be represented by psi4
        # reference needs to be the scf reference
        # all frozen orbitals need to be without gaps since we can not freeze individual orbitals
        frozen_docc = None
        if ref_idx == standard_ref:
            frozen_docc = [0] * self.nirrep
            frozen_docc_all = [self.orbitals[i] for i in standard_ref if self.orbitals[i].idx_total not in active_idx]
            for i, irrep in enumerate(self.irreps):
                sorted_array = sorted([x.idx_irrep for x in frozen_docc_all if x.irrep.upper() == irrep.upper()])
                frozen_docc[i] = len(sorted_array)
                if len(sorted_array) > 0 and (sorted_array[0] != 0 and sorted_array[-1] != len(sorted_array) - 1):
                    frozen_docc = None
                    print("active space not CAS type: frozen_docc of {} ".format(irrep), sorted_array)
                    break

        # and the same for the unoccupied ones
        frozen_uocc = None
        if frozen_docc is not None:
            frozen_uocc = [0] * self.nirrep
            frozen_uocc_all = [o for o in self.orbitals if o.idx_total not in active_idx + ref_idx]
            for i, irrep in enumerate(self.irreps):
                if irrep not in self.orbitals_by_irrep:
                    continue
                sorted_array = sorted([x.idx_irrep for x in frozen_uocc_all if x.irrep.upper() == irrep.upper()])
                frozen_uocc[i] = len(sorted_array)
                last = self.orbitals_by_irrep[irrep][-1]
                if len(sorted_array) > 0 and (
                        sorted_array[-1] != last.idx_irrep or sorted_array[-1] != sorted_array[0] + len(sorted_array) - 1):
                    frozen_uocc = None
                    break

        return ActiveSpaceData(active_orbitals=sorted(active_idx),
                               reference_orbitals=sorted(ref_idx),
                               frozen_docc=frozen_docc,
                               frozen_uocc=frozen_uocc)

    def __init__(self, parameters: ParametersQC,
                 transformation: typing.Union[str, typing.Callable] = None,
                 active_orbitals=None,
                 reference=None,
                 *args,
                 **kwargs):
        """

        Parameters
        ----------
        parameters
        transformation
        active_orbitals: dictionary :
            dictionary with irreps as keys and a list of integers as values
            i.e. occ = {"A1":[0,1], "A2":[0]}
            means the occupied active space is made up of spatial orbitals
            0A1, 1A1 and 0A2
            as list: Give a list of spatial orbital indices
            i.e. occ = [0,1,3] means that spatial orbital 0, 1 and 3 are used
        reference: (Default value=None)
            List of orbitals which form the reference
            Can be given in the same format as active_orbitals
            If given as None then the first N_electron/2 orbitals are taken
            and the corresponding active orbitals are removed
        args
        kwargs
        """

        self.psi4_mol = psi4.geometry(parameters.get_geometry_string())
        psi4.activate(self.psi4_mol)

        self.energies = {}  # history to avoid recomputation
        self.logs = {}  # store full psi4 output

        self.active_space = None # will be assigned in super
        # active space will be formed later
        super().__init__(parameters=parameters, transformation=transformation, active_orbitals=None, reference=None, *args, **kwargs)
        self.ref_energy = self.molecule.hf_energy
        self.ref_wfn = self.logs['hf'].wfn
        self.irreps = [self.psi4_mol.point_group().char_table().gamma(i).symbol().upper() for i in range(self.nirrep)]

        oenergies = []
        for i in self.irreps:
            oenergies += [(i, j, x) for j, x in enumerate(self.orbital_energies(irrep=i))]

        oenergies = sorted(oenergies, key=lambda x: x[2])
        self.orbitals = [self.OrbitalData(irrep=data[0], idx_irrep=data[1], idx_total=i, energy=data[2]) for i, data in
                         enumerate(oenergies)]
        orbitals_by_irrep = {o.irrep: [] for o in self.orbitals}
        for o in self.orbitals:
            orbitals_by_irrep[o.irrep] += [o]

        self.orbitals_by_irrep = orbitals_by_irrep

        if active_orbitals is not None:
            self.active_space = self._make_psi4_active_space_data(active_orbitals=active_orbitals, reference=reference)
            # need to recompute
            # (psi4 won't take over active space information otherwise)
            self.compute_energy(method="hf", recompute=True)
            self.ref_wfn = self.logs["hf"].wfn

    @property
    def n_orbitals(self) -> int:
        if self.active_space is not None:
            return len(self.active_space.active_orbitals)
        else:
            return super().n_orbitals

    @property
    def point_group(self):
        return self.psi4_mol.point_group().symbol()

    @property
    def nirrep(self):
        return self.ref_wfn.nirrep()

    def orbital_energies(self, irrep: typing.Union[int, str] = None, beta: bool = False, wfn=None):
        """
        Returns orbital energies of a given irrep
        or all orbital energies of all irreps (default)

        Parameters
        ----------
        irrep: int or str :
            int: specify the irrep by number (in cotton ordering)
            str: specify the irrep by name (like 'A1')
            specify from which irrep you want the orbital energies
            psi4 orders irreps in 'Cotton ordering'
            http://www.psicode.org/psi4manual/master/psithonmol.html#table-irrepordering
        beta: bool : (Default value=False)
            get the beta electrons

        Returns
        -------
        list or orbital energies
        """
        if wfn is None:
            wfn = self.ref_wfn

        if hasattr(irrep, "upper"):
            irrep = self.irreps.index(irrep.upper())

        if beta:
            tmp = psi4.driver.p4util.numpy_helper._to_array(self.ref_wfn.epsilon_b(), dense=False)
        else:
            tmp = psi4.driver.p4util.numpy_helper._to_array(self.ref_wfn.epsilon_a(), dense=False)

        if irrep is None:
            result = []
            for x in tmp:
                result += x
            return result
        else:
            return tmp[irrep]

    def make_molecular_hamiltonian(self):
        if self.active_space:
            return self.molecule.get_molecular_hamiltonian(occupied_indices=self.active_space.frozen_reference_orbitals, active_indices=self.active_space.active_orbitals)
        else:
            return self.molecule.get_molecular_hamiltonian()

    def do_make_molecule(self, *args, **kwargs) -> MolecularData:

        energy = self.compute_energy(method="hf", *args, **kwargs)
        wfn = self.logs['hf'].wfn

        molecule = MolecularData(**self.parameters.molecular_data_param)
        if wfn.nirrep() != 1:
            wfn = wfn.c1_deep_copy(wfn.basisset())

        molecule.one_body_integrals = self.compute_one_body_integrals(ref_wfn=wfn)
        molecule.two_body_integrals = self.compute_two_body_integrals(ref_wfn=wfn)
        molecule.hf_energy = energy
        molecule.nuclear_repulsion = wfn.variables()['NUCLEAR REPULSION ENERGY']
        molecule.canonical_orbitals = numpy.asarray(wfn.Ca())
        molecule.overlap_integrals = numpy.asarray(wfn.S())
        molecule.n_orbitals = molecule.canonical_orbitals.shape[0]
        molecule.n_qubits = 2 * molecule.n_orbitals
        molecule.orbital_energies = numpy.asarray(wfn.epsilon_a())
        molecule.fock_matrix = numpy.asarray(wfn.Fa())
        molecule.save()
        return molecule

    def compute_one_body_integrals(self, ref_wfn=None):
        if ref_wfn is None:
            self.compute_energy(method="hf")
            ref_wfn = self.logs['hf'].wfn
        if ref_wfn.nirrep() != 1:
            wfn = ref_wfn.c1_deep_copy(ref_wfn.basisset())
        else:
            wfn = ref_wfn
        Ca = numpy.asarray(wfn.Ca())
        h = wfn.H()
        h = numpy.einsum("xy, yi -> xi", h, Ca, optimize='optimize')
        h = numpy.einsum("xj, xi -> ji", Ca, h, optimize='optimize')
        return h

    def compute_two_body_integrals(self, ref_wfn=None):
        if ref_wfn is None:
            if 'hf' not in self.logs:
                self.compute_energy(method="hf")
            ref_wfn = self.logs['hf'].wfn

        if ref_wfn.nirrep() != 1:
            wfn = ref_wfn.c1_deep_copy(ref_wfn.basisset())
        else:
            wfn = ref_wfn

        mints = psi4.core.MintsHelper(wfn.basisset())

        # Molecular orbitals (coeffs)
        Ca = wfn.Ca()
        h = numpy.asarray(mints.ao_eri())
        h = numpy.einsum("psqr", h, optimize='optimize')  # meet openfermion conventions
        h = numpy.einsum("wxyz, wi -> ixyz", h, Ca, optimize='optimize')
        h = numpy.einsum("wxyz, xi -> wiyz", h, Ca, optimize='optimize')
        h = numpy.einsum("wxyz, yi -> wxiz", h, Ca, optimize='optimize')
        h = numpy.einsum("wxyz, zi -> wxyi", h, Ca, optimize='optimize')
        return h

    def compute_ccsd_amplitudes(self):
        return self.compute_amplitudes(method='ccsd')

    def _run_psi4(self, options: dict, method=None, return_wfn=True, point_group=None, filename: str = None,
                  guess_wfn=None, ref_wfn=None, *args, **kwargs):
        psi4.core.clean()

        if self.active_space and not self.active_space.psi4_representable:
            print("Warning: Active space is not Psi4 representable")

        if "threads" in kwargs:
            psi4.set_num_threads(nthread=kwargs["threads"])

        if filename is None:
            filename = "{}_{}.out".format(self.parameters.filename, method)

        psi4.core.set_output_file(filename)

        # easier guess read in
        if guess_wfn is not None:
            if isinstance(guess_wfn, QuantumChemistryPsi4):
                guess_wfn = guess_wfn.logs["hf"].wfn
            if isinstance(guess_wfn, str):
                guess_wfn = psi4.core.Wavefunction.from_file(guess_wfn)
            guess_wfn.to_file(guess_wfn.get_scratch_filename(180))  # this is necessary
            options["guess"] = "read"

        # prevent known flaws
        if "guess" in options and options["guess"].lower() == "read":
            options["basis_guess"] = False
            # additionally the outputfile needs to be the same
            # as in the previous guess
            # this can not be determined here
            # better pass down a guess_wfn

        mol = psi4.geometry(self.parameters.get_geometry_string())

        if point_group is not None:
            mol.reset_point_group(point_group.lower())

        if ref_wfn is None and hasattr(self, "ref_wfn"):
            ref_wfn = self.ref_wfn

        if point_group is not None and point_group.lower() == "c1":
            ref_wfn = None  # ref_wfn.c1_deep_copy(ref_wfn.basisset())  # CC will not converge otherwise
            guess_wfn = None

        psi4.activate(mol)

        psi4.set_options(options)
        if ref_wfn is None or method.lower() == "hf":
            energy, wfn = psi4.energy(name=method.lower(), return_wfn=return_wfn, molecule=mol)
        else:
            energy, wfn = psi4.energy(name=method.lower(), ref_wfn=ref_wfn, return_wfn=return_wfn, molecule=mol,
                                      guess_wfn=guess_wfn)
        self.energies[method.lower()] = energy
        self.logs[method.lower()] = Psi4Results(filename=filename, variables=copy.deepcopy(psi4.core.variables()),
                                                wfn=wfn, mol=mol)
        return energy, wfn

    def _extract_active_space(self, arr):
        if self.active_space is None:
            return arr

        if isinstance(arr, ClosedShellAmplitudes):
            result = {}
            for k, v in arr.__dict__.items():
                if v is not None:
                    result[k] = self._extract_active_space(arr=v)

            return ClosedShellAmplitudes(**result)

        asd = self.active_space
        aocc = [i for i in asd.active_orbitals if i in asd.reference_orbitals]
        avir = [i for i in asd.active_orbitals if i not in asd.reference_orbitals]
        nocc = self.n_electrons // 2
        nvirt = self.n_orbitals - nocc
        avir = [x - nocc for x in avir]
        nav = len(avir)
        nao = len(aocc)

        arr_shape = arr.shape
        final_shape = []
        active_sets = []
        for i in arr_shape:
            if i == nocc:
                final_shape.append(nao)
                active_sets.append(aocc)
            elif i == nvirt:
                final_shape.append(nav)
                active_sets.append(avir)
            else:
                assert i == nocc + nvirt
                final_shape.append(nao + nav)
                active_sets.append(aocc + avir)

        final_shape = tuple(final_shape)

        def func(*args):
            result = 1
            for i in range(len(args)):
                result *= args[i] in active_sets[i]
            return result

        c = numpy.fromfunction(
            function=numpy.vectorize(func),
            shape=arr_shape, dtype=numpy.int)
        return numpy.extract(condition=c, arr=arr).reshape(final_shape)

    def compute_mp2_amplitudes(self, active_orbitals=None) -> ClosedShellAmplitudes:
        return self._extract_active_space(super().compute_mp2_amplitudes())

    def compute_amplitudes(self, method: str,
                           options: dict = None,
                           filename: str = None,
                           *args,
                           **kwargs) -> typing.Union[
        Amplitudes, ClosedShellAmplitudes]:

        if options is None:
            options = {}

        options['basis'] = self.parameters.basis_set

        if method.lower() == "mp2":
            return self.compute_mp2_amplitudes()
        if __HAS_PSI4_PYTHON__:
            try:
                psi4.core.clean_options()
                psi4.core.clean_variables()
                energy, wfn = self._run_psi4(method=method,
                                             options=options,
                                             point_group='c1',
                                             ref_wfn=self.ref_wfn.c1_deep_copy(self.ref_wfn.basisset()),
                                             filename=filename,
                                             *args,
                                             **kwargs)
                all_amplitudes = wfn.get_amplitudes()
                closed_shell = isinstance(wfn.reference_wavefunction(), psi4.core.RHF)
                if closed_shell:
                    return self._extract_active_space(
                        ClosedShellAmplitudes(**{k: v.to_array() for k, v in all_amplitudes.items()}))
                else:
                    assert (self.active_space is None)  # only for closed-shell currently
                    return Amplitudes(**{k: v.to_array() for k, v in all_amplitudes.items()})
            except Exception as err:
                raise TequilaPsi4Exception("Failed to compute {} amplitudes."
                                           "Make sure you have no orbitals frozen in the psi4 options "
                                           "and that you don't read in previous wavefunctions".format(method))

        else:
            raise TequilaPsi4Exception("Can't find the psi4 python module, let your environment know the path to psi4")

    def compute_energy(self, method: str = "fci", options=None, recompute: bool = True, *args, **kwargs):
        if not recompute and method.lower() in self.energies and not "point_group" in kwargs:
            return self.energies[method.lower()]
        if __HAS_PSI4_PYTHON__:

            if options is None:
                options = {}

            options['basis'] = self.parameters.basis_set
            if self.active_space is not None and self.active_space.psi4_representable:
                options['frozen_docc'] = self.active_space.frozen_docc
                options['frozen_uocc'] = self.active_space.frozen_uocc

            return self._run_psi4(method=method, options=options, *args, **kwargs)[0]
        else:
            raise TequilaPsi4Exception("Can't find the psi4 python module, let your environment know the path to psi4")

    def __str__(self):
        result = super().__str__()
        result += "\nPsi4 Data\n"
        result += "{key:15} : {value:15} \n".format(key="Point Group (full)",
                                                    value=self.psi4_mol.get_full_point_group().lower())
        result += "{key:15} : {value:15} \n".format(key="Point Group (used)", value=self.point_group)
        result += "{key:15} : {value} \n".format(key="nirrep", value=self.nirrep)
        result += "{key:15} : {value} \n".format(key="irreps", value=self.irreps)
        result += "{key:15} : {value:15} \n".format(key="mos per irrep", value=str(
            [len(self.orbital_energies(irrep=i)) for i in range(self.nirrep)]))
        if self.active_space is not None:
            result += str(self.active_space)
        return result

