#!/bin/bash
IMAGE=$1
docker run --rm -it -p 8888:8888 ${IMAGE} zsh -c "jupyter lab --notebook-dir=/home/jovyan --ip=0.0.0.0 --no-browser \
                                                    --allow-root --port=8888 --LabApp.token='' --LabApp.password='' \
                                                    --LabApp.allow_origin='*' --LabApp.base_url=/"