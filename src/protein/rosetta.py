import pyrosetta

IS_ROSETTA_INITIALIZED=False

def rosetta_init():
    global IS_ROSETTA_INITIALIZED

    if not IS_ROSETTA_INITIALIZED:
        pyrosetta.init()
        IS_ROSETTA_INITIALIZED=True
