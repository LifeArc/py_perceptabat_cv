#!/usr/bin/env python

from setuptools import setup, find_packages

dependencies = []

setup(
    name="py_perceptabat_cv",
    version="1.1",
    url="https://github.com/Lifearc/py_perceptabat_cv",
    license="MIT",
    author="Aretas Gaspariunas",
    author_email="aretas.gaspariunas@lifearc.org, aretasgasp@gmail.com",
    description="Python wrapper for ACD/Percepta Batch with parallel processing support.",
    platforms="Linux",
    zip_safe=False,
    long_description=open("README.md").read(),
    packages=["py_perceptabat_cv"],
    install_requires=dependencies,
    python_requires=">=3.7.2",
    entry_points={"console_scripts": "py_perceptabat_cv = py_perceptabat_cv:main"},
    classifiers=[
        "Development Status :: Beta",
        "Intended Audience :: Developers :: Scientists",
        "Intended Audience :: Science",
        "Operating System :: Linux",
        "Programming Language :: Python :: 3",
        "Topic :: Scientific/Engineering :: chemical descriptors :: chemoinformatics",
    ],
)
