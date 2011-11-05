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


"""Conversion functions"""


import datetime

from biryani.baseconv import *
from biryani.bsonconv import *
from biryani.objectconv import *
from biryani.frconv import *
from biryani import states, strings
from territoria2.conv import str_to_postal_distribution


default_state = states.default_state
N_ = lambda message: message


def params_to_pois_directory(params, state = default_state):
    from . import ramdb
    data, errors = pipe(
        struct(
            dict(
                category = pipe(
                    str_to_category_slug,
                    function(lambda slug: ramdb.categories_by_slug[slug]),
                    make_test(lambda category: (category.tags_slug or set()).issuperset(state.category_tags_slug or []),
                        error = N_(u'Missing required tags to category')),
                    ),
                term = str_to_slug,
                territory = pipe(
                    str_to_postal_distribution,
                    postal_distribution_to_territory,
                    ),
                ),
            default = 'ignore',
            keep_empty = True,
            ),
        )(params, state = state)
    if errors is not None:
        return data, errors

    territory_id = data['territory']._id if data.get('territory') is not None else None

    if data.get('category') is None:
        directory_categories_slug = set(ramdb.iter_categories_slug(organism_types_only = True,
            tags_slug = state.category_tags_slug))
    else:
        directory_categories_slug = set([data['category'].slug])
    directory = {}
    for directory_category_slug in directory_categories_slug:
        categories_slug = set(state.base_categories_slug or [])
        categories_slug.add(directory_category_slug)
        directory[directory_category_slug] = list(ramdb.iter_pois_id(add_competent = True,
            categories_slug = categories_slug, term = data.get('term'), territory_id = territory_id))[:3]
    return directory, None


def params_to_pois_geojson(params, state = default_state):
    from . import pagers, ramdb
    data, errors = pipe(
        struct(
            dict(
                category = pipe(
                    str_to_category_slug,
                    function(lambda slug: ramdb.categories_by_slug[slug]),
                    make_test(lambda category: (category.tags_slug or set()).issuperset(state.category_tags_slug or []),
                        error = N_(u'Missing required tags to category')),
                    ),
                term = str_to_slug,
                territory = pipe(
                    str_to_postal_distribution,
                    postal_distribution_to_territory,
                    ),
                ),
            default = 'ignore',
            keep_empty = True,
            ),
        )(params, state = state)
    if errors is not None:
        return data, errors

    categories_slug = set(state.base_categories_slug or [])
    if data.get('category') is not None:
        categories_slug.add(data['category'].slug)
    territory_id = data['territory']._id if data.get('territory') is not None else None
    pois_id = list(ramdb.iter_pois_id(categories_slug = categories_slug, term = data.get('term'),
        territory_id = territory_id))
    pager = pagers.Pager(item_count = len(pois_id))
    pois = [
        ramdb.pois_by_id[poi_id]
        for poi_id in pois_id[pager.first_item_index:pager.last_item_number]
        ]
    return pois_to_geojson(pois, state = state)


def params_to_pois_list_pager(params, state = default_state):
    from . import pagers, ramdb
    data, errors = pipe(
        struct(
            dict(
                category = pipe(
                    str_to_category_slug,
                    function(lambda slug: ramdb.categories_by_slug[slug]),
                    make_test(lambda category: (category.tags_slug or set()).issuperset(state.category_tags_slug or []),
                        error = N_(u'Missing required tags to category')),
                    ),
                page = pipe(
                    str_to_int,
                    make_greater_or_equal(1),
                    default(1),
                    ),
                term = str_to_slug,
                territory = pipe(
                    str_to_postal_distribution,
                    postal_distribution_to_territory,
                    ),
                ),
            default = 'ignore',
            keep_empty = True,
            ),
        rename_item('page', 'page_number'),
        )(params, state = state)
    if errors is not None:
        return data, errors

    categories_slug = set(state.base_categories_slug or [])
    if data.get('category') is not None:
        categories_slug.add(data['category'].slug)
    territory_id = data['territory']._id if data.get('territory') is not None else None
    pois_id = list(ramdb.iter_pois_id(categories_slug = categories_slug, term = data.get('term'),
        territory_id = territory_id))
    pager = pagers.Pager(item_count = len(pois_id), page_number = data['page_number'])
    pager.items = [
        ramdb.pois_by_id[poi_id]
        for poi_id in pois_id[pager.first_item_index:pager.last_item_number]
        ]
    return pager, None


def pois_to_geojson(pois, state = default_state):
    if pois is None:
        return pois, None
    geojson = {
        'type': 'FeatureCollection',
        'properties': {'date': unicode(datetime.datetime.utcnow())},
        'features': [
            {
                'geometry': {
                    'type': 'Point',
                    'coordinates': [poi.geo[1], poi.geo[0]],
                    },
                'type': 'Feature',
                'properties': {
                    'id': str(poi._id),
                    'name': poi.name,
                    },
                }
            for poi in pois
            if poi.geo is not None
            ],
        }
    return geojson, None


def postal_distribution_to_territory(postal_distribution, state = default_state):
    from . import model
    if postal_distribution is None:
        return postal_distribution, None
    found_territories = list(model.Territory.find({
        'main_postal_distribution.postal_code': postal_distribution[0],
        'main_postal_distribution.postal_routing': postal_distribution[1],
        }).limit(2))
    if not found_territories:
        return postal_distribution, state._(u'Unknown territory')
    if len(found_territories) > 1:
        return postal_distribution, state._(u'Ambiguous territory')
    return found_territories[0], None


def str_to_category_slug(value, state = default_state):
    from . import ramdb
    return pipe(
        str_to_slug,
        make_test(lambda slug: slug in ramdb.categories_by_slug, error = N_(u'Invalid category')),
        )(value, state = state)
