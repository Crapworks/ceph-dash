#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json

from os.path import dirname
from os.path import join
from flask import Flask

from app.dashboard.views import DashboardResource

app = Flask(__name__)
app.template_folder = join(dirname(__file__), 'templates')
app.static_folder = join(dirname(__file__), 'static')


class FlaskReverseProxied(object):
    """
    Flask reverse proxy extension ripped of from:
    https://github.com/wilbertom/flask-reverse-proxy/
    """
    def __init__(self, app=None):
        self.app = None
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        self.app = app
        self.app.wsgi_app = ReverseProxied(self.app.wsgi_app)
        return self


class ReverseProxied(object):
    """
    Wrap the application in this middleware and configure the
    front-end server to add these headers, to let you quietly bind
    this to a URL other than / and to an HTTP scheme that is
    different than what is used locally.
    In nginx:
    location /prefix {
        proxy_pass http://192.168.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Scheme $scheme;
        proxy_set_header X-Script-Name /prefix;
        }
    :param app: the WSGI application
    """
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        script_name = environ.get('HTTP_X_SCRIPT_NAME', '')
        if script_name:
            environ['SCRIPT_NAME'] = script_name
            path_info = environ.get('PATH_INFO', '')
            if path_info and path_info.startswith(script_name):
                environ['PATH_INFO'] = path_info[len(script_name):]
        server = environ.get('HTTP_X_FORWARDED_SERVER_CUSTOM',
                             environ.get('HTTP_X_FORWARDED_SERVER', ''))
        if server:
            environ['HTTP_HOST'] = server

        scheme = environ.get('HTTP_X_SCHEME', '')

        if scheme:
            environ['wsgi.url_scheme'] = scheme

        return self.app(environ, start_response)


class UserConfig(dict):
    """ loads the json configuration file """

    def _string_decode_hook(self, data):
        rv = {}
        for key, value in data.items():
          try:
            if isinstance(key, unicode):
                key = key.encode('utf-8')
            if isinstance(value, unicode):
                value = value.encode('utf-8')
          # unicode does not exist if python3 is used
          # ignore and don't do encoding, it is not
          # needed in python3
          except NameError:
            pass
          rv[key] = value
        return rv

    def __init__(self):
        dict.__init__(self)
        configfile = join(dirname(dirname(__file__)), 'config.json')
        configfile = os.environ.get('CEPHDASH_CONFIGFILE', configfile)
        self.update(json.load(open(configfile), object_hook=self._string_decode_hook))

        if os.environ.get('CEPHDASH_CEPHCONFIG', False):
            self['ceph_config'] = os.environ['CEPHDASH_CEPHCONFIG']
        if os.environ.get('CEPHDASH_KEYRING', False):
            self['keyring'] = os.environ['CEPHDASH_KEYRING']
        if os.environ.get('CEPHDASH_ID', False):
            self['client_id'] = os.environ['CEPHDASH_ID']
        if os.environ.get('CEPHDASH_NAME', False):
            self['client_name'] = os.environ['CEPHDASH_NAME']


app.config['USER_CONFIG'] = UserConfig()

# only load influxdb endpoint if module is available
try:
    import influxdb
    assert influxdb
except ImportError:
    # remove influxdb config because we can't use it
    if 'influxdb' in app.config['USER_CONFIG']:
        del app.config['USER_CONFIG']['influxdb']

    # log something so the user knows what's up
    # TODO: make logging work!
    app.logger.warning('No influxdb module found, disabling influxdb support')
else:
    # only load endpoint if user wants to use influxdb
    if 'influxdb' in app.config['USER_CONFIG']:
        from app.influx.views import InfluxResource
        app.register_blueprint(InfluxResource.as_blueprint())

# only load endpoint if user wants to use graphite
if 'graphite' in app.config['USER_CONFIG']:
    from app.graphite.views import GraphiteResource
    app.register_blueprint(GraphiteResource.as_blueprint())

# load dashboard and graphite endpoint
app.register_blueprint(DashboardResource.as_blueprint())

# enable reverse proxy support
proxied = FlaskReverseProxied(app)
