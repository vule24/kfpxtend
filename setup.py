import os
import setuptools
from pathlib import Path

with open(os.path.join(os.getcwd(), 'configs/__VERSION__')) as fp:
    __VERSION__ = str(fp.read())

long_description = Path("README.md").read_text()

setuptools.setup(
    name="kfpxtend",
    version=__VERSION__,
    author="Le Tuan Vu",
    author_email="ltnv24@gmail.com",
    description="High level of kubeflow SDK",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=['kfpxtend'],
    install_requires=['kfp'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
