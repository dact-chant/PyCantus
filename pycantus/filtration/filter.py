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
    
    Attributes:
        name (str): Name of the filter, used in export.
        filters_include (defaultdict(list)): { Data fields : Values to be included after filtration }
        filters_exclude (defaultdict(list)): { Data fields : Values to be excluded after filtration }
    """

    def __init__(self, name: str):
        """
        Initialize the Source.

        Args:
            name (str): name of the filter, used in export
        """
        self.name = name
        self.filters_include = defaultdict(list)
        self.filters_exclude = defaultdict(list)
    
    def add_value_include(self, field : str, values : list[str] | list[int] | int | str):
        """
        Add a value of specific field to the filter to be included.
        Other non-specified values would be droped during filtration.

        Args:
            field (str): Data field (Chant or Source attribute).
            values: Either single value (str or int) or list of values to be included after filtration.
        """
        if not isinstance(values, list):
            values = [values]
        
        if field not in EXPORT_CHANTS_FIELDS and field not in EXPORT_SOURCES_FIELDS:
            raise ValueError(f"Field '{field}' is not a valid chant or source field.")

        self.filters_include[field] += values
        self.filters_include[field] = list(set(self.filters_include[field])) # discard dupliates
            
    def add_value_exclude(self, field : str, values : list[str] | list[int] | int | str):
        """
        Add a value of specific field to the filter to be excluded.

        Other non-specified values would be kept during filtration.

        Args:
            field (str): Data field (Chant or Source attribute).
            values: Either single value (str or int) or list of values to be included after filtration.
        """
        if not isinstance(values, list):
            values = [values]
        
        if field not in EXPORT_CHANTS_FIELDS and field not in EXPORT_SOURCES_FIELDS:
            raise ValueError(f"Field '{field}' is not a valid chant or source field.")

        self.filters_exclude[field] += values
        self.filters_exclude[field] = list(set(self.filters_exclude[field])) # discard dupliates

    
    def apply(self, chants : list, sources : list) -> tuple[list]:
        """
        Apply the filter to the given data.
        If no values for field are specified we expect that user does not care about the field.
        If no filter is to be applied, returns the original lists.

        Args:
            chants (list): 
            source (list):

        Returns:
            list: 
            list:
        """
        filter_fields = set(self.filters_include.keys()).union(self.filters_exclude.keys())
        if len(filter_fields) == 0:
            print("No filtering applied because no filtration values were present, returning original lists.")
            return chants, sources

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

        return chants, sources

    def delete_field(self, field):
        """
        Deletes a field from both the include and the exclude filters.
        """
        if field in self.filters_exclude.keys():
            del self.filters_exclude[field]
        elif field in self.filters_include.keys():
            del self.filters_include[field]

    def as_yaml(self) -> str:
        """
        Returns 
            str: yaml style string representation of filter configuration.
        """
        setting = {
            'name': self.name,
            'include_values' : dict(self.filters_include),
            'exclude_values' : dict(self.filters_exclude)
        }
        return yaml.dump(setting, allow_unicode=True, sort_keys=False)
    
    def __str__(self) -> str:
        """
        Returns 
            str: yaml style string representation of filter configuration.
        """
        return self.as_yaml()
    
    def export_yaml(self, path : str):
        """
        Export the filter configuration to a directory given as path 
        as '{self.name}.yaml' YAML file.

        Tries to create the directory if it does not exist.

        Args:
            path (str): Path to directory where export YAML file should be created.
        """
        file_name = f"{self.name}.yaml"
        file_path = os.path.join(path, file_name)

        try:
            os.makedirs(path, exist_ok=True)  # Create directory if it doesn't exist
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.as_yaml(), f, allow_unicode=True, sort_keys=False)
            print(f"Filter '{self.name}' successfully exported to: {file_path}")
        except Exception as e:
            print(f"Error exporting filter to YAML: {e}")
    
    def import_yaml(self, config_file_path : str):
        """
        Function that reads YAML file and transforms it into 
        self.filter_include and self.filter_exclude dictionaries.

        Args:
            config_file_path (str): Path to YAML to be loaded into filter configuration.
        """
        try:
            with open(config_file_path, 'r') as f:
                yaml_content = yaml.safe_load(f)
            self.name = yaml_content['name']
            self.filters_include = defaultdict(list, yaml_content['include_values'])
            self.filters_exclude = defaultdict(list, yaml_content['exclude_values'])
        except:
            raise IOError(f"Filter configuration file on path {config_file_path} load failed!")