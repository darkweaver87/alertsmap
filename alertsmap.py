#!/usr/bin/python
# -*- coding: utf-8 -*-

import argparse
from datetime import datetime, timedelta
import time
import sys
import ConfigParser
import socket
import re
import traceback
import simplejson

# login methods
def debug(string):
    if DEBUG:
        print '[%s]: [DEBUG] - %s' % (datetime.now(), string)

def error(string):
    print '[%s]: [ERROR] - %s' % (datetime.now(), string)

# get current alerts
class LiveStatus:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        debug('Initializing Livestatus %s:%d' % (host, port))

    def query(self, cmd, columns = None):
        debug('Executing \'%s\' on Livestatus %s:%d' % (cmd, self.host, self.port))
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.host, int(self.port)))

        if columns:
            cmd += '\nColumns: %s\n' % columns

        cmd += '\n\n'
        
        s.send(cmd)
        s.shutdown(socket.SHUT_WR)
    
        answer = ''
        while True:
            data = s.recv(2048)
            if not data: break
            answer += data

        tab = []
        headers = None
        for line in answer.split('\n'):
            if not line or line == '':
                continue

            if not headers and not columns: # first answer are headers
                headers = line.split(';')
                continue
            if not headers and columns:
                headers = columns.split(' ')
        
            row = {}
            r_raw = line.split(';')
            if len(r_raw) != len(headers): # avoid index out of range
                continue

            for i in range(0, len(headers)):
                row[headers[i]] = r_raw[i]

            tab.append(row)

        return tab

# locate an host against the conf
def locate_host(locations, type, h, comment = False):
    # try to find host equality
    for l in locations:
        if h['host_name'] in locations[l]['h_equal']:
            if comment:
                locations[l]['comments'].append(h)
            else:
                locations[l][type][NAGIOS_STATES[type][h['state']]].append(h)
            return

    # try to find hostgroup equality
    for l in locations:
        for hg in h['host_groups'].split(','):
            if hg in locations[l]['hg_equal']:
                if comment:
                    locations[l]['comments'].append(h)
                else:
                    locations[l][type][NAGIOS_STATES[type][h['state']]].append(h)
                return

    # try to find host match
    for l in locations:
        for r in locations[l]['h_match']:
            m = re.match('^'+r+'$', h['host_name'])
            if m:
                if comment:
                    locations[l]['comments'].append(h)
                else:
                    locations[l][type][NAGIOS_STATES[type][h['state']]].append(h)
                return
            
    # try to find hostgroup match
    for l in locations:
        for hg in h['host_groups'].split(','):
            for r in locations[l]['hg_match']:                        
                m = re.match('^'+r+'$', hg)
                if m:
                    if comment:
                        locations[l]['comments'].append(h)
                    else:
                        locations[l][type][NAGIOS_STATES[type][h['state']]].append(h)
                    return

    debug('not matched: %s' % h)

# generate HTML file
def generate_output(locations, output):
    debug('Generating %s' % output)

    f = open(output, 'w')
    f.write(simplejson.dumps(locations))

    f.close()

DEBUG = False
NAGIOS_STATES = {'services': {'0': 'ok', '1': 'warning', '2': 'critical', '3': 'unknown'},
                 'hosts': {'0': 'up', '1': 'down'}}

# main function, processes arguments, ...
def main():
    parser = argparse.ArgumentParser(description='Alert map generator')
    parser.add_argument('--conf', nargs=1, dest='conf', help='config file', required = True)
    parser.add_argument('--output', nargs=1, dest='output', help='HTML output file name to generate', required = True)
    parser.add_argument('--debug', action="store_true", default=False)

    args = parser.parse_args()
    
    if args.debug:
        global DEBUG
        DEBUG = True
        
    debug('Arguments:' + str(args))
    
    try:
        livestatus = {}
        config = ConfigParser.RawConfigParser()
        config.read(args.conf[0])

        # fill the location informations
        locations = {}
        for i in config.items('locations'):
            if i[0] not in locations: 
                locations[i[0]] = {}
                locations[i[0]]['hg_equal'] = []
                locations[i[0]]['hg_match'] = []
                locations[i[0]]['h_equal'] = []
                locations[i[0]]['h_match'] = []
                locations[i[0]]['services'] = {}
                locations[i[0]]['services']['ok'] = []
                locations[i[0]]['services']['warning'] = []
                locations[i[0]]['services']['unknown'] = []
                locations[i[0]]['services']['critical'] = []
                locations[i[0]]['hosts'] = {}
                locations[i[0]]['hosts']['up'] = []
                locations[i[0]]['hosts']['down'] = []
                locations[i[0]]['comments'] = []


            latitude, longitude = i[1].split(',')
            locations[i[0]]['position'] = {'latitude': latitude, 'longitude': longitude }

        for i in config.items('locations_match'):
            if i[0] not in locations: 
                raise Exception('Please specify the latitude and longitude of \'%s\' in locations section' % i[0])
            
            for item in i[1].split(','):
                matched = False
                m = re.match('^hg=(?P<hg>.*)$', item)
                if m:
                    matched = True
                    locations[i[0]]['hg_equal'].append(m.group('hg'))

                m = re.match('^hg~(?P<hg>.*)$', item)
                if m:
                    matched = True
                    locations[i[0]]['hg_match'].append(m.group('hg'))

                m = re.match('^h=(?P<h>.*)$', item)
                if m:
                    matched = True
                    locations[i[0]]['h_equal'].append(m.group('h'))

                m = re.match('^h~(?P<h>.*)$', item)
                if m:
                    matched = True
                    locations[i[0]]['h_match'].append(m.group('h'))

                if not matched:
                    raise Exception('Invalid pattern for locations_match \'%s\'' % i[0])

        # initialize the socket for all
        for i in config.items('brokers'):
            livestatus[i[0]] = LiveStatus(i[1].split(':')[0], int(i[1].split(':')[1]))

        # retrieve all stats of all brokers
        for i in config.items('brokers'):
            for j in livestatus[i[0]].query('GET services\nFilter: scheduled_downtime_depth = 0\nFilter: host_scheduled_downtime_depth = 0\nFilter: acknowledged = 0\nFilter: host_acknowledged = 0\nFilter: service_acknowledged = 0\nFilter: notifications_enabled = 1\nFilter: state_type = 1', 'host_name last_hard_state_change description plugin_output state comments_with_info host_comments_with_info host_groups'):
                locate_host(locations, 'services', j)

            for j in livestatus[i[0]].query('GET hosts\nFilter: scheduled_downtime_depth = 0\nFilter: host_scheduled_downtime_depth = 0\nFilter: acknowledged = 0\nFilter: host_acknowledged = 0\nFilter: state_type = 1', 'host_name last_hard_state_change state host_groups'):
                locate_host(locations, 'hosts', j)

            for j in livestatus[i[0]].query('GET comments\nFilter: entry_time > %d' % time.mktime((datetime.now() - timedelta(days=1)).timetuple()), 'id comment author entry_type host_name host_groups service_description entry_time'):
                if int(j['entry_type']) == 2:
                    j['entry_type_desc'] = 'downtime'

                if int(j['entry_type']) == 3:
                    j['entry_type_desc'] = 'flapping'

                if int(j['entry_type']) == 4:
                    j['entry_type_desc'] = 'acknowledgment'
                    
                locate_host(locations, 'comments', j, True)
                                
        generate_output(locations, args.output[0])

    except:
        e = sys.exc_info()
        error('Unable to parse the config file: ' + str(e))
        traceback.print_tb(e[2])
        sys.exit(1)

if __name__ == "__main__":
    main()
