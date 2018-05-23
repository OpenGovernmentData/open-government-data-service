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

from werkzeug.contrib.profiler import ProfilerMiddleware
from main import app

'''
This module helps debugging by enabling profiling methods.
'''

app.config['PROFILE'] = True
app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions = [30])
app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=True, threaded=False)
