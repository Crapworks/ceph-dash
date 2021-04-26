#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import json

from flask import request
from flask import render_template
from flask import abort
from flask import jsonify
from flask import current_app
from flask.views import MethodView

from rados import Rados
from rados import Error as RadosError

from app.base import ApiResource


class CephClusterProperties(dict):
    """
    Validate ceph cluster connection properties
    """

    def __init__(self, config):
        dict.__init__(self)

        self['conffile'] = config['ceph_config']
        self['conf'] = dict()

        if 'keyring' in config:
            self['conf']['keyring'] = config['keyring']
        if 'client_id' in config and 'client_name' in config:
            raise RadosError("Can't supply both client_id and client_name")
        if 'client_id' in config:
            self['rados_id'] = config['client_id']
        if 'client_name' in config:
            self['name'] = config['client_name']


class CephClusterCommand(dict):
    """
    Issue a ceph command on the given cluster and provide the returned json
    """

    def __init__(self, cluster, **kwargs):
        dict.__init__(self)
        ret, buf, err = cluster.mon_command(json.dumps(kwargs), '', timeout=5)
        if ret != 0:
            self['err'] = err
        else:
            self.update(json.loads(buf))


def find_host_for_osd(osd, osd_status):
    """ find host for a given osd """

    for obj in osd_status['nodes']:
        if obj['type'] == 'host':
            if osd in obj['children']:
                return obj['name']

    return 'unknown'


def get_unhealthy_osd_details(osd_status):
    """ get all unhealthy osds from osd status """

    unhealthy_osds = list()

    for obj in osd_status['nodes']:
        if obj['type'] == 'osd':
            # if OSD does not exists (DNE in osd tree) skip this entry
            if obj['exists'] == 0:
                continue
            if obj['status'] == 'down' or obj['reweight'] == 0.0:
                # It is possible to have one host in more than one branch in the tree.
                # Add each unhealthy OSD only once in the list
                if obj['status'] == 'down':
                    status = 'down'
                else:
                    status = 'out'
                entry = {
                    'name': obj['name'],
                    'status': status,
                    'host': find_host_for_osd(obj['id'], osd_status)
                }
                if entry not in unhealthy_osds:
                    unhealthy_osds.append(entry)

    return unhealthy_osds


class DashboardResource(ApiResource):
    """
    Endpoint that shows overall cluster status
    """

    endpoint = 'dashboard'
    url_prefix = '/'
    url_rules = {
        'index': {
            'rule': '/',
        }
    }

    def __init__(self):
        MethodView.__init__(self)
        self.config = current_app.config['USER_CONFIG']
        self.clusterprop = CephClusterProperties(self.config)

    def get(self):
        with Rados(**self.clusterprop) as cluster:
            cluster_status = CephClusterCommand(cluster, prefix='status', format='json')
            if 'err' in cluster_status:
                abort(500, cluster_status['err'])

            # check for unhealthy osds and get additional osd infos from cluster
            # ceph >= 15.2.5
            if 'osdmap' not in cluster_status['osdmap']:
                # osdmap has been converted to depth-1 dict
                cluster_status['osdmap']['osdmap'] = cluster_status['osdmap'].copy()
            total_osds = cluster_status['osdmap']['osdmap']['num_osds']
            in_osds = cluster_status['osdmap']['osdmap']['num_up_osds']
            up_osds = cluster_status['osdmap']['osdmap']['num_in_osds']

            if up_osds < total_osds or in_osds < total_osds:
                osd_status = CephClusterCommand(cluster, prefix='osd tree', format='json')
                if 'err' in osd_status:
                    abort(500, osd_status['err'])

                # find unhealthy osds in osd tree
                cluster_status['osdmap']['details'] = get_unhealthy_osd_details(osd_status)

            if request.mimetype == 'application/json':
                return jsonify(cluster_status)
            else:
                return render_template('status.html', data=cluster_status, config=self.config)
