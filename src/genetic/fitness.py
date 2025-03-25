import logging
from typing import Iterable

from src.genetic.mutation import num_to_aa
from src.protein.model import SequenceScorePredictor

logger = logging.getLogger(__name__)


class TwoStepFitness:
    def __call__(self, ga_instance, population: list[list[int]], idxs) -> list[float]:
        """
        Compute the fitness function(i.e energy of the folded sequence)
        on a batch of protein AA.

        The two-step approach is used:
            1. Model predicts the folding structure of the sequence
            2. Score the folded structure
        """
        ssp = SequenceScorePredictor()

        if not isinstance(population, Iterable) or not isinstance(
            population[0], Iterable
        ):
            raise RuntimeError("batch_size should be greater than 1")

        aa_sequences = ["".join(num_to_aa(num_seq)) for num_seq in population]
        return ssp(aa_sequences)
