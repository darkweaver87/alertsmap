alertsmap
=========

Small python script to generate a HTML page of multiple livestatus instances map

Overview
------------

The goal of this script is to generate an HTML file to summarize alerts (on the right of the screen, comments on the bottom) and have a clear overview of the alert number in each location.
The purpose of this is mainly to have to nice page to display on a monitoring screen.

Dependencies
------------

	Python >= 2.6
	argparse >= 1.1


Installation
------------

1. cp -r alerts.js index.html images /somewhere_on_your_server/
2. cp alertsmap.py /bin_dir_somewhere_on_your_server/
3. edit a configuration file like the following:
<pre>
# comma separated value
# location = latitude,longitude
[locations] 
Paris = 39.044036,-77.48709
Sydney = -33.880361,151.204152

# comma separated value
# location = hg=exact_host_group_matching,h=exact_host_matching,hg~regexp_host_group_matching,h~regexp_host_matching
[locations_match]
Sydney = hg=REALM_SYDNEY
Paris = hg=REALM_PARIS,h~paris.*

# livestatus broker modules
# broker_name = host:port
[brokers]
Broker1 = 127.0.0.1:50000
Broker2 = 127.0.0.1:50000
</pre>
4. Edit the index.html and add you own google api access key (replace __YOUR__GOOGGLE_API_KEY_HERE__) (cf. https://developers.google.com/maps/documentation/javascript/tutorial?hl=fr#api_key)
5. setup a cronjob like this one:
	* * * * * root python /bin_dir_somewhere_on_your_server/alertsmap.py --conf /somewhere_on_your_server/alertsmap.conf --output /somewhere_on_your_server/data.js > /dev/null 2>&1


Screenshot
----------

![alertsmap screenshot](https://raw.github.com/darkweaver87/alertsmap/master/docs/screenshot.png)
