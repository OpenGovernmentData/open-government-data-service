#!/usr/bin/env python
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

import requests
from random import randint
from timeit import default_timer as timer
import time
from retrieve import *

def test_local_api_endpoints(number, offset=0, random=False):
    basepath = '{}api/data/'.format(settings.HOST)

    if random:
        endpoints = [randint(0, 20000) for x in range(0, number)]
    else:
        endpoints = range(offset, offset + number)

    problems = []

    for e in endpoints:
        path = '{}{}?to=1'.format(basepath, e)
        print('Accessing {}'.format(path))
        try:
            response = requests.get(path, timeout=10)
        except:
            problems.append(path)
        #time.sleep(2)
    print('problems={}'.format(problems))

def benchmark_endpoints():
    number = 3
    offset = 910
    print('=== Downloading {} resources... ==='.format(number))
    start = timer()
    test_local_api_endpoints(number=number, offset=offset, random=False)
    end = timer()
    print('=== Download complete after {} seconds. === '.format(end - start))
    print('=== Retrieving {} resources from database... ==='.format(number))
    start = timer()
    test_local_api_endpoints(number=number, offset=offset, random=False)
    end = timer()
    print('=== Successfully retrieved {} resources after {} seconds. === '.format(number, (end - start)))

def write_status_codes_to_database(begin, n):
    for i in range(begin, begin + n):
        catalog_index = i
        target_url = get_target_url_by_catalog_index(catalog_index)

        #start = timer()
        try:
            #response = requests.get(target_url)
            response = requests.head(target_url, timeout=10)
        except:
            response = None
        #end = timer()
        #print('Download complete after {} seconds.'.format(end - start))

        status_code = 999 if response is None else response.status_code
        if status_code == 999:
            continue
        try:
            pd.DataFrame(data={'catalog_index': [catalog_index], 'status_code': [status_code]}).to_sql('catalog_status',
                                                                                                   database_io.get_postgres_engine(),
                                                                                                   if_exists='append',
                                                                                                   index=False)
            print('Wrote status_code pair ({},{}) to database.'.format(catalog_index, status_code))
        except:
            print('Status code could not be written to database.')


def benchmark_read_description_from_json_versus_from_database():
    times = 100
    sum = 0
    for i in range(times):
        start = timer()
        get_length_of_catalog()
        end = timer()
        # print('Took {} seconds.'.format(end - start))
        sum = sum + (end - start)
    print('avg (from json) = {}'.format(sum / times))
    sum = 0
    for i in range(times):
        start = timer()
        get_length_of_catalog(from_database=True)
        end = timer()
        # print('Took {} seconds.'.format(end - start))
        sum = sum + (end - start)
    print('avg (from database) = {}'.format(sum / times))

def benchmark_read_catalog_from_local_json_versus_from_database():
    times = 100
    sum = 0
    for i in range(times):
        start = timer()
        get_catalog()
        end = timer()
        # print('Took {} seconds.'.format(end - start))
        sum = sum + (end - start)
    print('avg (from json) = {}'.format(sum / times))
    sum = 0
    for i in range(times):
        start = timer()
        get_catalog(from_database=True)
        end = timer()
        # print('Took {} seconds.'.format(end - start))
        sum = sum + (end - start)
    print('avg (from database) = {}'.format(sum / times))

if __name__ == '__main__':
    #test_local_api_endpoints(15000)
    #write_status_codes_to_database(8700)
    #benchmark_read_catalog_from_local_json_versus_from_database()

    test_local_api_endpoints(80000, offset=7170, random=False)
    #write_status_codes_to_database(20000, 390)