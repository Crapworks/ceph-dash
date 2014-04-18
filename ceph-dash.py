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


class CephStatusView(MethodView):
    """
    Endpoint that shows overall cluster status
    """

    def __init__(self):
        MethodView.__init__(self)
        self.config = CephApiConfig()

    def get(self):
        kwargs = dict()
        conf = dict()
        kwargs['conffile'] = self.config['ceph_config']
        kwargs['conf'] = conf
        if 'keyring' in self.config:
            conf['keyring'] = self.config['keyring']
        if 'client_id' in self.config and 'client_name' in self.config:
            raise RadosError("Can't supply both client_id and client_name")
        if 'client_id' in self.config:
            kwargs['name'] = self.config['client_id']
        if 'client_name' in self.config:
            kwargs['rados_id'] = self.config['client_name']
        with Rados(**kwargs) as cluster:
            command = { 'prefix': 'status', 'format': 'json' }
            ret, buf, err = cluster.mon_command(json.dumps(command), '', timeout=5)
            if ret != 0:
                abort(500, err)

            if request.mimetype == 'application/json':
                return jsonify(json.loads(buf))
            else:
                return render_template('status.html', data=json.loads(buf))


class CephAPI(Flask):
    def __init__(self, name):
        Flask.__init__(self, name)

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
