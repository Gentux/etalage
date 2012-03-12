# -*- coding: utf-8 -*-


# Etalage -- Open Data POIs portal
# By: Emmanuel Raviart <eraviart@easter-eggs.com>
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


"""RAM-based database"""


import datetime
import logging
import sys

from biryani import strings
import threading2

from . import conf
from .ramindexes import *


categories_by_slug = {}
categories_slug_by_pivot_code = {}
categories_slug_by_tag_slug = {}
categories_slug_by_word = {}
indexed_pois_id = set()
last_timestamp = None
read_write_lock = threading2.SHLock()
log = logging.getLogger(__name__)
pois_by_id = {}
pois_id_by_category_slug = {}
pois_id_by_competence_territory_id = {}
pois_id_by_presence_territory_id = {}
pois_id_by_word = {}
schemas_title_by_name = {}
territories_by_id = {}
territories_id_by_ancestor_id = {}
territories_id_by_kind_code = {}
territories_id_by_postal_distribution = {}


def get_territory_related_territories_id(territory):
    related_territories_id = set()
    for sub_territory_id in territories_id_by_ancestor_id[territory._id]:
        sub_territory = territories_by_id[sub_territory_id]
        for ancestor_id in sub_territory.ancestors_id:
            related_territories_id.add(ancestor_id)
    return related_territories_id


def iter_categories_slug(organism_types_only = False, tags_slug = None, term = None):
    intersected_sets = []
    if organism_types_only:
        intersected_sets.append(set(categories_slug_by_pivot_code.itervalues()))
    for tag_slug in set(tags_slug or []):
        if tag_slug is not None:
            intersected_sets.append(categories_slug_by_tag_slug.get(tag_slug))
    if term:
        prefixes = strings.slugify(term).split(u'-')
        categories_slug_by_prefix = {}
        for prefix in prefixes:
            if prefix in categories_slug_by_prefix:
                # TODO? Handle categories with several words sharing the same prefix?
                continue
            categories_slug_by_prefix[prefix] = union_set(
                word_categories_slug
                for word, word_categories_slug in categories_slug_by_word.iteritems()
                if word.startswith(prefix)
                ) or set()
        intersected_sets.extend(categories_slug_by_prefix.itervalues())

    categories_slug = intersection_set(intersected_sets)
    if categories_slug is None:
        return categories_by_slug.iterkeys()
    return categories_slug


def iter_pois_id(categories_slug = None, competence_territories_id = None, presence_territory = None, term = None):
    intersected_sets = []

    if competence_territories_id is not None:
        territory_competent_pois_id = union_set(
            pois_id_by_competence_territory_id.get(competence_territory_id)
            for competence_territory_id in competence_territories_id
            )
        if not territory_competent_pois_id:
            return set()
        intersected_sets.append(territory_competent_pois_id)

    if presence_territory is not None:
        territory_present_pois_id = pois_id_by_presence_territory_id.get(presence_territory._id)
        if not territory_present_pois_id:
            return set()
        intersected_sets.append(territory_present_pois_id)

    for category_slug in set(categories_slug or []):
        if category_slug is not None:
            category_pois_id = pois_id_by_category_slug.get(category_slug)
            if not category_pois_id:
                return set()
            intersected_sets.append(category_pois_id)

    # We should filter on term *after* having looked for competent organizations. Otherwise, when no organization
    # matching term is found, the nearest organizations will be used even when there are competent organizations (that
    # don't match the term).
    if term:
        prefixes = strings.slugify(term).split(u'-')
        pois_id_by_prefix = {}
        for prefix in prefixes:
            if prefix in pois_id_by_prefix:
                # TODO? Handle pois with several words sharing the same prefix?
                continue
            pois_id_by_prefix[prefix] = union_set(
                pois_id
                for word, pois_id in pois_id_by_word.iteritems()
                if word.startswith(prefix)
                ) or set()
        intersected_sets.extend(pois_id_by_prefix.itervalues())

    found_pois_id = intersection_set(intersected_sets)
    if found_pois_id is None:
        return indexed_pois_id
    return found_pois_id


def load():
    """Load MongoDB data into RAM-based database."""
    from . import model

    start_time = datetime.datetime.utcnow()
    global last_timestamp
    # Remove a few seconds, for data changes that occur during startup.
    last_timestamp = start_time - datetime.timedelta(seconds = 30)

    for category_bson in model.db[conf['categories_collection']].find(None, ['code', 'tags_code', 'title']):
        category = model.Category(
            name = category_bson['title'],
            tags_slug = set(category_bson.get('tags_code') or []) or None,
            )
        category_slug = category_bson['code']
        categories_by_slug[category_slug] = category
        for word in category_slug.split(u'-'):
            categories_slug_by_word.setdefault(word, set()).add(category_slug)
        for tag_slug in (category.tags_slug or set()):
            categories_slug_by_tag_slug.setdefault(tag_slug, set()).add(category_slug)

    for organism_type_bson in model.db[conf['organism_types_collection']].find(None, ['code', 'slug']):
        if organism_type_bson['slug'] not in categories_by_slug:
            log.warning('Ignoring organism type "{0}" without matching category.'.format(organism_type_bson['code']))
            continue
        categories_slug_by_pivot_code[organism_type_bson['code']] = organism_type_bson['slug']

    territories_query = dict(
        kind = {'$in': conf['territories_kinds']},
        ) if conf['territories_kinds'] is not None else None
    for territory_bson in model.db[conf['territories_collection']].find(territories_query, [
            'ancestors_id',
            'code',
            'geo',
            'hinge_type',
            'kind',
            'main_postal_distribution',
            'name',
            ]):
        main_postal_distribution = territory_bson['main_postal_distribution']
        territory_class = model.Territory.kind_to_class(territory_bson['kind'])
        assert territory_class is not None, 'Invalid territory type name: {0}'.format(class_name)
        territory_id = territory_bson['_id']
        territory = territory_class(
            _id = territory_id,
            ancestors_id = territory_bson['ancestors_id'],
            code = territory_bson['code'],
            geo = territory_bson.get('geo'),
            hinge_type = territory_bson.get('hinge_type'),
            main_postal_distribution = main_postal_distribution,
            name = territory_bson['name'],
            )
        territories_by_id[territory_id] = territory
        for ancestor_id in territory_bson['ancestors_id']:
            territories_id_by_ancestor_id.setdefault(ancestor_id, set()).add(territory_id)
        territories_id_by_kind_code[(territory_bson['kind'], territory_bson['code'])] = territory_id
        territories_id_by_postal_distribution[(main_postal_distribution['postal_code'],
            main_postal_distribution['postal_routing'])] = territory_id

    for schema in model.db.schemas.find(None, ['name', 'title']):
        schemas_title_by_name[schema['name']] = schema['title']

    model.Poi.load_pois()
    model.Poi.index_pois()

#    # Remove unused categories.
#    for category_slug in categories_by_slug.keys():
#        if category_slug not in pois_id_by_category_slug:
#            log.warning('Ignoring category "{0}" not used by any POI.'.format(category_slug))
#            del categories_by_slug[category_slug]
#    for category_slug in pois_id_by_category_slug'].keys():
#        if category_slug not in categories_by_slug:
#            log.warning('Ignoring category "{0}" not defined in categories collection.'.format(category_slug))
#            del pois_id_by_category_slug[category_slug]

##    for category_slug in categories_by_slug.iterkeys():
#        for word in category_slug.split(u'-'):
#            categories_slug_by_word.setdefault(word, set()).add(category_slug)

    log.info('RAM-based database loaded in {0} seconds'.format(datetime.datetime.utcnow() - start_time))


def ramdb_based(controller):
    """A decorator that allow to use ramdb data and update it regularily from MongoDB data."""
    def invoke(req):
        from . import model
        global last_timestamp
        for data_update in model.db[conf['data_updates_collection']].find(dict(
                collection_name = 'pois',
                timestamp = {'$gt': last_timestamp},
                )).sort('timestamp'):
            id = data_update['document_id']
            poi_bson = model.Poi.get_collection().find_one(id)
            read_write_lock.acquire()
            try:
                # Note: POI's whose parent_id == id are not updated here. They will be updated when publisher will
                # publish their change.
                # First find changes to do on indexes.
                existing = {}
                indexes = sys.modules[__name__].__dict__
                find_existing(indexes, 'pois_id_by_category_slug', 'dict_of_sets', id, existing)
                find_existing(indexes, 'pois_id_by_competence_territory_id', 'dict_of_sets', id, existing)
                find_existing(indexes, 'pois_id_by_presence_territory_id', 'dict_of_sets', id, existing)
                find_existing(indexes, 'pois_id_by_word', 'dict_of_sets', id, existing)
                # Then update indexes.
                delete_remaining(indexes, existing)
                if poi_bson is None or poi_bson['metadata'].get('deleted', False):
                    pois_by_id.pop(id, None)
                    indexed_pois_id.discard(id)
                else:
                    load_poi(poi_bson)
            finally:
                read_write_lock.release()
            last_timestamp = data_update['timestamp']

        # TODO: Handle schemas updates & schemas_title_by_name.

        read_write_lock.acquire(shared = True)
        try:
            return controller(req)
        finally:
            read_write_lock.release()
    return invoke

