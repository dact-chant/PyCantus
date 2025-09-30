#!/usr/bin/env python
"""
This module contains Source class, which represents a single source entry from some database.
It provides methods for creating, modifying, and exporting source data in a standardized format.
"""

__version__ = "1.0.0"
__author__ = "Anna Dvorakova"


MANDATORY_SOURCES_FIELDS = {'title', 'srclink', 'siglum'}
OPTIONAL_SOURCES_FIELDS = {'century', 'provenance', 'numeric_century', 'cursus'}
EXPORT_SOURCES_FIELDS = ['title', 'siglum','century', 'provenance', 'srclink', 'numeric_century', 'cursus']
NON_EXPORT_SOURCES_FIELDS = ['locked']


class Source():
    """
    Represents one source entry in database.

    Attributes:
        title (str): \* Name of the source (can be same as siglum)
        srclink (str): \* URL link to the source in the external database (e.g., "https://yourdatabase.org/source/123").
        siglum (str): \* Abbreviation for the source manuscript or collection (e.g., "A-ABC Fragm. 1"). Use RISM whenever possible.
        numeric_century (int): Integer representing the value of century field.
        century (str): Century of source origin.
        provenance (str): Name of the place of source origin.
        cursus (str): Secular (Cathedral, Roman) or Monastic cursus of the source. 

        locked (bool): Indicates whether the object is locked for editing. If True, no attributes can be modified. (functional attribute)
    """

    def __init__(self,
                 title,
                 srclink, 
                 siglum,
                 numeric_century=None,
                 century=None,
                 provenance=None,
                 cursus=None):
        """
        Initialize the Source. 
        Args corresponds to class non-functional attributes.
        """
        self.locked = False # Indicates if the object is locked for editing
        self.title = title
        self.srclink = srclink
        self.siglum = siglum
        self.numeric_century = numeric_century
        self.century = century
        self.provenance = provenance
        self.cursus = cursus
    
    # setter
    def __setattr__(self, name, value):
        if name != "locked" and getattr(self, "locked", False):
            raise AttributeError(f"Cannot modify '{name}' because the object is locked.")
        super().__setattr__(name, value)


    def __str__(self):
        source_string = self.siglum + '\n'
        source_string += f"  Srclink: {self.srclink}\n"
        return source_string

    @property
    def to_csv_row(self):
        """
        Returns data fields of Source in "to be pasted to the csv export file" form.
        
        Returns:
            str: data of object as standardized csv row
        """
        csv_row = []
        for attr_name in EXPORT_SOURCES_FIELDS:
            attr_value = self.__getattribute__(attr_name)
            if attr_value is not None:
                attr_value = str(attr_value)
                if ',' in attr_value:
                    attr_value = f'"{attr_value}"'  # Enclose in quotes if it contains a comma
                csv_row.append(attr_value)
            else:
                csv_row.append('')
        return ','.join(csv_row)
    
    @staticmethod
    def header() -> str:
        """
        Constructs proper csv header of sources, e.g. for export.

        Returns:
            str: the header for the CSV file, which includes all mandatory and optional fields.
        """
        return ','.join(EXPORT_SOURCES_FIELDS)