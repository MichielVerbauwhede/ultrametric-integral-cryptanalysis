# Ultrametric integral cryptanalysis
This is supplementary material to the paper *Ultrametric integral cryptanalysis*.

## Setup
To run the code, install a python3.11 virtual environment with the packages listed in `requirements.txt`. Then follow the instructions in `bitarrays` to compile that module. The compilation step requires a c++20 compatible compiler.

The following instructions should correctly setup the environment.
```sh
python3.11 -m venv ultrametric;
source ultrametric/bin/activate;
pip install -r requirements.txt;
cd bitarrays;
less README.md; # follow instructions in this file.
```

To run the code in `Ciphers`, make sure to have activated the virtual environment, which is indicated by `(ultrametric)`. The environment can be activated with `source ultrametric/bin/activate`. Then run the python notebooks in any notebook environment. We personally used `jupyter-lab`, which is installed in the virtual environment.

## Overview
### Example.ipynb
This file contains as simple example and explanation of how ultrametric integral cryptanalysis can be automated.

### bitarrays
This folder contains code that performs operations on bitsets and bitarrays. It was used in *Integral Cryptanalysis Using Algebraic Transition Matrices* to compute ANF matrices and it is a dependency of `LogicOptimisation`.

### Ciphers
Contains the code that generated all the theoretical divisibility bounds presented in the paper. It also contains timing results from a 16-core Intel(R) Xeon(R) Gold 6244 CPU at 3.60GHz.

### Construction
Contains backend code for constructing directed acyclic graph representations of ciphers and using the DAG representation to construct models.

### Experiments
Contains the experiments on 4 and 5 rounds PRESENT that were presented in the paper.

### LogicOptimisation
Contains code to construct minimal CNF representations of truth tables.

### Modelling
Contains code to generate CNF models of simple components as well as methods to evaluate the ultrametric dominant trail approximation in different ways.