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

from . import conf, conv
from .ramindexes import *


categories_slug_by_tag_slug = {}
categories_slug_by_word = {}
category_by_slug = {}
category_slug_by_pivot_code = {}
last_timestamp = None
read_write_lock = threading2.SHLock()
log = logging.getLogger(__name__)
schema_title_by_name = {}
territories_id_by_ancestor_id = {}
territories_id_by_postal_distribution = {}
territory_by_id = {}
territory_id_by_kind_code = {}


def get_territory_related_territories_id(territory):
    related_territories_id = set()
    for sub_territory_id in territories_id_by_ancestor_id[territory._id]:
        sub_territory = territory_by_id[sub_territory_id]
        for ancestor_id in sub_territory.ancestors_id:
            related_territories_id.add(ancestor_id)
    return related_territories_id


def iter_categories_slug(organism_types_only = False, tags_slug = None, term = None):
    intersected_sets = []
    if organism_types_only:
        intersected_sets.append(set(category_slug_by_pivot_code.itervalues()))
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
        return category_by_slug.iterkeys()
    return categories_slug


def load():
    """Load MongoDB data into RAM-based database."""
    from . import model

    start_time = datetime.datetime.utcnow()
    global last_timestamp
    # Remove a few seconds, for data changes that occur during startup.
    last_timestamp = start_time - datetime.timedelta(seconds = 30)

    categories_slug_by_tag_slug.clear()
    categories_slug_by_word.clear()
    category_by_slug.clear()
    category_slug_by_pivot_code.clear()
    for category_bson in model.db[conf['categories_collection']].find(None, ['code', 'tags_code', 'title']):
        if not strings.slugify(category_bson.get('title')):
            continue
        category = model.Category.load(category_bson)
        category.index()

    for organism_type_bson in model.db[conf['organism_types_collection']].find(None, ['code', 'slug']):
        if organism_type_bson['slug'] not in category_by_slug:
            log.warning('Ignoring organism type "{0}" without matching category.'.format(organism_type_bson['code']))
            continue
        category_slug_by_pivot_code[organism_type_bson['code']] = organism_type_bson['slug']

    territories_id_by_ancestor_id.clear()
    territories_id_by_postal_distribution.clear()
    territories_query = dict(
        kind = {'$in': conf['territories_kinds']},
        )
    territory_by_id.clear()
    territory_id_by_kind_code.clear()
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
        territory_by_id[territory_id] = territory
        for ancestor_id in territory_bson['ancestors_id']:
            territories_id_by_ancestor_id.setdefault(ancestor_id, set()).add(territory_id)
        territory_id_by_kind_code[(territory_bson['kind'], territory_bson['code'])] = territory_id
        territories_id_by_postal_distribution[conv.check(conv.input_to_postal_distribution("{0} {1}".format(
            main_postal_distribution['postal_code'],
            main_postal_distribution['postal_routing'],
            )), clear_on_error = True)] = territory_id

    schema_title_by_name.clear()
    for schema in model.db.schemas.find(None, ['name', 'title']):
        schema_title_by_name[schema['name']] = schema['title']

    model.Poi.clear_indexes()
    model.Poi.load_pois()
    model.Poi.index_pois()

#    # Remove unused categories.
#    for category_slug in category_by_slug.keys():
#        if category_slug not in model.Poi.ids_by_category_slug:
#            log.warning('Ignoring category "{0}" not used by any POI.'.format(category_slug))
#            del category_by_slug[category_slug]
#    for category_slug in model.Poi.ids_by_category_slug'].keys():
#        if category_slug not in category_by_slug:
#            log.warning('Ignoring category "{0}" not defined in categories collection.'.format(category_slug))
#            del model.Poi.ids_by_category_slug[category_slug]

##    for category_slug in category_by_slug.iterkeys():
#        for word in category_slug.split(u'-'):
#            categories_slug_by_word.setdefault(word, set()).add(category_slug)

    log.info('RAM-based database loaded in {0} seconds'.format(datetime.datetime.utcnow() - start_time))


def ramdb_based(controller):
    """A decorator that allow to use ramdb data and update it regularily from MongoDB data."""
    def invoke(req):
        from . import model

        global last_timestamp
        reset_pois = False
        for data_update in model.db[conf['data_updates_collection']].find(dict(
                collection_name = {'$in': ['categories', 'pois', 'organism_types']},
                timestamp = {'$gt': last_timestamp},
                )).sort('timestamp'):
            if data_update['collection_name'] == 'categories':
                slug = data_update['document_id']
                category_bson = model.db[conf['categories_collection']].find_one(dict(code = slug),
                    ['code', 'tags_code', 'title'])
                read_write_lock.acquire()
                try:
                    # First find changes to do on indexes.
                    existing = {}
                    indexes = sys.modules[__name__]
                    find_existing(indexes, 'categories_slug_by_tag_slug', 'dict_of_sets', slug, existing)
                    find_existing(indexes, 'categories_slug_by_word', 'dict_of_sets', slug, existing)
                    find_existing(indexes, 'category_slug_by_pivot_code', 'dict_of_values', slug, existing)
                    # Then update indexes.
                    delete_remaining(indexes, existing)
                    if category_bson is None:
                        category_by_slug.pop(slug, None)
                        model.Poi.ids_by_category_slug.pop(slug, None)
                    else:
                        category = model.Category.load(category_bson)
                        category.index()
                finally:
                    read_write_lock.release()
            elif data_update['collection_name'] == 'organism_types':
                pivot_code = data_update['document_id']
                organism_type_bson = model.db[conf['organism_types_collection']].find_one(dict(code = pivot_code),
                    ['code', 'slug'])
                read_write_lock.acquire()
                try:
                    if organism_type_bson is None:
                        category_slug_by_pivot_code.pop(pivot_code, None)
                    elif organism_type_bson['slug'] not in category_by_slug:
                        log.warning('Ignoring organism type "{0}" without matching category.'.format(pivot_code))
                    else:
                        category_slug_by_pivot_code[pivot_code] = organism_type_bson['slug']
                finally:
                    read_write_lock.release()
            elif data_update['collection_name'] == 'pois':
                if conf['reset_on_poi_update']:
                    reset_pois = True
                else:
                    id = data_update['document_id']
                    poi_bson = model.Poi.get_collection().find_one(id)
                    read_write_lock.acquire()
                    try:
                        # Note: POI's whose parent_id == id are not updated here. They will be updated when publisher
                        # will publish their change.
                        # First find changes to do on indexes.
                        existing = {}
                        find_existing(model.Poi, 'ids_by_category_slug', 'dict_of_sets', id, existing)
                        find_existing(model.Poi, 'ids_by_competence_territory_id', 'dict_of_sets', id, existing)
                        find_existing(model.Poi, 'ids_by_parent_id', 'dict_of_sets', id, existing)
                        find_existing(model.Poi, 'ids_by_presence_territory_id', 'dict_of_sets', id, existing)
                        find_existing(model.Poi, 'ids_by_word', 'dict_of_sets', id, existing)
                        # Then update indexes.
                        delete_remaining(model.Poi, existing)
                        if poi_bson is None or poi_bson['metadata'].get('deleted', False):
                            model.Poi.instance_by_id.pop(id, None)
                            model.Poi.indexed_ids.discard(id)
                        else:
                            poi = model.Poi.load(poi_bson)
                            model.Poi.indexed_ids.add(poi._id)
                            poi.index(poi._id)
                            del poi.bson
                    finally:
                        read_write_lock.release()
            last_timestamp = data_update['timestamp']
        if reset_pois:
            read_write_lock.acquire()
            try:
                model.Poi.clear_indexes()
                model.Poi.load_pois()
                model.Poi.index_pois()
            finally:
                read_write_lock.release()

        # TODO: Handle schemas updates & schema_title_by_name.

        read_write_lock.acquire(shared = True)
        try:
            return controller(req)
        finally:
            read_write_lock.release()
    return invoke
