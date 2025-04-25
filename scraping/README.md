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
to the infrastructure -- it takes roughly days to scrape the entire Cantus Index,
and we cannot block it -- and all the component databases -- for other people!


Sizes and timing
----------------

Cantus Index says it has a total of 59529 Cantus IDs.
If downloading each takes 10 seconds, that's 595290 seconds, or nearly 10,000 hours.
Paralellizing to 100 processes is still 100 hours, or 4 days.
This is way too much to just run without some watching and management.
In order to do that, we will proceed by **genre**. This way, we will get
meaningful subsets.

The lists of Cantus IDs will be stored in the ```cid_lists_by_genre``` directory.

If we go by priority of chant genres, from core to periphery:

1. A: Antiphons (13344)
2. R: Responsories (5990)
3. In: Introits (425)
4. Gr: Graduals (254)
5. Al: Alleluias (1125)
6. Tc: Tracts (153)
7. Of: Offertories (321)
8. Cm: Communions (386)

But there are also responsory verses, verses for mass repertoire (introits, graduals, 
alleluias, offertories, communions).

9. V: Responsory verses (9544)
10. InV: Introit verses (842)
11. GrV: Gradual verses (347)
12. AlV: Alleluia verses (107)
13. TcV: Tract verses (421)
14. OfV: Offertory verses (415)
15. CmV: Communion verses (751)

And then there are Versus ad Repetendum genres for many of the mass genres,
and many, many other genres (but those will be mostly peripheral).
For instance: there are 729 Invitatories (I)!

A complete table is in the ```genre_counts.txt``` file. (TODO)


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
We use the SLURM cluster at UFAL. 

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

----------------------------
Example of workflow:
