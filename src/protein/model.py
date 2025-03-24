from functools import cache

from esm.esmfold.v1.pretrained import ESMFold
import torch
import esm
import logging
from rich.progress import Progress, SpinnerColumn, TextColumn
from multiprocessing import Pool
from typing import List, Optional, Dict, Any

from src.protein.index import ProteinIndex
from src.logging.timer import TimerLogger
from src.protein.thermostability import ThermostabilityFunction

logger = logging.getLogger(__name__)

esmfold_v1_model = None

def _load_esmfold_model() -> ESMFold:
    global esmfold_v1_model
    if esmfold_v1_model is None:
        logger.info('Started loading esmfold_v1')
        esmfold_v1_model = esm.pretrained.esmfold_v1().cuda()

        logger.info('Finished loading esmfold_v1')

    return esmfold_v1_model

class SequenceScorePredictor:
    def __init__(
        self,
        folder: Optional[Any] = None,
        thermostability_function_name: str = 'coarse_grained_v1',
        protein_index: Optional[ProteinIndex] = None,
        num_processes: int = 1,
    ) -> None:
        self.model = folder if folder is not None else _load_esmfold_model()
        self.scorer = ThermostabilityFunction(thermostability_function_name)
        self.protein_index = protein_index if protein_index is not None else ProteinIndex()
        self.num_processes = num_processes

    def __call__(self, sequences: List[str]) -> List[float]:
        logger.info(f"STARTING: evaluation of {len(sequences)} sequence scores")
        result = []
        non_cached_sequences = []

        for seq in sequences:
            if self._is_cached(seq):
                result.append(self._get_cached_score(seq))
            else:
                non_cached_sequences.append(seq)
                result.append(None)

        if not non_cached_sequences:
            logger.info("All scores were cached")
            return result


        logger.debug(f"CACHED: {len(sequences) - len(non_cached_sequences)} scores were cached")

        pdbs = self._get_or_infer_pdbs(non_cached_sequences)

        scores = self._compute_scores(pdbs, non_cached_sequences)

        self._update_results(result, non_cached_sequences, scores)

        return result

    def _is_cached(self, sequence: str) -> bool:
        metadata = self.protein_index.get_metadata(sequence)
        return bool(metadata and "thermostability" in metadata and self.scorer.name in metadata["thermostability"])

    def _get_cached_score(self, sequence: str) -> Optional[float]:
        metadata = self.protein_index.get_metadata(sequence)

        if not metadata:
            return None

        return metadata["thermostability"][self.scorer.name]

    def _get_or_infer_pdbs(self, sequences: List[str]) -> List[str]:
        known_pdbs = []
        unknown_sequences = []

        for seq in sequences:
            if self.protein_index.has_pdb(seq):
                known_pdbs.append(self.protein_index.get_pdb(seq))
            else:
                unknown_sequences.append(seq)

        logger.info(f"INFERRING: {len(unknown_sequences)} unknown sequences")

        if unknown_sequences:
            with TimerLogger(logger)(task=f"INFERRING {len(unknown_sequences)} unknown sequences)"):
                with torch.no_grad():
                    inferred = self.model.infer_pdbs(unknown_sequences)

            self.protein_index.save(inferred)
            known_pdbs.extend(inferred)

            logger.info(f"INFERRING: finished {len(unknown_sequences)} folded structure prediction")

        return known_pdbs

    def _compute_scores(self, pdbs: List[str], sequences: List[str]) -> List[float]:
        if not pdbs:
            return []

        logger.info(f"SCORING: {len(pdbs)} unknown sequence scores")

        with TimerLogger(logger)(task=f"SCORING {len(pdbs)} unknown sequence scores"):
            with Pool(self.num_processes) as pool:
                scores = pool.map(self.scorer, pdbs)

        self._update_cache(sequences, scores)

        logger.info(f"SCORING: finished {len(pdbs)} unknown sequence scores")


        return scores

    def _update_cache(self, sequences: List[str], scores: List[float]) -> None:
        for seq, score in zip(sequences, scores):
            self.protein_index.update_metadata(seq, {"thermostability": {self.scorer.name: score}})

    def _update_results(self, result: List[Optional[float]], sequences: List[str], scores: List[float]) -> None:
        for i, (seq, score) in enumerate(zip(sequences, scores)):
            result[sequences.index(seq)] = score
