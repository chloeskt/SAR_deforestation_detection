#!/bin/bash
DATAFOLDER=$1

echo "using $1 as storage for data"

docker run \
    -v $DATAFOLDER:/data \
    -v $(pwd)/source:/source \
    -v $(pwd)/source/eo_config:/eo_config \
    --rm -it registry.orfeo-toolbox.org/s1-tiling/s1tiling:0.3.2-ubuntu-otb7.4.0 \
    /source/S1Processor.cfg
