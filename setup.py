#!/usr/bin/env python

from setuptools import setup, find_packages

dependencies = []

setup(
    name="py_perceptabat",
    version="1.0",
    url='', #
    license='GNU General Public License v2 (GPLv2)',
    author='Aretas Gaspariunas',
    author_email='aretas.gaspariunas@lifearc.org, aretasgasp@gmail.com',
    description='Python wrapper function for ACD perceptabat_cv with parallel processing support.',
    platforms='Linux, macOS',
    zip_safe=False,
    long_description=open('README.md').read(),
    packages=['py_perceptabat'],
    install_requires=dependencies,
    python_requires='>=3.7.2',
    entry_points={
    'console_scripts':'py_perceptabat = py_perceptabat:main'
    },
    classifiers=[
        'Development Status :: Beta',
        'Intended Audience :: Developers :: Scientists',
        'Intended Audience :: Science',
        'Operating System :: Linux :: macOS',
        'Programming Language :: Python :: 3',
        'Topic :: Scientific/Engineering :: chemical descriptors'
    ]
)
