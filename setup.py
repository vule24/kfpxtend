import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="easykubeflow",
    version="0.0.4",
    author="Le Tuan Vu",
    author_email="ltnv24@gmail.com",
    description="High level of kubeflow SDK",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=['easykubeflow'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)