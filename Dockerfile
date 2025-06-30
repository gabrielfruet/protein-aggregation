# Use the newer tag to get a modern OS with the correct GLIBC version
FROM python:3.9-slim

RUN useradd -ms /bin/bash bio

# Has to install on bio user
USER bio


# Install other dependencies
USER root

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    python3-dev \
    git \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*


COPY requirements.txt .
COPY dev-requirements.txt .
COPY TemBERTure/ TemBERTure/ 

RUN pip install -r requirements.txt
# Add this line to install your dev dependencies
RUN pip install -r dev-requirements.txt

RUN pip install -r TemBERTure/requirements.txt
# Final user
USER bio