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


import argparse
import base64
import csv
import datetime
import getpass
import json
import logging
import operator
import os
import sys
import urllib
import urllib2


app_name = os.path.splitext(os.path.basename(__file__))[0]
log = logging.getLogger(app_name)


BASE_URL = u'https://webstats.easter-eggs.com/index.php'

PARAMS = {
    'module': 'API',
    'method': 'CustomVariables.getCustomVariables',
    'format': 'JSON',
    'idSite': '20',
    'period': 'month',
    'date': datetime.date.today().isoformat(),
    'expanded': '1',
    'filter_limit': '100'
    }

CUSTOM_VARS_URL = '{}?{}'.format(BASE_URL, urllib.urlencode(PARAMS))


def main():
    parser = argparse.ArgumentParser(description = __doc__)
    parser.add_argument('-u', '--user', help = 'username used for HTTP authentification')
    parser.add_argument('-v', '--verbose', action = 'store_true', help = 'increase output verbosity')

    args = parser.parse_args()

    if args.user is None:
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


if __name__ == "__main__":
    sys.exit(main())
