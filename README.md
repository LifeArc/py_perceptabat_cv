# py_perceptabat_cv
Python wrapper and API for ACD/Percepta Batch with parallel processing support.

## :gem: Features
* Automatic multithreading support enables to run calculations on multiple cores resulting in faster overall calculation time. Threads are CPU core bound i.e. one thread per a core.
* Can be imported in Python as a module or called from CLI.
* Results can be written to a CSV file.
* Use the same CLI options as with ```perceptabat_cv``` so you can feel right at home. For more information on flags please refer to the official documentation.
* Input [file](py_perceptabat_cv/tests/compounds.smi) must have two columns separated by a space with no header.

## :hatching_chick: Dependencies
* ```perceptabat_cv``` installed and in ```PATH``` on a Linux machine. Tested with [ACD/Percepta Batch](https://www.acdlabs.com/products/percepta/index.php) version 2018-2019.
* No non-standard library package dependencies - just modern Python. Tested with Python >=3.7.2.

## :wrench: Installation
```
cd py_perceptabat_cv
pip install .
```

## :computer: Example usage from CLI
```
py_perceptabat_cv -MLOGP -OLOGPALGA -TLOGP -TFNAME<output_filename> <input_filename>
```
## :snake: Example usage in Python
```
from py_perceptabat_cv import py_perceptabat_cv
results = py_perceptabat_cv("-MLOGP -OLOGPALGA -TLOGP -TFNAME<output_filename> <input_filename>")
```
or with Python API
```
from py_perceptabat_cv import perceptabat_api
d = {"benzene": "c1ccccc1"}
results = perceptabat_api(d)
```

## :checkered_flag: Benchmark
Computer used for this benchmark:

* OS: Linux CentOS 7.7.1908
* Hardware: Intel(R) Xeon(R) Platinum 8168 CPU @ 2.70GHz - 4 cores

With a conventional 4 core processor a 10000 compounds are processed in **50.25** seconds with ```py_perceptabat_cv``` vs **126.17** seconds with ```perceptabat_cv```.

## :anchor: Limitations
* Input files must contain Daylight SMILES and output must be specified as TXT. Extensions and file formats SDF and RDF are not supported.
* Incredibly large input files may take a lot of time to parse or may not work entirely. It is recommended to split it into smaller chunks.
* Python API does not support all available options for ```perceptabat_cv```. Please use ```py_perceptabat_cv()``` instead for access to all the options.

## :pencil2: Authors
Written by **Aretas Gaspariunas**. Have a question? You can always ask and I can always ignore.

## :apple: Citing
If you found py_perceptabat_cv useful for your work please acknowledge it by citing this repository.

## License
BSD license.

## :poop: Disclaimer
py_perceptabat_cv (the package) does not use or include any elements and/or principles ACD/Percepta Batch (the software).
This is not an attempt to reverse engineer the software or automate any of its elements except and only for enabling faster calculation time and parsing of the output file.
The software is provided as is with no charge and/or warranty. The author of the package holds no responsibility for any results and/or outcome due to the package usage and by using the package the user agrees with this disclaimer.
