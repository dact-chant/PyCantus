#!/usr/bin/env python
"""This is a script that scrapes Cantus IDs based on filters.
Output the list of Cantus IDs to stdout."""
from __future__ import print_function, unicode_literals

import argparse
import logging
import time

import requests
from bs4 import BeautifulSoup

__version__ = "0.0.2"
__author__ = "Jan Hajic jr."
__changelog__ = {
    "0.0.2": {"updated_by": "Anna Dvorakova", "date": "2025-02-27", "changes": "adapt to new CI web page"},
}


CANTUS_ENTRYPOINT_URL = 'https://cantusindex.org/master-chants'
CANTUS_BASE_URL = 'https://cantusindex.org'


def get_cantus_chants_soup():
    """Returns the BS entry point for all our scraping:
    the page https://cantusindex.org/master-chants."""
    url = CANTUS_ENTRYPOINT_URL
    page = requests.get(url)
    soup = BeautifulSoup(page.content, "html.parser")

    return soup


# No feast menu in current Cantus Index!!!
def get_feasts_index(chants_soup):
    """Returns an index feast names available from the chants soup.

    :returns: A dict translating plainly written feast names into
        values used in the filtering URL.

    """
    feasts_menu = chants_soup.find(id='edit-field-mc-feast-tid')

    feasts_index = {}
    for option in feasts_menu.findAll('option'):
        value = option['value']
        name = option.text
        feasts_index[name] = value

    return feasts_index


def get_genres_index(chants_soup):
    """Returns an index feast names available from the chants soup.

    :returns: A dict translating plainly written feast names into
        values used in the filtering URL.

    """
    genres_menu = chants_soup.find(id='edit-genre') #'edit-field-mc-genre-tid-1')

    genres_index = {}
    for option in genres_menu.findAll('option'):
        value = option['value']
        name = option.text
        genres_index[name] = value
    return genres_index


class CantusIndexFilter:
    def __init__(self):
        self.chant_soup = get_cantus_chants_soup()
        self.genres_index = get_genres_index(self.chant_soup)
        #self.feast_index = get_feasts_index(self.chant_soup)

    def scrape_one_page(self, soup: BeautifulSoup) -> [str]:
        """Scrapes the Cantus IDs from one page's soup.

        :return: List of Cantus IDs as strings.
        """
        table = soup.find('table', class_='views-table cols-4 table') #'views-table')
        tbody = table.find('tbody')
        cantus_ids = []
        for tr in tbody.findAll('tr'):
            td = tr.find('td', class_='views-field views-field-title') #'views-field-title')
            a = td.find('a')
            cantus_id = a.text
            cantus_ids.append(cantus_id)

        return cantus_ids

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

    def construct_url(self, genre=None, feast=None) -> str:
        """Builds the filter URL for the first page."""
        genre_value = None
        if genre is not None:
            if genre not in self.genres_index:
                raise ValueError('Genre {} not found in Cantus Index genre selection.'
                                 ''.format(genre))
            genre_value = self.genres_index[genre]

        feast_value = 'All'
        if feast is not None:
            if feast not in self.feast_index:
                raise ValueError('Feast {} not found in Cantus Index feast selection.'
                                 ''.format(feast))
            feast_value = self.feast_index[feast]

        url_suffix = ''
        if genre_value:
            url_suffix += '?t=&genre={}&'.format(genre_value) #'field_mc_genre_tid_1[0]={}&'.format(genre_value)
        #url_suffix += 'field_mc_feast_tid={}'.format(feast_value)

        return CANTUS_ENTRYPOINT_URL + url_suffix

    def scrape(self, genre=None, feast=None) -> [str]:
        """Runs the scraper of Cantus IDs.

        :param genre: Genre name.

        :param feast: Feast name.

        :return: A list of Cantus ID strings.
        """
        base_url = self.construct_url(genre, feast)
        page = requests.get(base_url)
        soup = BeautifulSoup(page.content, "html.parser")

        logging.info('Scraping first page: {}'.format(base_url))

        cantus_ids = self.scrape_one_page(soup)

        next_page_url = self.get_next_page_url(soup)
        while next_page_url:
            logging.info('Scraping next page: {}'.format(next_page_url))

            next_page = requests.get(next_page_url)
            next_soup = BeautifulSoup(next_page.content, "html.parser")
            next_cantus_ids = self.scrape_one_page(next_soup)
            cantus_ids.extend(next_cantus_ids)
            logging.info('\tAfter scraping: {} cantus IDs retrieved'.format(len(cantus_ids)))

            next_page_url = self.get_next_page_url(next_soup)

        return cantus_ids


def build_argument_parser():
    parser = argparse.ArgumentParser(description=__doc__, add_help=True,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('-g', '--genre', action='store', default=None,
                        help='A Cantus Index genre abbreviation.')
    # No feast menu in current Cantus Index !
    #parser.add_argument('-f', '--feast', action='store', default=None,
    #                    help='A Cantus Index feast name.')

    parser.add_argument('-o', '--output_file', action='store',
                        help='Output the list of Cantus IDs here. Output as a CSV, with the header'
                             ' row being cantus_id.')

    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Turn on INFO messages.')
    parser.add_argument('--debug', action='store_true',
                        help='Turn on DEBUG messages.')

    return parser


def main(args):
    logging.info('Starting main...')
    _start_time = time.process_time()


    ci_filter = CantusIndexFilter()
    cantus_ids = ci_filter.scrape(genre=args.genre, feast=None) #args.feast)
    if args.output_file:
        with open(args.output_file, 'w') as fh:
            fh.write('\n'.join(cantus_ids))
            fh.write('\n')
    else:
        for cantus_id in cantus_ids:
            print(cantus_id)

    _end_time = time.process_time()
    logging.info('scrape_cantus_ids.py done in {0:.3f} s'.format(_end_time - _start_time))


if __name__ == '__main__':
    parser = build_argument_parser()
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
    if args.debug:
        logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)

    main(args)
