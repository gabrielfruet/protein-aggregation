FROM athbaltzis/esmfold:1.1.0

RUN useradd -ms /bin/bash bio
USER bio

COPY requirements.txt .
RUN pip install -v -r requirements.txt
RUN python -c 'import esm; esm.pretrained.esmfold_v1()'
RUN python -c 'import pyrosetta_installer; pyrosetta_installer.install_pyrosetta()'
