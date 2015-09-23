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
            #url = config['url'] + "/render?format=json&from=" + metric['from']
            url = config['url'] + "/render?format=json&from=-1h"
            for target in metric.get('targets', []):
                url += '&target=' + target
            resp = urlopen(url, context=ssl._create_unverified_context())

            datapoints = []
            for dataset in json.load(resp):
                datapoints.append(dataset)

            graph = dict()
            graph['metric'] = datapoints
            graph['labels'] = metric.get('labels', [])
            graph['colors'] = metric.get('colors', [])
            graph['mode'] = metric.get('mode', '')
            results.append(graph)

        return jsonify(results=results)

