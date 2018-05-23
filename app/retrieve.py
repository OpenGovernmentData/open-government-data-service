#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This program is part of the **Open Government Data Service** project

Author: Elias Grünewald <gruenewald@tu-berlin.de>

License : GPL(v3)

The **Open Government Data Service** is free software: you can redistribute it and/or modify it under the terms of the
GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

The **Open Government Data Service** is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details. You should have received a copy of the GNU General Public License along
with **Open Government Data Service**. If not, see http://www.gnu.org/licenses.
"""

import csv
import requests
import pandas as pd
from pandas.io import sql
import json
import io
import re
import util_design
from math import *
from timeit import default_timer as timer
from database_io import *
from util import get_current_timestamp
import log_strings as log
import settings
import sqlalchemy

import database_io
import maps
import util
import recommender

def get_data_set(catalog_index, skip_rows=0, sep=';', update_local_database=False):
    if catalog_index > 20000:
        maps.get_geojson_by_catalog_index(catalog_index)

    catalog_index = settings.DEFAULT_CATALOG_INDEX if (catalog_index is None) else int(catalog_index)

    skip_rows = 0 if skip_rows is None else int(skip_rows)
    sep = ';' if (sep is None) or (sep == '') else str(sep)

    description = get_description_by_catalog_index(catalog_index)

    try:
        data = database_io.read_data_set_from_database(catalog_index)
        data = data[skip_rows:]
        print('Skipped {} rows.'.format(skip_rows))
        if not(sep == ';'):
            cols = data.columns[0].split(sep)
            cols_dict = dict((key, str(value)) for (key, value) in zip(range(0, len(cols)), cols))
            data = data[data.columns[0]].str.split(sep, expand=True).rename(index=str, columns=cols_dict)
        return data, description
    except ValueError:
        print('Resource #{} could not be read from database!'.format(catalog_index))
        update_local_database = True
    except AttributeError:
        print('Index could not be separated (AttributeError). Continue with download.')
    except sqlalchemy.exc.OperationalError:
        print('Database is probably not running!')
    except sqlalchemy.exc.NoSuchTableError:
        print('There is no such table {}'.format(catalog_index))

    target_url = get_target_url_by_catalog_index(catalog_index)

    print('Downloading resource...')
    start = timer()
    try:
        response = requests.get(target_url)
    except:
        print('RequestError: Is there something wrong with your internet connection?')
        return pd.DataFrame(), description
    end = timer()
    print('Download complete after {} seconds.'.format(end - start))

    status_code = response.status_code

    #try:
    #    pd.DataFrame(data={'catalog_index': [catalog_index], 'status_code': [status_code]}).to_sql('catalog_status', get_postgres_engine(), if_exists='append', index=False)
    #    print('Wrote status_code pair ({},{}) to database.'.format(catalog_index, status_code))
    #except:
    #    print('Status code could not be written to database.')

    if status_code == 404:
        print(log.DATA_SOURCE_NOT_FOUND_ERROR)
        data = pd.DataFrame()
        return data, description

    resource = response.content

#    encoding = 'utf-8'  # response.encoding if not(response.encoding is None) else 'utf-8' # 'latin-1'

    successfully_decoded = False
    encodings = ['utf-8', 'unicode-escape', response.encoding, 'ISO-8859-1', 'latin-1']
    for e in encodings:
        try:
            resource = io.StringIO(resource.decode(e))
            print('Encoding: {}'.format(e))
            successfully_decoded = True
        except UnicodeDecodeError:
            print('Error while decoding with {}'.format(e))
        if successfully_decoded:
            break

    try:
        print('Reading resource: resource={}, sep=<{}>, skip_rows={}'.format(resource, sep, skip_rows))
        data = pd.read_csv(resource, sep=sep, skiprows=skip_rows,
                           skip_blank_lines=True, error_bad_lines=False,  warn_bad_lines=True,
                           keep_default_na=False, quoting=csv.QUOTE_NONE)
    except pd.io.common.EmptyDataError:
        data = pd.DataFrame()
        update_local_database = False
        print(log.EMPTY_DATA_ERROR)
    except IOError:
        print('IO Error!')
        data = pd.DataFrame()
        print(log.EMPTY_DATA_ERROR)

    if int(skip_rows) > 0:
        update_local_database = False

    if update_local_database:
        try:
            database_io.write_data_set_to_database(data, str(catalog_index).zfill(5))
        except UnicodeDecodeError:
            print('Resource  #{} could not be written to database (UnicodeDecodeError)!'.format(catalog_index))

    return data, description

def get_status_code_of_data_set(catalog_index):
    sql = '''select status_code, description
from catalog_status cs natural join catalog_status_codes csc
where cs.status_code = csc.code
and catalog_index = {};'''.format(catalog_index)

    try:
        result = pd.read_sql_query(sql, database_io.get_postgres_engine())
        status, description = result['status_code'][0], result['description'][0]
    except:
        status = 999
        description = ''
        print('Status code could not be read from database.')
    return status, description

def join_data_sets(catalog_index_left, sep_left, catalog_index_right, sep_right, join_pairs):
    data_set_left, description_left   = get_data_set(catalog_index=catalog_index_left, sep=sep_left)
    data_set_right, description_right = get_data_set(catalog_index=catalog_index_right, sep=sep_right)

    print(join_pairs) # join predicate

    left_cols = data_set_left.columns.tolist()
    right_cols = data_set_right.columns.tolist()

    left_on = [left_cols[int(jp['left'])] for jp in join_pairs]
    right_on = [right_cols[int(jp['right'])] for jp in join_pairs]

    print((left_on), 'columns left')
    print((right_on), 'columns right')
    print(len(join_pairs), '#nb of join_pairs')
    print(left_cols, 'data_set_col_index_left')
    print(right_cols, 'data_set_col_index_right')

    try:
        joined_data_set = pd.merge(data_set_left.astype('str'), data_set_right.astype('str'), left_on=left_on, right_on=right_on, how='inner', sort=False)
    except:
        joined_data_set = pd.DataFrame()
        print('Returning empty DataFrame. Error while merging data sets!')

    joined_description = 'Joined data sets #{} and #{}.'.format(catalog_index_left, catalog_index_right)
    return joined_data_set, joined_description

def get_data_set_as_table(catalog_index=settings.DEFAULT_CATALOG_INDEX, skip_rows=0, sep=';', return_index=False, data=None, description=None):
    if (data is None) and (description is None):
        data, description = get_data_set(catalog_index, skip_rows, sep)
    else:
        data, description = data, description
    data_html = data.to_html()
    data_html = util_design.get_custom_table_header() + data_html[82:]
    if return_index:
        return data_html, description, get_current_timestamp(), list(data)
    else:
        return data_html, description, get_current_timestamp()

def get_data_set_as_json(catalog_index=settings.DEFAULT_CATALOG_INDEX, from_index=None, to_index=None, skip_rows=0, sep=';', data=None, description=None):
    if data is None:
        data, description = get_data_set(catalog_index, skip_rows, sep)
    else:
        data, description = data, description
    data_json = '{ "data": ' + data.to_json(orient='records') + '}'
    data_json_length = len(json.loads(data_json)['data'])

    if (from_index is None) and (to_index is None):
        return (data_json, 200)

    if (not from_index is None) and (not to_index is None):
        if (int(from_index) > int(to_index)):
            from_index, to_index = int(to_index), int(from_index)
            print('(swapped indices!)')

    if from_index is None:
        from_index = 0
    if (to_index is None) or (int(to_index) > data_json_length):
        to_index = data_json_length

    print('From index: {} \nTo index: {}'.format(from_index, to_index))

    try:
        result = []
        for i in range(int(from_index), int(to_index)):
            data_json_item = json.loads(data_json)['data'][i]
            result.append(data_json_item)

        data_json = '{ "data": ' + json.dumps(result, indent=4) + '}'
        return (data_json, 200)
    except IndexError:
        return (log.get_custom_error_message_as_json('IndexError'), 400)


def get_catalog(from_database=False):
    if from_database:
        try:
            catalog = pd.read_sql_table('data_catalog', database_io.get_postgres_engine())
            # print('Read catalog from database!')
            # catalog = catalog.to_json(orient='rows')
            # print('Converted to json!')
            return catalog
        except:
            print('Catalog could not be read from database!')

    catalog_path = 'db/catalog.json'
    catalog = None
    try:
        catalog = json.load(open(catalog_path))
        #print('Found catalog @ {}'.format(catalog_path))
    except:
        print('Catalog was not found. Please run polling first!')
    return catalog

def get_length_of_catalog(from_database=False):
    if from_database:
        return database_io.get_length_of_table('catalog')
    return int(len(CATALOG))

def get_target_url_by_catalog_index(catalog_index):
    if catalog_index < 20000: # csv
        df = pd.read_sql_query('select target_url from data_catalog where catalog_index = {}'.format(catalog_index), database_io.get_postgres_engine())
    else: # geojson
        df = pd.read_sql_query('select target_url from \"data-catalog-map\" where catalog_index = {}'.format(catalog_index), database_io.get_postgres_engine())

    return df['target_url'][0]
    # return catalog[catalog_index]['target_url']

def get_description_by_catalog_index(catalog_index, from_database=False):
    try:
        if from_database:
            if catalog_index < 20000:
                df = pd.read_sql_query('select description from data_catalog where catalog_index = {}'.format(catalog_index), database_io.get_postgres_engine())
                description = df['description'][0]
            else: # it's a (tr|m)ap ;-)
                df = pd.read_sql_query('select description from \"data-catalog-map\" where catalog_index = {}'.format(catalog_index), database_io.get_postgres_engine())
                description = df['description'][0]
        else:
            description = get_catalog(from_database=False)[catalog_index]['description']
        description_without_html_tags = re.sub('<[^>]*>', '', description)
        if len(description_without_html_tags) < len(description):
            print('HTML tags were deleted from description.')
            description = description_without_html_tags
        print('Data set: {}'.format(description if not (len(description) == 0) else '(no description available)'))
    except:
        description = ''
        print('Data set\'s description could not be loaded.')
    return description


def get_status_codes():
    # return [catalog_status_json[i]['status_code'] for i in range(catalog_status_length)]

    catalog_status_json = json.loads(CATALOG_STATUS)
    result = []
    for i in range(CATALOG_STATUS_LENGTH):
        try:
            result.append(catalog_status_json[i]['status_code'])
        except IndexError:
            # print('i=', i, 'catalog_status_length=', CATALOG_STATUS_LENGTH, 'IndexError in get_status_codes().')
            break
    return result


##############################################################################################
##############################################################################################
##############################################################################################
recommender.init_recommender()
print('INFO: Initialized recommender.')

CATALOG = get_catalog(from_database=False)
print('INFO: Initialized CATALOG.')

CATALOG_LENGTH = get_length_of_catalog(from_database=False)
print('INFO: Initialized CATALOG_LENGTH.')

CATALOG_STATUS = database_io.get_catalog_status(from_database=True)
print('INFO: Initialized CATALOG_STATUS.')

CATALOG_STATUS_LENGTH = database_io.get_length_of_table('catalog_status')
print('INFO: Counted CATALOG_STATUS_LENGTH.')

CATALOG_STATUS_CODES = get_status_codes()
print('INFO: Initialized CATALOG_STATUS_CODES.')

NUMBER_OF_MAPS = database_io.get_length_of_table('\"data-catalog-map\"')
print('INFO: Counted NUMBER_OF_MAPS.')
##############################################################################################
##############################################################################################
##############################################################################################


'''
reload is necessary for setting default encoding
helps while decoding data sets, not necessary when using Python3

importlib.reload(sys)                          
importlib.sys.setdefaultencoding('UTF8')       
'''
