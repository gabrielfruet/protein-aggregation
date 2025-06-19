from .thermostability_function import ThermostabilityFunction
from TemBERTure.temBERTure import TemBERTure

model = TemBERTure(
    adapter_path = '/workspaces/protein-aggregation/TemBERTure/temBERTure_CLS/',
    device = 'cuda',
    batch_size = 1,
    task = 'classification'
)

@ThermostabilityFunction.register('temberture')
def calculate_temberture_score(sequence: str, **kwargs) -> float:
    """
    Calculate the thermostability score of a sequence using the TemBERTure pre-trained model.
    """
    result = model.predict(sequence)
    return result[1] if isinstance(result, (list, tuple)) else result