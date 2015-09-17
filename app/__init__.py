#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json

from flask import Flask

app = Flask(__name__)
app.template_folder = os.path.join(os.path.dirname(__file__), 'templates')
app.static_folder = os.path.join(os.path.dirname(__file__), 'static')


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
        configfile = os.path.join(os.path.dirname(__file__), 'config.json')
        self.update(json.load(open(configfile), object_hook=self._string_decode_hook))

app.config['USER_CONFIG'] = UserConfig()

from app.dashboard.views import DashboardResource
from app.influx.views import InfluxResource

app.register_blueprint(DashboardResource.as_blueprint())
app.register_blueprint(InfluxResource.as_blueprint())
