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

DOMAIN_NAME_EXCEPTIONS = ('googleusercontent.com', 'justice.fr', 'entrouvert.org')


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

    collection = pymongo.MongoClient(j=True)[args.database][args.collection]
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

    save_website(subscribers_cursor, gadget_id_and_tracked_urls, collection)


def save_website(subscribers, gadget_id_and_tracked_urls, collection):
    """The important things happen here: filter and launch registering of URL, report results"""

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
            log.error(u'{}: incorrect URL'.format(tracked_url))
            continue
        tracked_domain_name = get_clean_domain_name(tracked_url)
        if tracked_domain_name is None:
            log.error(u'{}: URL doesn’t contain a valid domain name'.format(clean_tracked_url))
            continue
        if True in (s in tracked_domain_name for s in DOMAIN_NAME_EXCEPTIONS):
            continue

        if tracked_domain_name in db_domain_names:
            # different tracked_url can lead to the same clean_tracked_url, ignoring saved URL
            if clean_tracked_url in tracked_urls_saved:
                continue
            else:
                log.warning(u'{} not registered. Registering…'.format(tracked_url))
                new_subscriber = save_subscriber_url(
                    None,
                    tracked_url,
                    db_domain_names[tracked_domain_name],
                    )
                if new_subscriber is True:
                    nb_untouched_urls += 1
                elif new_subscriber is False:
                    nb_errors += 1
                else:
                    collection.save(subscriber)
                tracked_urls_saved.add(tracked_url)
        else:
            log.error(u'{} domain not registered (url: {})'.format(
                get_clean_domain_name(tracked_url),
                tracked_url
                ))
            nb_errors += 1

    print '{} url added or modified'.format(nb_modifications)
    print '{} untouched URLs'.format(nb_untouched_urls)
    print '{} errors'.format(nb_errors)


def get_clean_domain_name(url):
    """Only keep the domain name"""

    url = get_clean_url(url)
    # special case for IP address
    if url[7].isdigit() or (url[7] == '/' and url[8].isdigit()):
        return None
    else:
        parts_of_url = urlparse(url).netloc.split('.')
        size = len(parts_of_url)
        return '.'.join(parts_of_url[size - 2: size])  # http://example +'.'+ {tld}


def get_clean_url(url):
    """Remove HTML fragments (`#something`) and `;jsessionid`"""

    if url in ('Others', 'Autres'):  # depends of the locale
        return None
    if urlparse(url).scheme == '':
        url = 'http://' + url
    url = url.split('#')[0]  # eliminate HTML fragment
    url = url.split(';jsessionid=')[0]  # eliminate jessionid parameter
    return url


def save_subscriber_url(gadget_id, url, subscriber):
    """Return
    * modified subscriber if an URL has been modified
    * True if an URL has been untouched
    * False if we can’t add/check etalage URL
    """

    for i, site in enumerate(subscriber['sites'] or []):
        # errors when there’s no subcriptions
        if 'subscriptions' not in site:
            log.error(u'{}: no subscriptions found'.format(subscriber['_id']))
            return False
        elif site['subscriptions'] is None:
            log.error(u'{}: subscriptions is None'.format(subscriber['_id']))
            return False

        for j, subscription in enumerate(site['subscriptions']):
            if subscription['type'] != 'etalage' or \
                    (gadget_id is not None and subscription['id'] != gadget_id):
                continue
            if subscription['url'] == url:
                return True  # no modification because URLs are equals
            log.debug(subscriber['_id'])
            log.debug(u'DB:  {}\nURL: {}\n\n'.format(subscription['url'], url))
            subscription['url'] = url
            return subscriber

    log.error(u'{}, {}: no “etalage” subscription or valid gadget_id'.format(
        subscriber['_id'],
        gadget_id
        ))
    return False


if __name__ == "__main__":
    sys.exit(main())
