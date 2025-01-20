import numpy as np

aminoacids = ['ARNDCEQGHILKMFPSTWYV']

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
            mutated[mutation_idx] = np.random.choice(aminoacids)  # Random amino acid
            mutated_seq = "".join(mutated)
            if sequence_homology(initial_protein, mutated_seq) >= 0.8:
                new_offspring.append(mutated)
                break
            if retries > 100:
                new_offspring.append(mutated)
                break
    return np.array(new_offspring)
