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
3. edit a configuration file like the following the one in docs/alertmaps.sample.conf
4. Edit the index.html and add you own google api access key (replace __YOUR__GOOGGLE_API_KEY_HERE__) (cf. https://developers.google.com/maps/documentation/javascript/tutorial?hl=fr#api_key)
5. setup a cronjob like this one:

	* * * * * root python /bin_dir_somewhere_on_your_server/alertsmap.py --conf /somewhere_on_your_server/alertsmap.conf --output /somewhere_on_your_server/data.js > /dev/null 2>&1


Screenshot
----------

![alertsmap screenshot](https://raw.github.com/darkweaver87/alertsmap/master/docs/screenshot.png)
