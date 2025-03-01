import csv
import os


def load_cantus_corpus(cantus_corpus_root_path: str) -> (list[dict[str, str]], list[str]):
    """Load the CantusCorpus chants data. Returns the dataset loaded as a csv.DictReader output,
    and the ordered chant column labels.

    :param cantus_corpus_root_path: The path to the root of the CantusCorpus dataset.
                                    (The one that contains the 'README.md' file.)

    :return: A tuple of the chants dataset and the chant column labels.
    """
    chants_path = os.path.join(cantus_corpus_root_path, 'csv', 'chant.csv')
    with open(chants_path, 'r', newline='') as fh:
        chants_reader = csv.DictReader(fh)
        chants = [row for row in chants_reader]
        # Remember the column labels
        chant_column_labels = chants_reader.fieldnames
    return chants, chant_column_labels
