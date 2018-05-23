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

import pandas as pd
import json
from sqlalchemy import create_engine


def get_postgres_engine():
    '''
    Creates a PostgreSQL engine that can be uses in order to query the local data catalog database.
    :return: PostgreSQL engine
    '''
    secrets_path = 'secrets/secrets.json'
    secrets = json.load(open(secrets_path))
    database = secrets['postgres']['database']
    port     = secrets['postgres']['port']
    username = secrets['postgres']['username']
    password = secrets['postgres']['password']
    engine_config = 'postgresql://{}:{}@localhost:{}/{}'.format(username, password, str(port), database)
    engine = create_engine(engine_config, encoding='utf8', convert_unicode=True)
    return engine

def get_health_tables_of_catalog_status():
    '''
    :return: the health table indicating how many data sets share which http status code
    '''
    sql = '''select status_code, description, number_of_data_sets
from (select status_code, count(status_code) as number_of_data_sets
		from catalog_status
		group by status_code) as sq
	join catalog_status_codes on status_code = code
order by status_code;'''
    try:
        health_table = pd.read_sql_query(sql, get_postgres_engine())
    except:
        health_table = pd.DataFrame()
        print('Health table could not be read from database.')
    return health_table

def get_data_sets_list_by_status_code(status_code):
    '''
    :param status_code: http status code
    :return: a list of data sets as pd.DataFrame
    '''
    sql = '''select catalog_index, dc.description, target_url, status_code, csc.description as status_code_description
from data_catalog dc
	natural join catalog_status cs
	join catalog_status_codes csc on csc.code = cs.status_code
where status_code = {};'''.format(status_code)
    try:
        data_sets_list = pd.read_sql_query(sql, get_postgres_engine())
    except:
        data_sets_list = pd.DataFrame()
        print('Data sets list could not be read from database.')
    return data_sets_list


def get_data_sets_list_by_status_code_api(status_code):
    '''
    :param status_code:
    :return:  a list of data sets as pd.DataFrame
    '''
    sql = '''select dc.catalog_index, dc.target_url, dc.description
from data_catalog dc natural join catalog_status cs
where status_code = {};'''.format(status_code)
    try:
        data_sets_list = pd.read_sql_query(sql, get_postgres_engine())
    except:
        data_sets_list = pd.DataFrame()
        print('Data sets list could not be read from database (API).')
    return data_sets_list


def get_catalog_status(from_database=False):
    '''
    :param from_database: if it should be read from the postgres database or the local json file
    :return: a full list of status codes that can be joined with all data sets
    '''
    catalog_status_path = 'db/catalog_status.json'
    if from_database:
        sql = 'select catalog_index, status_code from data_catalog natural join catalog_status order by catalog_index asc;'
        try:
            catalog_status = pd.read_sql_query(sql, get_postgres_engine())
            catalog_status = catalog_status.to_json(orient='records')
            print('Read catalog status from database.')

            with open(catalog_status_path, 'w') as file:
                file.write(json.dumps(catalog_status, indent=4))
            print('Wrote catalog status to {}'.format(catalog_status_path))

        except:
            catalog_status = pd.DataFrame()
            print('Catalog status could not be read from database and/or written to {}.'.format(catalog_status_path))
    else:
        try:
            catalog_status = json.load(open(catalog_status_path))
            print('Found catalog status @ {}'.format(catalog_status_path))
        except:
            print('Catalog could not be read locally -> Reading from database...')
            return get_catalog_status(from_database=True)
    return catalog_status


def get_length_of_table(table):
    '''
    :param table: name of postgres table
    :return: length as int, -1 if not existent
    '''
    try:
        df = pd.read_sql_query('select count(*) as length from {}'.format(table), get_postgres_engine())
        return df['length'][0]
    except:
        print('Could not query length of table={} from database!'.format(table))
    return -1

def write_data_catalog_to_database():
    '''
    materialises data catalog as whole to the database
    :return:
    '''
    catalog_df = pd.read_json('db/catalog.json')
    table = 'data_catalog'
    catalog_df.to_sql(table, get_postgres_engine(), if_exists='replace', index=True)
    print('Success!')

def write_catalog_to_database():
     print('Be sure to uncomment the write_catalog_to_database() method. Danger zone: Replaces catalog!')
     #print('Writing catalog to database...')
     #catalog_path = 'db/catalog.json'
     #data = pd.read_json(catalog_path)
     #print(data)
     #engine = get_postgres_engine()
     #data.to_sql(catalog, engine, if_exists='replace')
     #print('Wrote catalog to database.')

def write_data_set_to_database(data, catalog_index):
    '''
    writes one data set to catalog
    :param data: data set as DataFrame object
    :param catalog_index:
    '''
    print('Writing #{} to database...'.format(catalog_index))
    engine = get_postgres_engine()
    table = 'dataset-{}'.format(catalog_index) # with leading 0s
    data.to_sql(table, engine, if_exists='replace', index=False)
    print('Wrote #{} to database.'.format(catalog_index))

def read_data_set_from_database(catalog_index):
    '''
    reads one data set from database and return DataFrame object
    :param catalog_index:
    :return:
    '''
    print('Reading #{} from database...'.format(catalog_index))
    engine = get_postgres_engine()
    table = 'dataset-{}'.format(str(catalog_index).zfill(5))
    data = pd.read_sql_table(table, engine)
    print('Read #{} successfully from database.'.format(catalog_index))
    return data

def create_recommender_and_comments_tables():
    '''
    creates tables for recommender system if they do not already exist
    '''
    engine = get_postgres_engine()
    create_recommender_table = 'create table if not exists recommender (catalog_index SERIAL, upvotes int, downvotes int);'
    create_comments_table = 'create table if not exists comments (catalog_index SERIAL, comment text, date timestamp);'
    engine.execute(create_recommender_table)
    engine.execute(create_comments_table)

def init_rating(catalog_index):
    '''
    creates a record for the rating of a data set (runs once for every data set)
    :param catalog_index:
    :return:
    '''
    get_postgres_engine().execute('insert into recommender (catalog_index, upvotes, downvotes) values ({}, 0, 0);'.format(catalog_index))

def get_rating(catalog_index):
    '''
    returns recommender rating
    :param catalog_index:
    :return:
    '''
    query = ('select * from recommender where catalog_index = {};'.format(catalog_index))
    df = pd.read_sql_query(query, get_postgres_engine())
    if df.empty:
        init_rating(catalog_index)
        return get_rating(catalog_index)
    else:
        return df

def get_comments(catalog_index):
    '''
    returns comments for any data set
    :param catalog_index:
    :return:
    '''
    query = ('select * from comments where catalog_index = {};'.format(catalog_index))
    return pd.read_sql_query(query, get_postgres_engine())

def set_rating(catalog_index, rating, offset):
    '''
    replaces the current rating of a data set with respect to the recommender system
    :param catalog_index:
    :param rating:
    :param offset:
    :return:
    '''
    update_rating = 'update recommender set {0} = {0} + {1} where catalog_index = {2};'.format(rating, offset, catalog_index)
    get_postgres_engine().execute(update_rating)

def get_top_k_recommmended_data_sets(k):
    '''
    returns recommended data sets if there are more upvotes than downvotes
    :param k: number of data sets
    :return:
    '''
    query = 'select * from recommender where upvotes > downvotes order by upvotes desc limit {};'.format(k)
    return pd.read_sql_query(query, get_postgres_engine())

def search_data_set(description):
    query = '''select catalog_index, description from (
		          select * from data_catalog where lower(description) like lower('%%{0}%%') 
	            union
		          select * from "data-catalog-map" where lower(description) like lower('%%{0}%%'))
	          as sq
              order by description;'''.format(description) # escape % with %% !
    df = pd.read_sql_query(query, get_postgres_engine())
    print('Performed search for: {}'.format(description))
    return df.to_json(orient='records')