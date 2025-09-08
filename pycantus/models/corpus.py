#!/usr/bin/env python
"""
This module contains the Corpus class, which represents a collection of chants and sources.
It provides methods for loading, filtering, and exporting data related to the chants and sources.
"""

from collections import Counter

from pycantus.models.chant import Chant
from pycantus.models.source import Source
from pycantus.models.melody import Melody
from pycantus.dataloaders.loader import CsvLoader
from pycantus.filtration.filter import Filter
from pycantus.history import HistoryEntry
from pycantus.history.utils import log_operation

__version__ = "0.0.6"
__author__ = "Anna Dvorakova"


class Corpus():
    """
    Represents a collection of chants and sources (piece of repertoire).

    Attributes:
        chants_filepath (str): path to file with chants
        sources_filepath (str, optional): path to file with sources
        chants_fallback_url (str, optional): URL for chants file download, is used when loading from filepath fails
        sources_fallback_url (str, optional): URL for sources file download, is used when loading from filepath fails
        other_download_parameters (dict, optional): [not used yet]
        is_editable (bool): indicates whether objects in Corpus should be locked
        check_missing_sources (bool): indicates whether load should an raise exception if some chant refers to source that is not in sources
        create_missing_sources (bool): indicates whether load should create Source entries for sources referred to in some of the chants and not being present in provided sources
        operations_history (list): list of operations applied on the corpus (from predefined list - see methods with @log_operation decorator)
    
    Only chants_filepath is mandatory.
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
        """
        Initialize the Corpus. 

        Args corresponds to class attributes.
        """
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

        if not self.is_editable:
            self._lock_chants()
            self._lock_sources()

        self.operations_history = []
    
    def _lock_chants(self):
        """ 
        Sets all chants to locked. 
        """
        for c in self._chants:
            c.locked = True

    def _lock_sources(self):
        """ 
        Sets all sources to locked. 
        """
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
    
    @property #getter
    def melody_objects(self) -> list[Melody]:
        """
        Collects melody_objects of Chants in self._chants .
        Returns:
            list : melody objects of chants in the Corpus
        """
        return [ch.melody_object for ch in self._chants if ch._has_melody]
    
    @property
    def csv_chants_header(self) -> str:
        """
        Returns proper csv header for chants export to csv.
        Returns:
            str: csv header for Chant
        """
        return Chant.header()

    @property
    def csv_sources_header(self) -> str:
        """
        Returns proper csv header for sources export to csv.
        Returns:
            str: csv header for Source
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

    @log_operation
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

    @log_operation
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
    
    @log_operation
    def keep_melodic_chants(self):
        """
        Keeps only chants that have a melody in the corpus.
        """
        self._chants = [ch for ch in self._chants if ch._has_melody]
    
    @log_operation
    def drop_empty_sources(self):
        """
        Discards all sources that have no chants in corpus.
        """
        sources_in_chant_data = {ch.srclink for ch in self._chants}
        self._sources = [s for s in self._sources if s.srclink in sources_in_chant_data]

    @log_operation
    def drop_small_sources_data(self, min_chants : int):
        """
        Discards all sources that have less than min_chants chants in corpus
        and discard their chants as well.
        """
        source_chant_counts = Counter([ch.srclink for ch in self._chants])
        sources_to_keep = {s for s, count in source_chant_counts.items() if count >= min_chants}
        self._sources = [s for s in self._sources if s.srclink in sources_to_keep]
        self._chants = [ch for ch in self._chants if ch.srclink in sources_to_keep]
    
    @log_operation
    def apply_filter(self, filter : Filter):
        """
        Applies the given filter on stored data in "in place" way.
        Stores filter setting into filtration_history.
        """
        self._chants, self._sources = filter.apply(self._chants, self._sources)
    
    def get_operations_history_string(self):
        """
        Returns the history of applied operations on the corpus.
        """
        history_string = '\n'.join([str(entry) for entry in self.operations_history])
        return history_string