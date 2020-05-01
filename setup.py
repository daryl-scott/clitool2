"""build script for setuptools"""
from __future__ import absolute_import
import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="clitool2",
    version="1.1",
    author="Daryl Scott",
    author_email="daryl_scott@live.com",
    description="Create command line interface for one or more functions",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/daryl-scott/clitool2",
    packages=["clitool2"],
    install_requires=["python-dateutil"],
    classifiers=[
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent"
    ],
    python_requires=">=2.7, !=3.0.*, !=3.1.*, !=3.2.*, <4"
)
