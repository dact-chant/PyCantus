"""
This module contains Source class, which represents a single source entry from some database.
It provides methods for creating, modifying, and exporting source data in a standardized format.
"""

__version__ = "0.0.1"
__author__ = "Anna Dvorakova"

class Source():
    """
    pycantus Source class
        - represents one source entry in database
    """
    MANDATORY_SOURCES_FIELDS = {'title', 'srclink', 'siglum'}
    OPTIONAL_SOURCES_FIELDS = {'century', 'provenance'}
    EXPORT_FIELDS = ['title', 'siglum','century', 'provenance', 'srclink',]
    NON_EXPORT_FIELD = ['locked']

    def __init__(self,
                 title,
                 srclink, 
                 siglum,
                 century=None,
                 provenance=None):
        """
        """
        self.locked = False # Indicates if the object is locked for editing
        self.title = title
        self.srclink = srclink
        self.siglum = siglum
        self.century = century
        self.provenance = provenance
    
    # setter
    def __setattr__(self, name, value):
        if name != "locked" and getattr(self, "locked", False):
            raise AttributeError(f"Cannot modify '{name}' because the object is locked.")
        super().__setattr__(name, value)


    def __str__(self):
        return self.siglum

    @property
    def to_csv_row(self):
        """
        Returns data of class as standardized csv row
        """
        csv_row = []
        for attr_name in self.EXPORT_FIELDS:
            attr_value = self.__getattribute__(attr_name)
            if attr_value is not None:
                csv_row.append(attr_value)
            else:
                csv_row.append('')
        return ','.join(csv_row)
    
    @property
    def header(self) -> str:
        """
        Returns the header for the CSV file, which includes all mandatory and optional fields.
        """
        return ','.join(self.EXPORT_FIELDS)