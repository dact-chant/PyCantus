"""
This module defines the base class for filters used in the PyCantus library.
It provides a structure for creating and applying filters to chant data.
"""
#import yaml
from collections import defaultdict

__version__ = "0.0.4"
__author__ = "Anna Dvorakova"


CHANT_FIELDS = ['cantus_id', 'incipit','chantlink', 'srclink', 'siglum', 'folio', 'db'
                'sequence', 'feast', 'genre', 'office', 'position', 'melody_id',
                'image', 'mode', 'full_text', 'melody', 'century', 'rite'] # 'srclink', 'siglum' - are present here bc not every corpus have sources...

SOURCE_FIELDS = ['title', 'siglum','century', 'provenance', 'srclink']


class Filter:
    """
    Base class for filters over Corpus data lists:
    - chants - objects of class pycantus.models.Chant
    - sources - objects of class pycantus.models.Source
    - melodies - objects of class pycantus.models.Melody
    """

    def __init__(self, name: str):
        self.name = name
        self.filters = defaultdict(list)
    
    def add_value(self, field : str, values : list[str]):
        """
        Add a value to the filter for a specific field.
        """
        if field not in CHANT_FIELDS and field not in SOURCE_FIELDS:
            raise ValueError(f"Field '{field}' is not a valid chant or source field.")
        
        self.filters[field] += values

    def apply(self, chants : list, sources : list, melodies : list):
        """
        Apply the filter to the given data.
        Returns filtered chants and sources based on the filter criteria.
        If no filter is applied, returns the original lists.
        """
        if len(self.filters) == 0:
            print("No filtering applied because no filtration values were present, returning original lists.")
            return chants, sources, melodies
        
        # First solve the sources
        source_fields = set(SOURCE_FIELDS).intersection(self.filters.keys())
        if source_fields:
            dicarded_sources = set()
            filtered_sources = []

            for source in sources:
                keep = True
                for field in source_fields:
                    value = getattr(source, field, None)
                    if value not in self.filters[field]:
                        dicarded_sources.add(source.srclink)
                        keep = False
                        break
                if keep:
                    filtered_sources.append(source)
            sources = filtered_sources

        chants_fields = set(CHANT_FIELDS).intersection(self.filters.keys())
        if chants_fields or dicarded_sources:
            filtered_chants = []
            for chant in chants:
                keep = True
                for field in chants_fields:
                    value = getattr(chant, field, None)
                    if value not in self.filters[field]:
                        keep = False
                        break
                if keep:
                    filtered_chants.append(chant)
            chants = filtered_chants
 
        if len(melodies) > 0:
            filtered_melodic_chantlinks = {chant.chanlink for chant in chants if chant._has_melody}
            # Discard melodies that are not in the filtered chants
            filtered_melodies = []
            for melody in melodies:
                if melody is not None and melody.chantlink in filtered_melodic_chantlinks:
                    filtered_melodies.append(melody)
            melodies = filtered_melodies

        return chants, sources, melodies
    
    def __str__(self):
        return f"Filter(name={self.name})"
    
    def export_yaml(self):
        """
        Export the filter configuration to YAML format.
        """
        setting = {
            'name': self.name,

        }