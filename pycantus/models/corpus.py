#!/usr/bin/env python
"""
This module contains the Corpus class, which represents a collection of chants and sources.
It provides methods for loading, filtering, and exporting data related to the chants and sources.
"""

import pandas as pd

from pycantus.models.chant import Chant
from pycantus.models.source import Source
from pycantus.dataloaders.loader import CsvLoader
from pycantus.filtration.filter import Filter


__version__ = "0.0.4"
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
                 check_missing_sources=False,
                 create_missing_sources=False,
                 **kwargs):
        
        self.chants_filepath = chants_filepath
        self.sources_filepath = sources_filepath
        self.chants_fallback_url = chants_fallback_url
        self.sources_fallback_url = sources_fallback_url
        self.other_download_parameters = other_parameters
        self.is_editable = is_editable
        self.create_missing_sources = create_missing_sources
        self.check_missing_sources = check_missing_sources

        loader = CsvLoader(self.chants_filepath, self.sources_filepath, self.check_missing_sources, 
                           self.create_missing_sources, self.chants_fallback_url, self.sources_fallback_url, 
                           other_parameters)
        chants, sources = loader.load()

        self._chants = chants
        self._sources = sources
        self._melodies = []

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
    
    def _lock_melodies(self):
        """ Sets all sources to locked. """
        for m in self._melodies:
            m.locked = True

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
    
    @property #getter
    def melodies(self):
        return self._melodies
    
    @property
    def csv_chants_header(self) -> str:
        """
        Returns proper csv header for chants export to csv
        """
        return Chant.header()

    @property
    def csv_sources_header(self) -> str:
        """
        Returns proper csv header for sources export to csv
        """
        return Source.header()

    def export_csv(self, chants_filepath : str, sources_filepath):
        """ 
        Exports the chants and sources to CSV files.
        If sources_filepath is not provided, only chants will be exported.
        """
        # Chants
        try:
            with open(chants_filepath, 'w') as s_file:
                print(self.csv_chants_header, file=s_file)
                for chant in self._chants:
                    print(chant.to_csv_row, file=s_file)
        except Exception as e:
            print(f"Error exporting chants file : {e}")

        # Sources
        if self._sources:
            try:
                with open(sources_filepath, 'w') as s_file:
                    print(self.csv_sources_header, file=s_file)
                    for source in self._sources:
                        print(source.to_csv_row, file=s_file)
            except Exception as e:
                print(f"Error exporting sources file : {e}")


    def drop_duplicate_chants(self):
        """
        Discards all chants that have the same chantlink as another chant.
        Keeps the last occurrence of each chant.
        """
        chantlinks = [ch.chantlink for ch in self._chants]
        i = 0
        for chant in self._chants:
            if chantlinks.count(chantlinks[i]) > 1:
                self._chants.remove(chant)
                chantlinks.remove(chantlinks[i])
            i += 1

    def drop_duplicate_sources(self):
        """
        Discards all sources that have the same srclink as another source.
        Keeps the last occurrence of each source.
        """
        srclinks = [s.srclink for s in self._sources]
        i = 0
        for source in self._sources:
            if srclinks.count(srclinks[i]) > 1:
                self._sources.remove(source)
                srclinks.remove(srclinks[i])
            i += 1


    def merge_with(self, to_be_merged, keep_duplicates=True):
        """
        Merges the current corpus with another corpus.
        If keep_duplicates is True, it keeps all chants, sources and possibly melodies from both corpora.
        """
        pass
    
    def create_melodies(self):
        """
        Creates Melody objects for all chants in the corpus that has melody encoded
        and stores them in _melodies list - locks if corpus is not editable.
        This method should be called after the chants are loaded.
        """
        self._melodies = []
        for chant in self._chants:
            chant.create_melody()
            if chant.melody_object is not None:
                self._melodies.append(chant.melody_object)
        if not self.is_editable:
            self._lock_melodies()

    def keep_melodic_chants(self):
        """
        Keeps only chants that have a melody in the corpus.
        """
        self._chants = [ch for ch in self._chants if ch._has_melody]
        # Just in case, we also need to create melodies again
        self.create_melodies()
    
    def drop_empty_sources(self):
        """
        Discards all sources that have no chants in corpus.
        """
        sources_in_chant_data = {ch.srclink for ch in self._chants}
        self._sources = [s for s in self._sources if s.srclink in sources_in_chant_data]


    def apply_filter(self, filter : Filter):
        """
        Applies the given filter on its data in "in place" way.
        """
        self._chants, self._sources, self._melodies = filter.apply(self._chants, self._sources, self._melodies)
        #print('Discarding empty sources after filtration...')
        #self.discard_empty_sources()
        #print('Number of chants after filtration:', len(self._chants), '\nNumber of sources after filtration:', len(self._sources))
        

