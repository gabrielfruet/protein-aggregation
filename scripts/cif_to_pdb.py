from Bio import PDB
import sys

def convert_cif_to_pdb(input_cif, output_pdb):
    """
    Convert a .cif file to .pdb using BioPython.

    Parameters:
    input_cif (str): Path to the input .cif file.
    output_pdb (str): Path to the output .pdb file.
    """
    try:
        # Initialize the parser for CIF files
        parser = PDB.MMCIFParser(QUIET=True)
        
        # Parse the structure
        structure = parser.get_structure("structure", input_cif)
        
        # Initialize the PDBIO writer
        io = PDB.PDBIO()
        io.set_structure(structure)
        
        # Write to the output PDB file
        io.save(output_pdb)
        print(f"Conversion successful: {input_cif} → {output_pdb}")
    except Exception as e:
        print(f"Error during conversion: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python cif_to_pdb_converter.py <input_cif> <output_pdb>")
    else:
        input_cif = sys.argv[1]
        output_pdb = sys.argv[2]
        convert_cif_to_pdb(input_cif, output_pdb)

