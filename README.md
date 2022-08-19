# ORKG-NLP Service Template

In case you would like to develop an NLP service, integrate it to
[``orkgnlp``](https://gitlab.com/TIBHannover/orkg/nlp/orkg-nlp-pypi) and automate/maintain
its retraining, you should probably follow our guidelines. We provide here a template for
a repository hosting an ORKG-NLP service with some set of instructions. Please also consider our
[integration requirements](https://orkg-nlp-pypi.readthedocs.io/en/latest/contribute.html#integration-requirements)
before starting your implementation! 

## Repository Structure
We recommend to have the following file structure as it seems generic to any NLP/ML service. 
Indeed, you also can change the naming/structure to fit your specific task. Most importantly is
the file ``main.py`` that is responsible for running all scripts in the repository in the correct order.
Please also consider to implement the script ``predict.py`` which is responsible for executing the 
model as an End-to-End service with input and output from an end-user perspective!


```commandline
.
└── orkg_nlp_service_template           <- root directory of the repository
    ├── data
    │   ├── processed             <- contains the processed data
    │   └── raw                   <- contains the raw data
    ├── models                          <- contains the trained/used models
    ├── notebooks                       <- contains the notebooks used
    ├── README.md                       <- README file for documenting the service.
    ├── requirements.txt                <- contains python requirements listed with specifying the versions
    └── src
        ├── data                        <- contains python scripts for interacting with the dataset
        │   ├── __init__.py
        │   └── make_dataset.py
        ├── __init__.py
        ├── main.py                     <- main python script that shows the order of running the scripts
        ├── models                      <- containts python scripts for interacting with the models
        │   ├── evaluate.py
        │   ├── __init__.py
        │   ├── predict.py
        │   └── train.py
        └── util                        <- contains utility scripts/functions
            └── __init__.py
```

## What to do ?

### Implement ``src/models/predict.py``
This script must show the workflow of the service as from an end-user perspective, i.e. its input
is what the user will be asked for (e.g. single text instance) and its output is what the user will
expect (e.g. list of annotated text segments).

**Important:** This script must be as **decoupled** as possible from all other scripts in this repository.

### Implement ``src/main.py``
This script must show the entire workflow of retraining the service. In case there are any intermediate 
steps that cannot be done fully-automated, the script shall be implemented with arguments
for the automated steps and associated with documentation of how and when to run the intermediate
steps. E.g.:
```commandline
1. python -m src.main -s dataset
2. run notebooks/train.ipynb and download the output model locally
3. python -m src.main -s evaluate
```

### Provide ``requirements.txt``
The version of the listed dependencies must be specified by mentioning the exact version or at least
a range of versions.

### Provide ``README.md``
Please find a README template below.

-----------------------------------------------------------------------------------
# README Template

## Overview

### Aims
``...``

### Approach
``...``

### Dataset
``...``

### Limitations 
``...``

### Useful Links
* ``...``
* ``...``

## How to Run

### Prerequisites

#### Software Dependencies
* Python version ``x.xx``
* Java version ``x.xx``
* ...

#### Hardware Resources
* RAM ``x GB``
* Storage ``x GB`` 
* GPU ``xxxx``
* ``...``

### Service Retraining

Here some text about how to re-build the dataset and re-train the model. 

```commandline
git clone <link to your repository>
cd <repository directory>
pip install -r requirements.txt
python -m src.main [any necessary arguments]
```

or 

```commandline
git clone <link to your repository>
cd <repository directory>
pip install -r requirements.txt
python -m src.main -s dataset [any necessary arguments]
// intermediate step e.g.: run notebooks/train.ipynb and store the output model locally.
python -m src.main -s evaluate [any necessary arguments]
```

### Service Integration

Here some text about how to use the existing model as an End-to-End service. Please consider
following the [integration requirements](https://orkg-nlp-pypi.readthedocs.io/en/latest/contribute.html#integration-requirements)
if you want your service to be integrated into ``orkgnlp``.

```commandline
git clone <link to your repository>
cd <repository directory>
pip install -r requirements.txt
python -m src.models.predict [any necessary arguments]
```


## Contribution
This service is developed and maintained by:
* Surname, Name <name.surname@domain.com>
* ``...``

## License
``...``

## How to Cite

```commandline
your bibtex entry.
```

## References

* 1st reference
* 2nd reference
* ``...``

