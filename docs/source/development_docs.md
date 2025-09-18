# PyCantus Development Documentation

PyCantus is a lightweight Python library for loading 
and manipulating Gregorian chant data, e.g. the CantusCorpus v1.0 dataset.
The “division of labour” between the library and dataset is shown in the schema bellow. 
Most importantly, PyCantus implements a data model for CantusCorpus v1.0.
However, the library is an independent component, so the data model can be re-used for datasets assembled
from other sources of chant data (e.g. Corpus Monodicum database).
  
  
![Schema of PyCantus and CCv1.0 contributions.](_static/img/pycantus_schema_cleaned.png)
  
PyCantus functionality is introduced by a tutorial which guides the user through the steps required to prepare a sub-corpus for experiments. The library source code and documentation are available at [https://github.com/dact-chant/PyCantus](https://github.com/dact-chant/PyCantus).

## Content
- [Data Model](#data-model)
  - [Corpus](#corpus)  
  - [Chant](#chant)  
  - [Source](#source)  
  - [Melody](#melody)  

- [Loaders + validation](#loaders--validation)

- [Filtering & preprocessing](#filtering--preprocessing) 
    - [History of operations](#history-of-operations)  


## Data Model
The core of PyCantus is the data model the `Chant` and `Source` classes representing the corresponding items of the dataset,
a `Corpus` class to aggregate them, and a `Melody` class to support abstracting away from specific melody encodings in the future. (We are aware of the chant21 library, but we opted not to make music21 a core dependency of PyCantus.)

Classes related to data model has its implementations in `models` folder.

For all four data classes we can divide their data attributes into to groups:
- data related (data fields based on CantusCorpus v1.0 structure)
- functional (quality-of-life fields such as locking or more flexible melody handling)

Besides that, some of the data model classes has convenience methods described bellow.


Here is a simplified schema of the data model:

![PyCantus data model simplified schema.](_static/img/data_model_pycantus.png)

More detailed lists of attributes and methods follows.  

### Corpus

`Corpus` class represents a collection of chants and sources.
It provides methods for loading, filtering, and exporting data related to the chants and sources.

The only way to initialize `Corpus` is via load from CSV files, it is not possible from chants and sources lists. That is due to "good replicability practice" we wanted to emphasize.

#### Attributes:
- `chants_filepath (str)`: path to file with chants
- `sources_filepath (str)`: path to file with sources
- `chants_fallback_url (str)`: URL for chants file download, is used when loading from filepath fails
- `sources_fallback_url (str)`: URL for sources file download, is used when loading from filepath fails
- `other_download_parameters (dict)`: [not used yet]
- `is_editable (bool)`: indicates whether objects in Corpus should be locked
- `check_missing_sources (bool)`: indicates whether load should an raise exception if some chant refers to source that is not in sources
- `create_missing_sources (bool)`: indicates whether load should create Source entries for sources referred to in some of the chants and not being present in provided sources
- `_chants (list)`: list of `Chant`s in the corpus
- `_sources (list)`: list of `Source`s in the corpus 
- `operations_history (list)`: list of operations applied on the corpus (from predefined list - see methods with `@log_operation` decorator)


#### Locked attribute
The 'locking logic' is quite simple. We don't want people to shoot themselves in the foot, so we tried to force them to make changes in the state of their data (in `Corpus`) explicit. Besides that, it is also part of the 'good replicability' strategy we want to emphasize.

In the initialization of `Corpus` object, argument `is_editable` is passed (with default value set to `False`). 

Then getters and setters of `Corpus` were overwritten so the 'I am a locked corpus' logic is controlled. 

Value of the `is_editable` attribute is propagated into all Chants, Sources and Melodies in the Corpus with `Corpus._lock_chants()`, `Corpus._lock_sources()` and in `Chant.create_melody()`, where attribute `locked` is set to `True` if 'is not editable corpus'. In these objects it "operates" in the overwritten method `__settatr__`. You can set the value of the `locked` attribute freely -- because that makes the intervention in the data state explicit, but not impossible.

#### Methods
For easier work with the data few methods were implemented directly on `Corpus`.

- `export_csv(chants_path, sources_path)` - saves `Corpus` data back to CSV files on give paths
- 

### Chant

`Chant` class represents a single chant entry from some database.
It provides methods for creating, modifying, and exporting chant data in a standardized format.


#### Data related attributes:
- `siglum (str)`: \* Abbreviation for the source manuscript or collection (e.g., "A-ABC Fragm. 1"). Use RISM whenever possible.  
- `srclink (str)`: \* URL link to the source in the external database (e.g., "https://yourdatabase.org/source/123").  
- `chantlink (str)`: \* URL link directly to the chant entry in the external database (e.g., "https://yourdatabase.org/chant/45678").  
- `folio (str)`: \* Folio information for the chant (e.g., "001v").  
- `sequence (str)`: The order of the chant on the folio (e.g., "1").  
- `incipit (str)`: \* The opening words or phrase of the chant (e.g., "Non sufficiens sibi semel aspexisse vis ").  
- `feast (str)`: Feast or liturgical occasion associated with the chant (e.g., "Nativitas Mariae").
- `genre (str)`: Genre of the chant, such as antiphon (A), responsory (R), hymn (H), etc. (e.g., "V").
- `office (str)`: The office in which the chant is used, such as Matins (M) or Lauds (L) (e.g., "M").
- `position (str)`: Liturgical position of the chant in the office (e.g., "01").
- `cantus_id (str)`: The unique Cantus ID associated with the chant (e.g., "007129a").
- `melody_id (str)`: The unique Melody ID associated with the chant (e.g., "001216m1").
- `image (str)`: URL link to an image of the manuscript page, if available (e.g., "https://yourdatabase.org/image/12345").
- `mode (str)`: Mode of the chant, if available (e.g., "1").
- `full_text (str)`: Full text of the chant (e.g., "Non sufficiens sibi semel aspexisse vis amoris multiplicavit in ea intentionem inquisitionis").
- `melody (str)`: Melody encoded in volpiano, if available (e.g., "1---dH---h7--h--ghgfed--gH---h--h---").
- `century (str)`: Number identifying the century of the source. If multiple centuries apply, the lowest number should be used. (e.g., "12").
- `db (str)`: \* Code for the database providing the data, used for identification within CI (e.g., "DBcode").

- `rite (str)`: Value of liturgical rite of the chant (not yet in CI, but possibly to be (so we want to be ready), not in export)

#### Functional attributes:
- `locked (bool)`: Indicates whether the object is locked for editing. If True, no attributes can be modified.
- `_has_melody (bool)`: True if the chant has a melody, False otherwise.
- `melody_object (Melody)`: If the chant has a melody, this should be an instance of the Melody class representing the chant's melody once created.

#### Property methods
Some of the methods of `Chant` are decorated with `@property` so that they can be called as property (attribute) of the object, because that is the intuitive comprehension we have about them.  
These are:
- `is_complete_chant` - bool value (checks presence of full text and long enough melody)
- `to_csv_row` - string value, method constructs 

So we can have a piece of code:
```
if chant.is_complete_chant:
    print(chant.to_csv_row)
```

#### Static methods


#### Methods

`Chant` has only one standard method which is `create_melody()`. It 


### Source
`Source` class represents a single source entry from some database.
It provides methods for creating, modifying, and exporting source data in a standardized format.


#### Data related attributes:
- `title (str)`: \* Name of the source (can be same as siglum)
- `srclink (str)`: \* URL link to the source in the external database (e.g., "https://yourdatabase.org/source/123").
- `siglum (str)`: \* Abbreviation for the source manuscript or collection (e.g., "A-ABC Fragm. 1"). Use RISM whenever possible.
- `numeric_century (int)`: Integer representing the value of century field.
- `century (str)`: Century of source origin.
- `provenance (str)`: Name of the place of source origin.
- `cursus (str)`: Secular (Cathedral, Roman) or Monastic cursus of the source. 

#### Functional attributes:
- locked (bool): Indicates whether the object is locked for editing. If True, no attributes can be modified. (functional attribute)

#### Property methods

#### Static methods



### Melody
`Melody` class represents a single chant melody.

It is linked to a specific chant record via `chantlink` as an unique chant record identifier.  

Right now, it is designed in volpiano-centric way, meaning it holds only the volpiano representation of the chant melody, if present. But it can be extended to hold other representations in the future (via new optional parameters).

We take the `volpiano.utils` as already prepared methods (functions) for working with volpiano and just wrapped them into `Melody` class methods. 
For more detailed documentation of the methods, see the `volpiano/utils.py` module.

#### Data related attributes
Here we see attributes. until some modification of `volpiano`, same to what is in `Chant` record directly, having these here should just make things more convenient for working with melodies (e.g. when we want to take only list of melodies from corpus while not being interested in source information in such situation, while still being able to get it form `chantlink` when needed).

- `volpiano (str)`: The melody encoded in volpiano notation.
- `chantlink (str)`: URL link directly to the chant entry in the external database.
- `cantus_id (str)`: The Cantus ID associated with the chant.
- `raw_volpiano (str)`: The original volpiano string before any processing.
- `mode (str)`: Mode of the melody (e.g., "1").

        

#### Functional attributes
- `locked (bool)`: Indicates if the object is locked for editing.

#### Methods
These are mostly wrappers for methods from `volpiano.utils` being applied to `Melody.volpiano`.




## Loaders + validation
The `data.load_dataset(...)` function from the `data` module (implemented in `data.py`) is used to load the dataset into the Corpus object and collect all needed parameters as well as .


Data are loaded into the `Corpus` class via a `CsvLoader` object (implemented in `dataloaders/loader.py`).
The loader also handles the possible download of missing CSV files from provided fallback URL addresses and 
validation. Given the lack of controlled vocabularies, currently it cannot do more than check whether mandatory fields and their values are present and also optionally check unavailable source records (arguments `check_missing_sources` and `create_missing_sources`).

While loading the data `CsvLoader` creates `Source.numeric_century` values from given `century` value (see `get_numerical_century(str)` function in `dataloaders/loader.py`).

## Filtering & preprocessing

Preprocessing  besides filtering is implemented in functions of `Corpus` (such as `drop_empty_sources()` and similar ones).

For filtering class `Filter` is introduced (implemented in `filtration/filter`). It stores values for each data field of `Chant` and `Source` that has to be included in or excluded from the resulting sub-corpus.

Filtration is supposed to be called on `Corpus` with `apply_filter(Filter)` method, internally method `apply(chants, sources)` of the passed `Filter` is called. This methods iterates over passed `Chants` and `Sources` and keeps those meeting the filtration criteria (include and exclude values definitions).

The setup can be stored in YAML file (simple string representation) with `export_yaml` and then loaded into `Filter` with `import_yaml(path)` or `import_string(yaml_string)` methods on `Filter` .



### History of operations

To support replicability we add sort of logging for selected operations so order of applied methods can be stored for later. For that there is `HistoryEntry` class, objects of whom are stored in a list that is a attribute of the `Corpus` class.

The process is secured using a decorator `@log_operation`, that has its implementation in `history/utils.py`.

Methods that are saved into `self.operations_history` of `Corpus`:
- `drop_duplicate_chants()`
- `drop_duplicate_sources()`
- `keep_melodic_chants()`
- `drop_empty_sources()`
- `drop_small_sources_data(int)`
- `apply_filter(Filter)`
- `drop_incomplete_chants()`
- `drop_incomplete_chants()`
- and also if `Corpus.create_missing_sources` is `True`, then that is noted to the history in `Corpus` initialization

Whole history can be represented as one human-readable string via calling `get_operations_history_string()` method on `Corpus`.

