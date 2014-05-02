#!/usr/bin/env python2
# -*- coding: utf-8 -*-


# Retrieve Piwik custom vars
# By: Sébastien Chauvel <schauvel@easter-eggs.com>
#
# Copyright (C) 2011, 2012 Easter-eggs
# http://gitorious.org/infos-pratiques/etalage
#
# This file is part of Etalage.
#
# Etalage is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# Etalage is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import base64
import csv
import datetime
import urllib
import urllib2
import json
import getpass
import operator


BASE_URL = u'https://webstats.easter-eggs.com/index.php'

params = {
    'module': 'API',
    'method': 'CustomVariables.getCustomVariables',
    'format': 'JSON',
    'idSite': '20',
    'period': 'month',
    'date': datetime.date.today().isoformat(),
    'expanded': '1',
    'filter_limit': '100'
    }

CUSTOM_VARS_URL = '{}?{}'.format(BASE_URL, urllib.urlencode(params))

print repr(CUSTOM_VARS_URL)

username = raw_input('username: ')
password = getpass.getpass('password: ')
basic_auth = base64.encodestring('{0}:{1}'.format(username, password)).strip()

request = urllib2.Request(CUSTOM_VARS_URL)
request.method = 'POST'
request.add_header('Authorization', 'Basic {0}'.format(basic_auth))
response = urllib2.urlopen(request)

json_custom_vars = json.loads(response.read())
get_urls = operator.itemgetter('label', 'sum_daily_nb_uniq_visitors', 'nb_visits')
infos = map(get_urls, json_custom_vars[0]['subtable'])

f = open('custom_vars_report.csv', 'wb')
wr = csv.writer(f, quoting=csv.QUOTE_ALL)
for info in infos:
    wr.writerow(info)
