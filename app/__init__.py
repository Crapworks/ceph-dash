#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json

from os.path import dirname
from os.path import join
from flask import Flask

from app.dashboard.views import DashboardResource
from optparse import OptionParser

app = Flask(__name__)
app.template_folder = join(dirname(__file__), 'templates')
app.static_folder = join(dirname(__file__), 'static')


class UserConfig(dict):
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

    def parse_options(self):
        parser = OptionParser()
        parser.add_option("-c", "--config", dest="conf",
                          help="use configuration FILE",
                          default=join(dirname(dirname(__file__)), 'config.json'))
        (self.options, self.args) = parser.parse_args()

    def __init__(self):
        dict.__init__(self)
        self.parse_options()
        self.update(json.load(open(self.options.conf), object_hook=self._string_decode_hook))


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
