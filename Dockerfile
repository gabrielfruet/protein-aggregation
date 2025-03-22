FROM athbaltzis/esmfold:1.1.0

RUN useradd -ms /bin/bash bio

# has to install on bio user
USER bio
RUN python -c 'import esm; esm.pretrained.esmfold_v1()'

# install other dependencies
USER root

COPY requirements.txt .
COPY dev-requirements.txt .

RUN pip install -r requirements.txt 

# final user
USER bio

