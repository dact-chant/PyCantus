#!/usr/bin/env python
"""
This module contains the CsvLoader class, which is responsible for loading chants and sources from CSV files.
It provides methods to download the files if they are not found, and to load the data into Chant and Source objects.
"""
import pandas as pd
import os
import requests
from importlib import resources as impresources
import re

from pycantus.models.chant import Chant, MANDATORY_CHANTS_FIELDS, OPTIONAL_CHANTS_FIELDS
from pycantus.models.source import Source, MANDATORY_SOURCES_FIELDS, OPTIONAL_SOURCES_FIELDS
import pycantus.dataset_files as dataset_files


__version__ = "0.0.3"
__author__ = "Anna Dvorakova"


def get_numerical_century(century : str) -> int:
    """
    Extracts the numerical century from a string representation of a century.
    E.g. for '12th century' -> 12
         for '1345 - 1390'  -> 14
    """
    try:
        two_digits_pattern = r'(?<!\d)\d{2}(?!\d)'
        two_digits_match = re.findall(two_digits_pattern, century)
        if len(two_digits_match) == 1:
            return int(two_digits_match[0])
        elif len(two_digits_match) > 1: 
            # take first anyway
            return int(two_digits_match[0])
        
        one_digit_pattern = r'(?<!\d)\d{1}(?!\d)'
        one_digit_match = re.findall(one_digit_pattern, century)
        if len(one_digit_match) == 1:
            return int(one_digit_match[0])
        
        four_digits_pattern = r'(?<!\d)\d{4}(?!\d)'
        four_digits_match = re.findall(four_digits_pattern, century)
        if four_digits_match is not None:
            if len(four_digits_match) == 1:
                return int(four_digits_match[0][0:2])+1
            elif len(four_digits_match) > 1: 
                # take first anyway
                return int(four_digits_match[0][0:2])+1
            else:
                print('PROBLEM:', century)
        else:
            print('PROBLEM:', century)
    except: # probably nan coming
        return None
    

class CsvLoader():
    """
    pycantus CsvLoader class
        - loads chants and sources from CSV files
        - downloads files if they are not found
        - creates Chant and Source objects from the data
        - checks for mandatory fields and raises an error if any are missing
        - initialized for particular dataset (provided or custom)
    """
    def __init__(self, chants_filename : str, sources_filename : str, 
                 chants_fallback_url=None, sources_fallback_url=None, other_parameters=None):
        self.chants_filename = chants_filename
        self.sources_filename = sources_filename
        self.chants_fallback_url = chants_fallback_url
        self.sources_fallback_url = sources_fallback_url
        self.other_parameters = other_parameters

        # Make correct paths for available_datasets data files
        if self.other_parameters == "available_dataset":
            chants_file = impresources.files(dataset_files) / self.chants_filename
            self.chants_filename = os.path.abspath(chants_file)
            if sources_filename is not None:
                sources_file = impresources.files(dataset_files) / self.sources_filename
                self.sources_filename = os.path.abspath(sources_file)

        # Ensure the CSV files exist or download them if fallback URLs are provided
        if not os.path.isfile(self.chants_filename):
            if not self.chants_fallback_url:
                raise ValueError(f"Non-existent chant CSV file or dataset name specified: {self.chants_filename}")
            self.download(url=self.chants_fallback_url, target=self.chants_filename)

        if self.sources_filename is not None:
            if not os.path.isfile(self.sources_filename):
                if not self.sources_fallback_url:
                    raise ValueError(f"Non-existent chant CSV file or dataset name specified: {self.sources_filename}")
                self.download(url=self.sources_fallback_url, target=self.sources_filename)


    def download(self, url : str, target : str) -> None:
        """
        Downloads a file from the given URL and saves it to the target path.
        """
        print(f"Downloading file from {url}...")
        dir = os.path.dirname(target)
        if not os.path.exists(dir):
            os.makedirs(dir)
        response = requests.get(url)
        response.raise_for_status()
        with open(target, 'wb') as f:
            f.write(response.content)
        print("Download complete.")


    def _load_chants(self, chants_f : pd.DataFrame) -> list[Chant]:
        """
        Loads chants from a DataFrame and creates Chant objects.
        """
        chants = []
        for idx, row in chants_f.iterrows():
            try:
                # Extract mandatory parameters
                mandatory_params = {
                    'siglum': row['siglum'],
                    'srclink': row['srclink'],
                    'chantlink': row['chantlink'],
                    'folio': row['folio'],
                    'db': row['db'],
                    'cantus_id': row['cantus_id'],
                    'incipit': row['incipit']
                }
                
                # Extract optional parameters if they exist and are not NaN
                optional_params = {}
                for field in OPTIONAL_CHANTS_FIELDS:
                    if field in row.index and pd.notna(row[field]):
                        optional_params[field] = row[field]
                # Create Chant object and add to list
                chant = Chant(**mandatory_params, **optional_params)
                chants.append(chant)
                
            except Exception as e:
                print(f"Error processing chants file row {idx+2}: {e}")

        return chants
    

    def _load_sources(self, sources_f : pd.DataFrame) -> list[Source]:
        """
        Loads sources from a DataFrame and creates Source objects.
        """
        sources = []
        for idx, row in sources_f.iterrows():
            try:
                # Extract mandatory parameters
                mandatory_params = {
                    'title' : row['title'],
                    'siglum' : row['siglum'],
                    'srclink' : row['srclink']
                }
                
                # Extract optional parameters if they exist and are not NaN
                optional_params = {}
                for field in OPTIONAL_SOURCES_FIELDS:
                    if field in row.index and pd.notna(row[field]):
                        optional_params[field] = row[field]
                # Handle numeric_century if needed
                if 'numeric_century' not in row.index: 
                    if 'century' in row.index and pd.notna(row['century']):
                        optional_params['numeric_century'] = get_numerical_century(row['century'])
                    else:
                        optional_params['numeric_century'] = None
                # Create Chant object and add to list
                source = Source(**mandatory_params, **optional_params)
                sources.append(source)
                
            except Exception as e:
                print(f"Error processing sources file row {idx+2}: {e}")
        
        return sources
    
    def load(self) -> tuple[list[Chant], list[Source]]:
        """
        Loads chants and sources from CSV files.
        Checks for mandatory fields and raises an error if any are missing.
        """
        print("Loading chants and sources...")
        
        # Chants
        try:
            chants = pd.read_csv(self.chants_filename, dtype=str)

            missing_fields = [field for field in MANDATORY_CHANTS_FIELDS if field not in chants.columns]
            if missing_fields:
                raise ValueError(f"Missing mandatory fields in CSV: {', '.join(missing_fields)}")
            
            chants = self._load_chants(chants)

        except FileNotFoundError:
            raise FileNotFoundError(f"CSV file not found: {self.chants_filename}")
        except Exception as e:
            raise Exception(f"Error loading CSV {self.chants_filename} file: {e}")
        
        # Sources
        if self.sources_filename is not None:
            try:
                sources = pd.read_csv(self.sources_filename, dtype={'num_century': 'Int64'})

                missing_fields = [field for field in MANDATORY_SOURCES_FIELDS if field not in sources.columns]
                if missing_fields:
                    raise ValueError(f"Missing mandatory fields in CSV: {', '.join(missing_fields)}")

                sources = self._load_sources(sources)

            except FileNotFoundError:
                raise FileNotFoundError(f"CSV file not found: {self.sources_filename}")
            except Exception as e:
                raise Exception(f"Error loading CSV {self.sources_filename} file: {e}")       
        else:
            sources = []

        print("Data loaded!")
        return chants, sources