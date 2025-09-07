#!/usr/bin/env python
"""
This module defines the HistoryEntry class to represent the history of main actions taken on a Corpus.
"""

__version__ = "0.0.6"
__author__ = "Anna Dvorakova"


class HistoryEntry:
    """
    A class to represent history of main actions taken on a Corpus.
    Attributes:
        method (str): The method used for the action.
        parameters (dict): Parameters used in the action.
    """
    def __init__(self, method, parameters):
        """
        Initialize the History object with method and parameters.

        Args:
            method (str): The method used for the action.
            parameters (dict): Parameters used in the action.
        """
        self.method = method
        self.parameters = parameters
    
    def __str__(self):
        """
        String representation of the History object.
        """
        return f"{self.method}\n{self.parameters}"