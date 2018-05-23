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

import mpld3
import numpy as np
import seaborn as sns
from matplotlib import pyplot as plt
import matplotlib
matplotlib.use("Agg") # removes the rocket icon in macOS dock

import settings
from retrieve import get_data_set

def get_visualization(catalog_index=settings.DEFAULT_CATALOG_INDEX, x_axis=None, y_axis=None, sep=';', skip_rows=0, data=None, description=None):
    if (data is None):
        data, description = get_data_set(catalog_index, sep=sep, skip_rows=skip_rows)
    else:
        data, description = data, description

    plottable_columns = data.select_dtypes(include=[np.number]).columns.tolist()

    # print('plottable columns={}'.format(plottable_columns))
    # print('number of plottable columns={}'.format(len(plottable_columns)))

    if (data is None) or len(plottable_columns) < 2:
        return None, None

    x = plottable_columns[0] if x_axis is None else plottable_columns[x_axis]
    y = plottable_columns[1] if y_axis is None else plottable_columns[y_axis]

    # print(plottable_columns[0])
    # print(plottable_columns[1])

    # styling with seaborn
    sns.set()
    sns.despine(trim=True)
    sns.set_context("poster")
    sns.set_style("whitegrid")
    sns.palplot(sns.color_palette("coolwarm", 7))

    fig, ax = plt.subplots()
    plot = plt.plot(data[[x]], data[[y]], 'o-') #, linewidth=2.5)

    # extend here with other diagram types as histogram or similar for example like this:
    # ax.hist(x=data[[x]], bins=1, histtype='bar')

    fig.set_figheight(7)
    fig.set_figwidth(13)
    #ax.set_aspect(0.0005000)
    #ax.grid(True, alpha=0.3, which='both')
    ax.set_title(description[:50])
    ax.set_xlabel(x)
    ax.set_ylabel(y)

    label_part1 = list(map(str, data[x]))
    label_part2 = list(map(str, data[y]))
    #span = '<span class="badge badge-primary">{}</span>' # change CSS of label from text to badge (needs to be escaped)
    labels = [('#' + str(i) + ': ' + label_part1[i] + ' | ' + label_part2[i]) for i in range(len(label_part1))]
    tooltip = mpld3.plugins.PointLabelTooltip(plot[0], labels=labels, voffset=20, hoffset=10)
    mpld3.plugins.connect(fig, tooltip)

    visualization_html = mpld3.fig_to_html(fig)
    # return visualization_html, [x.decode('unicode-escape') for x in plottable_columns]
    return visualization_html, plottable_columns