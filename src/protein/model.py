from pyrosetta import Pose, get_fa_scorefxn
from pyrosetta.rosetta.core.import_pose import pose_from_pdbstring

import torch
import esm
from src.protein.rosetta import rosetta_init

rosetta_init()

def pdb_score(pdb_string: str) -> float:
    pose = Pose()
    pose_from_pdbstring(pose, pdb_string)  
    scorefxn = get_fa_scorefxn()  
    total_score = scorefxn(pose)
    return total_score

esmfold_model = esm.pretrained.esmfold_v1()
esmfold_model.cuda()

class SequenceScorePredictor:
    def __init__(self, folder=esmfold_model, scorer=pdb_score) -> None:
        self.folder = folder
        self.scorer = scorer

    def __call__(self, sequences: list[str]) -> list[float]:
        with torch.no_grad():
            pdbs = self.folder.infer_pdbs(sequences)

        return [self.scorer(pdb) for pdb in pdbs]
