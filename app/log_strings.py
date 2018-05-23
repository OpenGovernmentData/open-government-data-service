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

EMPTY_DATA_ERROR = 'EmptyDataError: Maybe you skipped too many rows or resource is empty.'
ENDPOINT_DOES_NOT_EXIST_ERROR = 'EndpointDoesNotExistError: This endpoint does not exist.'
DATA_SOURCE_NOT_FOUND_ERROR = 'DataSourceNotFoundError: This external resource is not available (404).'

def get_custom_error_message_as_json(message='UnknownError'):
    '''
    creates custom error message as json
    :param message:
    :return:
    '''
    return '{ "error" : " ' + message + ' " }'