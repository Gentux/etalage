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
france_id = None
inited = False
log = logging.getLogger(__name__)
pois_by_id = None
pois_id_by_category_slug = None
pois_id_by_competence_territory_id = None
pois_id_by_territory_id = None
pois_id_by_word = None
territories_by_id = None


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
        territory = territories_by_id[territory_id]
        ancestors_id = territory.ancestors_id
        territory_competent_pois_id = union_set(
            pois_id_by_competence_territory_id.get(ancestor_id)
            for ancestor_id in (ancestors_id or [])
            ) if ancestors_id is not None and add_competent else None
    else:
        territory_competent_pois_id = None

    for category_slug in set(categories_slug or []):
        if category_slug is not None:
            category_pois_id = pois_id_by_category_slug.get(category_slug)
            if category_pois_id:
                if territory_competent_pois_id is None:
                    competent_pois_id = category_pois_id
                else:
                    competent_pois_id = category_pois_id.intersection(territory_competent_pois_id)
                intersected_sets.append(competent_pois_id)
            else:
                intersected_sets.append(set())

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
        france_id = None,
        pois_by_id = {},
        pois_id_by_category_slug = {},
        pois_id_by_competence_territory_id = {},
        pois_id_by_territory_id = {},
        pois_id_by_word = {},
        territories_by_id = {},
        )

    for category_bson in model.db[conf['categories_collection']].find(None, ['code', 'tags_code', 'title']):
        category = model.Category(
            name = category_bson['title'],
            tags_slug = set(category_bson.get('tags_code') or []) or None,
            )
        category_slug = category_bson['code']
        new_indexes['categories_by_slug'][category_slug] = category
        for word in category_slug.split(u'-'):
            new_indexes['categories_slug_by_word'].setdefault(word, set()).add(category_slug)
        for tag_slug in (category.tags_slug or set()):
            new_indexes['categories_slug_by_tag_slug'].setdefault(tag_slug, set()).add(category_slug)

    for organism_type_bson in model.db[conf['organism_types_collection']].find(None, ['code', 'slug']):
        if organism_type_bson['slug'] not in new_indexes['categories_by_slug']:
            log.warning('Ignoring organism type "{0}" without matching category.'.format(organism_type_bson['code']))
            continue
        new_indexes['categories_slug_by_pivot_code'][organism_type_bson['code']] = organism_type_bson['slug']

    # Temporary variable, not a permanent index
    territories_id_by_kind_code = {}
    for territory_bson in model.db[conf['territories_collection']].find(None, [
            'ancestors_id',
            'code',
            'hinge_type',
            'kind',
            'main_postal_distribution',
            'name',
            ]):
        territory_class = model.Territory.kind_to_class(territory_bson['kind'])
        assert territory_class is not None, 'Invalid territory type name: {0}'.format(class_name)
        territory = territory_class(
            _id = territory_bson['_id'],
            ancestors_id = territory_bson['ancestors_id'],
            code = territory_bson['code'],
            hinge_type = territory_bson.get('hinge_type'),
            main_postal_distribution = territory_bson['main_postal_distribution'],
            name = territory_bson['name'],
            )
        new_indexes['territories_by_id'][territory_bson['_id']] = territory
        territories_id_by_kind_code[(territory_bson['kind'], territory_bson['code'])] = territory_bson['_id']
        if territory_bson['kind'] == u'Country' and territory_bson['code'] == u'FR':
            new_indexes['france_id'] = territory_bson['_id']
    assert new_indexes['france_id'] is not None

    for poi_bson in model.db[conf['pois_collection']].find({'metadata.deleted': {'$exists': False}}):
        metadata = poi_bson['metadata']
        poi = model.Poi(
            _id = poi_bson['_id'],
            geo = poi_bson['geo'][0] if poi_bson.get('geo') is not None else None,
            name = metadata['title'],
            )

        fields_position = {}
        fields = []
        for field_id in metadata['positions']:
            field_position = fields_position.get(field_id, 0)
            fields_position[field_id] = field_position + 1
            field_metadata = metadata[field_id][field_position]
            field_value = poi_bson[field_id][field_position]
            fields.append(load_field(field_id, field_metadata, field_value, territories_id_by_kind_code))
        if fields:
            poi.fields = fields

        new_indexes['pois_by_id'][poi._id] = poi

        for category_slug in (metadata.get('categories-index') or set()):
            new_indexes['pois_id_by_category_slug'].setdefault(category_slug, set()).add(poi._id)

        for i, territory_metadata in enumerate(metadata.get('territories') or []):
            if strings.slugify(territory_metadata['label']) == u'territoires-de-competence':
                poi_competence_territories_id = set(
                    territories_id_by_kind_code[(territory_kind_code['kind'], territory_kind_code['code'])]
                    for territory_kind_code in poi_bson['territories'][i]
                    )
                break
        else:
            poi_competence_territories_id = None
        if poi_competence_territories_id is None:
            # A POI that has no explicit competence territories is considered to be competent everywhere.
            new_indexes['pois_id_by_competence_territory_id'].setdefault(new_indexes['france_id'], set()).add(poi._id)
        else:
            for territory_id in (poi_competence_territories_id or set()):
                new_indexes['pois_id_by_competence_territory_id'].setdefault(territory_id, set()).add(poi._id)

        poi_territories_id = set(
            territories_id_by_kind_code[(territory_kind_code['kind'], territory_kind_code['code'])]
            for territory_kind_code in metadata['territories-index']
            if territory_kind_code['kind'] not in (u'Country', u'InternationalOrganization', u'MetropoleOfCountry')
            ) if metadata.get('territories-index') is not None else None
        for territory_id in (poi_territories_id or set()):
            new_indexes['pois_id_by_territory_id'].setdefault(territory_id, set()).add(poi._id)

        for word in strings.slugify(poi.name).split(u'-'):
            new_indexes['pois_id_by_word'].setdefault(word, set()).add(poi._id)

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
        global france_id
        france_id = new_indexes['france_id']
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
        global territories_by_id
        territories_by_id = new_indexes['territories_by_id']

    inited = True
    log.info('RAM-based database loaded in {0} seconds'.format(datetime.datetime.utcnow() - start_time))


def load_field(id, metadata, value, territories_id_by_kind_code):
    from . import model

    if len(metadata) != (1 if 'kind' in metadata else 0) \
            + (1 if 'label' in metadata else 0) \
            + (1 if 'type' in metadata else 0) \
            + (1 + len(metadata['positions']) if 'positions' in metadata else 0):
        log.warning('Unexpected attributes in field {0}, metadata {1}, value {2}'.format(id, metadata, value))
    if 'positions' in metadata:
        fields_position = {}
        fields = []
        for field_id in metadata['positions']:
            field_position = fields_position.get(field_id, 0)
            fields_position[field_id] = field_position + 1
            field_metadata = metadata[field_id][field_position]
            field_value = value[field_id][field_position]
            fields.append(load_field(field_id, field_metadata, field_value, territories_id_by_kind_code))
        value = fields or None
    elif id == 'territories':
        # Replace each kind-code with the corresponding territory ID.
        if value is not None:
            value = [
                territories_id_by_kind_code[(territory_kind_code['kind'], territory_kind_code['code'])]
                for territory_kind_code in value
                ]
    return model.Field(
        id = id,
        kind = metadata.get('kind'),
        label = metadata['label'],
        type = metadata.get('type'),
        value = value,
        )


def ramdb_based(controller):
    """A decorator that allow to use ramdb data and update it regularily from MongoDB data."""
    def invoke(req):
        # Currently, ramdb works only when used inside a single process.
        assert not req.environ['wsgi.multiprocess']
        with dogpile.acquire(load):
            return controller(req)
    return invoke

