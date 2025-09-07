#!/usr/bin/env python
"""
This module provides utility functions for logging operations in the Corpus history.
"""
from functools import wraps
from .history import HistoryEntry

__version__ = "0.0.6"
__author__ = "Anna Dvorakova"

def log_operation(func):
    """
    Decorator to log Corpus operations into its history list.
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        # Execute the original method
        result = func(self, *args, **kwargs)

        # Create a History entry
        
        # Special handling for apply_filter 
        # to list the filter yaml instead of the object reference
        if func.__name__ == "apply_filter":
            args = args[0].__str__()
        else:
            # Transform kwargs into a string representation
            if args == () and kwargs != {}:
                args = '\n'.join([f"{k}: {v}" for k, v in kwargs.items()])
            else:
                args = '{}'

        entry = HistoryEntry(
            method=func.__name__,
            parameters=args,
        )
        self.operations_history.append(entry)

        return result
    return wrapper