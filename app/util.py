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

import os
import platform
import datetime
import time

def get_file_creation_date(path_to_file):
    """
    Try to get the date that a file was created, falling back to when it was
    last modified if that isn't possible.
    See http://stackoverflow.com/a/39501288/1709587 for explanation.

    :return ready parsed timestamp
    """
    if platform.system() == 'Windows':
        result = os.path.getctime(path_to_file)
    else:
        stat = os.stat(path_to_file)
        try:
            result = stat.st_birthtime
        except AttributeError:
            # We're probably on Linux. No easy way to get creation dates here,
            # so we'll settle for when its content was last modified.
            result = stat.st_mtime

    return datetime.datetime.fromtimestamp(result)

def get_current_timestamp(update_string='Update: '):
    return update_string + datetime.datetime.fromtimestamp(time.time()).strftime('%d.%m.%Y %H:%M') + 'h'

def get_installed_packages():
    '''
    lists all installed python packages
    :return: (installed_packages as sorted list, length of that list)
    '''
    import pip

    installed_packages = pip.get_installed_distributions()
    installed_packages_list = sorted(["%s==%s" % (i.key, i.version) for i in installed_packages])

    for i in installed_packages_list:
        print(i)

    print('nb of packages={}'.format(len(installed_packages_list)))
    return  installed_packages_list, len(installed_packages_list)
