#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import time
import threading

from os.path import dirname
from os.path import join
from flask import Flask

from app.dashboard.views import DashboardResource
from app.influxinjector import CephClusterStatus

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


def InfluxInject(url='http://localhost/', host='localhost', port=8086):
    # the program isnt finished starting up yet the first time
    # we run this thread... so we will wait a small while
    time.sleep(2)

    # print "DEBUG: Thread running..."
    status = CephClusterStatus(url)
    perfData = status.get_perf_data()
    status.InfluxDBInject(perfData, host, port)

    # now lets fire up the thread again in fewer than 10 seconds
    # I find that if we wait longer than 5 seconds there are sometimes
    # gaps in the graphing.
    threading.Timer(5, InfluxInject, [url, host, port]).start()


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

        if 'uri' in app.config['USER_CONFIG']['influxdb']:
            uriList = app.config['USER_CONFIG']['influxdb']['uri'].split('/')
            host = uriList[2].split(':')[0]
            port = uriList[2].split(':')[1]

            # run this in a seperate thread... will repeat until we close program
            threading.Thread(target=InfluxInject, args=('http://'+host, host, port)).start()

# only load endpoint if user wants to use graphite
if 'graphite' in app.config['USER_CONFIG']:
    from app.graphite.views import GraphiteResource
    app.register_blueprint(GraphiteResource.as_blueprint())

# load dashboard and graphite endpoint
app.register_blueprint(DashboardResource.as_blueprint())
