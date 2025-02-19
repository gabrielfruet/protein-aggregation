from src.logging.config import config_logging
config_logging()
# start of script


if __name__ == '__main__':
    from src.genetic.instance import EnergyMaximizerGA

    emga = EnergyMaximizerGA(
        population_size=64, 
        num_parents_mating=32,
        crossover_type='uniform',
        mutation_type='random',
        crossover_probability=0.2,
        mutation_probability = 1/51,
    )

    emga.run()


