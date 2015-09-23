#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json

from os.path import dirname
from os.path import join
from flask import Flask

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

    def __init__(self):
        dict.__init__(self)
        configfile = join(dirname(dirname(__file__)), 'config.json')
        self.update(json.load(open(configfile), object_hook=self._string_decode_hook))

app.config['USER_CONFIG'] = UserConfig()

from app.dashboard.views import DashboardResource
from app.influx.views import InfluxResource
from app.graphite.views import GraphiteResource

app.register_blueprint(DashboardResource.as_blueprint())
app.register_blueprint(InfluxResource.as_blueprint())
app.register_blueprint(GraphiteResource.as_blueprint())
