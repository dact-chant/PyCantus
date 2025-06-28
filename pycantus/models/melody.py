#!/usr/bin/env python
"""
This module contains the Melody class, which represents a single chant melody.
It is linked to a specific chant via chantlink.
Right now, it is designed in volpiano-centric way, meaning it holds only the volpiano representation of the chant melody,
if present. But it can be extended to hold other representations in the future (via new optional parameters).

We take the volpiano.utils as already prepered methods (functions) for working with volpiano and just
wrapped them into Melody class methods. 
For more detailed documentation of the methods, see the volpiano.utils module.
"""

from pycantus.volpiano.utils import clean_volpiano, expand_accidentals, normalize_liquescents, discard_differentia, get_range


__version__ = "0.0.4"
__author__ = "Anna Dvorakova"


class Melody():
    """
    Representation of one chant melody related to chant record.
    Attributes:
        volpiano (str): The melody encoded in Volpiano notation.
        chantlink (str): URL link directly to the chant entry in the external database.
        cantus_id (str): The Cantus ID associated with the chant.
        raw_volpiano (str): The original Volpiano string before any processing.
        locked (bool): Indicates if the object is locked for editing.
    """
    
    def __init__(self, volpiano : str, chantlink : str, cantus_id : str, mode : str):
        self.locked = False  # Indicates if the object is locked for editing
        self.raw_volpiano = volpiano
        self.volpiano = volpiano
        self.mode = mode
        self.chantlink = chantlink
        self.cantus_id = cantus_id


    # setter
    def __setattr__(self, name, value):
        if name != "locked" and getattr(self, "locked", False):
            raise AttributeError(f"Cannot modify '{name}' because the object is locked.")
        super().__setattr__(name, value)

    def __str__(self) -> str:
        return self.volpiano
    
    def clean_volpiano(self, keep_boundaries=False, allowed_chars=None,
                       neume_boundary=' ', syllable_boundary=' ', word_boundary=' ',
                       keep_bars=False, allowed_bars='345', bar='|'):
        """
        Extracts only the allowed characters (and optionally boundaries) from a volpiano string.
        """
        self.volpiano = clean_volpiano(volpiano=self.volpiano, keep_boundaries=keep_boundaries, allowed_bars=allowed_bars, 
                                       neume_boundary=neume_boundary, syllable_boundary=syllable_boundary, 
                                       word_boundary=word_boundary, keep_bars=keep_bars, allowed_chars=allowed_chars, bar=bar)
    
    def expand_accidentals(self, omit_notes=False, barlines='3456', apply_once_only=False):
        """
        Expand all accidentals in a volpiano string by adding the accidental
        to all other notes in the scope.
        """
        self.volpiano = expand_accidentals(volpiano=self.volpiano, omit_notes=omit_notes, 
                                           barlines=barlines, apply_once_only=apply_once_only)
    
    def normalize_liquescents(self):
        """Treat all liquescences as normal notes."""
        self.volpiano = normalize_liquescents(self.volpiano)
    
    def discard_differentia(self, text: str=None):
        """
        Determines whether the given volpiano melody ends
        with a differentia or not and if yes, strips it away.
        """
        self.volpiano = discard_differentia(self.volpiano, text=text)
    
    def get_range(self) -> tuple[int]:
        """
        Returns the range of the melody with respect to the last note:
        how many steps below and above this last note does the melody reach?

        Does NOT work with liquescents.
        """
        return get_range(self.volpiano)