#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import ssl
import json

from flask import jsonify
from flask import current_app

from urllib2 import urlopen

from app.base import ApiResource

class GraphiteResource(ApiResource):
    endpoint = 'graphite'
    url_prefix = '/graphite'
    url_rules = {
        'index': {
            'rule': '/',
        }
    }

    def get(self):
        config = current_app.config['USER_CONFIG'].get('graphite', {})
        results = []

        for metric in config.get('metrics', []):
            url = config['url'] + "/render?format=json&from=" + metric['from']
            for target in metric.get('targets', []):
                url += '&target=' + target
            resp = urlopen(url, context=ssl._create_unverified_context())

            collection = []
            for index, dataset in enumerate(json.load(resp)):
                series = {}
                # map graphite timestamp to javascript timestamp
                # TODO: fill null values with the last dataset OR remove null values
                data = [ [ts * 1000, value] for value, ts in dataset.get('datapoints', []) ]
                series['data'] = data
                series['label'] = metric['labels'][index] if 'labels' in metric else None
                series['lines'] = dict(fill=True)
                series['mode'] = metric['mode'] if 'mode' in metric else None 
                series['color'] = metric['colors'][index] if 'colors' in metric else None
                collection.append(series)

            results.append(collection)

        return jsonify(results=results)

