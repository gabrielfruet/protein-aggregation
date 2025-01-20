import numpy as np
import time

if __name__ == '__main__':
    from src.protein.model import SequenceScorePredictor 
    ssp = SequenceScorePredictor()
    sequence = "GIVEQCCTSICSLYQLENYCNFVNQHLCGSHLVEALYLVCGERGFFYTPKA"

    def generate_initial_population(protein, population_size):
        population = []
        for _ in range(population_size):
            protein_array = list(protein)
            mutation_idx = np.random.randint(len(protein_array))
            protein_array[mutation_idx] = np.random.choice(list("ACDEFGHIKLMNPQRSTVWY"))
            aa_seq = ''.join(protein_array)
            population.append(aa_seq)
        return population

    population = generate_initial_population(sequence, 10)
    print('Starting the energy calculation')
    start = time.perf_counter_ns()
    energies = ssp(population)
    print(f'Took {(time.perf_counter_ns() - start)*10e-9:.3f} seconds')

    for energy, sequence in zip(energies, population):
        print(f'For this sequence {sequence=} we have this energy {energy=}')

