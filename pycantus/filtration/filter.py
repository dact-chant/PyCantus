#!/usr/bin/env python
"""
This module defines the base class for filters used in the PyCantus library.
It provides a structure for creating and applying filters to chant data.
"""
import yaml
import os

from collections import defaultdict
from pycantus.models.source import EXPORT_SOURCES_FIELDS
from pycantus.models.chant import EXPORT_CHANTS_FIELDS

__version__ = "0.0.4"
__author__ = "Anna Dvorakova"



class Filter:
    """
    Base class for filters over Corpus data lists:
    - chants - objects of class pycantus.models.Chant
    - sources - objects of class pycantus.models.Source
    - melodies - objects of class pycantus.models.Melody
    """

    def __init__(self, name: str):
        self.name = name
        self.filters_include = defaultdict(list)
        self.filters_exclude = defaultdict(list)
    
    def add_value_include(self, field : str, values : list[str] | list[int] | int | str):
        """
        Add a value to the filter for a specific field to be included.
        """
        if not isinstance(values, list):
            values = [values]
        
        if field not in EXPORT_CHANTS_FIELDS and field not in EXPORT_SOURCES_FIELDS:
            raise ValueError(f"Field '{field}' is not a valid chant or source field.")

        self.filters_include[field] += values
        self.filters_include[field] = list(set(self.filters_include[field])) # discard dupliates
            
    def add_value_exclude(self, field : str, values : list[str] | list[int] | int | str):
        """
        Add a value to the filter for a specific field to be excluded.
        """
        if not isinstance(values, list):
            values = [values]
        
        if field not in EXPORT_CHANTS_FIELDS and field not in EXPORT_SOURCES_FIELDS:
            raise ValueError(f"Field '{field}' is not a valid chant or source field.")

        self.filters_exclude[field] += values
        self.filters_exclude[field] = list(set(self.filters_exclude[field])) # discard dupliates

    
    def apply(self, chants : list, sources : list, melodies : list):
        """
        Apply the filter to the given data.
        Returns filtered chants and sources based on the filter criteria.
        If no values for field are specified we expect that user do not care about the field.
        If no filter is to be applied, returns the original lists.
        """
        filter_fields = set(self.filters_include.keys()).union(self.filters_exclude.keys())
        if len(filter_fields) == 0:
            print("No filtering applied because no filtration values were present, returning original lists.")
            return chants, sources, melodies

        filtered_sources= []
        discarded_srclinks = set()
        source_filter_fields = set(EXPORT_SOURCES_FIELDS).intersection(filter_fields)
        if source_filter_fields:
            for source in sources:
                include_pass = all(
                    field not in self.filters_include or not self.filters_include[field] or
                    getattr(source, field, None) in self.filters_include[field]
                    for field in source_filter_fields
                )
                exclude_pass = all(
                    field not in self.filters_exclude or not self.filters_exclude[field] or
                    getattr(source, field, None) not in self.filters_exclude[field]
                    for field in source_filter_fields
                )

                if include_pass and exclude_pass:
                    filtered_sources.append(source)
                else:
                    discarded_srclinks.add(source.srclink)

            sources = filtered_sources    
            

        filtered_chants = []
        chants_filter_fields = set(EXPORT_CHANTS_FIELDS).intersection(filter_fields)
        if chants_filter_fields or discarded_srclinks:
            for chant in chants:
                if chant.srclink in discarded_srclinks:
                    continue

                include_pass = all(
                    field not in self.filters_include or not self.filters_include[field] or
                    getattr(chant, field, None) in self.filters_include[field]
                    for field in chants_filter_fields
                )
                exclude_pass = all(
                    field not in self.filters_exclude or not self.filters_exclude[field] or
                    getattr(chant, field, None) not in self.filters_exclude[field]
                    for field in chants_filter_fields
                )

                if include_pass and exclude_pass:
                    filtered_chants.append(chant)

            chants = filtered_chants
             
        if len(melodies) > 0:
            filtered_melodic_chantlinks = {chant.chantlink for chant in chants if chant._has_melody}
            # Discard melodies that are not in the filtered chants
            filtered_melodies = []
            for melody in melodies:
                if melody is not None and melody.chantlink in filtered_melodic_chantlinks:
                    filtered_melodies.append(melody)
            melodies = filtered_melodies

        return chants, sources, melodies

    def delete_field(self, field):
        """
        Delete a field from both the include and the exclude filters.
        """
        if field in self.filters_exclude.keys():
            del self.filters_exclude[field]
        elif field in self.filters_include.keys():
            del self.filters_include[field]

    def __str__(self):
        """
        Returns yaml style string representation of filter
        configuration.
        """
        setting = {
            'name': self.name,
            'include_values' : dict(self.filters_include),
            'exclude_values' : dict(self.filters_exclude)
        }
        return yaml.dump(setting, allow_unicode=True, sort_keys=False)
    
    def export_yaml(self, path : str):
        """
        Export the filter configuration to a directory given as path 
        as '{self.name}.yaml' yaml file.
        """
        setting = {
            'name': self.name,
            'include_values' : dict(self.filters_include),
            'exclude_values' : dict(self.filters_exclude)
        }
        file_name = f"{self.name}.yaml"
        file_path = os.path.join(path, file_name)

        try:
            os.makedirs(path, exist_ok=True)  # Create directory if it doesn't exist
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(setting, f, allow_unicode=True, sort_keys=False)
            print(f"Filter '{self.name}' successfully exported to: {file_path}")
        except Exception as e:
            print(f"Error exporting filter to YAML: {e}")
    
    def import_yaml(self, config_file_path : str):
        """
        Function that reads YAML file and transforms it into 
        self.filter_include and self.filter_exclude dictionaries.
        """
        try:
            with open(config_file_path, 'r') as f:
                yaml_content = yaml.safe_load(f)
            self.name = yaml_content['name']
            self.filters_include = defaultdict(list, yaml_content['include_values'])
            self.filters_exclude = defaultdict(list, yaml_content['exclude_values'])
        except:
            raise IOError(f"Filter configuration file on path {config_file_path} load failed!")