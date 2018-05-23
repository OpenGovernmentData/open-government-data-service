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

import requests
import json

def retrieve_catalog():
    '''
    Downloads CKAN package list grom govdata.de and filters for packages containing CSV resources.
    Prints comment when successfully done single steps.
    :return: returns data catalog
    '''
    print('Retrieving full CKAN index...')
    DATA_CATALOG_PACKAGES_URL = 'https://www.govdata.de/ckan/api/3/action/package_list?q='
    govdata_packages = requests.get(DATA_CATALOG_PACKAGES_URL).content
    print('Done.')

    ckan_start_index = 0
    ckan_end_index = 15000 # adjust size of catalog here

    print('Selecting {} packages...'.format(ckan_end_index - ckan_start_index))
    govdata_package_ids = []
    for i in range(ckan_start_index, ckan_end_index):
        if (i % 500) == 0:
            print(i)
        current_package_id = json.loads(govdata_packages)['result'][i]
        govdata_package_ids.append(current_package_id)
    print('Sucessfully selected packages.')

    # print(govdata_package_ids)

    catalog = []
    number_of_packages_retrieved = 0
    for i in govdata_package_ids:
        i_META_DATA_URL = 'https://www.govdata.de/ckan/api/3/action/package_show?id={}'.format(i)
        package = requests.get(i_META_DATA_URL).content
        resources = json.loads(package)['result']['resources']
        number_of_resources = len(resources)
        # print('\nid={} has {} resources:'.format(i, number_of_resources))
        for r in resources:
            is_csv = r['format'] == 'CSV'
            if is_csv:
                r_target_url = r['url']
                r_description = ''
                if r['name'] is not None:
                    r_description = r['name']
                if r['description'] is not None:
                    r_description = r_description + r['description']
                if len(r_description) == 0 or r_description is None:
                    r_description = r_description.strip()

                catalog.append({ 'description' : r_description,
                                 'target_url': r_target_url }, )
                print('id={}, resource-id={} is in csv format and was added!'.format(i, r['id']))
            else:
                # print('resource-id={} is not in csv format!'.format(r['id']))
                pass
        number_of_packages_retrieved = number_of_packages_retrieved + 1
        print('\n{} of {}'.format(number_of_packages_retrieved, (ckan_end_index - ckan_start_index)))

    print('\nSuccessfully collected {} resources.'.format(len(catalog)))
    return catalog

def write_catalog_as_json(catalog):
    catalog_path = 'db/catalog.json'
    with open(catalog_path, 'w') as file:
        file.write(json.dumps(catalog, indent=4))
    print('Wrote catalog to {}'.format(catalog_path))

if __name__ == '__main__':
    print('INFO: Started polling of catalog.')
    catalog = retrieve_catalog()
    write_catalog_as_json(catalog)
    print('INFO: Finished polling of catalog.')