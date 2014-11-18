import os
import json

from rados import Rados

class CephApiConfig(dict):
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
    def configure(self):
        self.config = CephApiConfig()
        self.clusterprop = CephClusterProperties(self.config)
        self.cluster = Rados(**self.clusterprop)

    def __init__(self, **kwargs):
        #self.config = CephApiConfig()
        #self.clusterprop = CephClusterProperties(self.config)
        #self.cluster = Rados(**self.clusterprop)
        self.configure()
        self.cmd = json.dumps(kwargs)
        dict.__init__(self)

    def run(self):
        self.configure()
        self.cluster.connect()
        self.cluster.require_state("connected")
        ret, buf, err = self.cluster.mon_command(self.cmd, '', timeout=5)
        if ret != 0:
            self['err'] = err
        else:
            self.update(json.loads(buf))
        self.cluster.shutdown()
        return self
