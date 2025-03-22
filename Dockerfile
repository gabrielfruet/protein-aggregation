FROM athbaltzis/esmfold:1.1.0

RUN useradd -ms /bin/bash bio

# has to install on bio user
USER bio
RUN python -c 'import esm; esm.pretrained.esmfold_v1()'

# install other dependencies
USER root

COPY pyproject.toml .
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# RUN uv pip install --system -r pyproject.toml
RUN uv sync --python-preference only-system --no-dev

# final user
# USER bio

