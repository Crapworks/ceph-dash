ceph-dash - a free ceph dashboard / monitoring api
==================================================

- [ceph-dash - a free ceph dashboard / monitoring api](#user-content-ceph-dash---a-free-ceph-dashboard--monitoring-api)
	- [Newest Feature](#user-content-newest-feature)
		- [Docker Container](#user-content-docker-container)
		- [InfluxDB support](#user-content-influxdb-support)
		- [Old content warning](#user-content-old-content-warning)
		- [Unhealthy OSD popover](#user-content-unhealthy-osd-popover)
	- [Quickstart](#user-content-quickstart)
	- [Dashboard](#user-content-dashboard)
	- [REST Api](#user-content-rest-api)
	- [Nagios Check](#user-content-nagios-check)
	- [Deployment](#user-content-deployment)
	- [Pictures!!](#user-content-pictures)
	- [Graphite Integration](#user-content-graphite-integration)
		- [Configuration](#user-content-configuration)
		- [Example](#user-content-example)
	- [FAQ](#user-content-faq)


This is a small and clean approach of providing the [Ceph](http://ceph.com) overall cluster health status via a restful json api as well as via a (hopefully) fancy web gui. There are no dependencies to the existing ```ceph-rest-api```. This wsgi application talks to the cluster directly via librados.

You can find a blog entry regarding monitoring a Ceph cluster with ceph-dash on [Crapworks](http://crapworks.de/blog/2015/01/05/ceph-monitoring/).

[Here](http://de.slideshare.net/Inktank_Ceph/07-ceph-days-sf2015-paul-evans-static) you can find a presentation from Paul Evans, taken from the Ceph Day in San Francisco (March 12, 2015) where he is comparing several Ceph-GUIs, including ceph-dash.

Newest Feature
--------------

### Docker container

Since everybody recently seems to be hyped as hell about the container stuff, I've decided that I can contribute to that with a ready-to-use docker container. Available at [Docker Hub](https://hub.docker.com/r/crapworks/ceph-dash/) you can pull the ceph-dash container and configure it via the following environment variables:

* Required: $CEPHMONS (comma separated list of ceph monitor ip addresses)
* Required: $KEYRING (full keyring that you want to use to connect to your ceph cluster)
* Optional: $NAME (name of the key you want to use)
* Optional: $ID (id of the key you want to use)

**Example**

```bash
docker run -p 5000:5000 -e CEPHMONS='10.0.2.15,10.0.2.16' -e KEYRING="$(sudo cat /etc/ceph/keyring)" crapworks/ceph-dash:latest
```

### InfluxDB support

I've refactored the code quite a bit to make use of [Blueprints](http://flask.pocoo.org/docs/0.10/blueprints/) instead of [Method Views](http://flask.pocoo.org/docs/0.10/views/). The structure of the code has changed, but I was keeping everything backwards compatible to all your deployments should still work with the current version. This is for now not a release, because I want to see if there is some negative feedback on this. And here are two new things you can cheer about!

#### Graphing Proxies

Your browser does not talk directly to [Graphite](graphite.wikidot.com) directly anymore! It uses the ```/graphite``` endpoint which already provides flot-formated json output. Ceph-dash will establish a connection to Graphite and gather all relevant data. This should prevent Cross-Domain issues and in case of [InfluxDB](https://influxdb.com), also hides the database password. Due to it's generic nature, it should be easy to add more graphing backends if needed.

#### InfluxDB support

Ceph-dash now supports also [InfluxDB](https://influxdb.com) as a graphing backend besides [Graphite](graphite.wikidot.com). You need client and server version ```> 0.9``` since the api broke with that release and is not backwards compatible. If you do not have the InfluxDB python module installed, Ceph-dash will *NOT* enable the InfluxDB proxy and will not load any configured InfluxDB resources. So please be sure to have the latest InfluxDB python module installed if you want to use InfluxDB as a backend.
You can find a sample configuration file called ```config.influxdb.json``` in the root folder, which should explain how to use it. Please understand that I can't give you support for you InfluxDB setup, because this would definitely exceed the scope of Ceph-Dash.

![screenshot04](https://github.com/crapworks/ceph-dash/raw/master/screenshots/ceph-dash-influxdb.png)

### Old content warning

If an AJAX call to the underlying ceph-dash API isn't answered within 3 seconds, a silent timeout is happening. The dashboard will still show the old data. I wanted to give the user a hint if something is wrong with the api or the ceph cluster, so I've added a little warning icon that tells you if the data shown in ceph-dash is getting to old. Reasons for that can be an slow or unresponsive cluster (some error handling is happening - a monitor failover for example).

![screenshot03](https://github.com/crapworks/ceph-dash/raw/master/screenshots/ceph-dash-content-warning.png)

### Unhealthy OSD popover

The current release features a popover, which becomes available if there are any unhealthy osds in the cluster. If the count for Unhealthy osds is not 0, hovering over the field with the number of unhealthy osds will show a popover with additional information about those osds (including the name, the state and the host that contains this osd). To do this, ceph-dash has to issue an additional command to the cluster. This additional request will only be triggered if the first command shows any unhealthy osds!

![screenshot03](https://github.com/crapworks/ceph-dash/raw/master/screenshots/ceph-dash-popover.png)

I also did some minor code refactoring to clean everything up a bit.

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

If you access the address via commandline tools or programming languages, use ```content-type: application/json``` and you will get all the information as a json output (which is actually the json formatted output of ```ceph status --format=json```.

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

I've integrated the flot graphing library to make it possible to show some graphs from [Graphite](graphite.wikidot.com) in ceph-dash. First of all: ceph-dash does **NOT** put any data into graphite! You have to do it yourself. We are using our [Icinga](https://www.icinga.org/) monitoring to push performance metrics to graphite. The graphs shown in the example were created by the above mentioned [Nagios check for ceph-dash](https://github.com/Crapworks/check_ceph_dash).

If you do not have a graphite section in your ```config.json``` the Metrics section will not appear in ceph-dash.

### Configuration

There is a sample configuration file called ```config.graphite.json```. Everything in there should be quite self-explanatory. If not, feel free to open an issue on github!

### Example

Here you can see an example where one graph shows the bytes read/write per second, and another one shows the IOPS during the last two hours:

![screenshot01](https://github.com/crapworks/ceph-dash/raw/master/screenshots/ceph-dash-graphite.png)

FAQ
---

### How can I change the port number

The development server of Ceph-dash runs by default on port 5000. If you can't use this port since it is already used by another application, you can change it by opening `ceph-dash.py` and change the line
```python
app.run(host='0.0.0.0', debug=True)
```
to
```python
app.run(host='0.0.0.0', port=6666, debug=True)
```
Please keep in mind that the development server should not be used in a production environment. Ceph-dash should be deployed into a proper webserver like Apache or Nginx.

### Running ceph-dash behind a reverse proxy

Since Version 1.2 ceph-dash is able to run behind a reverse proxy that rewrites the path where ceph-dash resides correctly. If you are using nginx, you need to use a config like this:

```
server {
    location /foobar {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Scheme $scheme;
        proxy_set_header X-Script-Name /foobar;
    }
}

```

See also: https://github.com/wilbertom/flask-reverse-proxy, which is where I got the code for doing this.

### Problems with NginX and uwsgi

See [this issue](/../../issues/35) for a detailed explanation how to fix errors with NginX and uwsgi (Thanks to [@Lighiche](https://github.com/Lighiche))
