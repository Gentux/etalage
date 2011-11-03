# -*- coding: utf-8 -*-


# Etalage -- Open Data POIs portal
# By: Emmanuel Raviart <eraviart@easter-eggs.com>
#     Romain Soufflet <rsoufflet@easter-eggs.com>
#
# Copyright (C) 2011 Easter-eggs
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


"""RAM-based database"""


import itertools
import logging

from biryani import strings
from dogpile import SyncReaderDogpile

from . import conf
from .ramindexes import *


categories_by_slug = None
categories_slug_by_pivot_code = None
categories_slug_by_tag_slug = None
categories_slug_by_word = None
dogpile = SyncReaderDogpile(24 * 3600) # Cache timeout can be very high, because it is not needed. TODO: Remove it.
inited = False
log = logging.getLogger(__name__)
pois_by_id = None
pois_id_by_category_slug = None
pois_id_by_competence_territory_id = None
pois_id_by_territory_id = None
pois_id_by_word = None
territories_ancestors_id_by_id = None
territories_id_by_kind_code = None # Temporary variable, not an index


def iter_categories_slug(organism_types_only = False, tags_slug = None, term = None):
    intersected_sets = []
    if organism_types_only:
        intersected_sets.append(set(categories_slug_by_pivot_code.itervalues()))
    for tag_slug in set(tags_slug or []):
        if tag_slug is not None:
            intersected_sets.append(categories_slug_by_tag_slug.get(tag_slug))
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


def iter_pois_id(add_competent = False, categories_slug = None, term = None, territory_id = None):
    intersected_sets = []

    if territory_id is not None:
        ancestors_id = territories_ancestors_id_by_id.get(territory_id)
        territory_competent_pois_id = union_set(
            pois_id_by_competence_territory_id.get(ancestor_id)
            for ancestor_id in (ancestors_id or set())
            ) if ancestors_id is not None and add_competent else None
    else:
        territory_competent_pois_id = None

    for category_slug in set(categories_slug or []):
        if category_slug is not None:
            category_pois_id = pois_id_by_category_slug.get(category_slug)
            if category_pois_id:
                if territory_competent_pois_id is None:
                    competent_pois_id = None
                else:
                    competent_pois_id = category_pois_id.intersection(territory_competent_pois_id)
                if competent_pois_id:
                    intersected_sets.append(competent_pois_id)
#                else:
                    # TODO: Use 3 nearest territories from category_pois_id.

#    if territory_id is not None:
#        if add_competent:
#            intersected_sets.append(union_set(
#                pois_id_by_competence_territory_id.get(ancestor_id)
#                for ancestor_id in (ancestors_id or set())
#                ))
#        else:
#            intersected_sets.append(pois_id_by_territory_id.get(territory_id))

    # We should filter on term *after* having looked for competent organizations. Otherwise, when no organization
    # matching term is found, the nearest organizations will be used even when there are competent organizations (that
    # don't match the term).
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

    found_pois_id = intersection_set(intersected_sets)
    if found_pois_id is None:
        return pois_by_id.iterkeys()
    return found_pois_id


def load():
    """Load MongoDB data into RAM-based database."""
    import datetime

    import pymongo

    from . import model

    start_time = datetime.datetime.utcnow()

    new_indexes = dict(
        categories_by_slug = {},
        categories_slug_by_pivot_code = {},
        categories_slug_by_tag_slug = {},
        categories_slug_by_word = {},
        pois_by_id = {},
        pois_id_by_category_slug = {},
        pois_id_by_competence_territory_id = {},
        pois_id_by_territory_id = {},
        pois_id_by_word = {},
        territories_ancestors_id_by_id = {},
        )

    for category_infos in model.db[conf['categories_collection']].find(None, ['code', 'tags_code', 'title']):
        category = model.Category(
            name = category_infos['title'],
            tags_slug = set(category_infos.get('tags_code') or []) or None,
            )
        category.add_to_ramdb(new_indexes)

    for organism_type_infos in model.db[conf['organism_types_collection']].find(None, ['code', 'slug']):
        if organism_type_infos['slug'] not in new_indexes['categories_by_slug']:
            log.warning('Ignoring organism type "{0}" without matching category.'.format(organism_type_infos['code']))
            continue
        new_indexes['categories_slug_by_pivot_code'][organism_type_infos['code']] = organism_type_infos['slug']

    global territories_id_by_kind_code
    territories_id_by_kind_code = {}
    for territory_infos in model.db[conf['territories_collection']].find(None, ['ancestors_id', 'code', 'kind']):
        territories_id_by_kind_code[(territory_infos['kind'], territory_infos['code'])] = territory_infos['_id']
        if territory_infos.get('ancestors_id') is not None:
            new_indexes['territories_ancestors_id_by_id'][territory_infos['_id']] = set(territory_infos['ancestors_id'])

    for poi in model.Poi.find({'metadata.deleted': {'$exists': False}}).limit(1000): # TODO
        poi.add_to_ramdb(new_indexes)

#    # Remove unused categories.
#    for category_slug in new_indexes['categories_by_slug'].keys():
#        if category_slug not in new_indexes['pois_id_by_category_slug']:
#            log.warning('Ignoring category "{0}" not used by any POI.'.format(category_slug))
#            del new_indexes['categories_by_slug'][category_slug]
#    for category_slug in new_indexes['pois_id_by_category_slug'].keys():
#        if category_slug not in new_indexes['categories_by_slug']:
#            log.warning('Ignoring category "{0}" not defined in categories collection.'.format(category_slug))
#            del new_indexes['pois_id_by_category_slug'][category_slug]

##    for category_slug in new_indexes['categories_by_slug'].iterkeys():
#        for word in category_slug.split(u'-'):
#            new_indexes['categories_slug_by_word'].setdefault(word, set()).add(category_slug)

    with dogpile.acquire_write_lock():
        global categories_by_slug
        categories_by_slug = new_indexes['categories_by_slug']
        global categories_slug_by_pivot_code
        categories_slug_by_pivot_code = new_indexes['categories_slug_by_pivot_code']
        global categories_slug_by_tag_slug
        categories_slug_by_tag_slug = new_indexes['categories_slug_by_tag_slug']
        global categories_slug_by_word
        categories_slug_by_word = new_indexes['categories_slug_by_word']
        global pois_by_id
        pois_by_id = new_indexes['pois_by_id']
        global pois_id_by_category_slug
        pois_id_by_category_slug = new_indexes['pois_id_by_category_slug']
        global pois_id_by_competence_territory_id
        pois_id_by_competence_territory_id = new_indexes['pois_id_by_competence_territory_id']
        global pois_id_by_territory_id
        pois_id_by_territory_id = new_indexes['pois_id_by_territory_id']
        global pois_id_by_word
        pois_id_by_word = new_indexes['pois_id_by_word']
        global territories_ancestors_id_by_id
        territories_ancestors_id_by_id = new_indexes['territories_ancestors_id_by_id']

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

