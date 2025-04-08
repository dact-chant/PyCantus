#!/usr/bin/env python
"""
Scrapes the Cantus Index for a list of genres.
The output is a CSV file (given as parameter) with the genre name, description, rite, and mass or office.
"""

from __future__ import print_function, unicode_literals

import argparse
import logging
import time
import csv

import requests
from bs4 import BeautifulSoup

__version__ = "0.0.1"
__author__ = "Anna Dvorakova"


CANTUS_ENTRYPOINT_URL = 'https://cantusindex.org/genre'
CANTUS_BASE_URL = 'https://cantusindex.org'


def get_cantus_chants_soup():
    """Returns the BS entry point for all our scraping:
    the page https://cantusindex.org/genre."""
    url = CANTUS_ENTRYPOINT_URL
    page = requests.get(url)
    soup = BeautifulSoup(page.content, "html.parser")

    return soup


class CantusIndexGenres:
    def __init__(self):
        self.chant_soup = get_cantus_chants_soup()

    def scrape_one_page(self, soup: BeautifulSoup) -> list[list[str]]:
        """Scrapes the genre rows from one page's soup.

        :return: List of genres as lists [genre_name, description, rite, mass_or_office] representing one genre.
        """
        table = soup.find('table', class_='views-table cols-4 table')
        tbody = table.find('tbody')
        genres = []
        for tr in tbody.findAll('tr'):
            td = tr.find('td', class_='views-field views-field-name')
            a = td.find('a')
            genre_name = a.text

            td = tr.find('td', class_='views-field views-field-description')
            p = td.find('p')
            description = p.text 

            td = tr.find('td', class_='views-field views-field-field-rite')
            if td is None:
                rite = ''
            else:
                rite = td.text

            td = tr.find('td', class_='views-field views-field-field-mass-office')
            if td is None:
                mass_or_office = ''
            else:
                mass_or_office = td.text

            genres.append([genre_name.strip(), description.strip(), rite.strip(), mass_or_office.strip()])

        return genres

    def get_next_page_url(self, soup: BeautifulSoup) -> str:
        """Returns the URL for the next page in a filter listing.
        If we are at the last page, returns None."""
        url = None
        pager = soup.find('ul', class_='pager')
        if not pager:
            return None
        pager_next = pager.find('li', class_='pager-next')
        if not pager_next:
            return None
        a = pager_next.find('a')
        if not a:
            return None
        try:
            href = a['href']
        except KeyError:
            return None
        url = CANTUS_BASE_URL + href
        return url


    def scrape(self) -> list[list[str]]:
        """Runs the scraper of Cantus IDs.

        :param genre: Genre name.

        :param feast: Feast name.

        :return: A list of Cantus ID strings.
        """
        base_url = CANTUS_ENTRYPOINT_URL
        page = requests.get(base_url)
        soup = BeautifulSoup(page.content, "html.parser")

        logging.info('Scraping first page: {}'.format(base_url))

        genres = self.scrape_one_page(soup)

        next_page_url = self.get_next_page_url(soup)
        while next_page_url:
            logging.info('Scraping next page: {}'.format(next_page_url))

            next_page = requests.get(next_page_url)
            next_soup = BeautifulSoup(next_page.content, "html.parser")
            next_cantus_ids = self.scrape_one_page(next_soup)
            genres.extend(next_cantus_ids)
            logging.info('\tAfter scraping: {} feasts retrieved'.format(len(genres)))

            next_page_url = self.get_next_page_url(next_soup)

        return genres


def build_argument_parser():
    parser = argparse.ArgumentParser(description=__doc__, add_help=True,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('-o', '--output_file', action='store',
                        help='Output the list of feasts here. Output as a CSV, with the header:'
                             ' genre_name, description, rite, mass_or_office.')

    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Turn on INFO messages.')
    parser.add_argument('--debug', action='store_true',
                        help='Turn on DEBUG messages.')

    return parser


def main(args):
    logging.info('Starting main...')
    _start_time = time.process_time()


    ci_filter = CantusIndexGenres()
    genres = ci_filter.scrape()
    if args.output_file:
        with open(args.output_file, 'w', newline='') as fh:
            writer = csv.writer(fh)
            writer.writerow(['genre_name', 'description', 'rite', 'mass_or_office'])
            writer.writerows(genres)
    else:
        for feast in genres:
            print(feast)

    _end_time = time.process_time()
    logging.info('scrape_ci_list_of_genres.py done in {0:.3f} s'.format(_end_time - _start_time))


if __name__ == '__main__':
    parser = build_argument_parser()
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
    if args.debug:
        logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)

    main(args)