#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json

from os.path import dirname
from os.path import join
from flask import Flask
from rados import Rados

from influxdb import InfluxDBClient

from app.dashboard.views import *
from app.dashboard.views import DashboardResource

import time
import datetime

app = Flask(__name__)
app.template_folder = join(dirname(__file__), 'templates')
app.static_folder = join(dirname(__file__), 'static')

class InsertDB():
    """ Insert Database """

    def create_json_body(self,rw,bytes_sec):
        return [
        {
            "measurement": "ceph",
            "time": datetime.datetime.now().isoformat(),
            "fields": {
                "type": rw,
                "bytes_sec": bytes_sec,
            }
        }
    ]

    def insert_data(self):
        with Rados(**self.clusterprop) as cluster:
            cluster_status = CephClusterCommand(cluster, prefix='status', format='json')
            while True:
                # support insert database
                if 'write_bytes_sec' in cluster_status['pgmap']:
                    self.client.write_points(self.create_json_body("write",cluster_status['pgmap']['write_bytes_sec']))
                else:
                    self.client.write_points(self.create_json_body("write",0))
                if 'read_bytes_sec' in cluster_status['pgmap']:
                    self.client.write_points(self.create_json_body("read",cluster_status['pgmap']['read_bytes_sec']))
                else:
                    self.client.write_points(self.create_json_body("read",0))
                if 'op_per_sec' in cluster_status['pgmap']:
                    self.client.write_points(self.create_json_body("op",cluster_status['pgmap']['op_per_sec']))
                else:
                    self.client.write_points(self.create_json_body("op",0))
                print "OK"
                time.sleep(10)

    def __init__(self):
        self.config = app.config['USER_CONFIG'].get('influxdb-selfinsert', {})
        self.client = InfluxDBClient.from_DSN(self.config['uri'], timeout=5)
        self.clusterprop = CephClusterProperties(app.config['USER_CONFIG'])

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

    # set to self insert node if user don't want to use external program
    if 'influxdb-selfinsert' in app.config['USER_CONFIG']:
        from app.influx.views import InfluxResource
        app.register_blueprint(InfluxResource.as_blueprint())
        insert = InsertDB()
        insert.insert_data()

# only load endpoint if user wants to use graphite
if 'graphite' in app.config['USER_CONFIG']:
    from app.graphite.views import GraphiteResource
    app.register_blueprint(GraphiteResource.as_blueprint())

# load dashboard and graphite endpoint
app.register_blueprint(DashboardResource.as_blueprint())
