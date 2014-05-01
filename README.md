ceph-dash - a free ceph dashboard / monitoring api
==================================================

This is a small and clean approach of providing the ceph overall cluster health status via a restful json api as well as via a (hopefully) fancy web gui. There are no dependecies to the existing ```ceph-rest-api```. This wsgi application talks to the cluster directly via librados. I'm aware that there already is an api for ceph, but I simply hate XML, so I decided to build one using json instead.

Quickstart
----------

1. clone this repository
2. place it on one of your ceph monitor nodes
3. run ```ceph-dash.py```
4. point your browser to http://<monitornode>:5000/
5. enjoy!

Dashboard
---------

If you hit the address via a browser, you see the web frontend, that will inform you on a single page about all important things of your ceph cluster.

REST Api
--------

If you access the address via commandline tools or programming languages, use ```content-type: application/json``` and you will get all the information as a json output (wich is acutally the json formatted output of ```ceph status --format=json```.

Anyways, this is not a wrapper arounf the ceph binary, it uses the python bindings of librados.

This api can be requested by, for example, a nagios check, to check your overall cluster health. This brings the advantage of querying this information without running local checks on your monitor nodes, just by accessing a read only http api.

**Hint:** a nagios check will appear soon here!

Deployment
----------

You may want to deploy this wsgi application into a real webserver like apache or nginx. For convenience, I've put the wsgi file and a sample apache vhost config inside of the ```contrib``` folder,

You can edit the config.json file to configure how to talk to the Ceph cluster.

 - `ceph\_config` is the location of /etc/ceph/ceph.conf
 - `keyring` points to a keyring to use to authenticate with the cluster
 - `client\_id` or `client\_name` is used to specify the name to use with the keyring

Pictures!!
----------

In case anyone wants to see what to expect, here you go:

![screenshot01](https://github.com/crapworks/ceph-dash/raw/master/screenshots/ceph-dash.png)
