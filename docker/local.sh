#!/bin/bash
IMAGE=$1
docker run --rm -it -p 2888:8888 ${IMAGE} 