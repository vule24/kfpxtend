#!/bin/bash

pip3 install --upgrade keyrings.alt
python3 setup.py sdist bdist_wheel
python3 -m twine upload dist/*