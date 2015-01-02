#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
    ceph-dash.py
    ~~~~~~~~~~~~

    Flask based api / dashboard for viewing a ceph clusters overall health
    status

    :copyright: (c) 2014 by Christian Eichelmann
    :license: BSD, see LICENSE for more details.
"""

import os
import json

from flask import Flask
from flask import request
from flask import render_template
from flask import abort
from flask import jsonify
from flask.views import MethodView

from rados import Rados
from rados import ObjectNotFound
from rados import PermissionError
from rados import Error as RadosError

from werkzeug.exceptions import default_exceptions
from werkzeug.exceptions import HTTPException


class CephApiConfig(dict):
    """ loads the json configuration file """

    def _string_decode_hook(self, data):
        rv = {}
        for key, value in data.iteritems():
            if isinstance(key, unicode):
                key = key.encode('utf-8')
            if isinstance(value, unicode):
                value = value.encode('utf-8')
            rv[key] = value
        return rv

    def __init__(self):
        dict.__init__(self)
        configfile = os.path.join(os.path.dirname(__file__), 'config.json')
        self.update(json.load(open(configfile), object_hook=self._string_decode_hook))


class CephClusterProperties(dict):
    """
    Validate ceph cluster connection properties
    """

    def __init__(self, config):
        dict.__init__(self)

        self['conffile'] = config['ceph_config']
        self['conf'] = dict()

        if 'keyring' in config:
            self['conf']['keyring'] = config['keyring']
        if 'client_id' in config and 'client_name' in config:
            raise RadosError("Can't supply both client_id and client_name")
        if 'client_id' in config:
            self['rados_id'] = config['client_id']
        if 'client_name' in config:
            self['name'] = config['client_name']


class CephClusterCommand(dict):
    """
    Issue a ceph command on the given cluster and provide the returned json
    """

    def __init__(self, cluster, **kwargs):
        dict.__init__(self)
        ret, buf, err = cluster.mon_command(json.dumps(kwargs), '', timeout=5)
        if ret != 0:
            self['err'] = err
        else:
            self.update(json.loads(buf))


def find_host_for_osd(osd, osd_status):
    """ find host for a given osd """

    for obj in osd_status['nodes']:
        if obj['type'] == 'host':
            if osd in obj['children']:
                return obj['name']

    return 'unknown'


def get_unhealthy_osd_details(osd_status):
    """ get all unhealthy osds from osd status """

    unhealthy_osds = list()

    for obj in osd_status['nodes']:
        if obj['type'] == 'osd':
            #if OSD does not exists (DNE in osd tree) skip this entry
            if obj['exists'] == 0: continue
            if obj['status'] == 'down' or obj['status'] == 'out':
                #It is possible to have one host in more than one branch in the tree. 
                #Add each unhealthy OSD only once in the list
                entry = {
                    'name': obj['name'],
                    'status': obj['status'],
                    'host': find_host_for_osd(obj['id'], osd_status)
                }
                if entry not in unhealthy_osds:
                    unhealthy_osds.append(entry)

    return unhealthy_osds


class CephStatusView(MethodView):
    """
    Endpoint that shows overall cluster status
    """

    def __init__(self):
        MethodView.__init__(self)
        self.config = CephApiConfig()
        self.clusterprop = CephClusterProperties(self.config)

    def get(self):
        with Rados(**self.clusterprop) as cluster:
            cluster_status = CephClusterCommand(cluster, prefix='status', format='json')
            if 'err' in cluster_status:
                abort(500, cluster_status['err'])

            # check for unhealthy osds and get additional osd infos from cluster
            total_osds = cluster_status['osdmap']['osdmap']['num_osds']
            in_osds = cluster_status['osdmap']['osdmap']['num_up_osds']
            up_osds = cluster_status['osdmap']['osdmap']['num_in_osds']

            if up_osds < total_osds or in_osds < total_osds:
                osd_status = CephClusterCommand(cluster, prefix='osd tree', format='json')
                if 'err' in osd_status:
                    abort(500, osd_status['err'])

                # find unhealthy osds in osd tree
                cluster_status['osdmap']['details'] = get_unhealthy_osd_details(osd_status)

            if request.mimetype == 'application/json':
                return jsonify(cluster_status)
            else:
                return render_template('status.html', data=cluster_status, config=self.config)


class CephAPI(Flask):
    def __init__(self, name):
        template_folder = os.path.join(os.path.dirname(__file__), 'templates')
        static_folder = os.path.join(os.path.dirname(__file__), 'static')
        Flask.__init__(self, name, template_folder=template_folder, static_folder=static_folder)

        status_view = CephStatusView.as_view('status')
        self.add_url_rule('/', view_func=status_view)

        # add custom error handler
        for code in default_exceptions.iterkeys():
            self.error_handler_spec[None][code] = self.make_json_error

    def make_json_error(self, ex):
        if isinstance(ex, HTTPException):
            code = ex.code
            message = ex.description
        elif isinstance(ex, ObjectNotFound):
            code = 404
            message = "object not found: " + str(ex)
        elif isinstance(ex, PermissionError):
            code = 403
            message = "permission error: " + str(ex)
        elif isinstance(ex, RadosError):
            code = 400
            message = "rados error: " + str(ex)
        else:
            code = 500
            message = str(ex)

        # TODO: make it possible to use fancy gui errors here
        response = jsonify(code=code, message=message)
        response.status_code = code

        if code == 401:
            response.headers['WWW-Authenticate'] = 'Basic realm="Login Required"'

        return response


def main():
    app = CephAPI(__name__)
    app.run(debug=False, host='0.0.0.0')


if __name__ == '__main__':
    main()
