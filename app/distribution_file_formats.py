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

def retrieve_distribution():
	formats = ['csv', 'html', 'xml', 'rdf', 'xls', 'xslx', 'doc', 'docx', 'odt', 'ods', 'pdf', 'jpeg', 'png', 'json', 'geojson', 'wms', 'wfs', 'kml']
	count_all = []

	api = 'https://www.govdata.de/ckan/api/3/action/resource_search?query=format:{}'

	for f in formats:
		try:
			response = requests.get(api.format(f)).content
			count = json.loads(response)['result']['count']
			count_all.append(int(count))
			print('({}, {})'.format(f, count))
		except:
			print('There went something wrong!')

	print('sum: ', sum(count_all))
	for i in range(0, len(formats)):
		percentage = float(count_all[i]) / sum(count_all) 
		print('{} & {} & {}\\\%\\\\'.format(formats[i], count_all[i], percentage))

print('Starting service...')
retrieve_distribution()
print('Finished!')
