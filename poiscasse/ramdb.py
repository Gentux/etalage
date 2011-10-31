# -*- coding: utf-8 -*-


# PoisCasse -- Open Data POIs portal
# By: Emmanuel Raviart <eraviart@easter-eggs.com>
#     Romain Soufflet <rsoufflet@easter-eggs.com>
#
# Copyright (C) 2011 Easter-eggs
# http://gitorious.org/infos-pratiques/poiscasse
#
# This file is part of PoisCasse.
#
# PoisCasse is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# PoisCasse is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


"""RAM-based database"""


import itertools
import logging

from biryani import strings
from dogpile import SyncReaderDogpile

from . import conf
from .ramindexes import *


categories_by_slug = None
categories_slug_by_word = None
dogpile = SyncReaderDogpile(24 * 3600) # Cache timeout can be very high, because it is not needed. TODO: Remove it.
inited = False
log = logging.getLogger(__name__)
pois_id_by_category_slug = None
pois_id_by_territory_kind_code = None
pois_id_by_word = None
ram_pois_by_id = None


def iter_categories_slug(term = None):
    intersected_sets = []
    if term:
        prefixes = strings.slugify(term).split(u'-')
        iterables_by_prefix = {}
        for prefix in prefixes:
            if prefix in iterables_by_prefix:
                # TODO? Handle categories with several words sharing the same prefix?
                continue
            iterables_by_prefix[prefix] = (
                category_slug
                for word, category_slug in categories_slug_by_word.iteritems()
                if word.startswith(prefix)
                )
        intersected_sets.extend(
            union_set(iterables_by_prefix.get(prefix))
            for prefix in prefixes
            )

    categories_slug = intersection_set(intersected_sets)
    if categories_slug is None:
        return categories_by_slug.iterkeys()
    return categories_slug


def iter_pois_id(categories_slug = None, term = None, territory_kind_code = None):
    intersected_sets = []
    for category_slug in set(categories_slug or []):
        if category_slug is not None:
            intersected_sets.append(pois_id_by_category_slug.get(category_slug))
    if term:
        prefixes = strings.slugify(term).split(u'-')
        iterables_by_prefix = {}
        for prefix in prefixes:
            if prefix in iterables_by_prefix:
                # TODO? Handle pois with several words sharing the same prefix?
                continue
            iterables_by_prefix[prefix] = (
                pois_id
                for word, pois_id in pois_id_by_word.iteritems()
                if word.startswith(prefix)
                )
        intersected_sets.extend(
            union_set(iterables_by_prefix.get(prefix))
            for prefix in prefixes
            )
    if territory_kind_code is not None:
        assert isinstance(territory_kind_code, tuple) and len(territory_kind_code) == 2, territory_kind_code
        intersected_sets.append(pois_id_by_territory_kind_code.get(territory_kind_code))

    # Note: Brackets below are mandatory. Without then iter_prefixes_based_territories_id([u'MILON', u'CHAPELLE'])))
    # returns an empty set.
    found_pois_id = intersection_set(intersected_sets)
    if found_pois_id is None:
        return ram_pois_by_id.iterkeys()
    return found_pois_id


def load():
    """Load MongoDB data into RAM-based database."""
    import datetime

    import pymongo

    from . import model

    start_time = datetime.datetime.utcnow()

    new_indexes = dict(
        categories_by_slug = {},
        categories_slug_by_word = {},
        pois_id_by_category_slug = {},
        pois_id_by_territory_kind_code = {},
        pois_id_by_word = {},
        ram_pois_by_id = {},
        )

    for category_infos in model.db[conf['categories_collection']].find(None, ['code', 'title']):
        new_indexes['categories_by_slug'][category_infos['code']] = category_infos['title']

    for poi in model.Poi.find({'metadata.deleted': {'$exists': False}},
            ['geo', 'metadata.categories-index', 'metadata.territories-index', 'metadata.title']).limit(1000):
        metadata = poi.metadata

        ram_poi = model.RamPoi(
            _id = poi._id,
            geo = poi.geo[0] if poi.geo is not None else None,
            name = metadata['title'],
            )
        territories_kind_code = set(
            (territory_kind_code['kind'], territory_kind_code['code'])
            for territory_kind_code in metadata['territories-index']
            if territory_kind_code['kind'] not in (u'Country', u'InternationalOrganization', u'MetropoleOfCountry')
            ) if metadata.get('territories-index') is not None else None
        ram_poi.add_to_ramdb(new_indexes, metadata.get('categories-index'), territories_kind_code)

    # Remove unused categories.
    for category_slug in new_indexes['categories_by_slug'].keys():
        if category_slug not in new_indexes['pois_id_by_category_slug']:
            log.warning('Ignoring category "{0}" not used by any POI.'.format(category_slug))
            del new_indexes['categories_by_slug'][category_slug]
    for category_slug in new_indexes['pois_id_by_category_slug'].keys():
        if category_slug not in new_indexes['categories_by_slug']:
            log.warning('Ignoring category "{0}" not defined in categories collection.'.format(category_slug))
            del new_indexes['pois_id_by_category_slug'][category_slug]

    for category_slug in new_indexes['categories_by_slug']:
        for word in category_slug.split(u'-'):
            new_indexes['categories_slug_by_word'].setdefault(word, set()).add(category_slug)

    with dogpile.acquire_write_lock():
        global categories_by_slug
        categories_by_slug = new_indexes['categories_by_slug']
        global categories_slug_by_word
        categories_slug_by_word = new_indexes['categories_slug_by_word']
        global pois_id_by_category_slug
        pois_id_by_category_slug = new_indexes['pois_id_by_category_slug']
        global pois_id_by_territory_kind_code
        pois_id_by_territory_kind_code = new_indexes['pois_id_by_territory_kind_code']
        global pois_id_by_word
        pois_id_by_word = new_indexes['pois_id_by_word']
        global ram_pois_by_id
        ram_pois_by_id = new_indexes['ram_pois_by_id']

    inited = True
    log.info('RAM-based database loaded in {0} seconds'.format(datetime.datetime.utcnow() - start_time))


def ramdb_based(controller):
    """A decorator that allow to use ramdb data and update it regularily from MongoDB data."""
    def invoke(req):
        # Currently, ramdb works only when used inside a single process.
        assert not req.environ['wsgi.multiprocess']
        with dogpile.acquire(load):
            return controller(req)
    return invoke

