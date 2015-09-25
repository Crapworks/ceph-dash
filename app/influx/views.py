#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from flask import jsonify
from flask import current_app

from influxdb import InfluxDBClient

from app.base import ApiResource

class InfluxResource(ApiResource):
    endpoint = 'influxdb'
    url_prefix = '/influxdb'
    url_rules = {
        'index': {
            'rule': '/',
        }
    }

    def get(self):
        config = current_app.config['USER_CONFIG'].get('influxdb', {})
        client = InfluxDBClient.from_DSN(config['uri'], timeout=5)
        results = []

        for metric in config.get('metrics', []):
            collection = []
            for query in metric.get('queries', []):
                result = client.query(query, epoch='ms')
                print query

                if result:
                    for index, dataset in enumerate(result.raw['series']):
                        series= {}
                        series['data'] = dataset['values']
                        series['label'] = metric['labels'][index] if 'labels' in metric else None
                        series['lines'] = dict(fill=True)
                        series['mode'] = metric['mode'] if 'mode' in metric else None
                        series['color'] = metric['colors'][index] if 'colors' in metric else None

                        collection.append(series)

            results.append(collection)

        return jsonify(results=results)
