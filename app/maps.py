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
import psycopg2
import requests
import pandas as pd
from pandas.io import sql
import datetime
import time
import json
import io
import sys
import re
import util_design
from math import *
from sqlalchemy import create_engine
from sqlalchemy import text
from timeit import default_timer as timer
import matplotlib
matplotlib.use("Agg") # removes the rocket icon in macOS dock
import matplotlib.pyplot as plt
import numpy as np
import log_strings as log
import settings
import sqlalchemy
import database_io
from pandas.io.json import json_normalize

import retrieve

import geopandas as gpd
from shapely.geometry import *

def get_geojson_by_catalog_index(catalog_index):
    try:
        response = read_geojson_from_database(catalog_index)
        return response
    except:
        source = download_resource(catalog_index)
        write_geojson_to_database(catalog_index, source)
        return get_geojson_by_catalog_index(catalog_index)

def write_geojson_to_database(catalog_index, source):
    print('Writing #{} geojson to database...'.format(catalog_index))
    table = '\"dataset-{}\"'.format(str(catalog_index).zfill(5))

    drop_table = 'drop table if exists {}'.format(table)
    database_io.get_postgres_engine().execute(drop_table)

    create_table = 'create table if not exists {} (geojson json);'.format(table)
    database_io.get_postgres_engine().execute(create_table)

    delete_records = 'delete from {};'.format(table)
    database_io.get_postgres_engine().execute(delete_records)

    source_decoded = None
    successfully_decoded = False
    encodings = ['utf-8', 'unicode-escape', 'ISO-8859-1', 'latin-1']
    for e in encodings:
        try:
            source_decoded = source.decode(e)
            print('Encoding: {}'.format(e))
            successfully_decoded = True
        except UnicodeDecodeError:
            print('Error while decoding with {}'.format(e))
        if successfully_decoded:
            break

    insert_values = 'insert into {} (geojson) values (\'{}\');'.format(table, source_decoded.replace('%', '%%'))
    database_io.get_postgres_engine().execute(insert_values)
    print('Wrote #{} geojson to database!'.format(catalog_index))

def read_geojson_from_database(catalog_index):
    print('Reading #{} geojson from database...'.format(catalog_index))
    table = '\"dataset-{}\"'.format(str(catalog_index).zfill(5))

    select_geojson = 'select * from {} limit 1;'.format(table)
    result = database_io.get_postgres_engine().execute(select_geojson)

    rows = [row for row in result]
    geojson = rows[0][0]

    print('Read #{} geojson from database!'.format(catalog_index))

    return json.dumps(geojson)

def download_resource(catalog_index):
    target_url = retrieve.get_target_url_by_catalog_index(catalog_index)
    print(target_url)
    try:
        print('Downloading #{}'.format(catalog_index))
        return requests.get(target_url).content
    except:
        print('Resource could not be downloaded! Returning empty resource!')
        return ''

def get_geojson_table(geojson, description):
    df_normalized = json_normalize(json.loads(geojson))
    df = pd.DataFrame(data=df_normalized['features'][0])
    return retrieve.get_data_set_as_table(data=df, description=description)

def write_geojson_catalog_json():
    response = requests.get('https://www.govdata.de/ckan/api/3/action/resource_search?query=format:geojson').content
    resources = json.loads(response)['result']['results']

    geojson_catalog = []
    for r in resources:
        r_target_url = r['url']

        r_description = ''
        if r['name'] is not None:
            r_description = r['name']
        if r['description'] is not None:
            r_description = r_description + ' ' + r['description']
        if len(r_description) == 0 or r_description is None:
            r_description = r_description.strip()

        geojson_catalog.append({'description': r_description,
                        'target_url': r_target_url})

    catalog_path = 'db/catalog-geojson.json'
    with open(catalog_path, 'w') as file:
        file.write(json.dumps(geojson_catalog, indent=4))
    print('Wrote catalog to {}'.format(catalog_path))
    return geojson_catalog


def write_map_catalog_to_database():
    gsc = write_geojson_catalog_json()
    catalog_path = 'db/catalog-geojson.json'
    df = pd.read_json(json.dumps(gsc), orient='records')
    # source = json.loads(catalog_path)
    l = 20000 # starting at 20000  not interfering with other CSV data sets
    for i in range(0, 385):
        try:
            insert_values = 'insert into \"data-catalog-map\" (catalog_index, description, target_url) values ({}, \'{}\', \'{}\');'.format(
                l, df['description'][i], df['target_url'][i])
            database_io.get_postgres_engine().execute(insert_values)
        except:
            print(insert_values)
            continue
        l = l + 1
    # df.to_sql('data-catalog-map', engine, if_exists='replace')
    print('Wrote map catalog to database.')


if __name__ == '__main__':
    write_map_catalog_to_database()
