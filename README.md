# :rocket: py_perceptabat_cv
Python wrapper and API for ACD/Percepta Batch with parallel processing support

## :gem: Features
* Uses the same CLI flags as perceptabat_cv so you can feel right at home. For more information on flags please refer to the official documentation
* Input [file](py_perceptabat_cv/tests/compounds.smi) must have two columns separated by space with no header
* Automatic multithreading support enables to run calculations on multiple cores resulting in faster overall calculation time. Threads are CPU core bound i.e. one thread per a core
* Can be imported in Python as a module
* Results can be written to a CSV file in the same directory as the input file

## :hatching_chick: Dependencies
* perceptabat_cv installed and in ```PATH``` on a Linux machine. Tested with ACD/Percepta Batch version 2018-2019
* No non-standard library package dependencies. Tested with Python 3.7.2

## :wrench: Installation
```
cd py_perceptabat_cv
pip install .
```
or without pip
```
python setup.py install
```
## :computer: Example usage from CLI
```
py_perceptabat_cv -MLOGP -OLOGPALGA -TLOGP -TFNAME<output_filename> <input_filename>
```
## :snake: Example usage in Python
```
from py_perceptabat_cv import py_perceptabat_cv
py_perceptabat_cv("-MLOGP -OLOGPALGA -TLOGP -TFNAME<output_filename> <input_filename>")
```

## :anchor: Limitations
* Input must be Daylight SMILES files and output specified as TXT. Extensions and file formats SDF and RDF are not supported
* Incredibly large input file may take a lot of time to parse or may not work entirely. It is recommended to split it into smaller chunks

## :poop: Disclaimer
py_perceptabat_cv (the package) does not use or include any elements and/or principles ACD/Percepta Batch (the software). This is not an attempt to reverse engineer the software or automate any of its elements except for enabling faster processing using multithreading and parsing output file to convert to a CSV file. The software is provided as is with no charge and/or warranty. The author of the package holds no responsibility for any results and/or outcome due to the package usage and by using the package the user agrees with this disclaimer.
