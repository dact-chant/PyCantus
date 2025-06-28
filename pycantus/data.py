#!/usr/bin/env python
"""
This module is responsible for loading datasets and possibly their metadata.
It provides a function to load a dataset based on its name or file path.
It loads available datasets from a JSON file from library static.
"""

import json
from importlib import resources as impresources

import pycantus.static as static
from pycantus.models.corpus import Corpus


__version__ = "0.0.4"
__author__ = "Anna Dvorakova"


def _load_available_datasets() -> dict:
    """ 
    Loads the available datasets and their metainfo from a JSON file.
    """
    aval_datas_file = impresources.files(static) / "available_datasets.json"
    with aval_datas_file.open("rt") as f:
        available_datasets = json.load(f)
    return available_datasets
AVAILABLE_DATASETS = _load_available_datasets()


def load_dataset(name_or_chant_filepath : str, source_filepath : str =None, 
                 is_editable : bool =False, check_missing_sources : bool=False,
                 create_missing_sources : bool =False, **corpus_kwargs): # -> Corpus
    """ 
    Returns a Corpus object based on the name of dataset or filepath provided.
    If the name is in the available datasets, it will load that dataset.
    If a filepath is provided, it will try load the dataset from that filepath.
    If the filepath is not found, it will raise an error.
    If a source filepath is provided, it will be used to load the sources.
    If the source filepath is given and not found, it will raise an error.
    """
    if name_or_chant_filepath in AVAILABLE_DATASETS:
        # We know we are being asked for a pre-defined corpus.
        dataset_name = name_or_chant_filepath  
        dataset_metadata = AVAILABLE_DATASETS[dataset_name]
        corpus = Corpus(**dataset_metadata, is_editable=is_editable, check_missing_sources=check_missing_sources,
                        create_missing_sources=create_missing_sources)

    else:
        # We know to expect a custom CSV
        csv_chant_file_path = name_or_chant_filepath
        corpus = Corpus(csv_chant_file_path, source_filepath, check_missing_sources=check_missing_sources,
                        create_missing_sources=create_missing_sources, is_editable=is_editable, 
                        **corpus_kwargs)

    return corpus

def list_available_datasets():
    """
    Lists all available dataset of current PyCantus based on 
    static/available_datsets.json file.
    """
    print('List of available datasets:')
    for dataset, dataset_metadata in AVAILABLE_DATASETS.items():
        print(f"\t{dataset}: {dataset_metadata['name']} ({dataset_metadata['description']})")