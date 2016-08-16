#!/usr/bin/env python

import sys
import json
import time
import argparse
from urllib2 import Request
from urllib2 import urlopen
from influxdb import InfluxDBClient

class CephClusterStatus(dict):
    def __init__(self, url):
        dict.__init__(self)
        req = Request(url)
        req.add_header('Content-Type', 'application/json')
        try:
            self.update(json.load(urlopen(req)))
        except Exception as err:
            print "UNKNOWN: %s" % (str(err), )
            sys.exit(1)

    def get_perf_data(self):
        perf_values = {
            'pgmap': ['read_bytes_sec', 'write_bytes_sec', 'read_op_per_sec', 'write_op_per_sec'],
        }

        perfdata = dict()
        for map_type, values in perf_values.iteritems():
            for value in values:
                perfdata[value] = self[map_type].get(value, 0)

        return perfdata

    def InfluxDBInject(self, perfData, host='localhost', port=8086):
        dbname = 'cephstats'
        data = [
            {
                "measurement": "ceph.cluster",
                "tags": {
                    "hostname": "ceph-mon-0",
                    "type": "read_bytes_sec"
                },
                "fields": {
                    "value": float(perfData['read_bytes_sec'])
                }
            },
            {
                "measurement": "ceph.cluster",
                "tags": {
                    "hostname": "ceph-mon-0",
                    "type": "write_bytes_sec"
                },
                "fields": {
                    "value": float(perfData['write_bytes_sec'])
                }
            },
            {
                "measurement": "ceph.cluster",
                "tags": {
                    "hostname": "ceph-mon-0",
                    "type": "read_ops_sec"
                },
                "fields": {
                    "value": float(perfData['read_op_per_sec'])
                }
            },
            {
                "measurement": "ceph.cluster",
                "tags": {
                    "hostname": "ceph-mon-0",
                    "type": "write_ops_sec"
                },
                "fields": {
                    "value": float(perfData['write_op_per_sec'])
                }
            }
        ]
    
        client = InfluxDBClient(host, port, database=dbname)
        client.create_database(dbname)
        client.create_retention_policy('standard', '1h', 3, default=True)
    
        result = client.write_points(data)
        #print 'DEBUG: Wrote data to Influx'
