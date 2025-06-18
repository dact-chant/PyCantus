CantusCorpus 1.0
========================

Here we present dataset of plainchant intented for computational research.  
It has two parts:
- chants
- sources

The dataset consist of chants from Cantus Index. The database network was scraped using its JSON API genre-by-genre, and converted to easy-to use CSV files.  
Sources metadata were scraped from individual databases, again joined into CSV file.  
Description on scraping procedures with code can be found in the `scraping` directory.  

After scraping we did and some basic celaning.  

Main steps taken:
- join all chant files by genres into one file
- discarding duplicates in chantlinks
- genre standardization based on from what genre list in CI those records where from (issues only aroud Tp...)
- discarding data (from chants and sources), where for sources we cannot collect additional info
- add numerical century in sources
- inspecting duplicate sources - discarding and unifying duplicates

Details on that can be found in the `get_dataset_from_scrapes.ipynb`.  
____________________

### About dataset
Basic overview of size:
- number of chant entries: 888010
- number of them with some melody record: 60588
- number of them with melody record of more then 20 notes: 44625
_____
- number of sources with metadata: 2278
- number of sources with provenance information: 1606
- number of sources with century information: 2240
- number of sources with cursus information: 345

Mode distribution  
Main genre distribution  
Standard office distribution  


![Century distribution plot](img/century_distribution.png "Century distribution")


### Fileds
### Licence
The CantusCorpus is released under a CC BY-NC-SA 4.0 license, just like the Cantus Index itself.

### Citation
Please, if you use
