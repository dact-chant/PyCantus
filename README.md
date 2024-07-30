# PyCantus
PyCantus is envisioned as a Python API to the Cantus family of databases that makes it easy to use this data for computational processing. Primarily we intend this to be used for research in digital chant scholarship, but of course it can be used to build chant-centric apps, new websites, extract data for comparative studies across different repertoires, study liturgy, etc.


## Data model
At the heart of the library is the Cantus Database and Cantus Index data model. The two elementary objects in this model are a `Chant`, and a `Source`.

* A `Source` is a physical manuscript or print that contains Gregorian chant. Primarily, this will be a liturgical book such as an antiphonary, gradual, or other sources. Fragments are, in principle, also sources. (Note: tonaries may get special handling.)

* A `Chant` is one instance of a chant in a source. Typically it has a text, a melody (which is not necessarily transcribed), and a Cantus ID assigned, and it should link to a source in which it is found. It should align with the cantus API: https://github.com/DDMAL/CantusDB/wiki/APIs 

## Installing PyCantus library locally
1. clone the repository 
    
    ```git clone https://github.com/dact-chant/PyCantus```
2. go to the root directory of the project
3. run the following command 

    ```pip install -e .```
4. import the pycantus library and call its functionality

    ```python
    from pycantus import hello_pycantus
    hello_pycantus()
    ```
