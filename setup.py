from setuptools import setup, find_packages

dependencies = []

setup(
    name="py_perceptabat_cv",
    version="1.2.2",
    url="https://github.com/Lifearc/py_perceptabat_cv",
    license="BSD",
    author="Aretas Gaspariunas",
    author_email="aretasgasp@gmail.com, aretas.gaspariunas@lifearc.org",
    description="Python wrapper and API for ACD/Percepta Batch with parallel processing support",
    platforms="Linux",
    zip_safe=False,
    long_description="See https://github.com/Lifearc/py_perceptabat_cv for a detailed description.",
    packages=["py_perceptabat_cv"],
    install_requires=dependencies,
    python_requires=">=3.7.2",
    entry_points={"console_scripts": "py_perceptabat_cv = py_perceptabat_cv:main"},
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Topic :: Scientific/Engineering :: Chemistry",
    ],
)
