import asyncio
import logging
from typing import List, Optional

from src.services import esmfold_async_service, aggrescan_async_service
from src.protein.index import ProteinIndex
from src.cli import GeneticAlgorithmConsoleManager
from src.protein.thermostability import ThermostabilityFunction

logger = logging.getLogger(__name__)

class CombinedFitnessPredictorAsync:
    def __init__(
        self,
        protein_index: Optional[ProteinIndex] = None,
        thermostability_function_name: str = 'temberture_score',
        thermo_weight: float = 0.6,
        agg_weight: float = 0.4,
    ) -> None:
        self.protein_index = protein_index if protein_index is not None else ProteinIndex()
        self.cli = GeneticAlgorithmConsoleManager()
        self.temberture_scorer = ThermostabilityFunction(thermostability_function_name)
        self.thermo_weight = thermo_weight
        self.agg_weight = agg_weight

    def __call__(self, sequences: List[str]) -> List[float]:
        return asyncio.run(self.calculate_fitness_async(sequences))

    async def calculate_fitness_async(self, sequences: List[str]) -> List[float]:
        """The main async method that orchestrates fetching and scoring."""
        logger.info(f"STARTING ASYNC: evaluation of {len(sequences)} sequences")
        
        final_results = []
        sequences_to_process = []

        with self.cli.spinner("[bright_cyan]Checking for cached fitness scores..."):
            for seq in sequences:
                if self._is_cached(seq):
                    final_results.append(self._get_cached_score(seq))
                else:
                    sequences_to_process.append(seq)
                    final_results.append(None)

        if not sequences_to_process:
            logger.info("All fitness scores were found in cache.")
            return final_results

        pdbs_to_process = await self._get_or_infer_pdbs_async(sequences_to_process)
        new_scores = await self._compute_scores_async(sequences_to_process, pdbs_to_process)
        
        self._update_results(final_results, sequences_to_process, new_scores)
        return final_results

    async def _get_or_infer_pdbs_async(self, sequences: List[str]) -> List[str]:
        """
        Asynchronously gets PDBs, using cache or inferring via API.
        This corrected version handles saving PDBs one by one.
        """
        pdbs = [None] * len(sequences)
        unknown_sequences = []
        seq_map = {}

        for i, seq in enumerate(sequences):
            if self.protein_index.has_pdb(seq):
                pdbs[i] = self.protein_index.get_pdb(seq)
            else:
                unknown_sequences.append(seq)
                seq_map[seq] = i
        
        if unknown_sequences:
            with self.cli.spinner(f"[bright_cyan]Inferring {len(unknown_sequences)} folded structures via API (async)"):
                inferred_pdbs = await esmfold_async_service.get_pdbs_from_sequences_async(unknown_sequences)
                
                for seq, pdb_content in zip(unknown_sequences, inferred_pdbs):
                    original_index = seq_map[seq]
                    pdbs[original_index] = pdb_content
                    
                    if pdb_content:
                        self.protein_index.save(seq, pdb_content)
        return pdbs

    async def _compute_scores_async(self, sequences: List[str], pdbs: List[str]) -> List[float]:
        """Asynchronously computes fitness for a list of sequences and their PDBs."""
        with self.cli.spinner(f"[bright_cyan]Requesting {len(pdbs)} aggregation scores (async)"):
            raw_aggs = await aggrescan_async_service.get_aggregation_scores_in_parallel(pdbs)

        valid_aggs = [a for a in raw_aggs if a is not None]
        a_min, a_max = (min(valid_aggs), max(valid_aggs)) if valid_aggs else (0.0, 1.0)
        denom = a_max - a_min if (a_max - a_min) > 0 else 1.0

        final_scores = []
        for seq, agg in zip(sequences, raw_aggs):
            T = self.temberture_scorer(seq)
            A_fit = (1.0 - (agg - a_min) / denom) * self.agg_weight if agg is not None else 0.0
            fitness = (self.thermo_weight * T) + A_fit
            final_scores.append(fitness)
            
            self.protein_index.update_metadata(seq, {
                "fitness": float(fitness),
                "thermostability": float(T),
                "aggregation": float(agg) if agg is not None else None
            })
        return final_scores

    def _is_cached(self, sequence: str) -> bool:
        metadata = self.protein_index.get_metadata(sequence)
        return bool(metadata and "fitness" in metadata)

    def _get_cached_score(self, sequence: str) -> Optional[float]:
        metadata = self.protein_index.get_metadata(sequence)
        return metadata.get("fitness") if metadata else None
        
    def _update_results(self, final_results: list, processed_sequences: list, new_scores: list) -> None:
        score_map = {seq: score for seq, score in zip(processed_sequences, new_scores)}
        processed_idx = 0
        for i in range(len(final_results)):
            if final_results[i] is None:
                seq = processed_sequences[processed_idx]
                final_results[i] = score_map[seq]
                processed_idx += 1
