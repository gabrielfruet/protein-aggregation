from src.protein.model import SequenceScorePredictor

def two_step_fitness(sequences: list[str], ga_instance) -> list[float]:
    """
    Compute the fitness function(i.e energy of the folded sequence)      
    on a batch of protein AA.

    The two-step approach is used:
        1. Model predicts the folding structure of the sequence
        2. Score the folded structure
    """
    ssp = SequenceScorePredictor()
    return ssp(sequences)

