# PyCantus
PyCantus is envisioned as a Python API to the Cantus family of databases that makes it easy to use this data for computational processing. Primarily we intend this to be used for research in digital chant scholarship, but of course it can be used to build chant-centric apps, new websites, extract data for comparative studies across different repertoires, study liturgy, etc.


## Data model

At the heart of the library is the Cantus Database and Cantus Index data model. The two elementary objects in this model are a `Chant`, and a `Source`.

* A `Source` is a physical manuscript or print that contains Gregorian chant. Primarily, this will be a liturgical book such as an antiphonary, gradual, or other sources. Fragments are, in principle, also sources. (Note: tonaries may get special handling.)

* A `Chant` is one instance of a chant in a source. Typically it has a text, a melody (which is not necessarily transcribed), and a Cantus ID assigned, and it should link to a source in which it is found. It should align with the Cantus API: `https://github.com/dact-chant/cantus-index/blob/main/README.md`

## Tutorial

For an introduction to using PyCantus, run the `tutorial.ipynb` Jupyter notebook.

## Installing PyCantus library locally

1. Clone the repository:
    
    ```git clone https://github.com/dact-chant/PyCantus```
   
2. Go to the root directory of the project
3. Run the following command:

    ```pip install -e .```
   
4. Import the pycantus library and verify it works:

    ```python
    from pycantus import hello_pycantus
    hello_pycantus()
    ```
