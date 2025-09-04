#!/usr/bin/env python
"""
This module contains the Chant class, which represents a single chant entry from some database.
It provides methods for creating, modifying, and exporting chant data in a standardized format.
"""

import pandas as pd
import os
from importlib import resources as impresources

import pycantus.static as static
from pycantus.models.melody import Melody


__version__ = "0.0.5"
__author__ = "Anna Dvorakova"

@staticmethod
def get_rite_dict() -> dict[str]:
    """
    Loads data about rites of genres.

    Returns:
        dict: {genre : rite}
    """
    genre_file = impresources.files(static) / "genre.csv"
    with genre_file.open("rt") as f:
        genre = pd.read_csv(f)
    return genre.set_index('genre_name')['rite'].to_dict()
GENRE_TO_RITE = get_rite_dict()

MANDATORY_CHANTS_FIELDS = {'cantus_id', 'incipit', 'srclink', 'siglum','chantlink', 'folio', 'db'}
OPTIONAL_CHANTS_FIELDS = {'sequence', 'feast', 'genre', 'office', 'position', 'melody_id', 'image', 'mode',
                               'full_text', 'melody', 'century', 'rite'}
NON_EXPORT_CHATN_FIELDS = ['locked', 'rite', '_has_melody', 'melody_object']
EXPORT_CHANTS_FIELDS = ['cantus_id', 'incipit', 'siglum', 'srclink', 'chantlink', 'folio', 'db', 'sequence', 'feast', 'genre',
                     'office', 'position', 'melody_id', 'image', 'mode', 'full_text', 'melody', 'century']


class Chant():
    """
    Represents one chant entry (record of chant occurrence) in database.

    Attributes:
        siglum (str): \* Abbreviation for the source manuscript or collection (e.g., "A-ABC Fragm. 1"). Use RISM whenever possible.  
        srclink (str): \* URL link to the source in the external database (e.g., "https://yourdatabase.org/source/123").  
        chantlink (str): \* URL link directly to the chant entry in the external database (e.g., "https://yourdatabase.org/chant/45678").  
        folio (str): \* Folio information for the chant (e.g., "001v").  
        sequence (str): The order of the chant on the folio (e.g., "1").  
        incipit (str): \* The opening words or phrase of the chant (e.g., "Non sufficiens sibi semel aspexisse vis ").  
        feast (str): Feast or liturgical occasion associated with the chant (e.g., "Nativitas Mariae").
        genre (str): Genre of the chant, such as antiphon (A), responsory (R), hymn (H), etc. (e.g., "V").
        office (str): The office in which the chant is used, such as Matins (M) or Lauds (L) (e.g., "M").
        position (str): Liturgical position of the chant in the office (e.g., "01").
        cantus_id (str): The unique Cantus ID associated with the chant (e.g., "007129a").
        melody_id (str): The unique Melody ID associated with the chant (e.g., "001216m1").
        image (str): URL link to an image of the manuscript page, if available (e.g., "https://yourdatabase.org/image/12345").
        mode (str): Mode of the chant, if available (e.g., "1").
        full_text (str): Full text of the chant (e.g., "Non sufficiens sibi semel aspexisse vis amoris multiplicavit in ea inten]tionem inquisitionis").
        melody (str): Melody encoded in volpiano, if available (e.g., "1---dH---h7--h--ghgfed--gH---h--h---").
        century (str): Number identifying the century of the source. If multiple centuries apply, the lowest number should be used. (e.g., "12").
        db (str): \* Code for the database providing the data, used for identification within CI (e.g., "DBcode").

        rite (str): (not yet in CI, but possibly to be (so we want to be ready), not in export)

        locked (bool): Indicates whether the object is locked for editing. If True, no attributes can be modified. (functional attribute)
        _has_melody (bool): True if the chant has a melody, False otherwise. (functional attribute)
        melody_object (Melody): If the chant has a melody, this should be an instance of the Melody class representing the chant's melody once created. (functional attribute)
    
    (Fields marked with an asterisk (*) are obligatory and must be included in every record. 
    Other fields are optional but recommended when data is available.)
    """

    def __init__(self, 
                 cantus_id : str,
                 incipit : str,
                 siglum : str, 
                 srclink : str, 
                 chantlink : str,
                 folio : str,
                 db : str,
                 sequence=None,
                 feast=None,
                 genre=None,
                 office=None,
                 position=None,
                 melody_id=None,
                 image=None,
                 mode=None,
                 full_text=None,
                 melody=None,
                 century=None,
                 rite=None,
                ):
        """
        Initialize the Chant. 
        Args corresponds to class non-functional attributes.
        """
        self.locked = False  # Indicates if the object is locked for editing
        self.cantus_id = cantus_id
        self.incipit = incipit
        self.siglum = siglum
        self.srclink = srclink
        self.chantlink = chantlink
        self.folio = folio
        self.db = db
        self.feast = feast
        self.genre = genre
        self.office = office
        self.sequence = sequence
        self.position = position
        self.mode = mode
        self.melody_id = melody_id
        self.melody = melody
        self.century = century
        self.full_text = full_text
        self.image = image

        if rite is not None:
            self.rite = rite
        else: # add rite based on the genre
            self.rite = GENRE_TO_RITE.get(genre, None)
        
        self._has_melody = False
        self.melody_object = None

        if self.melody is not None:
            self._has_melody = True
            self.create_melody()
            
    # setter
    def __setattr__(self, name, value):
        if name != "locked" and getattr(self, "locked", False):
            raise AttributeError(f"Cannot modify '{name}' because the object is locked.")
        super().__setattr__(name, value)

    @staticmethod
    def header() -> str:
        """
        Constructs proper csv header of chants, e.g. for export.

        Returns:
            str: the header for the CSV file, which includes all mandatory and optional fields.
        """
        return ','.join(EXPORT_CHANTS_FIELDS)


    def __str__(self) -> str:
        return str(self.chantlink) + ' : ' + str(self.cantus_id)
    
    @property
    def to_csv_row(self) -> str:
        """
        Returns data fields of Chant in "to be pasted to the csv export file" form.
        
        Returns:
            str: data of object as standardized csv row
        """
        csv_row = []
        for attr_name in EXPORT_CHANTS_FIELDS:
            attr_value = self.__getattribute__(attr_name)
            if attr_value is not None:
                csv_row.append(attr_value)
            else:
                csv_row.append('')
        return ','.join(csv_row)
    
    def create_melody(self):
        """
        Creates a Melody object for the chant if it has a melody.
        Expects volpiano to be provided.
        """
        if self._has_melody:
            self.melody_object = Melody(self.melody, self.chantlink, self.cantus_id, self.mode)