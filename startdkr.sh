#!/bin/env bash

docker run \
    -i \
    --rm \
    --gpus=all \
    -p 8888:8888 \
    --name=bioinformatics \
    -v /home/fruet/dev/python/bioinformatics:/usr/src/work \
    bioinformatics

