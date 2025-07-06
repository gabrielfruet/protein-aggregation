import logging
from typing import List, Optional

from src.services import esmfold_service, aggrescan_service
from src.protein.index import ProteinIndex
from src.logging.timer import TimerLogger
from src.cli import GeneticAlgorithmConsoleManager
from src.protein.thermostability import ThermostabilityFunction


logger = logging.getLogger(__name__)

class CombinedFitnessPredictor:
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
        """
        Main method to get fitness scores, structured to check for cached results first.
        """
        logger.info(f"STARTING: evaluation of {len(sequences)} sequences")
        
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

        logger.info(f"CACHED: Found {len(sequences) - len(sequences_to_process)} scores in cache.")
        logger.info(f"PROCESSING: {len(sequences_to_process)} new sequences.")

        pdbs_to_process = self._get_or_infer_pdbs(sequences_to_process)
        
        new_scores = self._compute_scores(sequences_to_process, pdbs_to_process)
        
        self._update_results(final_results, sequences_to_process, new_scores)

        return final_results

    def _is_cached(self, sequence: str) -> bool:
        """Checks if a final 'fitness' score is already cached for a sequence."""
        metadata = self.protein_index.get_metadata(sequence)
        return bool(metadata and "fitness" in metadata)

    def _get_cached_score(self, sequence: str) -> Optional[float]:
        """Retrieves the cached 'fitness' score for a sequence."""
        metadata = self.protein_index.get_metadata(sequence)
        return metadata.get("fitness") if metadata else None

    def _get_or_infer_pdbs(self, sequences: List[str]) -> List[str]:
        """
        Gets PDBs for a list of sequences, using cache or inferring via API.
        This now operates only on the subset of sequences needing processing.
        """
        pdbs = []
        unknown_sequences = []

        for seq in sequences:
            if self.protein_index.has_pdb(seq):
                pdbs.append(self.protein_index.get_pdb(seq))
            else:
                unknown_sequences.append(seq)

        logger.info(f"INFERRING: {len(unknown_sequences)} unknown sequences")

        if unknown_sequences:
            with self.cli.spinner(f"[bright_cyan]Inferring {len(unknown_sequences)} folded structures via API"):
                with TimerLogger(logger)(task=f"INFERRING {len(unknown_sequences)} unknown sequences)"):
                    inferred_pdbs = esmfold_service.get_pdbs_from_sequences(unknown_sequences)
                
            self.protein_index.save(inferred_pdbs)
            pdbs.extend(inferred_pdbs)

            logger.info(f"INFERRING: finished {len(unknown_sequences)} folded structure prediction")

        return pdbs
        
    def _compute_scores(self, sequences: List[str], pdbs: List[str]) -> List[float]:
        """
        Computes the fitness for a given list of sequences and their PDBs.
        This method now only runs on non-cached items.
        """
        raw_aggs = [
            aggrescan_service.get_aggregation_score_from_server(pdb) if pdb else None
            for pdb in pdbs
        ]

        valid_aggs = [a for a in raw_aggs if a is not None]
        if valid_aggs:
            a_min, a_max = min(valid_aggs), max(valid_aggs)
            denom = a_max - a_min if (a_max - a_min) > 0 else 1.0
        else:
            a_min, denom = 0.0, 1.0

        final_scores = []
        for seq, agg in zip(sequences, raw_aggs):
            T = self.temberture_scorer(seq)

            if agg is None:
                A_fit = 0.0
            else:
                norm = (agg - a_min) / denom
                inv  = 1.0 - norm
                A_fit = self.agg_weight * inv

            fitness = (self.thermo_weight * T) + A_fit
            final_scores.append(fitness)

            self.protein_index.update_metadata(seq, {
                "fitness": float(fitness),
                "thermostability": float(T),
                "aggregation": float(agg) if agg is not None else None
            })
            #self._update_cache(sequences, final_scores)

        return final_scores

    #def _update_cache(self, sequences: List[str], scores: List[float]) -> None:
    #    for seq, score in zip(sequences, scores):
    #        self.protein_index.update_metadata(seq, {"fitness": {self.scorer.name: score}})


    def _update_results(self, final_results: list, processed_sequences: list, new_scores: list) -> None:
        """Fills in the 'None' placeholders with newly computed scores."""
        score_map = {seq: score for seq, score in zip(processed_sequences, new_scores)}
        
        original_index = 0
        for i in range(len(final_results)):
            if final_results[i] is None:
                sequence_to_find = processed_sequences[original_index]
                final_results[i] = score_map[sequence_to_find]
                original_index += 1