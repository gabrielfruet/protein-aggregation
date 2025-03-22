import mdtraj as md
import tempfile
import numpy as np
from .thermostability_function import ThermostabilityFunction
from .tmp_pdb import receive_pdb_content_instead_of_path

@ThermostabilityFunction.register('coarse_grained_v1')
@receive_pdb_content_instead_of_path
def calculate_thermostability_score(pdb_path, weights=None):
    """
    Calculate a composite thermostability score using coarse-grained structural metrics.

    Args:
        pdb_path (str): Path to PDB file
        weights (dict): Dictionary of weights for each metric

    Returns:
        float: Composite stability score (higher = more stable)
    """
    default_weights = {
        'hydrophobic_sasa': -0.4,  # Lower exposed hydrophobics is better
        'salt_bridges': 1.2,       # More salt bridges is better
        'packing_density': 0.7,    # Tighter packing is better
        'contact_order': -0.3      # Lower contact order is better
    }
    weights = weights or default_weights

    traj = md.load(pdb_path)
    traj = traj.atom_slice(traj.topology.select("protein"))

    # 1. Hydrophobic Solvent Accessible Surface Area
    hydrophobic_residues = ['ALA', 'VAL', 'ILE', 'LEU', 'MET', 'PHE', 'TRP']
    sasa = md.shrake_rupley(traj, mode='residue')[0]
    hydrophobic_mask = [res.name in hydrophobic_residues for res in traj.topology.residues]
    h_sasa = np.sum(sasa[hydrophobic_mask])

    # 2. Salt Bridge Count (acidic-basic residue pairs within 4Å)
    acidic = traj.topology.select("(resname ASP or resname GLU) and element != 'H'")
    basic = traj.topology.select("(resname LYS or resname ARG) and element != 'H'")
    pairs = md.compute_neighbors(traj, 0.4, acidic, basic)[0]
    salt_bridges = set()
    for atom in pairs:
        if atom in acidic:
            acidic_res = traj.topology.atom(atom).residue
            for neighbor in md.compute_neighbors(traj, 0.4, [atom], basic)[0]:
                basic_res = traj.topology.atom(neighbor).residue
                salt_bridges.add((acidic_res, basic_res))
        elif atom in basic:
            basic_res = traj.topology.atom(atom).residue
            for neighbor in md.compute_neighbors(traj, 0.4, [atom], acidic)[0]:
                acidic_res = traj.topology.atom(neighbor).residue
                salt_bridges.add((acidic_res, basic_res))

    salt_bridges = len(salt_bridges)
    # 3. Packing Density (residues within 4.5Å)
    neighbor_list = md.compute_neighborlist(traj, 0.45)
    packing_scores = []
    for residue in traj.topology.residues:
        res_atoms = [a.index for a in residue.atoms]
        neighbors = set()
        for atom in res_atoms:
            neighbors.update(neighbor_list[atom])
        neighbor_res = {traj.topology.atom(a).residue for a in neighbors}
        packing_scores.append(len(neighbor_res - {residue}))
    packing_density = np.mean(packing_scores)

    # 4. Contact Order (normalized by chain length)
    ca_indices = traj.topology.select("name CA")
    n_ca = len(ca_indices)
    distances = md.compute_distances(traj, [[i,j] for i in ca_indices 
                                     for j in ca_indices if j > i])
    contacts = [d < 0.6 for d in distances[0]]  # 6Å cutoff

    sequence_seps = []
    contact_idx = 0
    for i in range(n_ca):
        for j in range(i + 1, n_ca):
            if contacts[contact_idx]:
                res_i = traj.topology.atom(ca_indices[i]).residue
                res_j = traj.topology.atom(ca_indices[j]).residue
                sep = abs(res_i.index - res_j.index)
                sequence_seps.append(sep)
            contact_idx += 1

    contact_order = np.mean(sequence_seps)/traj.n_residues if sequence_seps else 0
    # Calculate composite score
    score = (weights['hydrophobic_sasa'] * h_sasa +
        weights['salt_bridges'] * salt_bridges +
        weights['packing_density'] * packing_density +
        weights['contact_order'] * contact_order)

    return score
