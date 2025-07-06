from typing import Iterable, List
#from src.protein.model import SequenceScorePredictor
from src.genetic.mutation import num_to_aa
from src.protein.thermostability.temberture import calculate_temberture_score
from src.protein.index import ProteinIndex
import logging
from src.protein.predictor import CombinedFitnessPredictor 
from src.protein.predictor_async import CombinedFitnessPredictorAsync
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
        try:
            from src.protein.model import SequenceScorePredictor
        except ImportError as e:
            raise RuntimeError("ESMFold dependencies not available") from e
        ssp = SequenceScorePredictor()

        if not isinstance(population, Iterable) or not isinstance(population[0], Iterable):
            raise RuntimeError("batch_size should be greater than 1")

        aa_sequences = ["".join(num_to_aa(num_seq)) for num_seq in population]
        return ssp(aa_sequences)

class TemBERTureFitness:
    def __call__(self, ga_instance, population: list[list[int]], idxs) -> list[float]:
        """
        Compute the fitness function using TemBERTure directly on amino acid sequences.
        """
        if not isinstance(population, Iterable) or not isinstance(population[0], Iterable):
            raise RuntimeError("batch_size should be greater than 1")

        aa_sequences = ["".join(num_to_aa(num_seq)) for num_seq in population]
        
        return [calculate_temberture_score(seq) for seq in aa_sequences]
        
class CombinedFitness:
    def __init__(self, protein_index: ProteinIndex):
        self.protein_index = protein_index
        self.predictor = CombinedFitnessPredictor(protein_index=self.protein_index)

    def __call__(self, ga_instance, population: List[List[int]], solution_indices) -> List[float]:
        """
        Computes the fitness score for an entire population (batch).

        This method matches the signature required by PyGAD's batch fitness mode.
        """
        aa_sequences = ["".join(num_to_aa(num_seq)) for num_seq in population]

        fitness_scores = self.predictor(aa_sequences)

        return fitness_scores

class CombinedFitnessAsync:
    """
    This class wraps the asynchronous fitness predictor to be used with PyGAD.
    """
    def __init__(self, protein_index: ProteinIndex):
        self.protein_index = protein_index
        self.predictor = CombinedFitnessPredictorAsync(protein_index=self.protein_index)

    def __call__(self, ga_instance, population: List[List[int]], solution_indices) -> List[float]:
        """
        Computes the fitness score for an entire population (batch).
        This method is called by PyGAD.
        """
        aa_sequences = ["".join(num_to_aa(num_seq)) for num_seq in population]
        fitness_scores = self.predictor(aa_sequences)
        return fitness_scores