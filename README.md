ceph-dash - a free ceph dashboard / monitoring api
==================================================

- [ceph-dash - a free ceph dashboard / monitoring api](#user-content-ceph-dash---a-free-ceph-dashboard--monitoring-api)
	- [Newest Feature](#user-content-newest-feature)
	- [Quickstart](#user-content-quickstart)
	- [Dashboard](#user-content-dashboard)
	- [REST Api](#user-content-rest-api)
	- [Nagios Check](#user-content-nagios-check)
	- [Deployment](#user-content-deployment)
	- [Pictures!!](#user-content-pictures)
	- [Graphite Integration](#user-content-graphite-integration)
		- [Configuration](#user-content-configuration)
		- [Example](#user-content-example)


This is a small and clean approach of providing the [Ceph](http://ceph.com) overall cluster health status via a restful json api as well as via a (hopefully) fancy web gui. There are no dependecies to the existing ```ceph-rest-api```. This wsgi application talks to the cluster directly via librados.

Newest Feature
--------------

The current github version (which has no release yet) features a popover, which becomes available if there are any unhealthy osds in the cluster. If the count for Unhealthy osds is not 0, hovering over the field with the number of unhealthy osds will show a popover with additional information about those osds (including the name, the state and the host that contains this osd). To do this, ceph-dash has to issue an additional command to the cluster. This additional request will only be triggered if the first command shows any unhealthy osds!

![screenshot03](https://github.com/crapworks/ceph-dash/raw/master/screenshots/ceph-dash-popover.png)

I also did some minor code refactoring to clean everything up a bit. If I don't get any negative responses, I will create a new release in the next weeks.

Quickstart
----------

1. clone this repository
2. place it on one of your ceph monitor nodes
3. run ```ceph-dash.py```
4. point your browser to http://ceph-monitor:5000/
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

If you do not have a graphite section in your ```config.json``` the Metrics section will not appear in ceph-dash.

### Configuration

There is a sample configuration file called ```config.graphite.json```. Everything in there should be quite self-explanatory. If not, feel free to open an issue on github!

### Example

Here you can see an example where one graph shows the bytes read/write per second, and another one shows the IOPS during the last two hours:

![screenshot01](https://github.com/crapworks/ceph-dash/raw/master/screenshots/ceph-dash-graphite.png)

