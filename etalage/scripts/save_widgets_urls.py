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
Add URLs of widgets in the DB when domain is declared but not complete URL.
"""


import argparse
import base64
import datetime
import getpass
import json
import logging
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
    'period': 'year',
    'date': datetime.date.today().isoformat(),
    'expanded': '1',
    'filter_limit': '100'
    }

CUSTOM_VARS_URL = '{}?{}'.format(BASE_URL, urllib.urlencode(PARAMS))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-u', '--username', help='username for HTTP authentification')
    parser.add_argument('-d', '--database', default='souk', help='database to use')
    parser.add_argument('-c', '--collection', default='subscribers', help='collection to use')
    parser.add_argument('-v', '--verbose', action='store_true', help='increase output verbosity')

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.ERROR,
        format='%(asctime)s %(levelname)-5.5s [%(name)s:%(funcName)s l.%(lineno)d] %(message)s',
        stream=sys.stdout,
        )

    global collection
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
    gadget_id_and_tracked_urls = map(
        lambda item: tuple(item.get('label', '').split('@')),
        json_custom_vars[2]['subtable']
        )
    subscribers_cursor = collection.find()

    add_website_in_database(subscribers_cursor, gadget_id_and_tracked_urls)


def add_website_in_database(subscribers, gadget_id_and_tracked_urls):
    log.info(u'number of Piwik URLs: {}'.format(len(gadget_id_and_tracked_urls)))

    db_domain_names = dict()  # establish domain_name → subscriber correspondance
    for subscriber in subscribers:
        for site in subscriber['sites'] or []:
            db_domain_name = get_clean_domain_name(site['domain_name'])
            db_domain_names[db_domain_name] = subscriber

    nb_modifications = 0
    nb_untouched_urls = 0
    nb_errors = 0
    tracked_urls_saved = set()
    for gadget_id, tracked_url in gadget_id_and_tracked_urls:
        clean_tracked_url = get_clean_url(tracked_url)
        if clean_tracked_url is None:
            log.error('{}: incorrect URL'.format(tracked_url))
            continue
        tracked_domain_name = get_clean_domain_name(tracked_url)
        if tracked_domain_name is None:
            log.error('{}: URL doesn’t contain a valid domain name'.format(clean_tracked_url))
            continue
        if 'googleusercontent.com' in tracked_domain_name:
            continue

        if tracked_domain_name in db_domain_names:
            if tracked_url in tracked_urls_saved:
                pass  # TODO: make useful comment
            else:
                log.warning(u'{} not registered. Registering…'.format(tracked_url))
                url_modified = save_subscriber_url_to_db(
                    None,
                    tracked_url,
                    db_domain_names[tracked_domain_name]
                    )
                if url_modified is True:
                    nb_modifications += 1
                elif url_modified is False:
                    nb_untouched_urls += 1
                else:
                    nb_errors += 1
                tracked_urls_saved.add(tracked_url)
        else:
            log.error('{} domain not registered'.format(get_clean_domain_name(tracked_url)))

    print '{} url added or modified'.format(nb_modifications)
    print '{} untouched URLs'.format(nb_untouched_urls)
    print '{} errors'.format(nb_errors)


def get_clean_domain_name(url):
    """
    Only keep the domain name
    """

    url = get_clean_url(url)
    # special case for IP address
    if url[7].isdigit() or (url[7] == '/' and url[8].isdigit()):
        return None
    else:
        parts_of_url = urlparse(url).netloc.split('.')
        size = len(parts_of_url)
        return '.'.join(parts_of_url[size - 2: size])  # http://example +'.'+ {tld}


def get_clean_url(url):
    if url in ('Others', 'Autres'):  # depends of the locale
        return None
    if urlparse(url).scheme == '':
        url = 'http://' + url
    url = url.split('#')[0]  # eliminate HTML fragment
    url = url.split(';jsessionid=')[0]  # eliminate jessionid parameter
    return url


def save_subscriber_url_to_db(gadget_id, url, subscriber):
    for i, site in enumerate(subscriber['sites'] or []):
        # errors when there’s no subcriptions
        if 'subscriptions' not in site:
            log.error('{}: no subscriptions found'.format(subscriber['_id']))
            return None
        elif site['subscriptions'] is None:
            log.error('{}: subscriptions is None'.format(subscriber['_id']))
            return None

        for j, subscription in enumerate(site['subscriptions']):
            if subscription['type'] != 'etalage' or \
                    (gadget_id is not None and subscription['id'] != gadget_id):
                continue
            if subscription['url'] == url:
                return False  # no modification because URLs are equals
            subscriber['sites'][i]['subscriptions'][j]['url'] = url
            collection.save(subscriber)
            return True

    log.error('{}, {}: no “etalage” subscription or valid gadget_id'.format(
        subscriber['_id'],
        gadget_id
        ))


if __name__ == "__main__":
    sys.exit(main())
