from src.logging.config import config_logging
config_logging()
# start of script

from matplotlib import pyplot as plt

from src.genetic.instance import EnergyMaximizerGA

if __name__ == '__main__':

    emga = EnergyMaximizerGA(
        population_size=64, 
        num_parents_mating=32,
        crossover_type='uniform',
        mutation_type='',
        crossover_probability=0.2,
        mutation_probability = [4/51, 1/51],
    )

    emga.run()


