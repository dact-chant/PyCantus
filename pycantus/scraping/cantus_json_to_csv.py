#!/usr/bin/env python
"""This is a script that converts a JSON file downloaded
from Cantus Index through the json-cid interface into a CSV
file that can be uploaded into the database.

Will throw away items that do not have a record for one or more
required fields:

    incipit
    siglum
    srclink
    chantlink
    folio
    db
    cantus_id

This can be relaxed by --allow_no_incipit, --allow_no_siglum

"""
from __future__ import print_function, unicode_literals
import argparse
import json
import csv
import logging
import os
import pprint
import time

__version__ = "0.0.2"
__author__ = "Jan Hajic jr."
__changelog__ = {
    "0.0.2": {"updated_by": "Anna Dvorakova", "date": "2025-02-27", "changes": "adapt to new DB web pages"},
}


CSV_KEYS = [
    'id',
    'corpus_id',
    'chantlink',
    'incipit',
    'cantus_id',
    'mode',
    'finalis',
    'differentia',
    'siglum',
    'position',
    'folio',
    'sequence',
    'marginalia',
    'cao_concordances',
    'feast',
    'feast_code',
    'genre',
    'office',
    'srclink',
    'melody_id',
    'full_text',
    'full_text_manuscript',
    'volpiano',
    'notes',
    'dataset_name',
    'dataset_idx',
    'db',               # This field is not among CantusCorpus v0.2 CSV fields.
    'image_link',       # This field is not among CantusCorpus v0.2 CSV fields.
]

REQUIRED_NONNULL_CSV_KEYS = [
    'incipit',
    'siglum',
    'srclink',
    'chantlink',
    'folio',
    'db',
    'cantus_id',
]

JSON_KEYS = [
            "siglum",
            "incipit",
            "fulltext",
            "melody",
            "srclink",
            "chantlink",
            "folio",
            "feast",
            "genre",
            "office",
            "position",
            "image",
            "mode",
            "db",
]

JSON_KEYS2CSV_KEYS = {
    'siglum': 'siglum',
    'incipit': 'incipit',
    'fulltext': 'full_text',
    'melody': 'volpiano',
    'folio': 'folio',
    'feast': 'feast',
    'genre': 'genre',
    'office': 'office',
    'position': 'position',
    'mode': 'mode',
    'image': 'image_link',
    'srclink': 'srclink',
    'chantlink':'chantlink',
    'db' : 'db'
}
CSV_KEYS2JSON_KEYS = {v: k for k, v in JSON_KEYS2CSV_KEYS.items() }
CSV_KEYS2JSON_KEYS['feast_code'] = 'feast'

# List of CSV columns to which nothing from JSON can be used to fill information
CSV_KEYS_NOT_IN_JSON = [k for k in CSV_KEYS if k not in JSON_KEYS2CSV_KEYS.values()]


# Some fields unfortunately require processing of their contents based
# on mappings between names in JSON and computed IDs in csv.
def load_mapping(path_to_file, from_column, to_column, delimiter=","):
    column_names = []
    mapping = {}
    with open(path_to_file) as inputfile:
        csv_reader = csv.reader(inputfile, delimiter=delimiter)
        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                column_names = row
                line_count += 1
                continue
            mapping[row[from_column]] = row[to_column]
    return mapping

# For current state of data we decided to use CI office values of office
"""
OFFICE_MAP_CSV2JSON = load_mapping(
    path_to_file=os.path.join(os.path.dirname(__file__), 'static', 'office.csv'),
    from_column=0, to_column=1
)
OFFICE_MAP_JSON2CSV = {v: k for k, v in OFFICE_MAP_CSV2JSON.items()}
def office2office_id(office: str):
    office_id = OFFICE_MAP_JSON2CSV[office]
    return office_id
"""

# For current state of data we decided to use CI feast codes (column 1)
FEAST_MAP_CSV2JSON = load_mapping(
    path_to_file=os.path.join(os.path.dirname(__file__), 'static', 'feast_CI.csv'),
    from_column=1, to_column=0
)
FEAST_MAP_JSON2CSV = {v: k for k, v in FEAST_MAP_CSV2JSON.items()}
FEAST_MAP_JSON2CSV_LOWER = {k.lower(): v for k, v in FEAST_MAP_JSON2CSV.items()}
FEAST_MAP_CSV_LOWER2CSV_UPPER = {v.lower(): v for k, v in FEAST_MAP_CSV2JSON.items()}

def feast2feast_id(feast: str):
    try:
        feast_id = FEAST_MAP_JSON2CSV_LOWER[feast]
    except KeyError:
        logging.warning('Feast {} not found!'.format(feast))
        raise
    return feast_id


# For current state of data we decided to use CI genre values of genre
"""
GENRE_MAP_CSV2JSON = load_mapping(
    path_to_file=os.path.join(os.path.dirname(__file__), 'static', 'genre.csv'),
    from_column=0, to_column=1
)
GENRE_MAP_JSON2CSV = {v: k for k, v in GENRE_MAP_CSV2JSON.items()}
def genre2genre_id(genre: str):
    genre_id = GENRE_MAP_JSON2CSV[genre]
    return genre_id
"""
JSON_KEYS_REQUIRING_PROCESSING = {
    #'office': office2office_id,
    'feast': feast2feast_id,
    #'genre': genre2genre_id,
}




def convert_json_data_to_csv_data(json_data,
                                  external_csv_fields=dict(),
                                  required_nonnul_csv_fields=REQUIRED_NONNULL_CSV_KEYS):
    """Takes a list of JSON chant objects and converts them to
    PyCantus-compatible CSV for dataset upload.

    :param json_data: A parsed Cantus Index json.

    :param external_csv_fields: A dictionary of constant values for CSV fields
        that are not among the JSON fields but should be added to the output csv.

    :param required_nonnul_csv_fields: Fields that have to be in the CSV for an item
        to not be filtered out.

    :return:
    """
    csv_data = []
    CSV_EMPTY_VALUE = ''

    logging.debug('Processing JSON data:')
    logging.debug(pprint.pformat(json_data))

    chants = json_data['chants']

    if isinstance(chants, dict): # case where chants is dict with num keys
        chants = list(chants.values())

    for chant_json in chants:
        logging.debug('Processing JSON item:')
        logging.debug(pprint.pformat(chant_json))

        csv_row = []

        _skip_item = 0

        for idx_csv_key, csv_key in enumerate(CSV_KEYS):

            logging.debug('Processing CSV key no.{}: {}, csv row length: {}'.format(idx_csv_key, csv_key, len(csv_row)))

            # If the key is something not mapped:
            if csv_key not in CSV_KEYS2JSON_KEYS:
                # Check if it is externally supplied (e.g. a cantus ID)
                if csv_key in external_csv_fields:
                    logging.debug('\tKey {} externally supplied'.format(csv_key))
                    csv_row.append(external_csv_fields[csv_key])
                else:
                    logging.debug('\tKey {} not expected in JSON, not supplied externally. Adding empty.'.format(csv_key))
                    csv_row.append(CSV_EMPTY_VALUE)

            else:
                json_key = CSV_KEYS2JSON_KEYS[csv_key]
                try:
                    json_value = chant_json[json_key]
                    logging.debug('\tKey {} has value in json: {}'.format(csv_key, json_value))
                except KeyError:
                    if csv_key in required_nonnul_csv_fields:
                        logging.info('JSON item does not contain required field {}.'
                                    ' SKIPPING ITEM.\nJSON:\n{}'.format(csv_key, chant_json))
                        _skip_item = 1
                        break  # No need to process the other fields if the item gets skipped.
                    else:
                        logging.info('JSON item does not contain field {}. Using empty value.\n'
                                    'JSON:\n{}'.format(csv_key, chant_json))
                        #csv_row.append(CSV_EMPTY_VALUE)
                        json_value = CSV_EMPTY_VALUE

                except TypeError as e:
                    logging.error('JSON key {}: invalid key for json_item {}'.format(json_key, pprint.pformat(chant_json)))
                    # logging.error('JSON data: {}'.format(pprint.pformat(json_data)))
                    raise e

                # Check for non-null presence of a required value.
                if ((not json_value) or (json_value == '')) and (csv_key in required_nonnul_csv_fields):
                    logging.debug('JSON item does not contain value for required field'
                                ' {}, or mapping is missing. SKIPPING ITEM. \nJSON:\n{}'
                                ''.format(csv_key, chant_json))
                    _skip_item = 1
                    break  # No need to process the other fields if the item gets skipped.

                csv_value = json_value
                # Transform JSON value into CSV value if necessary, add both
                if csv_key == 'feast':
                    logging.debug('\t(JSON key {} requires processing.)'.format(json_key))
                    json_processing_fn = JSON_KEYS_REQUIRING_PROCESSING[json_key]
                    try:
                        feast_code = json_processing_fn(json_value.lower())
                        csv_value = FEAST_MAP_CSV_LOWER2CSV_UPPER[json_value.lower()]
                    except KeyError:
                        if csv_key in required_nonnul_csv_fields:
                            logging.debug('Could not process required field {} from JSON item.'
                                        ' SKIPPING ITEM.\nJSON:\n{}'.format(csv_key, chant_json))
                            _skip_item = 1
                            break
                        else:
                            logging.debug('Could not process JSON key {} with value {}. Using empty value.\n'
                                        'JSON:\n{}'
                                        ''.format(json_key, json_value, chant_json))
                            feast_code = CSV_EMPTY_VALUE

                elif csv_key == 'feast_code':
                    csv_value = feast_code
                    feast_code = ''


                logging.debug('\tAdding {}-th CSV value to row: "{}"'.format(len(csv_row) + 1, csv_value))
                csv_row.append(csv_value)

        if _skip_item:
            _skip_item = 0
        else:
            if len(csv_row) != len(CSV_KEYS):
                raise ValueError("Generated line has {} fields instead of target {}!\n"
                                 "Line:\n{}\nJSON item:\n{}\nFields and row:\n{}"
                                 "".format(len(csv_row),
                                           len(CSV_KEYS),
                                           list(enumerate(csv_row)),
                                           chant_json,
                                           list(zip(CSV_KEYS, csv_row))))
            csv_data.append(csv_row)

    return csv_data


def write_csv_data(csv_data, csv_writer):
    """Given a CSV writer over an open file handle, writes the CSV data.
    Adds header row at the beginning.

    :param csv_data: A list of lists of CSV values.
    :param csv_writer:
    :return:
    """
    header_row = CSV_KEYS
    csv_writer.writerow(header_row)
    for row in csv_data:
        csv_writer.writerow(row)


def _get_required_csv_fields(args):
    required_keys = REQUIRED_NONNULL_CSV_KEYS
    """
    if args.allow_all:
        return required_keys

    if not args.allow_no_full_text:
        required_keys.append('full_text')
    if not args.allow_no_siglum:
        required_keys.append('siglum')
    if not args.allow_no_incipit:
        required_keys.append('incipit')
    if not args.allow_no_volpiano:
        required_keys.append('volpiano')
    """
    return required_keys


def build_argument_parser():
    parser = argparse.ArgumentParser(description=__doc__, add_help=True,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('-i', '--input_json', action='store',
                        help='Single input file mode. Cannot be used together with --input_dir.')
    parser.add_argument('--input_dir', action='store',
                        help='Combines output from all JSON files in this directory.'
                             ' Cannot be used together with -i/--input_json.')
    parser.add_argument('--test_run', action='store', type=int, default=-1,
                        help='Only process this many files from the directory as a test run.')

    parser.add_argument('--treat_filenames_as_cid', action='store_true',
                        help='To be used with --input_dir. If set, will assume the JSON file names'
                             ' in the input dir are Cantus IDs.')

    parser.add_argument('--allow_no_full_text', action='store_true',
                        help='Output to JSON also items that do not contain full_text.')
    parser.add_argument('--allow_no_siglum', action='store_true',
                        help='Output to JSON also items that do not contain sigla. NOT RECOMMENDED.')
    parser.add_argument('--allow_no_incipit', action='store_true',
                        help='Output to JSON also items that do not contain incipits.')
    parser.add_argument('--allow_no_volpiano', action='store_true',
                        help='Output to JSON also items that do not contain melody.')
    parser.add_argument('--allow_all', action='store_true',
                        help='No required fields.')

    parser.add_argument('-o', '--output_csv', action='store', required=True)

    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Turn on INFO messages.')
    parser.add_argument('--debug', action='store_true',
                        help='Turn on DEBUG messages.')

    return parser


def main(args):
    logging.info('Starting main...')
    _start_time = time.process_time()

    _REQUIRED_NONNULL_CSV_KEYS = _get_required_csv_fields(args)

    json_data = []
    csv_data = []

    if args.input_json:
        with open(args.input_json) as input_json:
            json_data = json.load(input_json)
            _EXTERNAL_CSV_FIELDS = {}
            if args.treat_filenames_as_cid:
                cantus_id = input_json[:-5]    # the '.json' suffix is an invariant now
                _EXTERNAL_CSV_FIELDS = {'cantus_id': cantus_id}

            csv_data = convert_json_data_to_csv_data(json_data,
                                                     required_nonnul_csv_fields=_REQUIRED_NONNULL_CSV_KEYS,
                                                     external_csv_fields=_EXTERNAL_CSV_FIELDS)

    elif args.input_dir:
        input_jsons = os.listdir(args.input_dir)
        
        for input_json_idx, input_json in enumerate(input_jsons):

            if args.test_run >= 0:
                if input_json_idx >= args.test_run:
                    logging.info('Test run size {} completed, stopped reading further JSONs.'.format(args.test_run))
                    break

            # First, check for non-JSON files (like .DS_Store)
            if not input_json.endswith('.json'):
                logging.info('Skipping non-json file: {}'
                             ''.format(os.path.join(args.input_dir, input_json)))
                continue

            input_path = os.path.join(args.input_dir, input_json)
            _EXTERNAL_CSV_FIELDS = {}
            if args.treat_filenames_as_cid:
                cantus_id = input_json[:-5]    # the '.json' suffix is an invariant now
                _EXTERNAL_CSV_FIELDS = {'cantus_id': cantus_id}
            
            try:
                with open(input_path, encoding="utf-8-sig") as fh:
                    current_json_data = json.load(fh)
                    # json_data.extend(current_json_data)

                    current_csv_data = convert_json_data_to_csv_data(current_json_data,
                                                                     required_nonnul_csv_fields=_REQUIRED_NONNULL_CSV_KEYS,
                                                                     external_csv_fields=_EXTERNAL_CSV_FIELDS)
                    csv_data.extend(current_csv_data)

            #except json.decoder.JSONDecodeError:
            #    logging.error('Could not decode file with json.decoder: {}'.format(input_path))
            #    continue
            except Exception as e:
                logging.error('Could not process file, skipping: {}\n{}'.format(input_path, e))
                continue

    logging.info('Put {} items into CSVs.'.format(len(csv_data)))
    #logging.info('First CSV row:')
    #logging.info(csv_data[0])

    # csv_data = convert_json_data_to_csv_data(json_data,
    #                                          required_nonnul_csv_fields=REQUIRED_NONNULL_CSV_KEYS)

    with open(args.output_csv, 'w', newline='') as output_csv:
        csv_writer = csv.writer(output_csv)
        write_csv_data(csv_data, csv_writer)

    _end_time = time.process_time()
    logging.info('cantus_json_to_csv.py done in {0:.3f} s'.format(_end_time - _start_time))


if __name__ == '__main__':
    parser = build_argument_parser()
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
    if args.debug:
        logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)

    main(args)
