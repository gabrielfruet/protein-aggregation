import os
import json
from pathlib import Path
from typing import Union, List, Dict, Optional
from Bio.PDB import PDBParser, PPBuilder
import asyncio
import logging

from src.logging.timer import TimerLogger

logger = logging.getLogger(__name__)
timer_logger = TimerLogger(logger, level=logging.INFO)

class ProteinIndex:
    def __init__(self, directory: str = './protein_index'):
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
            self.indices = json.load(f)

    def _infer_sequence_from_pdb_content(self, pdb_content: str) -> str:
        """Infer the amino acid sequence from PDB content using BioPython.
        Args:
            pdb_content (str): PDB file content as a string.
        Returns:
            str: The inferred amino acid sequence.
        """
        parser = PDBParser(QUIET=True)
        from io import StringIO
        structure = parser.get_structure("protein", StringIO(pdb_content))
        ppb = PPBuilder()
        sequences = [str(pp.get_sequence()) for pp in ppb.build_peptides(structure)]
        return "".join(sequences)

    def _generate_pdb_filename(self) -> str:
        """Generate a unique PDB filename incrementally.
        Returns:
            str: Generated filename.
        """
        existing_files = {file.stem for file in self.directory.glob("*.pdb")}
        counter = len(existing_files)
        return f"protein_{counter}"

    def _save_indices(self):
        """Save the indices to the indices.json file."""
        with open(self.indices_file, "w") as f:
            json.dump(self.indices, f, indent=4)

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

    async def async_save(self, pdb_files: Union[str, List[str]], metadata: Optional[Dict] = None):
        """Async wrapper for saving PDB files.
        Args:
            pdb_files (Union[str, List[str]]): PDB content as a string or list of strings.
            metadata (Optional[Dict]): Metadata to associate with the sequence.
        """
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.save, pdb_files, metadata)

    def get_metadata(self, sequence: str) -> Dict[str, Union[str, Dict]]:
        """Retrieve metadata for a given sequence.
        Args:
            sequence (str): Amino acid sequence.
        Returns:
            Dict[str, Union[str, Dict]]: Metadata associated with the sequence.
        """
        return self.indices.get(sequence, None)

    def has_pdb(self, sequence: str) -> bool:
        """Check if sequence has pdb already computed
        Args:
            sequence (str): Amino acid sequence.
        Returns:
            bool: Whether pdb was already computed.
        """
        return sequence in self.indices

    def get_pdb(self, sequence: str) -> str:
        """Retrieve the PDB content as a string for a given sequence.
        Args:
            sequence (str): Amino acid sequence.
        Returns:
            str: PDB content as a string.
        """
        entry = self.indices.get(sequence)
        if not entry:
            raise ValueError(f"Sequence {sequence} not found in the index.")

        pdb_path = self.directory / entry["path"]
        if not pdb_path.exists():
            raise FileNotFoundError(f"PDB file {pdb_path} does not exist.")

        with open(pdb_path, "r") as pdb_file:
            return pdb_file.read()

