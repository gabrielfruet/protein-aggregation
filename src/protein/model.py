import torch
import esm
import logging
from multiprocessing import Pool

from src.protein.index import ProteinIndex
from src.logging.timer import TimerLogger
from src.protein.thermostability import ThermostabilityFunction

scorefxn = None

esmfold_model = None
logger = logging.getLogger(__name__)
timer_logger = TimerLogger(logger)

class SequenceScorePredictor:
    esmfold_model = None
    
    def __init__(self, folder=None, thermostability_function_name='coarse_grained_v1', protein_index=None) -> None:
        if folder is None:
            global esmfold_model
            esmfold_model = esm.pretrained.esmfold_v1()
            esmfold_model.cuda()
            folder = esmfold_model

        self.folder = folder
        self.scorer = ThermostabilityFunction(thermostability_function_name)
        self.protein_index = protein_index if protein_index is not None else ProteinIndex()
        self.function_name = thermostability_function_name

    def __call__(self, sequences: list[str]) -> list[float]:
        logger.info(f"STARTING: evaluation of {len(sequences)} sequence scores")

        result = [None] * len(sequences)
        non_cached_sequences = []
        indices_to_compute = []

        for i, seq in enumerate(sequences):
            metadata = self.protein_index.get_metadata(seq)
            if metadata and "thermostability" in metadata and self.scorer.name in metadata["thermostability"]:
                result[i] = metadata["thermostability"][self.scorer.name]
            else:
                non_cached_sequences.append(seq)
                indices_to_compute.append(i)

        logger.debug(f"CACHED: {len(result) - len(non_cached_sequences)} thermostability scores were cached")
        timer_logger.start(f'evaluation of {len(non_cached_sequences)} SEQUENCE scores')

        known_pdbs = []
        unknown_sequences = []
        for seq in non_cached_sequences:
            if self.protein_index.has_pdb(seq):
                known_pdbs.append(self.protein_index.get_pdb(seq))
            else:
                unknown_sequences.append(seq)

        logger.debug(f"CACHED: {len(known_pdbs)} PDBs were cached for non_cached_sequences")

        new_pdbs = []
        if unknown_sequences:
            with torch.no_grad():
                new_pdbs = self.folder.infer_pdbs(unknown_sequences)
            self.protein_index.save(new_pdbs)

        pdbs_for_scoring = known_pdbs + new_pdbs

        if pdbs_for_scoring:
            with Pool(processes=4) as pool:
                computed_scores = pool.map(self.scorer, pdbs_for_scoring)
        else:
            computed_scores = []

        for idx, score in zip(indices_to_compute, computed_scores):
            result[idx] = score

        for seq, score in zip(non_cached_sequences, computed_scores):

            metadata = {
                "thermostability": {
                    self.scorer.name: score
                }
            }

            self.protein_index.update_metadata(seq, metadata)

        timer_logger.end()

        return result
