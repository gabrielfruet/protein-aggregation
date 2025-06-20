from .thermostability_function import ThermostabilityFunction
from TemBERTure.temBERTure import TemBERTure

model_score = TemBERTure(
    adapter_path = '/workspaces/protein-aggregation/TemBERTure/temBERTure_CLS/',
    device = 'cuda',
    batch_size = 1,
    task = 'classification'
)

model_temperature = TemBERTure(
    adapter_path = '/workspaces/protein-aggregation/TemBERTure/temBERTure_TM/replica2/',
    device = 'cuda',
    batch_size = 16,
    task = 'regression'
)

@ThermostabilityFunction.register('temberture_score')
def calculate_temberture_score(sequence: str, **kwargs) -> float:
    """
    Calculate the thermostability score of a sequence using the TemBERTure pre-trained model.
    """
    result = model_score.predict(sequence)
    return result[1] if isinstance(result, (list, tuple)) else result

@ThermostabilityFunction.register('temberture_temperature')
def calculate_temberture_temperature(sequence: str, **kwargs)->float:
    """
    Calculate the thermostability temperature of a sequence using the TemBERTure pre-trained model.
    """
    result = model_temperature.predict(sequence)
    return result[0] if isinstance(result, (list, tuple)) else result