import pygad
import json
from pathlib import Path
import numpy as np

from src.genetic.fitness import two_step_fitness
from src.genetic.mutation import get_aminoacids, aa_to_num, num_to_aa

import logging

logger = logging.getLogger(__name__)

class EnergyMaximizerGA:
    filename="energy_maximizer_instance"
    def __init__(self, 
                 directory='./genetic/instance1', 
                 initial = "GIVEQCCTSICSLYQLENYCNFVNQHLCGSHLVEALYLVCGERGFFYTPKA",
                 num_generations=2,
                 num_parents_mating=10,
                 batch_size=16,
                 population_size=20,
                 **kwargs):
        self.dir: Path = Path(directory)
        self.initial = initial
        self.population_size = population_size

        if not self.dir.exists():
            logger.info(f"Instance directory for EnergyMaximizerGA was not already created at: {str(self.dir)}")
            self.dir.mkdir(parents=True)

        self.ga_instance = pygad.GA(
            num_generations=num_generations,
            num_parents_mating=num_parents_mating,
            initial_population=self.get_initial_population(),
            fitness_func=two_step_fitness,
            fitness_batch_size=batch_size,
            on_generation=self.on_generation,
            gene_space=aa_to_num(get_aminoacids()),
            **kwargs
        )

    def run(self):
        self.ga_instance.run()

    def _generate_initial_population(self,population_size: int):
        population = []
        for _ in range(population_size):
            protein_array = list(self.initial)
            mutation_idx = np.random.randint(len(protein_array))
            protein_array[mutation_idx] = np.random.choice(get_aminoacids())
            population.append(aa_to_num(protein_array))
        return np.array(population)

    def _generations(self) -> int:
        return len(list(self.dir.glob("generation_*.json")))

    def _get_last_generation_fname(self) -> str:
        return self._get_generation_fname(self._generations() - 1)

    def _get_last_population(self):
        fname = self._get_last_generation_fname()
        path = self.dir/fname
        with open(path, 'r') as f:
            generation = json.load(f)

        return [aa_to_num(individual['sequence']) for individual in generation['population']]

    def get_initial_population(self):
        if self._generations() == 0:
            logger.info("Generating a population from scratch")
            return self._generate_initial_population(population_size=self.population_size)

        logger.info("Using the last computed population")
        return self._get_last_population()

    def _get_generation_fname(self, generation: int) -> str:
        filename = f"generation_{generation}.json"
        return filename

    def on_generation(self, ga_instance: pygad.GA):
        logger.debug("on_generation called")
        generation = self._generations()

        population = ga_instance.population
        fitness = ga_instance.last_generation_fitness

        if population is None:
            raise RuntimeError("Population is None on pygad.GA instance")

        if fitness is None:
            raise RuntimeError("fitness is None on pygad.GA instance")

        sequence_fitness_pairs = {
            'population':[{"sequence": "".join(num_to_aa(solution)), "fitness": fit} for solution, fit in zip(population, fitness)]
        }

        filename = self.dir / self._get_generation_fname(generation)

        with open(filename, "w") as file:
            json.dump(sequence_fitness_pairs, file, indent=4)

        logger.info(f"SAVED generation {generation} to file {filename.absolute()}")
