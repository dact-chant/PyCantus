CantusCorpus 1.0
========================

CantusCorpus 1.0 is a large dataset of Gregorian chant data intended for computational research.
The dataset consists of all chants that are searchable through Cantus Index, combining data from 10 individual
chant databases. Primarily these are catalogue records: which chants appear in which manuscripts.
What allows us to identify multiple instances of a chant across different manuscripts
is the **CantusID** mechanism, established from the long history of the Cantus Database.
Thus, CantusCorpus 1.0 has two components: **chants**, and **sources** (manuscripts).

CantusCorpus lies inherently downstream of the Cantus Database and the whole Cantus Index network
of compatbile chant databases: we do not revisit anyone's editorial decisions. However, the value
of this dataset is that the sum of all the editorial decisions made over the databases' decades of existence
are being made available as a dataset for computational research, together with the PyCantus library
that makes handling this dataset (almost) easy.

## Licence

The CantusCorpus is released under a CC BY-NC-SA 4.0 license, just like the Cantus Index itself.


## Dataset contents

Summary | |
----- | -----: |
Cantus Index was scraped on | 20th May 2025
CantusCorpus 1.0 was completed on | 19th June 2025
Number of chant entries | 888010
Number of them with some melody record |60588
Number of them with melody record of more than 20 notes | 44625
Number of sources with metadata | 2278
Number of sources with provenance information | 1606
Number of sources with century information | 2240
Number of sources with cursus information | 345

<br/><br/>

![Genre distribution plot](img/genre_distr.png "Main genres distribution")
*Main genres distribution*

![Office distribution plot](img/office_distr.png "Main offices distribution")
*Main offices distribution*

![Mode distribution plot](img/mode_distr.png "Main modes distribution")
*Main modes distribution*

![Century distribution plot](img/century_distr.png "Centuries distribution")
*Century distribution*

<br/>

## Data fields
### Chants
Field | Description
----- | ------
**siglum** (*) | Abbreviation for the source manuscript or collection (e.g., `CZ-Pu (Praha) VI G 3a`), RISM possibly.
**srclink** (*) | URL link to the source in the external database (e.g., `https://cantusbohemiae.cz/source/9147`).
**chantlink** (*) | URL link directly to the chant entry in the external database (e.g., `https://cantusbohemiae.cz/chant/38731`).
**folio** (*) | Folio information for the chant (e.g., `207v`).
**sequence** | The order of the chant on the folio (e.g., `1`).
**incipit** (*) | The opening words or phrase of the chant (e.g., `Virginis ob meritum manet hoc memorabile`).
**feast** | Feast or liturgical occasion associated with the chant (e.g., `Catharinae`).
**genre** | Genre of the chant, such as antiphon (A), responsory (R), hymn (H), etc. (e.g., `V`).
**office** | The office in which the chant is used, such as Matins (M) or Lauds (L) (e.g., `V`).
**position** | Liturgical position of the chant in the office (e.g., `01`).
**cantus_id** (*) | The unique Cantus ID associated with the chant (e.g., `"601551a"`).
**melody_id** | The unique Melody ID associated with the chant (e.g., `"001216m1"`).
**image** | URL link to an image of the manuscript page (e.g., `https://manuscripta.at/diglit/AT5000-589/0241`).
**mode** | Mode of the chant (e.g., `1`).
**full_text** | Full text of the chant (e.g., `Virginis ob meritum manet hoc memorabile signum`).
**melody** | Melody encoded in Volpiano (e.g., `1---dH---h7--h--ghgfed--gH---h--h---`).
**db** (*) | Code for the database providing the data, used for identification within CI (e.g., `"FCB"`).

### Sources
Field | Description
----- | ------
**title** | Name of manuscript
**siglum** (*) | Abbreviation for the source manuscript or collection (e.g., `CZ-Pu (Praha) VI G 3a`), RISM possibly.
**srclink** (*) | URL link to the source in the external database (e.g., `https://cantusbohemiae.cz/source/9147`).
**century** | Textual value identifying the century of the source. (e.g., `14th century`).
**num_century** | Number only representation of century value.
**provenance** | Place of origin or place of use of the source.
**cursus** | Secular (Cathedral, Roman) or Monastic cursus of the source.


Fields marked with (*) are required and thus should be present in all records of CantusCorpus 1.0.

We decided to collect these sources' metadata partly because we see how they can be useful for computational chant research, but also because of their support among source databases. Here we present an overview of what is supported by what database.  


![Genre distribution plot](img/source_metadata_support.png "")
*Overview of support for different source metadata among CI databases*

Databases in the list of *Other Cantus Index databases* are not analysed because they are not (at least currently) included in our scraping process, which is because their entries are not accessible via the Cantus Index JSON API. 

<br/>


## Obtaining the data

The database network was scraped using its JSON API genre-by-genre and converted to easy-to-use CSV files.  
Source metadata was scraped from individual databases and again joined into a CSV file.  
A description of scraping procedures with code can be found in the `scraping` directory.  

After scraping, we did some basic cleaning.  

Main steps taken:
- Join all chant files by genre into one file
- Discard duplicates in chantlinks
- genre standardisation based on the genre list in CI from which those records were from (issues only around Tp...)
- discard data (from chants and sources), where for sources we cannot collect additional info
- Add a numerical century in sources
- inspecting duplicate sources - discarding and unifying duplicates

Details on that can be found in the `get_dataset_from_scrapes.ipynb`.  
____________________

