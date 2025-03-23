import os
import json
from pathlib import Path
import tempfile
from typing import IO, Any, Callable, Union, List, Dict, Optional
from Bio.PDB import PDBParser, PPBuilder
import uuid
import re
from io import StringIO
import asyncio
import logging

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

            logger.info(f"Creating directory {self.directory}")

        if not self.indices_file.exists():
            self._write_file_safely(self.indices_file, lambda f: json.dump({}, f, indent=4))

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

    def _generate_pdb_destination(self) -> Path:
        """
        Generate a pdb file name using uuid4

        Returns:
            str: Generated filename.
        """
        destination: Optional[Path] = None

        while destination is None or destination.exists():
            new_filename = f"protein_{uuid.uuid4()}.pdb"
            destination = self.directory / new_filename

        return destination

    def _write_file_safely(
        self,
        destination: Path,
        writer_func: Callable[[IO], Any],
    ):
        """Write content to a file safely using a temporary file pattern.

        Args:
            content: The content to write (can be string, dict, or list)
            directory: The target directory
            filename: The target filename
            writer_func: A function that takes a file object and writes the content

        Returns:
            The path of the written file

        Raises:
            RuntimeError: If writing fails
        """
        try:
            with tempfile.NamedTemporaryFile(mode="w", dir=self.directory, delete=False) as tmp:
                writer_func(tmp)
                Path(tmp.name).rename(destination)

                return destination
        except IOError as e:
            logger.error(f"Failed to write file {destination}: {e}")
            raise RuntimeError(f"Failed to write file {destination}") from e


    def _save_indices(self):
        """Save the indices to the indices.json file."""
        self._write_file_safely(self.indices_file, lambda f: json.dump(self.indices, f, indent=4))

    def _write_pdb(self, pdb_content: str) -> Path:
        """
        Writes the given PDB content to a file and returns the path of the destination file.

        Args:
            pdb_content (str): The PDB content to be written to the file.

        Returns:
            Path: The path of the destination file where the PDB content was written.
        """
        destination = self._generate_pdb_destination()

        self._write_file_safely(destination, lambda f: f.write(pdb_content))

        return destination


    def _save_pdb(self, pdb_content, metadata):
        """
        Saves a PDB file to a destination and updates the indices with the sequence and file metadata.

        Args:
            pdb_content (str): The content of the PDB file to be saved.
            metadata (dict, optional): Additional metadata to be stored with the PDB file. Defaults to an empty dictionary.

        Returns:
            Path: The path to the saved PDB file.

        Raises:
            ValueError: If the sequence cannot be inferred from the PDB content.
            RuntimeError: If the PDB file cannot be saved to the destination.
        """
        try:
            sequence = self._infer_sequence_from_pdb_content(pdb_content)
        except Exception as e:
            logger.error(f"Failed to infer sequence from PDB content: {e}")
            raise ValueError("Could not infer sequence from PDB content") from e

        if sequence in self.indices:
            logger.debug(f"ALREADY CACHED {sequence=} on index")
            return

        logger.debug(f"SAVING {sequence=} index")
        destination = self._write_pdb(pdb_content)

        self.indices[sequence] = {
            "path": str(destination.relative_to(self.directory)),
            "metadata": metadata or {}
        }

        return destination

    def save(self, pdb_files: Union[str, List[str]], metadata: Optional[Dict] = None):
        """Save a PDB content or multiple PDB contents to the index.
        Args:
            pdb_files (Union[str, List[str]]): PDB content as a string or list of strings.
            metadata (Optional[Dict]): Metadata to associate with the sequence.
        """
        if isinstance(pdb_files, str):
            pdb_files = [pdb_files]

        timer_logger.start(task=f'SAVING {len(pdb_files)} pdbs to index' )

        try:
            for pdb_content in pdb_files:
                self._save_pdb(pdb_content, metadata)
        except Exception as e:
            raise RuntimeError("Failed to save PDB files to index") from e
        finally:
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

