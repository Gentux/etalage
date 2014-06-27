#!/usr/bin/env python2
# -*- coding: utf-8 -*-


# Add URLs of pages with a widget not declared by clients in the database
# By: Sébastien Chauvel (sinma) <schauvel@easter-eggs.com>
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

from pprint import pprint

from moncomarquage.config.environment import load_environment
from moncomarquage.model import meta, Subscriber, SubscriberSite, SubscriberSubscription, VolatileSubscriberSubscription
from paste.deploy import appconfig


app_name = os.path.splitext(os.path.basename(__file__))[0]
log = logging.getLogger(app_name)

BASE_URL = u'https://webstats.easter-eggs.com/index.php'

PARAMS = {
    'module': 'API',
    'method': 'CustomVariables.getCustomVariables',
    'format': 'JSON',
    'idSite': None,
    'period': 'day',
    'date': datetime.date.today().isoformat(),
    'expanded': '1',
    'filter_limit': '100'
    }

# name of site and corresponding ID in Piwik
SITE_ID = {
     'etalage': 20,
     'cosmetic': 32,
     'metanol': 17,
     }

# don’t count those
DOMAIN_NAME_EXCEPTIONS = ('googleusercontent.com', 'justice.fr', 'entrouvert.org')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('config_file', metavar='moncomarquage config file', type=str, nargs=1)
    parser.add_argument('-s', '--site_names', nargs='*', help='etalage, cosmetic or metanol')
    parser.add_argument('-u', '--username', help='username for HTTP authentification')
    parser.add_argument('-d', '--database', default='souk', help='database to use')
    parser.add_argument('-c', '--collection', default='subscribers', help='collection to use')
    parser.add_argument('-v', '--verbose', action='store_true', help='increase output verbosity')

    args = parser.parse_args()

    if args.site_names is None or len(args.site_names) == 0:
        tuple_id_sites = [(x, SITE_ID[x]) for x in SITE_ID]
    else:
        tuple_id_sites = [(x, SITE_ID[x]) for x in args.site_names if x in SITE_ID] or SITE_ID.values()
        nb_false_site_names = len(tuple_id_sites) - len(args.site_names)
        if nb_false_site_names != 0:
            print 'incorrect site name'
            sys.exit(1)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.ERROR,
        format='%(asctime)s %(levelname)-5.5s [%(name)s:%(funcName)s l.%(lineno)d] %(message)s',
        stream=sys.stdout,
        )

    # To make PostgreSQL works
    site_conf = appconfig('config:%s' % os.path.abspath(args.config_file[0]))
    load_environment(site_conf.global_conf, site_conf.local_conf)

    # TODO: build a subset of MongoDB data structure from PostgreSQL tables, to make the script work
    # Example (I guess not all the data fields are necessary):
    #
    # {u'_id': ObjectId('5018f7f92935943af5000007'),
    #  u'sites': [{u'domain_name': u'www.mairie-peyrignac.fr',
    #    u'id': 419,
    #    u'name': u'www.mairie-peyrignac.fr',
    #    u'subscriptions': [{u'original': <equivalent in PostgreSQL to edit>
    #      u'type': u'service-public-v3-mobile',
    #      u'url': None},
    #     {u'original': <equivalent in PostgreSQL to edit>
    #      u'type': u'service-public-v3-particuliers',
    #      u'url': u'http://www.mairie-peyrignac.fr/default.asp?sCode=demarches'}]}

    # The following code is a rest of the trial to change the script, in order to edit PostgreSQL
    # and not the MongoDB database. I left it here because it was a nightmare, solution described
    # above seems way better

    #subscriber_subscriptions = dict()
    #site_query = meta.Session.query(Subscriber)
    #for subscriber in site_query:
        #subscriber_sites_query = meta.Session.query(SubscriberSite).filter(
            #SubscriberSite.subscriber_id == subscriber.id
            #)
        #subscriber_subscriptions[subscriber] = dict()
        #for subscriber_site in subscriber_sites_query:
            #subscriber_subscriptions_query = meta.Session.query(SubscriberSubscription).filter(
                #SubscriberSubscription.subscriber_site_id == subscriber_site.id
                #)
            #subscriber_site_list = []
            #for subscriber_subscription in subscriber_subscriptions_query:
                #subscriber_site_list.append(subscriber_subscription)
            #subscriber_subscriptions[subscriber][subscriber_site] = subscriber_site_list

    collection = pymongo.MongoClient(j=True)[args.database][args.collection]
    if collection.count() == 0:
        log.error(u'Database {} or collection {} doesn’t exist'.format(
            args.database, args.collection).encode('utf-8'))
        sys.exit(1)

    username = args.username
    if username is None:
        username = raw_input('username: ')
    password = getpass.getpass('password: ')
    basic_auth = base64.encodestring('{0}:{1}'.format(username, password)).strip()

    for site_name, id in tuple_id_sites:
        PARAMS['idSite'] = id
        custom_vars_url = '{}?{}'.format(BASE_URL, urllib.urlencode(PARAMS))

        request = urllib2.Request(custom_vars_url)
        request.method = 'POST'
        request.add_header('Authorization', 'Basic {0}'.format(basic_auth))

        print '##### {} #####'.format(site_name)
        print 'Querying {}'.format(request.__dict__['_Request__original'])

        response = urllib2.urlopen(request)
        json_custom_vars = json.loads(response.read())

        if len(json_custom_vars) < 3:
            print 'Error: no data for {}'.format(site_name)
            continue  # ignore site

        gadget_id_and_tracked_urls = map(
            lambda item: tuple(item.get('label', '').split('@')),
            json_custom_vars[2]['subtable']
            )
        subscribers_cursor = collection.find()

        # SITE_ID is used to check subscription type (field in subscribers_site in PgSQL,
        # db.souk.subscribers then sites.subscriptions.type), but cosmetic type doesn’t exist,
        # it’s service-public-v3-*, so using service-public-v3 and later we use `in`, not `==`.
        if site_name == 'cosmetic':
            site_name = 'service-public-v3'
        save_website(subscribers_cursor, gadget_id_and_tracked_urls, site_name, collection)


def save_website(subscribers, gadget_id_and_tracked_urls, site_name, collection):
    """The important things happen here: filter and launch registering of URL, report results"""

    log.info(u'number of Piwik URLs: {}'.format(len(gadget_id_and_tracked_urls)))

    db_domain_names = dict() # establish domain_name to subscription correspondance
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
        if True in (s in tracked_domain_name for s in DOMAIN_NAME_EXCEPTIONS):
            continue

        if tracked_domain_name in db_domain_names:
            # different tracked_url can lead to the same clean_tracked_url, ignoring saved URL
            if clean_tracked_url in tracked_urls_saved:
                continue
            else:
                log.warning(u'registering {}'.format(tracked_url))
                subscriber = add_url_to_subscription(
                    gadget_id,
                    tracked_url,
                    site_name,
                    db_domain_names[tracked_domain_name],
                    )
                if subscriber is True:
                    nb_untouched_urls += 1
                elif subscriber is False:
                    nb_errors += 1
                else:  # a valid subscriber
                    #new_subscriber_subscription = VolatileSubscriberSubscription()
                    #new_subscriber_subscription.update_classic_attributes(subscription)
                    #subscriber_subscription.update(new_subscriber_subscription)
                    collection.save(subscriber)
                    nb_modifications += 1
                tracked_urls_saved.add(tracked_url)
        else:
            log.error(u'{} domain not registered (url: {})'.format(
                get_clean_domain_name(tracked_url),
                tracked_url
                ))
            nb_errors += 1

    print u'{} url added or modified'.format(nb_modifications)
    print u'{} untouched URLs'.format(nb_untouched_urls)
    print u'{} errors'.format(nb_errors)


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
    """
    return None if it’s an invalid URL ('Others' or 'Autres'),
    else add http:// if there’s no scheme and remove HTML fragments (`#something`) and `;jsessionid`
    """

    if url in ('Others', 'Autres'):  # depends of the locale
        return None
    if urlparse(url).scheme == '':
        url = 'http://' + url
    url = url.split('#')[0]  # eliminate HTML fragment
    url = url.split(';jsessionid=')[0]  # eliminate jessionid parameter
    return url


def add_url_to_subscription(gadget_id, url, site_name, subscriber):
    """
    Return
    * modified subscriber if an URL has been modified
    * True if an URL has been untouched
    * False if we can’t add/check etalage URL
    """

    for site in subscriber['sites'] or []:
        # errors when there’s no subscriptions
        if 'subscriptions' not in site:
            log.error('{}: no subscriptions found'.format(subscriber['_id']))
            return False
        elif site['subscriptions'] is None:
            log.error('{}: subscriptions is None'.format(subscriber['_id']))
            return False

        for subscription in site['subscriptions']:
            # if incorrect type or gadget ID, continue
            if site_name not in subscription['type'] or str(subscription['id']) != str(gadget_id):
                continue
            if subscription['url'] == url:
                return True  # no modification because URLs are equals
            log.debug(u'\nwriting…\nID:  {}\nDB:  {}\nURL: {}\n'.format(
                subscriber['_id'], subscription['url'], url))
            subscription['url'] = url

            return subscriber

    log.error(u'ID: {}, gadget_id: {} — no “{}” subscription or valid gadget_id'.format(
        subscriber['_id'],
        gadget_id,
        site_name if site_name != 'service-public-v3' else 'cosmetic',
        ).encode('utf-8'))
    return False


if __name__ == "__main__":
    sys.exit(main())
