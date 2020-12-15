#!/bin/bash
IMAGE=$1
docker run --rm -it -p 2888:2888 ${IMAGE} zsh -c "jupyter lab --notebook-dir=/home/jovyan --ip=0.0.0.0 --no-browser \
                                                    --allow-root --port=2888 --LabApp.token='' --LabApp.password='' \
                                                    --LabApp.allow_origin='*' --LabApp.base_url=/"