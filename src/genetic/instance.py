from functools import cache, cached_property, lru_cache
import operator
from statistics import mean, stdev
from typing import Iterable
import pygad
import rich
from rich.console import Console
from rich.spinner import Spinner
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn
from rich.layout import Layout
import json
from pathlib import Path
import numpy as np

from src.genetic.fitness import TwoStepFitness, TemBERTureFitness
from src.genetic.mutation import get_aminoacids, aa_to_num, num_to_aa

from src.protein.thermostability.temberture import calculate_temberture_temperature

import logging

logger = logging.getLogger(__name__)

class EnergyMaximizerGA:
    filename="energy_maximizer_instance"
    def __init__(self,
                 directory='./genetic_instances/instance1', 
                 initial = "GIVEQCCTSICSLYQLENYCNFVNQHLCGSHLVEALYLVCGERGFFYTPKA",
                 num_generations=2,
                 num_parents_mating=10,
                 batch_size=16,
                 population_size=20,
                 **kwargs):
        self.dir: Path = Path(directory)
        self.initial = initial
        self.population_size = population_size
        self.base_color = "bright_cyan"
        self.num_generations = num_generations
        self.fitness = TemBERTureFitness()

        from src.cli.ga import GeneticAlgorithmConsoleManager
        self.cli = GeneticAlgorithmConsoleManager()

        self.num_generations = num_generations
        self.kwargs = kwargs

        if not self.dir.exists():
            logger.info(f"Instance directory for EnergyMaximizerGA was not already created at: {str(self.dir)}")
            self.dir.mkdir(parents=True)

        self.ga_instance: pygad.GA = pygad.GA(
            num_generations=num_generations,
            num_parents_mating=num_parents_mating,
            initial_population=self.get_initial_population(),
            fitness_func=self.fitness.__call__,
            fitness_batch_size=batch_size,
            on_generation=self.on_generation,
            gene_space=aa_to_num(get_aminoacids()),
            **kwargs
        )

    def run(self):
        with self.cli(self, total=self.num_generations):
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

        #logger.info("Using the last computed population")
        #return self._get_last_population()
        logger.info("Trying to use the last computed population")
        try:
            last_population = self._get_last_population()
            if not last_population:
                raise ValueError("Last population is empty.")
            logger.info("Successfully loaded last population.")
            return last_population
        except (json.JSONDecodeError, FileNotFoundError, ValueError) as e:
            logger.warning(f"Could not load the last population due to error: {e}. Generating a new population from scratch.")
            try:
                path = self.dir / self._get_last_generation_fname()
                path.unlink()
                logger.info(f"Removed corrupt generation file: {path}")
            except FileNotFoundError:
                pass 
            return self._generate_initial_population(population_size=self.population_size)

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

        filename = self.dir / self._get_generation_fname(generation)

        with self.cli.spinner(f"[bright_green] Saving generation to {filename}"):

            sequence_fitness_pairs = {
                'population':[{"sequence": "".join(num_to_aa(solution)), "fitness": float(fit)} for solution, fit in zip(population, fitness)]
            }

            with open(filename, "w") as file:
                json.dump(sequence_fitness_pairs, file, indent=4)

            logger.info(f"SAVED generation {generation} to file {filename.absolute()}")

        self.cli.update_progress()
        self.cli.metric_after_generation(self)

class GAMetricCalculator:
    def __init__(self, emga: EnergyMaximizerGA):
        self.emga: EnergyMaximizerGA = emga

    def get_generation_population(self, n=-1):
        no_generations = self.emga._generations()

        if n < 0:
            n = no_generations + n + 1

        fpath = self.emga.dir / self.emga._get_generation_fname(n-1)

        with open(fpath, "r") as f:
            generation = json.load(f)

        return generation

    def fitness(self, n=-1) -> Iterable[float]:
        generation = self.get_generation_population(n)
        return map(operator.itemgetter("fitness"),generation["population"])

    def get_best_individual(self, n=-1):
        generation = self.get_generation_population(n)
        population = generation.get("population", [])
        if not population:
            return None
        return max(population, key=operator.itemgetter("fitness"))
    
    def get_worst_individual(self, n=-1):
        generation = self.get_generation_population(n)
        population = generation.get("population", [])
        if not population:
            return None
        return min(population, key=operator.itemgetter("fitness"))


    def best_fitness(self, n=-1):
        return max(self.fitness(n))

    def worst_fitness(self, n=-1):
        return min(self.fitness(n))
    
    def best_melting(self, n=-1):  
        return calculate_temberture_temperature(self.get_best_individual(n)["sequence"])
    
    def worst_melting(self, n=-1):
        return calculate_temberture_temperature(self.get_worst_individual(n)["sequence"])

    def change_in_best_fitness(self):
        return self.best_fitness(-1) - self.best_fitness(-2)

    def change_in_worst_fitness(self):
        return self.worst_fitness(-1) - self.worst_fitness(-2)

    def generation(self):
        return self.emga._generations()

    def mean(self):
        return mean(self.fitness(-1))

    def std(self):
        return stdev(self.fitness(-1))

    def population_size(self):
        return len(self.get_generation_population(-1)["population"])

