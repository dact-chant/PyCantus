# PyCantus
`PyCantus` is envisioned as a Python API to the Cantus family of databases that makes it easy to use this data for computational processing. Primarily we intend this to be used for research in digital chant scholarship, but of course it can be used to build chant-centric apps, new websites, extract data for comparative studies across different repertoires, study liturgy, etc.  
  
The [CantusCorpus v1.0](https://github.com/DvorakovaA/CantusCorpus) dataset, containing data from the [Cantus Index](https://cantusindex.org/), can be used with the PyCantus library easily.

Finally, Django template of web API providing easier creation of YAML filtration setups called [Filter for PyCantus](https://github.com/DvorakovaA/filterforpycantus) was implemented  while also being deployed at [https://filterforpycantus.owx.cz](https://filterforpycantus.owx.cz).

## Data model

At the heart of the library is the Cantus Database and Cantus Index data model. The two elementary objects in this model are a `Chant`, and a `Source`.

* A `Chant` is one instance of a chant in a source. Typically it has a text, a melody (which is not necessarily transcribed), and a Cantus ID assigned, and it should link to a source in which it is found. In principle it uses fields from the [API defined by Cantus Index](https://github.com/dact-chant/cantus-index/blob/main/README.md); the exact data model is documented in the module.
* A `Source` is a physical manuscript or print that contains Gregorian chant. Primarily, this will be a liturgical book such as an antiphonary, gradual, or other types of books. Fragments are also sources. Provenance (geographical and institutional) and century of origin metadata are carried by source records.

There are two further important classes in the data model: `Melody`, and `Corpus`.

* A `Melody` contains the chant's melody at various levels of representation.
* A `Corpus` contains a dataset composed of sources and chants (that may have melodies). Filtering is done on `Corpus` objects.

## User documentation

We realize that two types of users come together at a library of this type – a group of programmers who are getting into Gregorian chant, and then (hopefully) a group of chant experts who are getting into its computer processing. Therefore, be warned that, quite inevitably, when examining the user documentation, each group will encounter things that are obvious to them, but that is fine, as these parts are there precisely for "the others."

### Introduction for Computer Science people
In the documentation (`doc` folder) we attempted to compile some basic overview information about Gregorian chant, that is a 'nice to have' before getting into work with the material. It should also serve as a cheat sheet for basic terms and concepts.


### Tutorials

For an introduction to using `PyCantus`, run the `tutorials\01_intro_to_pycantus.ipynb` Jupyter notebook.  
  
For more advanced and specific tasks there are four other tutorials in the `tutorials` folder, one describing some basics about the data for Gregorian chant beginners (`02_intro_to_chant_data.ipynb`), two working with repertoire (`03_traditions_detection.ipynb` and `04_unseen_species.ipynb`) and two working with melodies (`05_melody_vs_mode.ipynb` and `06_melody_classification.ipynb`). They would show you
more possibilities in using `PyCantus` and hopefully also possibilities in Gregorian chant research in general.


### Installing PyCantus library locally

1. Clone the repository:
    
    ```git clone https://github.com/dact-chant/PyCantus```
   
2. Go to the root directory of the project (the one where `pyproject.toml` is)
3. Run the following command:

    ```pip install .```
   
4. Import the pycantus library and verify it works:

    ```python
    from pycantus import hello_pycantus
    hello_pycantus()
    ```
