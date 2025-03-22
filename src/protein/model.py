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
    def __init__(self, folder=None, thermostability_function_name='coarse_grained_v1',protein_index=None) -> None:
        if folder is None:
            global esmfold_model
            esmfold_model = esm.pretrained.esmfold_v1()
            esmfold_model.cuda()
            folder = esmfold_model

        self.folder = folder
        self.scorer = ThermostabilityFunction(thermostability_function_name)
        self.protein_index = protein_index if protein_index is not None else ProteinIndex()

    def __call__(self, sequences: list[str]) -> list[float]:
        logger.info(f"STARTING: evaluation of {len(sequences)} sequence scores")

        known_pdbs_idxs = [0] * len(sequences)
        known_pdbs = []
        unknown_sequences = []
        for i,seq in enumerate(sequences):
            if self.protein_index.has_pdb(seq):
                known_pdbs_idxs[i] = 1
                known_pdbs.append(self.protein_index.get_pdb(seq))
            else:
                unknown_sequences.append(seq)

        logger.debug(f"CACHED: {sum(known_pdbs_idxs)} folded structures were cached")
        timer_logger.start(f'evaluation of {len(sequences) - sum(known_pdbs_idxs)} SEQUENCE scores')

        new_pdbs = []

        if not all(known_pdbs_idxs):
            with torch.no_grad():
                new_pdbs = self.folder.infer_pdbs(unknown_sequences)

            self.protein_index.save(new_pdbs)

        pdbs = [
            known_pdbs.pop(0) if known else new_pdbs.pop(0) \
            for known in known_pdbs_idxs
        ]

        timer_logger.start(f'evaluation of {len(sequences)} FOLDED structure scores', timer='folded')

        with Pool(processes=4) as pool:
            result = pool.map(self.scorer, pdbs)

        timer_logger.end('folded')

        timer_logger.end()

        return result
