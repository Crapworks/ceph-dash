ceph-dash - a free ceph dashboard / monitoring api
==================================================

This is a small and clean approach of providing the [Ceph](http://ceph.com) overall cluster health status via a restful json api as well as via a (hopefully) fancy web gui. There are no dependecies to the existing ```ceph-rest-api```. This wsgi application talks to the cluster directly via librados.

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

Anyways, this is not a wrapper around the ceph binary, it uses the python bindings of librados.

This api can be requested by, for example, a nagios check, to check your overall cluster health. This brings the advantage of querying this information without running local checks on your monitor nodes, just by accessing a read only http api.

Nagios Check
------------

A Nagios check that uses ceph-dash for monitoring your ceph cluster status is available [here](https://github.com/Crapworks/check_ceph_dash)

Deployment
----------

You may want to deploy this wsgi application into a real webserver like apache or nginx. For convenience, I've put the wsgi file and a sample apache vhost config inside of the ```contrib``` folder,

You can edit the config.json file to configure how to talk to the Ceph cluster.

 - `ceph_config` is the location of /etc/ceph/ceph.conf
 - `keyring` points to a keyring to use to authenticate with the cluster
 - `client_id` or `client_name` is used to specify the name to use with the keyring

Pictures!!
----------

In case anyone wants to see what to expect, here you go:

![screenshot01](https://github.com/crapworks/ceph-dash/raw/master/screenshots/ceph-dash.png)

Graphite Integration
--------------------

In the latest git version, I've integrated the flot graphing library to make it possible to show some graphs from [Graphite](graphite.wikidot.com) in ceph-dash. First of all: ceph-dash does **NOT** put any data into graphite! You have to do it yourself. We are using our [Icinga](https://www.icinga.org/) monitoring to push performance metrics to graphite. The graphs shown in the example were created by the above mentioned [Nagios check for ceph-dash](https://github.com/Crapworks/check_ceph_dash).

This is currently **TESTING**!

If you do not have a graphite section in your ```config.json``` the Metrics section will not appear in ceph-dash. This has currently the status **works for me**. If no one will complain, I will create a new stable release after a few weeks.

### Configuration

There is a sample configuration file called ```config.graphite.json```. Everything in there should be quite self-explanatory. If not, feel free to open an issue on github!

### Example

Here you can see an example where one graphs show the bytes read/write per second, and another one shows the IOPS during the last two hours:

![screenshot01](https://github.com/crapworks/ceph-dash/raw/master/screenshots/ceph-dash-graphite.png)

