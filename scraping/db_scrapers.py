#!/usr/bin/env python
"""This is a script that scrapes information about sources from the Cantus database
URLs such as https://cantus.uwaterloo.ca/source/123610."""
from __future__ import print_function, unicode_literals

import argparse
import collections
import logging
import os
import re
import time

import json
import requests
import csv

from bs4 import BeautifulSoup

__version__ = "0.0.2"
__author__ = "Jan Hajic jr."
__changelog__ = {
    "0.0.2": {"updated_by": "Anna Dvorakova", "date": "2025-02-27", "changes": "adapt to new DB web pages"},
}

class Century:
    @staticmethod
    def normalize_from_roman_numeral_cantus_label(century_roman):
        """Musmed.eu has the genius idea of showing century info
        as roman numerals. This mehtod normalizes them to look like
        Cantus DB labels: 12th century, etc."""
        ROMAN_DIGITS = set(list('IVXLCDMivxlcdm'))
        ROMAN_DIGITS_VALUES = {'I': 1, 'i': 1, 'V': 5, 'v': 5,
                               'X': 10, 'x': 10, 'L': 50, 'l': 50,
                               'C': 100, 'c': 100, 'D': 500, 'd': 500,
                               'M': 1000, 'm': 1000}
        def _gt(a, b):
            """returns whether a > b"""
            return ROMAN_DIGITS_VALUES[a] > ROMAN_DIGITS_VALUES[b]

        digits = list(century_roman.strip())
        n_digits = len(digits)
        result = 0
        for i, d in enumerate(digits):
            if d not in ROMAN_DIGITS:
                raise ValueError('Century label contains other characters than Roman digits: {}'.format(digits))
            if (i + 1) < n_digits and _gt(digits[i+1], d):
                result -= ROMAN_DIGITS_VALUES[d]
            else:
                result += ROMAN_DIGITS_VALUES[d]
        return result


class SourceData:
    '''POD class for chant sources. Fields taken from CantusCorpus source.csv, but the fields
    specific to CantusCorpus (id, provenance_id, feast_id, century_id) were taken out, since
    those are specifically computed during generating CantusCorpus from Cantus db records.

    On the other hand, we add the siglum field, which is not in Hymnologica chant records but
    only in the source record.

    Currently copied over from scrape_hymnologica.py.
    '''
    def __init__(self):

        self._fields = [
            'title',
            'siglum',
            'description',
            'rism',
            'date',
            'century',
            'provenance',
            'provenance_detail',
            'segment',
            'summary',
            'indexing_notes',
            'liturgical_occasions',
            'indexing_date',
            'srclink',      # We (mis)use this one for URL.
            'cursus',      # This one is not in CantusCorpus and scrape_hymnologica yet.
            'image_link',  # This one is not in CantusCorpus and scrape_hymnologica yet.
            'n_cantus_chants',    # This one is not in CantusCorpus and scrape_hymnologica yet.
            'n_cantus_melodies',  # This one is not in CantusCorpus and scrape_hymnologica yet.
        ]

        for f in self._fields:
            self.__setattr__(f, None)

    def to_dict(self):
        output = collections.OrderedDict()
        for f in self._fields:
            output[f] = self.__getattribute__(f)
        return output

    def to_json(self):
        output = json.dumps(self.to_dict(), ensure_ascii=False)
        return output

    def to_csv_row(self, delimiter=','):
        output_fields = []
        for f in self._fields:
            fv = self.__getattribute__(f)
            if self.__getattribute__(f) is None:
                output_fields.append('')
            elif len(fv.split()) > 1:    # Quote everything with whitespace
                output_fields.append('\"{}\"'.format(fv))
            elif fv.startswith('http'):  # Qoute URLs
                output_fields.append('\"{}\"'.format(fv))
            else:
                output_fields.append(str(fv))
        output = delimiter.join(output_fields)
        return output

    @staticmethod
    def get_field_names():
        _source = SourceData()
        return _source._fields

    @staticmethod
    def csv_header_row(delimiter=','):
        _source = SourceData()
        return delimiter.join(_source._fields)


class _AbstractSourceScraper:

    def __init__(self,
                 require_title=True,
                 require_siglum=True,
                 require_provenance=False,
                 require_century=False):
        # We can set these URLS in the abstract parent class because all the sites
        # that we use are just differently styled copies of the Cantus Drupal site.
        self.DB_URL = ''
        self._set_derived_drupal_db_urls()
        self._force_http = False

        self._sources_url_cache = {}

        # Error handling: which fields to fail on?
        self.important_fields = ['title', 'siglum', 'provenance', 'century']
        self.required_fields = []
        if require_title:
            self.required_fields.append('title')
        if require_siglum:
            self.required_fields.append('siglum')
        if require_provenance:
            self.required_fields.append('provenance')
        if require_century:
            self.required_fields.append('century')

    def handle_missing_important_field(self, field):
        _message = 'Could not find required field in source soup: {}'.format(field)
        if field in self.required_fields:
            raise ValueError(_message)
        else:
            logging.warning(_message)

    def _set_derived_drupal_db_urls(self):
        """All the Drupal-based websites seem to use the same URL structure. In that case,
        for every database, only the base DB_URL needs to be set explicitly."""
        self.DB_SOURCE_BASE_URL = self.DB_URL + '/source'
        self.DB_SOURCE_LISTING_URL = self.DB_URL + '/sources'
        self.DB_SOURCE_CSV_BASE_URL = self.DB_URL + '/sites/default/files/csv'

    def build_url_from_source_id(self, source_id: str) -> str:
        """Creates an URL to the database source page corresponding
        to the given source ID.

        This may have be overridden, because each database in the Cantus network
        may use a different URL system for the pages of its individual sources.
        However, in practice, this pattern seems to be kept across all the Drupal
        sites.

        :param source_id:
        """
        return self.DB_SOURCE_BASE_URL + '/{}'.format(source_id)

    def source_data_from_source_soup(self, soup: BeautifulSoup) -> SourceData:
        raise NotImplementedError()

    def scrape_source_id(self, source_id: str) -> SourceData:
        source_url = self.build_url_from_source_id(source_id)
        return self.scrape_source_url(source_url)

    def scrape_source_url(self, source_url: str) -> SourceData:
        """Returns the SourceData object corresponding to the source at the given URL.
        If `_force_http` is set, changes URLs from `https://` to `http://`. (Many Cantus
        network databases do not have HTTPS configured.) Caches SourceData results into
        `_sources_url_cache` according to the true URL from which they were scraped.
        """
        if self._force_http:
            source_url = self._url_to_http(source_url)

        # Check cache
        if source_url in self._sources_url_cache:
            return self._sources_url_cache[source_url]

        page = requests.get(source_url)
        if not page.ok:
            raise requests.RequestException('Requests for source URL {} unsuccessful.'.format(source_url))
        soup = BeautifulSoup(page.content, "html.parser")
        source_data = self.source_data_from_source_soup(soup)

        # Clean source_data field to eliminate wrong csv fileds separation
        source_data.title = source_data.title.replace('"', '')

        # Add the link -- which is a relatively good de facto unique ID for sources,
        # since the sigla are done inconsistently anyway -- to the source data,
        # so that it carries its own origin.
        source_data.srclink = source_url

        # Cache result
        self._sources_url_cache[source_url] = source_data

        return source_data

    def scrape_sources_listing(self) -> [SourceData]:
        """This is the entrypoint for bulk scraping. Based on the given database's
        source listing page (if it exists), attempts to scrape information about
        all the sources that exist in the database."""
        raise NotImplementedError()

    def _url_to_http(self, source_url: str) -> str:
        """Converts a https:// URL to point to just http://, which is what all the
        Cantus Network databases run on."""
        if source_url.startswith('https'):
            return 'http' + source_url[5:]
        else:
            return source_url


class CantusSKScraper(_AbstractSourceScraper):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.DB_URL = 'https://cantus.sk'
        self._set_derived_drupal_db_urls()
        self._force_http = True

    def source_data_from_source_soup(self, soup: BeautifulSoup) -> SourceData:
        container = soup.find('div', class_='l-wrapper')
        if not container:
            raise ValueError('Source does not contain the data container section!?')
        source = SourceData()

        title_container = soup.find('h1', class_='page-title')
        if title_container:
            title = title_container.text
            source.title = title

        siglum_container = container.find('div', class_='field-name-field-siglum')
        if siglum_container:
            siglum = siglum_container.find('div', class_='field-item').text
            source.siglum = siglum
        else:
            raise ValueError('Source data must have siglum!')

        #     'century',
        century_container = container.find(href=re.compile('century'))
        if century_container:
            century = century_container.text
            source.century = century
        else:
            self.handle_missing_important_field('century')

        #     'provenance'
        provenance_container = container.find('div', class_='field-name-field-provenance')
        if provenance_container:
            provenance = provenance_container.find('div', class_='field-item')
            if provenance:
                source.provenance = provenance.text
            else:
                self.handle_missing_important_field('provenance')
        else:
            self.handle_missing_important_field('provenance')

        #     'cursus' -> no cursus present in SK

        return source


class IspanPLScraper(_AbstractSourceScraper):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.DB_URL = 'https://cantusplanus.pl' #'http://cantus.ispan.pl'
        self._set_derived_drupal_db_urls()
        self._force_http = True

    def source_data_from_source_soup(self, soup: BeautifulSoup) -> SourceData:
        container = soup.find(class_='l-wrapper') #='content-region-inner')
        if not container:
            raise ValueError('Source does not contain the data container section!?')
        source = SourceData()

        title_container = container.find('h1', class_='page-title')
        if title_container:
            title = title_container.text
            source.title = title

        #   'siglum'
        shelfmark_container = container.find('div', class_='field-name-field-shelf-mark')
        if shelfmark_container:
            shelfmark = shelfmark_container.find('div', class_='field-item').text
            # To get reasonable RISM style siglum we wanna add first token (Country-Archive, e.g. Pl-PE) from title 
            try:
                siglum = title.split()[0] + " " + shelfmark
                source.siglum = siglum
            except:
                source.siglum = shelfmark
        else:
            raise ValueError('Source data must have siglum!')

        #     'century',
        century_container = container.find(href=re.compile('century'))
        if century_container:
            century = century_container.text
            source.century = century
        else:
            self.handle_missing_important_field('century')

        #     'provenance'
        provenance_container = container.find('div', class_='field-name-field-provenance')
        if provenance_container:
            provenance = provenance_container.find('div', class_='field-item')
            if provenance:
                source.provenance = provenance.text
            else:
                self.handle_missing_important_field('provenance')
        else:
            self.handle_missing_important_field('provenance')

        #     'cursus' -> no cursus present in ispan (Cantus Planus in Polonia)
        
        return source


class MusmedDBScraper(_AbstractSourceScraper):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # We set these URLS
        self.DB_URL = 'http://musmed.eu'
        self._set_derived_drupal_db_urls()
        self._force_http = True

    def source_data_from_source_soup(self, soup: BeautifulSoup) -> SourceData:
        """Get the SourceData from the given source page soup."""
        container = soup.find(id='main')
        if not container:
            raise ValueError('Source does not contain the data container section!?')

        source = SourceData()

        #     'title',
        title_container = soup.find(id='page-title')
        title = title_container.text
        source.title = title

        #     'siglum',
        # In the MusMed interface, the siglum is split between a RISM and a shelf-mark field.
        rism_container = container.find('div', class_='field-name-field-rism')
        if not rism_container:
            raise ValueError('Source data must have siglum, which in MusMed means also the RISM field.')
        rism = rism_container.find('div', class_='field-item').text
        siglum_container = container.find('div', class_='field-name-field-shelf-mark')
        if not siglum_container:
            raise ValueError('Source data must have siglum!')
        siglum = siglum_container.find('div', class_='field-item').text
        source.siglum = rism + ' ' + siglum

        #     'description',
        #     'rism',
        #     'date',
        # We ignore this for now.

        #     'century',
        century_container = container.find(href=re.compile('century'))
        if century_container:
            century = self._normalize_century(century_container.text)
            source.century = century
        else:
            self.handle_missing_important_field('century')

        #     'provenance',
        # MusMed is a bit complicated with provenance.
        provenance = None
        # It can be called "provenance"
        provenance_container = container.find('div', class_='field-name-field-provenance')
        if not provenance_container:
            # or it can be called "origin"
            provenance_container = container.find('div', class_='field-name-field-origin')
        if provenance_container:
            provenance = provenance_container.find('div', class_='field-item').text
        else:
            # or at least we can take the combination of city + country where
            # the manuscript is now, and hope that it is not stored in a different country or something
            provenance_container = container.find('div', class_='field-name-field-city')
            if provenance_container:
                country_container = container.find('div', class_='field-name-field-country')
                country = country_container.find('div', class_='field-item').text
                city = provenance_container.find('div', class_='field-item').text
                provenance = city + ', ' + country
        if not provenance_container:
            self.handle_missing_important_field('provenance')
        elif not provenance:
            self.handle_missing_important_field('provenance')
        else:
            source.provenance = provenance

        # The rest we can ignore for now.
        #     'provenance_detail',
        #     'segment',
        #     'summary',
        #     'indexing_notes',
        #     'liturgical_occasions',
        #     'indexing_date',
        #     'drupal_path'

        #     'cursus'
        cursus_container = container.find('div', class_='field-name-field-cursus')
        if cursus_container:
            cursus_span = cursus_container.find(href=re.compile('cursus'))
            if cursus_span:
                cursus = cursus_span.text
                source.cursus = self._normalize_cursus(cursus)

        return source

    def _normalize_cursus(self, cursus_text: str):
        if cursus_text.lower().startswith('monastic'):
            return 'Monastic'
        elif cursus_text.lower().startswith('secul'):
            return 'Secular'
        else:
            return cursus_text

    def _normalize_century(self, century_text: str):
        numeric_value = Century.normalize_from_roman_numeral_cantus_label(century_text)
        century_string = '{}th century'.format(numeric_value)
        return century_string


class CantusDBScraper(_AbstractSourceScraper):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # We set these URLS
        self.DB_URL = 'https://cantusdatabase.org' # 'https://cantus.uwaterloo.ca'
        self._set_derived_drupal_db_urls()
        # self.DB_SOURCE_BASE_URL = self.DB_URL + '/source'
        # self.DB_SOURCE_LISTING_URL = self.DB_URL + '/sources'
        # self.DB_SOURCE_CSV_BASE_URL = self.DB_URL + '/sites/default/files/csv'

    def source_data_from_source_soup(self, soup: BeautifulSoup) -> SourceData:
        """Get the SourceData from the given source page soup."""
        cards = soup.find_all('div', class_='card mb-3 w-100')
        if len(cards) >= 2:
            container = cards[1]
        else:
            raise ValueError('Source does not contain the data container section!?')
        
        source = SourceData()

        # self._fields = [
        #     'title',
        title_container = soup.find('h3') #id='page-title')
        title = title_container.text
        source.title = title

        #     'siglum',
        siglum_container = container.find('div', class_='card-header') #'views-field-field-siglum')
        if siglum_container:
            siglum = siglum_container.find('b').text #, class_='field-content').text
            source.siglum = siglum
        else:
            raise ValueError('Source data must have siglum!')

        #     'description',
        #     'rism',
        #     'date',
        # We ignore this for now.

        #     'century',
        century_container = container.find(href=re.compile('century'))
        if century_container:
            source.century = century_container.text
        else:
            self.handle_missing_important_field('century')

        #     'provenance',
        provenance_container = container.find(href=re.compile('provenance')) # 'div', class_='views-field views-field-field-provenance-tax')
        if provenance_container:
            source.provenance = provenance_container.text
        else:
            self.handle_missing_important_field('provenance')

        # The rest we can ignore for now.
        #     'provenance_detail',
        #     'segment',
        #     'summary',
        #     'indexing_notes',
        #     'liturgical_occasions',
        #     'indexing_date',
        #     'drupal_path'

        #     'cursus'
        cursus_container = container.find('div', class_='card-body small')
        match = re.search(r"Cursus:\s*(\w+)", cursus_container.text)  # Look for "Cursus: <word>"
        if match:
            cursus = match.group(1)  # Extract "Secular"
            source.cursus = cursus

        return source

    def scrape_sources_listing(self) -> [SourceData]:
        """Scrapes the information from the https://cantus.uwaterloo.ca/sources page.
        The listing itself already has all the information about provenance that we
        need, so here we have no need to go into the pages for individual sources."""
        url = self.DB_SOURCE_LISTING_URL
        page = requests.get(url)
        if not page.ok:
            raise ValueError('Could not retrieve soruce listings page: {}'.format(url))

        soup = BeautifulSoup(page.content, "html.parser")

        sources = []

        _re_pattern_srclink = re.compile('source')
        _re_pattern_century = re.compile('century')
        _re_pattern_provenance = re.compile('provenance')

        table = soup.find('table', class_='views-table')
        if not table:
            raise ValueError('Source listing table not found! URL: {}, page:\n{}'.format(url, page.content))

        rows = table.find('tbody').findAll('tr')

        _n_skipped = 0
        for row_idx, row in enumerate(rows):
            logging.debug('Parsing row no. {}'.format(row_idx))

            source = SourceData()

            siglum_cell = row.find('td', class_='views-field-field-siglum')
            siglum = siglum_cell.text.strip()
            source.siglum = siglum

            siglum_href = siglum_cell.find('a', href=_re_pattern_srclink)['href']
            source_url = self.DB_URL + siglum_href
            source.drupal_path = source_url

            summary_cell = row.find('td', class_='views-field-field-summary')
            source.summary = summary_cell.text.strip()

            provenance_century_cell = row.find('td', class_='views-field-nothing')
            try:
                century_link = provenance_century_cell.find('a', href=_re_pattern_century)
                source.century = century_link.text

                provenance_link = provenance_century_cell.find('a', href=_re_pattern_provenance)
                source.provenance = provenance_link.text
            except AttributeError:
                logging.warning('Row no. {} does not contain required provenance and century information. Skipping.'.format(row_idx))
                logging.debug(' Row:\n{}'.format(row))
                _n_skipped += 1
                continue

            image_cell = row.find('td', class_='views-field-field-image-link')
            image_a = image_cell.find('a')
            if image_a:
                image_link = image_a['href']
                source.image_link = image_link

            count_cell = row.find('td', class_='views-field-php')
            count_text = count_cell.text.strip()
            n_chants = 0
            n_melodies = 0
            if count_text:  # Parse the chant and melody counts.
                fields = count_text.split('/')
                if len(fields) > 1:
                    n_chants = fields[0].strip()
                    n_melodies = fields[1].strip()
                else:
                    n_chants = fields[0].strip()
            source.n_cantus_chants = n_chants
            source.n_cantus_melodies = n_melodies

            sources.append(source)

        logging.info('Processed {} source listing rows, out of which {} were skipped and {} completed.'
                     ''.format(len(rows), _n_skipped, len(rows) - _n_skipped))

        return sources

    def scrape_source_csv(self, source_id):
        """Scrapes the CSV file with a full inventory of the given source."""
        source_csv_url = self.DB_SOURCE_CSV_BASE_URL + '/{}.csv'.format(source_id)
        response = requests.get(source_csv_url)
        # print('Inventory response encoding: {}'.format(response.encoding))
        return response.text


class PemDBScraper(_AbstractSourceScraper):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # We set these URLS
        self.DB_URL = 'https://pemdatabase.eu'
        self._set_derived_drupal_db_urls()
        self._force_http = True

    def source_data_from_source_soup(self, soup: BeautifulSoup) -> SourceData:
        """Get the SourceData from the given source page soup."""
        container = soup.find('div', class_='region region-content') #'section', class_='col-sm-6')
        if not container:
            raise ValueError('Source does not contain the data container section!?')
        
        source = SourceData()

        # self._fields = [
        #     'title',
        title_container = soup.find('span', class_='field field--name-title field--type-string field--label-hidden')
        title = title_container.text
        source.title = title

        #     'siglum',
        siglum_container = container.find('div', class_='field--name-field-siglum')
        if not siglum_container:
            raise ValueError('Source data must have siglum!')
        siglum = siglum_container.find('div', class_='field__item').text
        source.siglum = siglum.strip()

        #     'description',
        #     'rism',
        #     'date',
        # We ignore this for now.

        #     'century',
        date_container = container.find('div', class_='field field--name-field-date field--type-string field--label-inline clearfix') #'field-name-field-date')
        if date_container:
            date_text = date_container.find('div', class_='field__item').text
            century = self._normalize_date(date_text)
            source.century = century
        else:
            self.handle_missing_important_field('century')

        #     'provenance',
        # PEM provides three fields: Origin, Main place of use, and Provenance.
        # For simplicity's sake, we use Provenance as provenance and secondary Origin as provenance, but this might change.
        provenance = None
        # It can be called "provenance"
        provenance_container = container.find('div', class_='field field--name-field-provenance field--type-entity-reference field--label-inline clearfix') #'field-name-field-provenance')
        if provenance_container:
            provenance = provenance_container.find('div', class_='field__item').text
            source.provenance = provenance
        else:
            # It can be called "origin"
            provenance_container = container.find('div', class_='field field--name-field-origin field--type-entity-reference field--label-inline clearfix') #'field-name-field-origin')
            if provenance_container:
                provenance = provenance_container.find('div', class_='field__item').text
                source.provenance = provenance
            else:
                self.handle_missing_important_field('provenance')


        # The rest we can ignore for now.
        #     'provenance_detail',
        #     'segment',
        #     'summary',
        #     'indexing_notes',
        #     'liturgical_occasions',
        #     'indexing_date',
        #     'drupal_path'

        #     'cursus'
        cursus_container = container.find('div', class_='field field--name-field-cursus field--type-entity-reference field--label-inline clearfix')
        if cursus_container:
            cursus = cursus_container.find('div', class_='field__item').text
            source.cursus = cursus

        return source

    def _normalize_date(self, date_text):
        return date_text
        # raise NotImplementedError()


class FontesCantusBohemiaeScraper(_AbstractSourceScraper):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # We set these URLS
        self.DB_URL = 'https://cantusbohemiae.cz'
        self._set_derived_drupal_db_urls()
        self._force_http = True

    def source_data_from_source_soup(self, soup: BeautifulSoup) -> SourceData:
        """Get the SourceData from the given source page soup."""
        container = soup.find(id='block-system-main')
        if not container:
            raise ValueError('Source does not contain the data container section!?')
        
        source = SourceData()

        # self._fields = [
        #     'title',
        title_container = soup.find('h1', class_='title')
        title = title_container.text
        source.title = title

        #     'siglum',
        shelfmark_container = container.find('div', class_='field-name-field-shelf-mark')
        if not shelfmark_container:
            raise ValueError('Source data must have shelfmark!')
        shelfmark = shelfmark_container.find('div', class_='field-item').text

        archive_container = container.find('div', class_='field-name-field-archive')
        if archive_container:
            #raise ValueError('Source data must have archive!')
            archive = archive_container.find('div', class_='field-item').find('a').text
            if not archive:
                raise ValueError('Source data must have archive! Found container, but text empty.')
            archive_siglum = archive.split()[0]
        else:
            archive_siglum = ''
        

        siglum = archive_siglum + ' ' + shelfmark
        source.siglum = siglum

        #     'description',
        #     'rism',
        #     'date',
        # We ignore this for now.

        #     'century',
        century_container = container.find('div', class_='field-name-field-century')
        if not century_container:
            self.handle_missing_important_field('century')
        century_text = century_container.find('div', class_='field-item').find('a').text
        source.century = century_text

        #     'provenance',
        provenance_container = container.find('div', class_='field-name-field-provenance')
        if provenance_container:
            provenance = provenance_container.find('div', class_='field-item').text
            source.provenance = provenance
        else:
            self.handle_missing_important_field('provenance')

        # The rest we can ignore for now.
        #     'provenance_detail',
        #     'segment',
        #     'summary',
        #     'indexing_notes',
        #     'liturgical_occasions',
        #     'indexing_date',
        #     'drupal_path'

        #     'cursus' -> no cursus in FCB

        return source
    

class HungarianChantScraper(_AbstractSourceScraper):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # We set these URLS
        self.DB_URL = 'https://hun-chant.eu'
        self._set_derived_drupal_db_urls()
        self._force_http = True

    def source_data_from_source_soup(self, soup: BeautifulSoup) -> SourceData:
        """Get the SourceData from the given source page soup."""
        container = soup.find(id='main')
        if not container:
            raise ValueError('Source does not contain the data container section!?')
        
        source = SourceData()

        # self._fields = [
        #     'title',
        title_container = soup.find('h1', class_='title')
        title = title_container.text
        source.title = title

        #     'siglum',
        archive_siglum = title.split()[0]

        shelfmark_container = container.find('div', class_='field field-name-field-shelf-mark field-type-text field-label-above')
        if not shelfmark_container:
            raise ValueError('Source data must have shelfmark!')
        shelfmark = shelfmark_container.find('div', class_='field-item').text

        siglum = archive_siglum + ' ' + shelfmark
        source.siglum = siglum

        #     'description',
        #     'rism',
        #     'date',
        # We ignore this for now.

        #     'century',
        century_container = container.find('div', class_='field field-name-field-century field-type-taxonomy-term-reference field-label-above')
        if not century_container:
            self.handle_missing_important_field('century')
        century_text = century_container.find('div', class_='field-item').find('a').text
        source.century = century_text

        #     'provenance',
        # Look for provenance (country)
        provenance_country_container = container.find('div', class_='field field-name-field-provenance-country- field-type-taxonomy-term-reference field-label-above')
        # Look for provenance (place) - more specific, better
        provenance_place_container = container.find('div', class_='field field-name-field-provenance-location- field-type-text field-label-above')
        # Store
        if provenance_place_container:
            provenance = provenance_place_container.find('div', class_='field-item').text
            source.provenance = provenance
        elif provenance_country_container:
            provenance = provenance_country_container.find('div', class_='field-item').text
            source.provenance = provenance
        else:
            self.handle_missing_important_field('provenance')

        # The rest we can ignore for now.
        #     'provenance_detail',
        #     'segment',
        #     'summary',
        #     'indexing_notes',
        #     'liturgical_occasions',
        #     'indexing_date',
        #     'drupal_path'

        #     'cursus' -> no cursus in HunChant

        return source


class MusicaHispanicaScraper(_AbstractSourceScraper):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.DB_URL = 'https://musicahispanica.eu'
        self._set_derived_drupal_db_urls()
        self._force_http = True

    def source_data_from_source_soup(self, soup: BeautifulSoup) -> SourceData:
        """Extract the SourceData from the given source page soup."""
        container = soup.find(class_='l-wrapper') #id='post-content')
        if not container:
            raise ValueError('Source does not contain the data container section!?')

        source = SourceData()

        #     'title' (serves also as to provide the RISM siglum code of the archive, if it exists)
        title_container = container.find('h1', class_='page-title')
        title = title_container.text
        source.title = title

        #     'siglums
        siglum_rism_prefix = title.split()[0]
        siglum_container = container.find('div', class_='field-name-field-shelf-mark')
        if not siglum_container:
            raise ValueError('Source data must have siglum!')
        siglum_suffix = siglum_container.find('div', class_='field-item').text
        siglum = siglum_rism_prefix + ' ' + siglum_suffix
        source.siglum = siglum

        #     'provenance'
        provenance_container = container.find('div', class_='field-name-field-provenance')
        if provenance_container:
            provenance = provenance_container.find('div', class_='field-item').text
            source.provenance = provenance
        else:
            self.handle_missing_important_field('provenance')

        #     'century'
        century_container = container.find('div', class_='field-name-field-century')
        if not century_container:
            self.handle_missing_important_field('century')
        # In musica hispanica, century is a link.
        else:
            century = century_container.find('div', class_='field-item').find('a').text
            if not century:
                self.handle_missing_important_field('century')
            source.century = century

        #     'cursus' 
        cursus_container = container.find('div', class_='field-name-field-cursus')
        if cursus_container:
            cursus = cursus_container.find('div', class_='field-item').text
            source.cursus = self._normalize_cursus(cursus)

        return source
    
    def _normalize_cursus(self, cursus_text: str):
        if cursus_text.lower().startswith('monastic'):
            return 'Monastic'
        elif cursus_text.lower().startswith('secul'):
            return 'Secular'
        else:
            return cursus_text


class AustriaManusScraper(_AbstractSourceScraper):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.DB_URL = 'http://austriamanus.org'
        self._set_derived_drupal_db_urls()
        self._force_http = True

    def source_data_from_source_soup(self, soup: BeautifulSoup) -> SourceData:
        """Extract the SourceData from the given source page soup."""
        container = soup.find('div', class_='l-wrapper-inner')

        source = SourceData()

        #     'title' (serves also as to provide the RISM siglum code of the archive, if it exists)
        title_container = container.find('h1', class_='page-title')
        title = title_container.text
        source.title = title

        #     'siglum'
        siglum_container = container.find('div', class_='field-name-field-siglum')
        if not siglum_container:
            self.handle_missing_important_field('siglum')
        siglum_item = siglum_container.find('div', class_='field-item')
        if not siglum_item:
            self.handle_missing_important_field('siglum')
        siglum = siglum_item.text
        if not siglum:
            self.handle_missing_important_field('siglum')

        source.siglum = siglum

        #     'provenance'
        provenance_container = container.find('div', class_='field-name-field-provenance')
        if provenance_container:
            # In austriamanus, provenance is a link.
            provenance = provenance_container.find('div', class_='field-item').find('a').text
            source.provenance = provenance
        else:
            self.handle_missing_important_field('provenance')

        #     'century'
        century_container = container.find('div', class_='field-name-field-century')
        if century_container:
            # In austriamanus, century is also a link.
            century = century_container.find('div', class_='field-item').find('a').text
            source.century = century
        else:
            self.handle_missing_important_field('century')

        return source


class HymnologicaScraper(_AbstractSourceScraper):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.DB_URL = 'https://hymnologica.cz'
        #self._set_derived_drupal_db_urls()
        #self._force_http = True

    def source_data_from_source_soup(self, soup: BeautifulSoup) -> SourceData:
        """Extract the SourceData from the given source page soup."""
        source = SourceData()
        # 'title',
        source.title = soup.find('h1', class_='page-header').text

        # Searching only in the container section element speeds us up.
        container_section = soup.find(id='block-system-main')
        if not container_section:
            raise ValueError('Cound not find container section in source!')

        # 'siglum'
        siglum_div = container_section.find('div', class_='field-name-field-siglum')
        if not siglum_div:
            raise ValueError('Required value not found: siglum')
        source.siglum = siglum_div.find(
            'div', class_='field-item').text
        
        # 'provenance'
        provenance_container = container_section.find('div', class_='field-name-field-provenance')
        if not provenance_container:
            self.handle_missing_important_field('provenance')
        else:
            source.provenance = provenance_container.find('div', class_='field-item').text

        # 'century'
        century_container = container_section.find('div', class_='field-name-field-century')
        if not century_container:
            self.handle_missing_important_field('century')
        else:
            # century is a link
            source.century = century_container.find('div', class_='field-item').find('a').text

        # 'cursus' - Hymnologica does not annotate cursus

        return source



class UniversalSourceScraper(_AbstractSourceScraper):
    """The Universal Scraper wraps all the other implemented database scrapers.
    It uses the URLs to select which scraper is appropriate for the given source
    link (or drupal_path, or source_id, depending on how the chants CSV was built).
    Anyway, the URL must be a valid URL to a source page in one of the Cantus network
    databases.

    Currently supported:

    - Cantus DB (new: cantusdatabase.org, old: cantus.uwaterloo.ca)
    - MusMed (musmed.eu)
    - Cantus Planus in Polonia (cantusplanus.pl) 
    - Slovak Early Music Database (cantus.sk)
    - Portugese Early Music Database (pemdatabase.eu)
    - Fontes Cantus Bohemiae (cantusbohemiae.cz)
    - Musica Hispanica (musicahispanica.eu)
    - Austrimanus (austriamanus.org)
    - Hungarian Chant Database (hun-chant.eu)
    - Hymnologica (hymnologica.cz)

    Must be used via URL, not via just the source ID, because the source ID itself
    does not carry information about which database to look into. Different databases
    might have different sources under the same source ID.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.scrapers = {
            'cantus': CantusDBScraper(**kwargs),
            'musmed': MusmedDBScraper(**kwargs),
            'ispan': IspanPLScraper(**kwargs),
            'sk': CantusSKScraper(**kwargs),
            'pem': PemDBScraper(**kwargs),
            'fcb': FontesCantusBohemiaeScraper(**kwargs),
            'musica_hispanica': MusicaHispanicaScraper(**kwargs),
            'austriamanus': AustriaManusScraper(**kwargs),
            'hun-chant' : HungarianChantScraper(**kwargs),
            'hymnologica' : HymnologicaScraper(**kwargs)
        }

    def _select_scraper_by_url(self, url: str):
        if 'cantusdatabase' in url: 
            return self.scrapers['cantus']
        elif 'musmed.eu' in url:
            return self.scrapers['musmed']
        elif 'cantusplanus.pl' in url: 
            return self.scrapers['ispan']
        elif 'cantus.sk' in url:
            return self.scrapers['sk']
        elif 'pemdatabase.eu' in url:
            return self.scrapers['pem']
        elif 'cantusbohemiae.cz' in url:
            return self.scrapers['fcb']
        elif 'musicahispanica.eu' in url:
            return self.scrapers['musica_hispanica']
        elif 'austriamanus.org' in url:
            return self.scrapers['austriamanus']
        elif 'hun-chant.eu' in url:
            return self.scrapers['hun-chant']
        elif 'hymnologica' in url:
            return self.scrapers['hymnologica']
        else:
            raise NotImplementedError('No scraper implemented yet for url: {}'.format(url))

    def scrape_source_id(self, source_id: str) -> SourceData:
        raise ValueError('Universal scraper cannot scrape from source ID only, a full URL'
                         ' has to be provided to select the right scraper to use.')

    def scrape_source_url(self, source_url: str) -> SourceData:
        scraper = self._select_scraper_by_url(source_url)
        return scraper.scrape_source_url(source_url)

    def scrape_sources_listing(self) -> [SourceData]:
        """This is the entrypoint for bulk scraping. Based on the given database's
        source listing page (if it exists), attempts to scrape information about
        all the sources that exist in the database."""
        raise NotImplementedError('Cannot scrape the source listing of an unspecified database.')