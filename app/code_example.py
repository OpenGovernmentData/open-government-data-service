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

def get_code_example(path, catalog_index=950, sep=';', skip_rows=0, _from=0, _to=10):
    '''
    returns a code example with the ability to speak with the **Open Government Data Service**
    :param path: basepath of api
    :param catalog_index:
    :param sep:
    :param skip_rows:
    :param _from:
    :param _to:
    :return: a python code example, string representation
    '''
    return '#!/usr/bin/env python3\n# -*- coding: utf-8 -*-\n\nimport requests\n\nresponse = requests.get(\'{}api/data/{}?sep={}&skip_rows={}&from={}&to={}\')\nprint(response.content)'.format(path, catalog_index, sep, skip_rows, _from, _to)
