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

import numpy as np
import util_design
import database_io

def init_recommender():
    try:
        database_io.create_recommender_and_comments_tables()
    except:
        print('Could not initialise recommender!')

def set_rating(catalog_index, rating, offset=1):
    try:
        database_io.set_rating(catalog_index, rating, offset)
        print('Updated rating for #{} ({} by {})!'.format(catalog_index, rating, offset))
    except:
        print('Could not increase rating!')

def get_rating(catalog_index):
    df = database_io.get_rating(catalog_index)
    return df

def get_top_k_recommended_data_sets(k=10):
    df = database_io.get_top_k_recommmended_data_sets(k)
    df.index = np.arange(1, len(df) + 1)
    return df

def get_k_recommended_table(k=10):
    recommended_data_sets = get_top_k_recommended_data_sets(k).to_html()
    recommended_data_sets = recommended_data_sets.replace('catalog_index', 'Catalog index')
    recommended_data_sets = recommended_data_sets.replace('upvotes', '&#128077;') # thumbs up
    recommended_data_sets = recommended_data_sets.replace('downvotes', '&#128077;') # thumbs down
    recommended_data_sets = recommended_data_sets.replace('text-align: right;', 'text-align: left;')
    recommended_data_sets = recommended_data_sets.replace('<table border="1" class="dataframe">', '<table class="table" id="recommender-table">')
#     import re
#     recommended_data_sets = re.sub(
# '''<tr>
# <th>[0-9]</th>
# <td>[0-9]</td>
# <td>[0-9]</td>
# <td>[0-9]</td>
# </tr>''',
# '''<tr>
# <th>[0-9]</th>
# <td><a href="data/[0-9]">[0-9]</a></td>
# <td>[0-9]</td>
# <td>[0-9]</td>
#</tr>''', recommended_data_sets)
    return recommended_data_sets

def get_comments(catalog_index):
    '''
    needs to be implemented. database is already set up
    :param catalog_index:
    :return:
    '''
    #comments = database_io.get_comments(catalog_index)
    pass
