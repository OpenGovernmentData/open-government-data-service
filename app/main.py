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

from flask import Flask, request, render_template, redirect, send_file
from flask_compress import Compress
from flask_swagger_ui import get_swaggerui_blueprint
import json
import database_io
import recommender
import retrieve
import settings
import code_example
import log_strings
import util
import maps
import visualization
import util_design

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['EXPLAIN_TEMPLATE_LOADING'] = False

Compress(app)

@app.route('/', methods=['GET'])
def get_view_index(catalog_index=settings.DEFAULT_CATALOG_INDEX, sep=';'):
    health_table = database_io.get_health_tables_of_catalog_status()

    return app.make_response(render_template(template_name_or_list='index.html',
                                             health_table=health_table,
                                             length=retrieve.CATALOG_LENGTH,
                                             nb_maps=retrieve.NUMBER_OF_MAPS))

@app.route('/data/<int:catalog_index>', methods=['POST'])
def get_view_index_by_catalog_index(catalog_index=settings.DEFAULT_CATALOG_INDEX):
    form_catalog_index  = request.form.get('catalog_index', type=int)
    if (form_catalog_index is None) or (form_catalog_index == ''):
        redirect('/data/{}'.format(settings.DEFAULT_CATALOG_INDEX))

    form_sep = request.form.get('sep', type=str)
    form_sep = ';' if ((form_sep is None) or (form_sep == '')) else form_sep

    form_x_axis = int(request.form.get('x_axis')) if request.form.get('x_axis') is not None else None
    form_y_axis = int(request.form.get('y_axis')) if request.form.get('y_axis') is not None else None
    form_catalog_index_hidden = int(request.form.get('catalog_index_hidden')) if request.form.get('catalog_index_hidden') is not None else None
    if form_catalog_index is None and not(form_catalog_index_hidden is None):
        form_catalog_index = form_catalog_index_hidden

    print('View for data set #{}.'.format(form_catalog_index))
    return get_view_data_set_by_catalog_index(catalog_index=form_catalog_index, sep=form_sep, x_axis=form_x_axis, y_axis=form_y_axis, embedded=True)

@app.route('/data/<int:catalog_index>', methods=['GET'])
def get_view_data_set_by_catalog_index(catalog_index=settings.DEFAULT_CATALOG_INDEX, sep=';', skip_rows=0, x_axis=None, y_axis=None, embedded=True):
    if(catalog_index >= 20000):
        return get_data_catalog_index_map(catalog_index)

    template = 'data_set.html'
    query_sep = request.args.get('sep', type=str)
    sep = sep if ((query_sep is None) or (query_sep == '')) else query_sep
    query_skip_rows = request.args.get('skip_rows', type=int)
    skip_rows_ = skip_rows if (query_skip_rows is None) else query_skip_rows
    #print(query_skip_rows)

    table, description, timestamp = retrieve.get_data_set_as_table(catalog_index=catalog_index, sep=sep, skip_rows=skip_rows_)
    target_url_external = retrieve.get_target_url_by_catalog_index(catalog_index)
    status_code, status_code_description = retrieve.get_status_code_of_data_set(catalog_index)

    catalog_length = retrieve.CATALOG_LENGTH

    visualization_html, plottable_columns = visualization.get_visualization(catalog_index, x_axis, y_axis, sep=sep, skip_rows=skip_rows_)
    jump_to_visualization = False if (visualization_html is None) else True

    rating = recommender.get_rating(catalog_index)
    recommended_data_sets = recommender.get_k_recommended_table(5)

    return app.make_response(render_template(template_name_or_list=template,
                                                 catalog_table=table,
                                                 timestamp=timestamp,
                                                 catalog_index=catalog_index,
                                                 sep=sep,
                                                 skip_rows = skip_rows_,
                                                 status_code=status_code,
                                                 status_code_description=status_code_description,
                                                 description=description,
                                                 catalog_length=catalog_length,
                                                 target_url_external=target_url_external,
                                                 visualization=visualization_html,
                                                 plottable_columns=plottable_columns,
                                                 x_axis=x_axis,
                                                 y_axis=y_axis,
                                                 jump_to_visualization=jump_to_visualization,
                                                 embedded=embedded,
                                                 upvotes=rating['upvotes'][0],
                                                 downvotes=rating['downvotes'][0],
                                                 recommended_data_sets=recommended_data_sets,
						                         service_url=settings.HOST))

@app.route('/data/join/', methods=['GET'])
def get_view_data_join():
    return app.make_response(render_template(template_name_or_list='join.html'))

@app.route('/data/join/<int:catalog_index_left>/<int:catalog_index_right>', methods=['GET'])
def get_view_join_data_sets_by_catalog_ids(catalog_index_left, catalog_index_right, sep_left=';', sep_right=';'):
    template_main = 'data_set_join.html'
    template_single = 'data_set.html'
    catalog_length = retrieve.CATALOG_LENGTH

    query_sep_left = request.args.get('sep_left', type=str)
    sep_left = sep_left if ((query_sep_left is None) or (query_sep_left == '')) else query_sep_left

    table_left, description_left, timestamp_left, index_left = retrieve.get_data_set_as_table(catalog_index=catalog_index_left, sep=sep_left, return_index=True)
    target_url_external_left = retrieve.get_target_url_by_catalog_index(catalog_index_left)
    status_code_left, status_code_description_left = retrieve.get_status_code_of_data_set(catalog_index_left)

    template_left = render_template(template_name_or_list=template_single,
                                   catalog_table=table_left,
                                   timestamp=timestamp_left,
                                   catalog_index=catalog_index_left,
                                   sep=sep_left,
                                   status_code=status_code_left,
                                   status_code_description=status_code_description_left,
                                   description=description_left,
                                   catalog_length=catalog_length,
                                   target_url_external=target_url_external_left,
                                   visualization=None,
                                   embedded=False,
				                   service_url=settings.HOST)

    query_sep_right = request.args.get('sep_right', type=str)
    sep_right = sep_right if ((query_sep_right is None) or (query_sep_right == '')) else query_sep_right

    table_right, description_right, timestamp_right, index_right = retrieve.get_data_set_as_table(catalog_index=catalog_index_right, sep=sep_right, return_index=True)
    target_url_external_right = retrieve.get_target_url_by_catalog_index(catalog_index_right)
    status_code_right, status_code_description_right = retrieve.get_status_code_of_data_set(catalog_index_left)

    template_right = render_template(template_name_or_list=template_single,
                                   catalog_table=table_right,
                                   timestamp=timestamp_right,
                                   catalog_index=catalog_index_right,
                                   sep=sep_right,
                                   status_code=status_code_right,
                                   status_code_description=status_code_description_right,
                                   description=description_right,
                                   catalog_length=catalog_length,
                                   target_url_external=target_url_external_right,
                                   visualization=None,
                                   embedded=False,
                                   service_url=settings.HOST)

    print('index_left={}, index_right={}'.format(index_left, index_right))

    return app.make_response(render_template(template_name_or_list=template_main,
                                                 view_left= template_left,
                                                 view_right=template_right,
                                                 index_left=index_left,
                                                 index_right=index_right))

@app.route('/data/join/<int:catalog_index_left>/<int:catalog_index_right>', methods=['POST'])
def get_view_perform_join(catalog_index_left, catalog_index_right, sep_left=';', sep_right=';', sep_joined=';'):
    template = 'data_set.html'

    query_sep_left = request.args.get('sep_left', type=str)
    sep_left = sep_left if ((query_sep_left is None) or (query_sep_left == '')) else query_sep_left

    query_sep_right = request.args.get('sep_right', type=str)
    sep_right = sep_right if ((query_sep_right is None) or (query_sep_right == '')) else query_sep_right

    query_sep_joined = request.args.get('sep_joined', type=str)
    sep_joined = sep_joined if ((query_sep_joined is None) or (query_sep_joined == '')) else query_sep_joined

    join_pairs = json.loads(request.form.get('joinPairsForm'))
    joined_data_set, joined_description = retrieve.join_data_sets(catalog_index_left, sep_left, catalog_index_right, sep_right, join_pairs)
    table, description, timestamp = retrieve.get_data_set_as_table(data=joined_data_set, description=joined_description)

    target_url_internal = 'join/{}/{}?sep_left={}&sep_right={}'.format(catalog_index_left, catalog_index_right, sep_left, sep_left)
    status_code, status_code_description = retrieve.get_status_code_of_data_set(catalog_index_left)
    joined_catalog_index = 'join/{}/{}'.format(catalog_index_left, catalog_index_right)
    catalog_length = retrieve.CATALOG_LENGTH

    visualization_html, plottable_columns = visualization.get_visualization(data=joined_data_set, description=joined_description)
    jump_to_visualization = False if (visualization_html is None) else True

    return app.make_response(render_template(template_name_or_list=template,
                                                 catalog_table=table,
                                                 timestamp=timestamp,
                                                 catalog_index=joined_catalog_index,
                                                 sep=sep_joined,
                                                 status_code=status_code,
                                                 status_code_description=status_code_description,
                                                 description=joined_description,
                                                 catalog_length=catalog_length,
                                                 target_url_external=target_url_internal,
                                                 visualization=visualization_html,
                                                 plottable_columns=plottable_columns,
                                                 x_axis=None,
                                                 y_axis=None,
                                                 jump_to_visualization=jump_to_visualization,
                                                 embedded=True,
						                         service_url=settings.HOST))

@app.route('/api/data/<int:catalog_index>', methods=['GET'])
def get_api_data_by_catalog_index(catalog_index=None):
    if catalog_index > (20000 + retrieve.NUMBER_OF_MAPS):
        # print(catalog_index, retrieve.CATALOG_LENGTH + retrieve.NUMBER_OF_MAPS, retrieve.CATALOG_LENGTH, retrieve.NUMBER_OF_MAPS)
        return app.response_class(response=log_strings.get_custom_error_message_as_json(log_strings.ENDPOINT_DOES_NOT_EXIST_ERROR),
                                  status=404, mimetype='application/json')

    query_from      = request.args.get('from', type=int)
    query_to        = request.args.get('to', type=int)
    query_skip_rows = request.args.get('skip_rows', type=str)
    query_sep       = request.args.get('sep', type=str)

    data_json, status = retrieve.get_data_set_as_json(catalog_index, query_from, query_to, query_skip_rows, query_sep)
    return app.response_class(response=data_json, status=status, mimetype='application/json')

@app.route('/api/data/visualization/<int:catalog_index>', methods=['GET'])
def get_api_visualization(catalog_index):
    if catalog_index > retrieve.CATALOG_LENGTH:
        return app.response_class(response=log_strings.get_custom_error_message_as_json(log_strings.ENDPOINT_DOES_NOT_EXIST_ERROR),
                                  status=404, mimetype='application/json')
    x_axis = 0      if request.args.get('x_axis', type=int) is None     else request.args.get('x_axis', type=int)
    y_axis = 0      if request.args.get('y_axis', type=int) is None     else request.args.get('y_axis', type=int)
    sep = ';'       if request.args.get('sep', type=str)  is None       else request.args.get('sep', type=str)
    skip_rows = 0   if request.args.get('skip_rows', type=int) is None  else request.args.get('skip_rows', type=int)

    visualization_html, plottable_columns = visualization.get_visualization(catalog_index, x_axis=x_axis, y_axis=y_axis, sep=sep, skip_rows=skip_rows)

    if visualization_html is None:
        response = log_strings.get_custom_error_message_as_json('There is something wrong with the query parameters!')
        return app.response_class(response=response, status=400, mimetype='application/json')

    return visualization_html

@app.route('/api/data/join/<int:catalog_index_left>/<int:catalog_index_right>', methods=['POST'])
def get_api_data_perform_join(catalog_index_left, catalog_index_right, sep_left=';', sep_right=';', sep=';'):
    if catalog_index_left  > retrieve.CATALOG_LENGTH or catalog_index_right > retrieve.CATALOG_LENGTH:
        return app.response_class(response=log.get_custom_error_message_as_json(log_strings.ENDPOINT_DOES_NOT_EXIST_ERROR),
                                  status=404, mimetype='application/json')

    query_from      = request.args.get('from', type=int)
    query_to        = request.args.get('to', type=int)
    query_skip_rows = request.args.get('skip_rows', type=str)
    query_sep       = request.args.get('sep', type=str)

    join_pairs = request.get_json()
    joined_data_set, joined_description = retrieve.join_data_sets(catalog_index_left, sep_left, catalog_index_right, sep_right, join_pairs)

    data_json, status = retrieve.get_data_set_as_json(None, query_from, query_to, query_skip_rows, query_sep, data=joined_data_set)
    return app.response_class(response=data_json,
                              status=status,
                              mimetype='application/json')

@app.route('/api/data', methods=['GET'])
def get_api_data():
    query_status_code = request.args.get('status_code', type=int)
    query_search = request.args.get('search', type=str)

    if not (query_search is None):
        result = database_io.search_data_set(query_search)
        return app.response_class(response=result, status=200, mimetype='application/json')

    if query_status_code is None:
        data_json, status = '{ "data": ' + json.dumps(retrieve.CATALOG, indent=4) + '}', 200
    else:
        df = database_io.get_data_sets_list_by_status_code_api(query_status_code)
        data_json, status = '{ "data": ' + df.to_json(orient="records") + '}', 200

    return app.response_class(response=data_json, status=status, mimetype='application/json')


@app.route('/data', methods=['GET'])
def get_view_data_catalog():
    catalog_timestamp = 'Last update: {}'.format(util.get_file_creation_date('db/catalog.json'))
    query_status_code = request.args.get('status_code', type=int)

    if query_status_code is None:
        template = 'catalog.html'
        response = app.make_response(render_template(template,
                                                     catalog=retrieve.CATALOG,
                                                     catalog_length=retrieve.CATALOG_LENGTH,
                                                     catalog_status=retrieve.CATALOG_STATUS_CODES,
                                                     catalog_status_length=retrieve.CATALOG_STATUS_LENGTH,
                                                     catalog_timestamp=catalog_timestamp))
    else:
        template = 'catalog_by_status_code.html'
        catalog_by_status_code = database_io.get_data_sets_list_by_status_code(query_status_code)
        response = app.make_response(render_template(template,
                                                     status_code=query_status_code,
                                                     catalog=catalog_by_status_code,
                                                     catalog_timestamp=catalog_timestamp))
    return response


def get_data_catalog_index_map(catalog_index):
    template = 'map.html'
    description = retrieve.get_description_by_catalog_index(catalog_index, from_database=True)
    geo_json_feature_collection = maps.get_geojson_by_catalog_index(catalog_index)
    table, description_, current_timestamp = maps.get_geojson_table(geo_json_feature_collection, description)
    status_code, status_code_description = retrieve.get_status_code_of_data_set(catalog_index)

    rating = recommender.get_rating(catalog_index)
    recommended_data_sets = recommender.get_k_recommended_table(5)

    return app.make_response(render_template(template,
                                             catalog_index=catalog_index,
                                             leaflet=True,
                                             geo_json_feature_collection=geo_json_feature_collection,
                                             target_url_external=retrieve.get_target_url_by_catalog_index(catalog_index),
                                             description=description,
                                             catalog_table=table,
                                             status_code=status_code,
                                             status_code_description=status_code_description,
                                             upvotes=rating['upvotes'][0],
                                             downvotes=rating['downvotes'][0],
                                             recommended_data_sets=recommended_data_sets,
						                     service_url=settings.HOST))

@app.route('/api/data/rating/<int:catalog_index>', methods=['POST'])
def update_rating(catalog_index=950):
    rating = 'upvotes' if request.args.get('rating', type=str) is None else request.args.get('rating', type=str)
    offset = 0         if request.args.get('offset', type=int) is None else request.args.get('offset', type=int)
    recommender.set_rating(catalog_index, rating, offset)
    return app.response_class(response=recommender.get_rating(catalog_index).to_json(orient='records'), status=200, mimetype='application/json')

@app.route('/api/data/rating/<int:catalog_index>', methods=['GET'])
def get_rating(catalog_index=950):
    return app.response_class(response=recommender.get_rating(catalog_index).to_json(orient='records'), status=200, mimetype='application/json')


@app.route('/api/client', methods=['GET'])
def get_client_python():
    catalog_index   = request.args.get('catalog_index', type=int) if not request.args.get('catalog_index', type=int) is None else 950
    query_from      = request.args.get('from', type=int) if not request.args.get('from', type=int) is None else 0
    query_to        = request.args.get('to', type=int) if not request.args.get('to', type=int) is None else 10
    query_skip_rows = request.args.get('skip_rows', type=str) if not request.args.get('skip_rows', type=str) is None else 0
    query_sep       = request.args.get('sep', type=str) if not request.args.get('sep', type=str) is None else ';'

    file_string = code_example.get_code_example(settings.HOST, catalog_index, query_sep, query_skip_rows, query_from, query_to)
    return app.response_class(response=file_string, status=200, mimetype='text/plain')

    #strIO = io.StringIO().write(file_string).seek(0)
    #return send_file(strIO, attachment_filename='example.py', as_attachment=True)

@app.errorhandler(403)
def get_403(e):
    errors = [e, 'Please go back or start from {}.'.format(util_design.getLink('Dashboard', '/'))]
    return app.make_response(render_template(template_name_or_list='error.html', errors=errors)), 403

@app.errorhandler(404)
def get_404(e):
    errors = [e, 'Please go back or start from {}.'.format(util_design.getLink('Dashboard', '/'))]
    return app.make_response(render_template(template_name_or_list='error.html', errors=errors)), 404

@app.errorhandler(405)
def get_405(e):
    errors = [e, 'Please go back or start from {}.'.format(util_design.getLink('Dashboard', '/'))]
    return app.make_response(render_template(template_name_or_list='error.html', errors=errors)), 500

@app.errorhandler(500)
def get_500(e):
    errors = [e, 'Please go back or start from {}.'.format(util_design.getLink('Dashboard', '/'))]
    return app.make_response(render_template(template_name_or_list='error.html', errors=errors)), 500


@app.route('/api/data/docs', methods=['GET'])
def view_swagger_ui():
    template = 'swagger-ui.html'
    return render_template(template_name_or_list=template, service_url=settings.HOST)

@app.route('/data/api/swagger.yml')
def swagger_json():
    return send_file('swagger/api.yml')

# see https://github.com/sveint/flask-swagger-ui/tree/master/flask_swagger_ui#usage
SWAGGER_URL = '/data/api/docs/standalone'  # URL for exposing Swagger UI
API_URL = '{}data/api/swagger.yml'.format(settings.HOST)

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,  # Swagger UI static files will be mapped to '{SWAGGER_URL}/dist/'
    API_URL,
    config = {  'app_name': "Open Government Data Service"},
    # oauth_config={  # OAuth config. See https://github.com/swagger-api/swagger-ui#oauth2-configuration .
    #    'clientId': "your-client-id",
    #    'clientSecret': "your-client-secret-if-required",
    #    'realm': "your-realms",
    #    'appName': "your-app-name",
    #    'scopeSeparator': " ",
    #    'additionalQueryStringParams': {'test': "hello"}
    # }
    )

app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)




if __name__ == '__main__':
    #app.run(HOST='0.0.0.0', port=5000, debug=True, use_reloader=True, threaded=True)
    app.run(host='0.0.0.0', port=80, debug=False, use_reloader=False, threaded=False)