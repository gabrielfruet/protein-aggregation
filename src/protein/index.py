import os
import json
from pathlib import Path
from typing import Any, Union, List, Dict, Optional
from Bio.PDB import PDBParser, PPBuilder
import re
from io import StringIO
import asyncio
import logging

from PIL.Image import tempfile

from src.logging.timer import TimerLogger

logger = logging.getLogger(__name__)
timer_logger = TimerLogger(logger, level=logging.INFO)

class ProteinIndex:
    def __init__(self, directory: str = './protein_index2'):
        """Initialize the ProteinIndex class.
        Args:
            directory (str): Path to the protein index directory.
        """
        self.directory = Path(directory)
        self.indices_file = self.directory / "indices.json"

        if not self.directory.exists():
            logger.warning(f"Directory {self.directory} does not exist.")
            os.makedirs(self.directory)

        if not self.indices_file.exists():
            with open(self.indices_file, "w") as f:
                json.dump({}, f, indent=4)

        with open(self.indices_file, "r") as f:
            self.indices: Dict[str, Any] = json.load(f)


    def _infer_sequence_from_pdb_content(self, pdb_content: str) -> str:
        """Infer the amino acid sequence from PDB content using BioPython.
        Args:
            pdb_content (str): PDB file content as a string.
        Returns:
            str: The inferred amino acid sequence.
        """
        try:
            parser = PDBParser(QUIET=True)
            structure = parser.get_structure("protein", StringIO(pdb_content))
            ppb = PPBuilder()
            sequences = [str(pp.get_sequence()) for pp in ppb.build_peptides(structure)]
            return "".join(sequences)

        except Exception as e:
            raise ValueError(f"Error parsing PDB content: {str(e)}") from e

    def _generate_pdb_filename(self) -> str:
        """Generate a unique PDB filename based on the highest existing number using regex.

        Returns:
            str: Generated filename.
        """
        next_number = len(self.indices.keys()) + 1
        return f"protein_{next_number}.pdb"


    def _save_indices(self):
        """Save the indices to the indices.json file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            json.dump(self.indices, temp_file, indent=4)
            temp_file.close()
            os.replace(temp_file.name, self.indices_file)

    def save(self, pdb_files: Union[str, List[str]], metadata: Optional[Dict] = None):
        """Save a PDB content or multiple PDB contents to the index.
        Args:
            pdb_files (Union[str, List[str]]): PDB content as a string or list of strings.
            metadata (Optional[Dict]): Metadata to associate with the sequence.
        """
        if isinstance(pdb_files, str):
            pdb_files = [pdb_files]

        timer_logger.start(task=f'SAVING {len(pdb_files)} pdbs to index' )

        for pdb_content in pdb_files:
            sequence = self._infer_sequence_from_pdb_content(pdb_content)

            if sequence in self.indices:
                logger.debug(f"ALREADY CACHED {sequence=} on index")
                continue  # Skip if the sequence already exists

            new_filename = self._generate_pdb_filename()
            destination = self.directory / f"{new_filename}.pdb"

            with open(destination, "w") as pdb_file:
                pdb_file.write(pdb_content)

            logger.debug(f"SAVING {sequence=} index")

            self.indices[sequence] = {
                "path": str(destination.relative_to(self.directory)),
                "metadata": metadata or {}
            }

        self._save_indices()
        timer_logger.end()


    def get_metadata(self, sequence: str) -> Optional[Dict[str, Any]]:
        """Retrieve metadata for a given sequence.
        Args:
            sequence (str): Amino acid sequence.
        Returns:
            Metadata associated with the sequence.
        """
        return self.indices.get(sequence)


    def has_pdb(self, sequence: str) -> bool:
        """Check if sequence has pdb already computed
        Args:
            sequence (str): Amino acid sequence.
        Returns:
            bool: Whether pdb was already computed.
        """
        return sequence in self.indices

    def update_metadata(self, sequence: str, metadata: Dict[str, Any]):
        """Set or update metadata for a given sequence.
        Args:
            sequence (str): Amino acid sequence.
            metadata (Dict[str, Any]): Metadata to associate with the sequence.
        Raises:
            ValueError: If the sequence is not found in the index.
        """
        if sequence not in self.indices:
            raise ValueError(f"Sequence {sequence} not found in the index.")

        self.indices[sequence]["metadata"].update(metadata)

        self._save_indices()

    def get_pdb(self, sequence: str) -> str:
        """Retrieve the PDB content as a string for a given sequence.
        Args:
            sequence (str): Amino acid sequence.
        Returns:
            str: PDB content as a string.
        Raises:
            ValueError: If the sequence is not found in the index.
            FileNotFoundError: If the PDB file does not exist.
        """
        entry = self.indices.get(sequence)
        if not entry:
            raise ValueError(f"Sequence {sequence} not found in the index.")

        pdb_path = self.directory / entry["path"]
        if not pdb_path.exists():

            self.indices.pop(sequence)
            self._save_indices()

            raise FileNotFoundError(f"PDB file {pdb_path} does not exist.")

        with open(pdb_path, "r") as pdb_file:
            return pdb_file.read()

