import torch
import esm
import time
from pathlib import Path

base_dir = Path(__file__).parent.parent.resolve()
protein_dir = base_dir/"data/proteins"

model = esm.pretrained.esmfold_v1()
model = model.eval().cuda()

# Optionally, uncomment to set a chunk size for axial attention. This can help reduce memory.
# Lower sizes will have lower memory requirements at the cost of increased speed.
# model.set_chunk_size(128)

sequence = "MKTVRQERLKSIVRILERSKEPVSGAQLAEELSVSRQVIVQDIAYLRSLGYNIVATPRGYVLAGG"
sequence = "GIVEQCCTSICSLYQLENYCNFVNQHLCGSHLVEALYLVCGERGFFYTPKA"
# Multimer prediction can be done with chains separated by ':'

print("Starting timer")
start = time.perf_counter_ns()

with torch.no_grad():
    output = model.infer_pdb(sequence)

end = time.perf_counter_ns()
print("Ending timer")

elapsed_time = (end - start)*1e-9
print("Elapsed time: ",elapsed_time, "seconds")

with open(protein_dir/"predicted_insulin.pdb", "w") as f:
    f.write(output)

import biotite.structure.io as bsio
struct = bsio.load_structure(protein_dir/"predicted_insulin.pdb", extra_fields=["b_factor"])
print(struct.b_factor.mean())  # this will be the pLDDT
