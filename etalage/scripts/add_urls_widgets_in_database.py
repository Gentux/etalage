#!/usr/bin/env python2
# -*- coding: utf-8 -*-


# Add URLs of pages with a widget not declared by clients in the database
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


"""
Retrieve visited websites from Piwik and add in the database URLs when the domain is declared but not the complete URL.
"""


import argparse
import base64
import csv
import datetime
import getpass
import json
import logging
import operator
import os
import pymongo
import sys
import urllib
import urllib2
from urlparse import urlparse


app_name = os.path.splitext(os.path.basename(__file__))[0]
log = logging.getLogger(app_name)

collection = None

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
    parser.add_argument('-u', '--username', help = 'username for HTTP authentification')
    parser.add_argument('-d', '--database', default = 'souk', help = 'database to use')
    parser.add_argument('-c', '--collection', default = 'subscribers', help = 'collection to use')
    parser.add_argument('-v', '--verbose', action = 'store_true', help = 'increase output verbosity')

    args = parser.parse_args()

    logging.basicConfig(
        level = logging.DEBUG if args.verbose else logging.WARNING,
        format = '%(asctime)s %(levelname)-5.5s [%(name)s:%(funcName)s l.%(lineno)d] %(message)s',
        stream = sys.stdout,
        )

    collection = pymongo.Connection()[args.database][args.collection]
    if collection.count() == 0:
        log.error(u'La base de données {} ou la collection {} n’existe pas'.format(
            args.database, args.collection).encode('utf-8'))
        sys.exit(1)

    username = args.username
    if username is None:
        username = raw_input('username: ')
    password = getpass.getpass('password: ')
    basic_auth = base64.encodestring('{0}:{1}'.format(username, password)).strip()

    request = urllib2.Request(CUSTOM_VARS_URL)
    request.method = 'POST'
    request.add_header('Authorization', 'Basic {0}'.format(basic_auth))
    response = urllib2.urlopen(request)

    json_custom_vars = json.loads(response.read())
    get_urls = operator.itemgetter('label')
    tracked_urls = map(get_urls, json_custom_vars[0]['subtable'])
    subscribers_cursor = collection.find()

    add_website_in_database(subscribers_cursor, tracked_urls)


def add_website_in_database(subscribers, tracked_urls):
    log.info(u'number of Piwik URLs: {}'.format(len(tracked_urls)))

    db_domain_names = dict()
    for subscriber in subscribers:
        for site in subscriber['sites'] or []:
            db_domain_name = get_clean_domain_name(site['domain_name'])
            db_domain_names[db_domain_name] = subscriber

    tracked_urls_saved = set()
    for tracked_url in tracked_urls:
        tracked_url = get_clean_url(tracked_url)
        tracked_domain_name = get_clean_domain_name(tracked_url)
        if 'googleusercontent.com' in tracked_domain_name:
            continue

        if tracked_domain_name in db_domain_names:
            if tracked_url in tracked_urls_saved:
                pass  # ignore
            else:
                save_subscriber_website_to_db(tracked_url, db_domain_names[tracked_domain_name])
                tracked_urls_saved.add(tracked_url)
        else:
            log.error('{} domain not registered'.format(get_clean_domain_name(tracked_url)))


def get_clean_domain_name(domain_name):
    domain_name = get_clean_url(domain_name)
    # special case for IP address
    if domain_name[8].isdigit():  # 8 because it’s the second digit after http:// and first after https://
        parts_of_domain_name = domain_name.split('/')
        return '/'.join(parts_of_domain_name[0:3])  # http: +'/'+ '' +'/'+ {address}
    else:
        parts_of_domain_name = urlparse(domain_name).netloc.split('.')
        size = len(parts_of_domain_name)
        return '.'.join(parts_of_domain_name[size - 2: size])  # http://example +'.'+ {tld}


def get_clean_url(url):
    if urlparse(url).scheme == '':
        url = 'http://' + url
    url = url.split('#')[0]  # eliminate HTML fragment
    url = url.split(';jsessionid=')[0]  # eliminate jessionid parameter
    return url


def save_subscriber_website_to_db(url, subscriber):
    for i, site in enumerate(subscriber['sites'] or []):
        if get_clean_domain_name(site['domain_name']) == get_clean_domain_name(url):
            if 'subscriptions' not in site:
                log.error('{}: no subscriptions found'.format(subscriber['_id']))
                return
            elif site['subscriptions'] == None:
                log.error('{}: subscriptions is None'.format(subscriber['_id']))
                return
            for j, subscription in enumerate(site['subscriptions']):
                if subscription['type'] == 'etalage':
                    subscription['url'] = url
                    # edit subscriber to add URL
                    # collection.save(subscriber)
                    return
    log.error('{}: no “etalage” subscription site for that URL'.format(url))


if __name__ == "__main__":
    sys.exit(main())
