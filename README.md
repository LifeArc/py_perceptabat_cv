# py_perceptabat
Python wrapper function for ACD perceptabat_cv with parallel processing support.

## Description
* Calculates logP, logD, most acidic and basic apparent pKa and sigma using classic, GALAS or consensus algorithms;
* Multithreading support enables to run calculations on multiple cores resulting in decreased calculation time;
* Results are returned as a dictionary and are written to a CSV file.

## Dependencies
* ACD Labs perceptabat_cv installed and in PATH;
* No non-standard lib package dependencies. Tested with Python 3.7.2.

## Example usage
### From CLI
```
py_perceptabat 'input_filepath' 'logD pH' 'number of threads' 'logP algorithm' 'pKa alogrithm' 'logD algorithms'
```
e.g.
```
py_perceptabat <input_filepath> 7.4 4 classic classic classic-classic
```
### Using as a package
```
from py_perceptabat import py_perceptabat
py_perceptabat(smiles_filepath='smiles.smi', logd_ph=7.4, threads=1, logp_algo='classic',
    pka_algo='classic', logd_algo='classic-classic', logp_train=None)
```
### As a standalone file
```
python py_perceptabat.py <input_filepath> 7.4 4 classic classic classic-classic
```

## Arguments
* Set smiles_filepath to specify SMILES input file. The file must have two columns: SMILES and ID separated by a space;
* Set logd_ph to define at which pH logD will be calculated;
* Set threads argument to specify the number of threads for parallelization. Threads are CPU core bound i.e. one thread per a core;
* Set *_algo arguments to specify algorithm for each property prediction. Note that when pka_algo='galas' perceptabat_cv outputs all pKa vlaues for the molecule - this is an expected behaviour of perceptabat_cv;
* LogD predictions use logP and pKa properties; algorithms for both respectively must be provided separated by a dash e.g. classic-galas. Please refer to ACD documentation for more details about algorithms;
* Set logp_train to specify .PCD training file for logP prediction. NOTE training from CLI is currently disabled as the feature has not been properly tested yet.

## Authors
* This script was written by **Aretas Gaspariunas** (aretas.gaspariunas@lifearc.org or aretasgasp@gmail.com). Have a question? You can always ask and I can always ignore.

todo: add pKa and GALAS training support, add Windows support
