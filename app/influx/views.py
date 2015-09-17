#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from flask import jsonify
from flask import current_app

from influxdb import InfluxDBClient

from app.base import ApiResource

class InfluxResource(ApiResource):
    endpoint = 'influx'
    url_prefix = '/influx'
    url_rules = {
        'index': {
            'rule': '/',
            'defaults': { 'query': None  }
        },
        'show': {
            'rule': '/<query>'
        },
    }

    def get(self, query):
        client = InfluxDBClient.from_DSN(current_app.config['INFLUX_DATABASE_URI'], timeout=5)
        result = client.query(query)

        fmtResults = []
        if result:
            for series in result.raw['series']:
                fmtSeries= {}
                fmtSeries['name'] = series['name']
                if 'tags' in series:
                    fmtSeries['tags'] = series['tags']

                columns = series['columns']
                values = series['values']

                fmtSeries['data'] = [ dict(zip(columns, v)) for v in values ]

                fmtResults.append(fmtSeries)

            return jsonify(result=fmtResults)
        else:
            return jsonify(result=[])

