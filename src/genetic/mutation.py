import numpy as np
from typing import Union

_aminoacids = list('ARNDCEQGHILKMFPSTWYV')

_aminoacids_to_num = {
    aa:i for i, aa in enumerate(_aminoacids)
}

_aminoacids_from_num = {
    i:aa for i, aa in enumerate(_aminoacids)
}

def get_aminoacids() -> list[str]:
    return _aminoacids

def aa_to_num(seq: Union[str, list[str]]) -> list[int]:
    if type(seq) is list:
        for e in seq:
            if len(e) > 1:
                raise ValueError("Sequence should be either a string or an\
                    array of characters. Your sequence has some positions with\
                    more than one characters")

    if type(seq) is str:
        seq = list(seq)

    return [_aminoacids_to_num[residue] for residue in seq]

def num_to_aa(num_seq: list[int] ) -> list[str]:
    return [_aminoacids_from_num[num] for num in num_seq]

def sequence_homology(seq1, seq2):
    matches = sum(1 for a, b in zip(seq1, seq2) if a == b)
    return matches / len(seq1)

def custom_mutation(offspring, ga_instance, initial_protein: str):
    new_offspring = []
    for individual in offspring:
        retries = 0
        while True:
            retries += 1
            mutated = individual.copy()
            mutation_idx = np.random.randint(len(mutated))
            mutated[mutation_idx] = np.random.choice(_aminoacids)  # Random amino acid
            mutated_seq = "".join(mutated)
            if sequence_homology(initial_protein, mutated_seq) >= 0.8:
                new_offspring.append(mutated)
                break
            if retries > 100:
                new_offspring.append(mutated)
                break
    return np.array(new_offspring)
