Cantus Index Full Scrape
========================

Cantus Index is an amazing tool for digital musicology.
All of the data in Cantus Index is public, mostly produced with public
funding from scientific grants. However, the data is not available as
a clear export and the computational infrastructure is less than ideal:
fragile. In order to bring all the information that has been made available
through Cantus Index to computational research, it has to be properly exported
and stored in a static, well-documented format.

This repository is a collection of scripts and documentation that will
allow us to scrape all the data from Cantus Index and store it in a
bunch of JSON files. These files are something that Cantus Index creates
for itself as it is used. The JSON files are a snapshot of the data in
all 20-ish component databases at the point when a user last requested
a refresh. There is a (semi-secret) endpoint that Cantus Index provides
for these JSON files directly. We can use this endpoint after requesting
refreshes!

The issue is that the refresh takes quite a bit of time, because it takes
some 20-odd requests (at least!) from the Cantus Index server to the individual
database servers. So, the process needs to be paralellized, and also sensitive
to the infrastructure - it takes roughly days to scrape the entire Cantus Index,
and we cannot block it - and all the component databases - for other people!


Sizes and timing
----------------

Cantus Index says it has at least total of 59529 Cantus IDs.
If downloading each takes 10 seconds, that's 595290 seconds at least, or nearly 10,000 hours.
Paralellizing to 100 processes is still 100 hours, or 4 days.
This is way too much to just run without some watching and management.
In order to do that, we will proceed by **genre**. This way, we will get
meaningful subsets.

The lists of Cantus IDs will be stored in the ```cid_lists_by_genre``` directory.


Workflow
--------

The basic workflow is as follows:

1. Find out what Cantus IDs are available.
2. For each Cantus ID, refresh CI and then download the JSON from its CI endpoint.

Because there are many thousands of Cantus IDs and each refresh can take some
10 seconds, we need to paralellize this process. (And introduce timeouts in between,
so we might end up with 20 seconds per Cantus ID.)

We therefore split the workflow as follows:

1. Find out what Cantus IDs are available.
2. For each set of K Cantus IDs:
    1. For each Cantus ID in the set, refresh CI and then download the JSON from its CI endpoint. 

The first step is done by the `scrape_cid_values.py` script.
The inner step is done by the `scrape_ci_jsons.sh` script.

Because of the long time this all will take to complete, we will split it into
human-manageable chunks by chant genre. This splitting is a bit more complex.
We use the SLURM cluster.  
  
For each chant genre, a separate chunking
is performed. For a genre, the `prepare_slurm_script.sh` script is run to generate
a SLURM wrapper for the individual chunks, each again in their own `chunk_${i}`
subdirectory of the genre directory. The wrapper script, 
`${GENRE_DIR}/${CHUNK_DIR}/slurm_wrapper.sh`, is finally ready to be run on the SLURM cluster
with `cd ${GENRE_DIR}/${CHUNK_DIR}/; sbatch slurm_wrapper.sh`.

Then, the `run_slurm_scripts.sh` script should be run from a SLURM head node
from the directory containing this README.

Finally, after the jobs finish, the JSONs can be collected from 
the `genre_dir/chunk_${i}/jsons` directories via `collect_slurm_results.sh`.

After that we might want to get information about sources of collected chants which can be done via running `scrape_source_csv.py`.  

We have scrapers ready for those source databases:
- Cantus Database (https://cantusdatabase.org/)
- MMMO Database (https://musmed.eu/)
- Slovak Early Music Database (https://cantus.sk/)
- Cantus Fontes Bohemiae (https://cantusbohemiae.cz)
- Cantus Planus in Polonia (https://cantusplanus.pl/)
- Portuguese Early Music Database (https://pemdatabase.eu/)
- Spanish Early Music Manuscripts Database (https://musicahispanica.eu)
- Hungarian Chant Database (https://hun-chant.eu/)
- Medieval Music Manuscripts from Austrian Monasteries (https://austriamanus.org/)
- Codicologica et Hymnologica Bohemica Liturgica (https://hymnologica.cz/)

----------------------------  

**Example of particular workflow steps:**
1) run `get_cids_lists.sh` 
    - calls `scrape_cid_values.py` for each genre from `static/genre.csv` (first column is expected to be CI abreviation of genre)
    - outputs GENRE.txt list of CIDs into cantus_ids_list_by_genre directory

2) run `get_scripts_prep_by_genre.sh`
    - calls `prepare_slurm_script.sh` for all genre from `static/genre.csv`
    - that creates diectory with scraping scripts for each genre in `static/genre.csv`

3) check that `wrapper_logs` folder in same directory as `run_slurm_scripts.sh` exists

4) run `run_slurm_scripts.sh` for each genre (to somehow reasonably use resources, some genre are quite exhaustive)
    - runs all `scrape_ci_json.sh` by prepared chunks of CIDs in proper `slurm_wrapper.sh` runs

5) run `get_collected_by_genre.sh`
    - runs `collect_scrape_results.sh` for each genre in `static/genre.csv`
    - that joins all collected json files into one `all_jsons` directory
    - and then runs `cantus_json_to_csv.py` script to create CSV CantusCorpus style file from that collected json records
    - do not get scared when 
------  

6) run `scrape_sources_csv.py` for all those CSV files whose sources info you want to collect (with correct arguments) 
    - possibly concatenate all genre files into one big file and collect sources on that one  
  
  
Finally, do not forget that after collecting all the data, some cleaning (e.g. looking for duplicates etc.) might be needed.