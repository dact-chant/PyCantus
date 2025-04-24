"""
This module contains the Corpus class, which represents a collection of chants and sources.
It provides methods for loading, filtering, and exporting data related to the chants and sources.
"""

import pandas as pd

from pycantus.models.chant import Chant
from pycantus.models.source import Source
from pycantus.dataloaders.loader import CsvLoader


__version__ = "0.0.1"
__author__ = "Anna Dvorakova"


class Corpus():
    """
    pycantus Corpus class 
        - represents a collection of chants and sources (piece of repertoire)
        - provides methods for loading, filtering, and exporting data related to the chants and sources
        - can be editable or not (if not, it is locked for editing)
    """
    def __init__(self,
                 chants_filepath,
                 sources_filepath=None,
                 chants_fallback_url=None,
                 sources_fallback_url=None,
                 other_parameters=None,
                 is_editable=False,
                 **kwargs):
        
        self.chants_filepath = chants_filepath
        self.sources_filepath = sources_filepath
        self.chants_fallback_url = chants_fallback_url
        self.sources_fallback_url = sources_fallback_url
        self.other_download_parameters = other_parameters
        self.is_editable = is_editable
        
        loader = CsvLoader(self.chants_filepath, self.sources_filepath, 
                           self.chants_fallback_url, self.sources_fallback_url, 
                           other_parameters)
        chants, sources = loader.load()

        self._chants = chants
        self._sources = sources

        if not self.is_editable:
            self._lock_chants()
            self._lock_sources()

    
    def _lock_chants(self):
        """ Sets all chants to locked. """
        for c in self._chants:
            c.locked = True

    def _lock_sources(self):
        """ Sets all sources to locked. """
        for s in self._sources:
            s.locked = True

    @property #getter
    def chants(self):
        return self._chants
    
    @chants.setter
    def chants(self, new_chants: list[Chant]):
        if self.is_editable:
            self._chants = new_chants
        else:
            raise PermissionError('Corpus is not editable, cannot replace chant list.')

    @property #getter
    def sources(self):
        return self._sources
    
    @sources.setter
    def sources(self, new_sources: list[Source]):
        if self.is_editable:
            self._sources = new_sources
        else:
            raise PermissionError('Corpus is not editable, cannot replace sources list.')
    
    @property
    def csv_chants_header(self) -> str:
        """
        Returns proper csv header for chants export to csv
        """
        if len(self._chants) == 0:
            raise ValueError('No chants in the corpus.')

        first_chant = self._chants[0]
        return first_chant.header

    @property
    def csv_sources_header(self) -> str:
        """
        Returns proper csv header for sources export to csv
        """
        if len(self._sources) == 0:
            raise ValueError('No sources in the corpus.')

        first_source = self._sources[0]
        return first_source.header

    def all_cids_list(self) -> [str]:
        """
        """
        pass
    
    def all_srclinks_list(self) -> [str]:
        """
        """
        pass

    def export_csv(filepath : str):
        """ """
        pass



    # Filtration methods

    # srclink
    # office
    # genre
    # feast
