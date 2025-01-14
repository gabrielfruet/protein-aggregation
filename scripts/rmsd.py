from Bio import PDB
import numpy as np
import sys

from pathlib import Path

base_dir = Path(__file__).parent.parent.resolve()
protein_dir = base_dir/"data/proteins"

def calculate_rmsd(pdb1_path, pdb2_path):
    # Parse the structures
    parser = PDB.PDBParser(QUIET=True)
    structure1 = parser.get_structure("ref", pdb1_path)
    structure2 = parser.get_structure("pred", pdb2_path)
    
    # Extract C-alpha atoms
    def get_ca_atoms(structure):
        return [
            atom for atom in structure.get_atoms()
            if atom.get_name() == "CA"
        ]
    
    ca_atoms1 = get_ca_atoms(structure1)
    ca_atoms2 = get_ca_atoms(structure2)
    
    # Ensure the number of C-alpha atoms matches
    if len(ca_atoms1) != len(ca_atoms2):
        raise ValueError("Structures have different numbers of C-alpha atoms.")
    
    # Compute RMSD
    coords1 = np.array([atom.get_coord() for atom in ca_atoms1])
    coords2 = np.array([atom.get_coord() for atom in ca_atoms2])
    diff = coords1 - coords2
    rmsd = np.sqrt(np.mean(np.sum(diff**2, axis=1)))
    
    return rmsd

# Example usage

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python rmsd.py <pdb1> <pdb2>")
    else:
        pdb1 = sys.argv[1]
        pdb2 = sys.argv[2]
        rmsd_value = calculate_rmsd(pdb1, pdb2)
        print(f"RMSD: {rmsd_value:.3f} Å")

