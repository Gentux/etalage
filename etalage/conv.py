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


from cStringIO import StringIO
import csv
import datetime
import itertools

from biryani.baseconv import *
from biryani.bsonconv import *
from biryani.objectconv import *
from biryani.frconv import *
from biryani import states, strings
from territoria2.conv import split_postal_distribution, str_to_postal_distribution


default_state = states.default_state
N_ = lambda message: message


def params_to_pois_csv(params, state = default_state):
    from . import ramdb
    data, errors = struct(
        dict(
            category = pipe(
                str_to_category_slug,
                function(lambda slug: ramdb.categories_by_slug[slug]),
                test(lambda category: (category.tags_slug or set()).issuperset(state.category_tags_slug or []),
                    error = N_(u'Missing required tags for category')),
                ),
            term = str_to_slug,
            territory = pipe(
                str_to_postal_distribution,
                postal_distribution_to_territory,
                ),
            ),
        default = 'ignore',
        keep_empty = True,
        )(params, state = state)
    if errors is not None:
        return data, errors

    categories_slug = set(state.base_categories_slug or [])
    if data.get('category') is not None:
        categories_slug.add(data['category'].slug)
    territory_id = data['territory']._id if data.get('territory') is not None else None
    pois_id = list(ramdb.iter_pois_id(categories_slug = categories_slug, term = data.get('term'),
        territory_id = territory_id))
    pois = [
        ramdb.pois_by_id[poi_id]
        for poi_id in pois_id
        ]
    return pois_to_csv(pois, state = state)


def params_to_pois_directory_data(params, state = default_state):
    from . import model, ramdb
    return pipe(
        struct(
            dict(
                category = pipe(
                    str_to_category_slug,
                    function(lambda slug: ramdb.categories_by_slug[slug]),
                    test(lambda category: (category.tags_slug or set()).issuperset(state.category_tags_slug or []),
                        error = N_(u'Missing required tags for category')),
                    ),
                term = str_to_slug,
                territory = pipe(
                    str_to_postal_distribution,
                    postal_distribution_to_territory,
                    test(lambda territory: territory.__class__.__name__ in model.communes_kinds,
                        error = N_(u'In "directory" mode, territory must be a commune')),
                    test(lambda territory: territory.geo is not None,
                        error = N_(u'In "directory" mode, commune must have geographical coordinates')),
                    test_exists(error = N_(u'In "directory" mode, a commune is required')),
                    ),
                ),
            default = 'ignore',
            keep_empty = True,
            ),
        )(params, state = state)


def params_to_pois_geojson(params, state = default_state):
    from . import ramdb
    data, errors = pipe(
        struct(
            dict(
                bbox = pipe(
                    function(lambda bounding_box: bounding_box.split(u',')),
                    struct(
                        [
                            # West longitude
                            pipe(
                                str_to_float,
                                test_between(-180, 180),
                                exists,
                                ),
                            # South latitude
                            pipe(
                                str_to_float,
                                test_between(-90, 90),
                                exists,
                                ),
                            # East longitude
                            pipe(
                                str_to_float,
                                test_between(-180, 180),
                                exists,
                                ),
                            # North latitude
                            pipe(
                                str_to_float,
                                test_between(-90, 90),
                                exists,
                                ),
                            ],
                        ),
                    function(lambda bounding_box: dict(
                        bottom = bounding_box[1],
                        left = bounding_box[0],
                        right = bounding_box[2],
                        top = bounding_box[3],
                        )),
                    ),
                category = pipe(
                    str_to_category_slug,
                    function(lambda slug: ramdb.categories_by_slug[slug]),
                    test(lambda category: (category.tags_slug or set()).issuperset(state.category_tags_slug or []),
                        error = N_(u'Missing required tags for category')),
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
        rename_item('bbox', 'bounding_box'),
        )(params, state = state)
    if errors is not None:
        return data, errors

    categories_slug = set(state.base_categories_slug or [])
    if data.get('category') is not None:
        categories_slug.add(data['category'].slug)
    territory_id = data['territory']._id if data.get('territory') is not None else None
    pois_id_iter = ramdb.iter_pois_id(categories_slug = categories_slug,
        term = data.get('term'), territory_id = territory_id)
    pois_by_id = ramdb.pois_by_id
    if data.get('bounding_box') is None:
        pois_iter = itertools.islice(
            (
                poi
                for poi in (
                    pois_by_id[poi_id]
                    for poi_id in pois_id_iter
                    )
                if poi.geo is not None
                ),
            20) # TODO
    else:
        bottom = data['bounding_box']['bottom']
        left = data['bounding_box']['left']
        right = data['bounding_box']['right']
        top = data['bounding_box']['top']
        pois_iter = itertools.islice(
            (
                poi
                for poi in (
                    pois_by_id[poi_id]
                    for poi_id in pois_id_iter
                    )
                if poi.geo is not None and bottom <= poi.geo[0] <= top and left <= poi.geo[1] <= right
                ),
            20) # TODO
    geojson = {
        'type': 'FeatureCollection',
        'properties': {
            'context': params.get('context'), # Parameter given in request that is returned as is.
            'date': unicode(datetime.datetime.utcnow())
        },
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
                    'postal_distribution': poi.postal_distribution_str,
                    'street_address': poi.street_address,
                    },
                }
            for poi in pois_iter
            ],
        }
    return geojson, None


def params_to_pois_list_pager(params, state = default_state):
    from . import pagers, ramdb
    data, errors = pipe(
        struct(
            dict(
                category = pipe(
                    str_to_category_slug,
                    function(lambda slug: ramdb.categories_by_slug[slug]),
                    test(lambda category: (category.tags_slug or set()).issuperset(state.category_tags_slug or []),
                        error = N_(u'Missing required tags for category')),
                    ),
                page = pipe(
                    str_to_int,
                    test_greater_or_equal(1),
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


def pois_to_csv(pois, state = default_state):
    if not pois:
        return None, None

    columns_label = []
    columns_ref = []
    rows = []
    for poi in pois:
        columns_index = {}
        row = [None] * len(columns_ref)
        for field_ref, field in poi.iter_csv_fields(state):
            # Detect column number to use for field. Create a new column if needed.
            column_ref = tuple(field_ref[:-1])
            same_ref_columns_count = field_ref[-1]
            if columns_ref.count(column_ref) == same_ref_columns_count:
                column_index = len(columns_ref)
                columns_label.append(field.label) # or u' - '.join(label for label in field_ref[::2])
                columns_ref.append(column_ref)
                row.append(None)
            else:
                column_index = columns_ref.index(column_ref, columns_index.get(column_ref, -1) + 1)
            columns_index[column_ref] = column_index
            row[column_index] = unicode(field.value).encode('utf-8')
        rows.append(row)

    csv_file = StringIO()
    writer = csv.writer(csv_file, delimiter = ',', quotechar = '"', quoting = csv.QUOTE_MINIMAL)
    writer.writerow([label.encode("utf-8") for label in columns_label])
    for row in rows:
        writer.writerow(row)
    return csv_file.getvalue().decode('utf-8'), None


def postal_distribution_to_territory(postal_distribution, state = default_state):
    from . import ramdb
    if postal_distribution is None:
        return postal_distribution, None
    territory_id = ramdb.territories_id_by_postal_distribution.get(postal_distribution)
    if territory_id is None:
        return postal_distribution, state._(u'Unknown territory')
    territory = ramdb.territories_by_id.get(territory_id)
    if territory is None:
        return postal_distribution, state._(u'Unknown territory')
    return territory, None


def str_to_category_slug(value, state = default_state):
    from . import ramdb
    return pipe(
        str_to_slug,
        test(lambda slug: slug in ramdb.categories_by_slug, error = N_(u'Invalid category')),
        )(value, state = state)

