# py_perceptabat_cv
Python wrapper for ACD/Percepta Batch with parallel processing support.

## Description
* Uses the same CLI flags as perceptabat_cv so you can feel right at home. For more information on flags please refer to official documentation;
* Input file must have two columns separated by space with no header: SMILES compound ID;
* Automatic multithreading support enables to run calculations on multiple cores resulting in faster overall calculation time. Threads are CPU core bound i.e. one thread per a core;
* Results are written to a CSV file in the same directory as the input file.

## Dependencies
* perceptabat_cv installed and in PATH on a Linux machine. Tested with ACD/Percepta Batch version 2018;
* No non-standard library package dependencies. Tested with Python 3.7.2.

## Example usage
### Installing as a command line tool
```
cd py_perceptabat_cv
pip install .
```
or without pip
```
python setup.py install
```
#### 1. Example usage from CLI
```
py_perceptabat_cv -MLOGP -OLOGPALGA -TLOGP -TFNAME<output_filename> <input_filename>
```
#### 2. Example usage within Python
```
from py_perceptabat_cv import py_perceptabat_cv
py_perceptabat_cv("-MLOGP -OLOGPALGA -TLOGP -TFNAME<output_filename> <input_filename>")
```

## Limitations
* Input file must be Daylight SMILES files and output .TXT. Extensions .SDF and .RDF file formats are not supported;
* Incredibly large input file may take a lot of time to parse or may not work entirely. It is recommended to split it into smaller chunks.

## Authors
This script was written by **Aretas Gaspariunas** (aretas.gaspariunas@lifearc.org or aretasgasp@gmail.com). Have a question? You can always ask and I can always ignore.

## Disclaimer
py_perceptabat_cv (the package) does not use or include any elements and/or principles ACD/Percepta Batch (the software). This is not an attempt to reverese engineer the software or automate any of its elements except for enabling faster processing using multithreading and parsing output file to convert to a CSV file. The software is provided as is with no charge and/or warranty. The author of the package holds no responsibility for any results and/or outcome due to the package usage and by using the package the user agrees with this disclaimer.
