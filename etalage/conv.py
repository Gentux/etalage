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
from biryani import states
from territoria2.conv import split_postal_distribution, str_to_postal_distribution


default_state = states.default_state
N_ = lambda message: message


def layer_data_to_clusters(data, state = default_state):
    from . import model, ramdb
    if data is None:
        return None, None
    categories_slug = set(state.base_categories_slug or [])
    if data.get('category') is not None:
        categories_slug.add(data['category'].slug)
    filter = data.get('filter')
    territory = data.get('territory')
    related_territories_id = ramdb.get_territory_related_territories_id(territory) if territory is not None else None
    if filter == 'competence':
        competence_territories_id = related_territories_id
        presence_territory = None
    elif filter == 'presence':
        competence_territories_id = None
        presence_territory = territory
    else:
        competence_territories_id = None
        presence_territory = None
    pois_id_iter = ramdb.iter_pois_id(categories_slug = categories_slug,
        competence_territories_id = competence_territories_id, presence_territory = presence_territory,
        term = data.get('term'))
    pois_by_id = ramdb.pois_by_id
    if data.get('bounding_box') is None:
        pois_iter = (
            poi
            for poi in (
                pois_by_id[poi_id]
                for poi_id in pois_id_iter
                )
            if poi.geo is not None
            )
        if territory is None:
            bottom = None
            left = None
            right = None
            top = None
            pois = []
            for poi in pois_iter:
                poi_latitude = poi.geo[0]
                poi_longitude = poi.geo[1]
                if bottom is None:
                    bottom = poi_latitude
                    left = poi_longitude
                    right = poi_longitude
                    top = poi_latitude
                else:
                    if poi_latitude < bottom:
                        bottom = poi_latitude
                    elif poi_latitude > top:
                        top = poi_latitude
                    if poi_longitude < left:
                        left = poi_longitude
                    elif poi_longitude > right:
                        right = poi_longitude
                pois.append(poi)
        else:
            center_latitude = territory.geo[0]
            center_longitude = territory.geo[1]
            bottom = center_latitude
            left = center_longitude
            right = center_longitude
            top = center_latitude
            distance_and_poi_couples = []
            for poi in pois_iter:
                poi_latitude = poi.geo[0]
                if poi_latitude < bottom:
                    bottom = poi_latitude
                elif poi_latitude > top:
                    top = poi_latitude
                poi_longitude = poi.geo[1]
                if poi_longitude < left:
                    left = poi_longitude
                elif poi_longitude > right:
                    right = poi_longitude
                distance_and_poi_couples.append((
                    # distance from given territory
                    ((poi_latitude - center_latitude) ** 2 + (poi_longitude - center_longitude) ** 2),
                    # POI
                    poi,
                    ))
            distance_and_poi_couples.sort(key = lambda distance_and_poi_couple: distance_and_poi_couple[0])
            pois = [
                poi
                for distance, poi in distance_and_poi_couples
                ]
    else:
        bottom = data['bounding_box']['bottom']
        left = data['bounding_box']['left']
        right = data['bounding_box']['right']
        top = data['bounding_box']['top']
        center_latitude = (bottom + top) / 2.0
        center_longitude = (left + right) / 2.0
        pois_iter = (
            poi
            for poi in (
                pois_by_id[poi_id]
                for poi_id in pois_id_iter
                )
            if poi.geo is not None and bottom <= poi.geo[0] <= top and left <= poi.geo[1] <= right
            )
        distance_and_poi_couples = sorted(
            (
                (
                    # distance from center of map
                    ((poi.geo[0] - center_latitude) ** 2 + (poi.geo[1] - center_longitude) ** 2),
                    # POI
                    poi,
                    )
                for poi in pois_iter
                ),
            key = lambda distance_and_poi_couple: distance_and_poi_couple[0],
            )
        pois = [
            poi
            for distance, poi in distance_and_poi_couples
            ]
    horizontal_iota = (right - left) / 16.0
    vertical_iota = (top - bottom) / 12.0
    clusters = []
    for poi in pois:
        poi_latitude = poi.geo[0]
        poi_longitude = poi.geo[1]
        for cluster in clusters:
            if abs(poi_latitude - cluster.main_latitude) <= vertical_iota \
                    and abs(poi_longitude - cluster.main_longitude) <= horizontal_iota:
                cluster.count += 1
                if poi_latitude < cluster.bottom:
                    cluster.bottom = poi_latitude
                elif poi_latitude > cluster.top:
                    cluster.top = poi_latitude
                if poi_longitude < cluster.left:
                    cluster.left = poi_longitude
                elif poi_longitude > cluster.right:
                    cluster.right = poi_longitude
                break
        else:
            cluster = model.Cluster()
            cluster.count = 1
            cluster.bottom = cluster.top = cluster.main_latitude = poi_latitude
            cluster.left = cluster.right = cluster.main_longitude = poi_longitude
            cluster.main_poi = poi
            clusters.append(cluster)
    return clusters, None


def params_and_clusters_to_geojson((params, clusters), state = default_state):
    if clusters is None:
        return clusters, None

    geojson = {
        'type': 'FeatureCollection',
        'properties': {
            'context': params.get('context'), # Parameter given in request that is returned as is.
            'date': unicode(datetime.datetime.utcnow()),
        },
        'features': [
            {
                'type': 'Feature',
                'bbox': [
                    cluster.left,
                    cluster.bottom,
                    cluster.right,
                    cluster.top,
                    ] if cluster.count > 1 else None,
                'geometry': {
                    'type': 'Point',
                    'coordinates': [cluster.main_longitude, cluster.main_latitude],
                    },
                'properties': {
                    'count': cluster.count,
                    'id': str(cluster.main_poi._id),
                    'name': cluster.main_poi.name,
                    'postalDistribution': cluster.main_poi.postal_distribution_str,
                    'streetAddress': cluster.main_poi.street_address,
                    },
                }
            for cluster in clusters
            ],
        }
    return geojson, None


def params_and_pois_iter_to_csv((params, pois_iter), state = default_state):
    if pois_iter is None:
        return None, None

    columns_label = []
    columns_ref = []
    rows = []
    for poi in pois_iter:
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


def params_to_pois_csv(params, state = default_state):
    from . import ramdb
    data, errors = struct(
        dict(
            category = str_to_slug_to_category,
            filter = str_to_filter,
            term = str_to_slug,
            territory = str_to_postal_distribution_to_geolocated_territory,
            ),
        default = 'ignore',
        keep_empty = True,
        )(params, state = state)
    if errors is not None:
        return data, errors

    categories_slug = set(state.base_categories_slug or [])
    if data.get('category') is not None:
        categories_slug.add(data['category'].slug)
    filter = data.get('filter')
    territory = data.get('territory')
    related_territories_id = ramdb.get_territory_related_territories_id(territory) if territory is not None else None
    if filter == 'competence':
        competence_territories_id = related_territories_id
        presence_territory = None
    elif filter == 'presence':
        competence_territories_id = None
        presence_territory = territory
    else:
        competence_territories_id = None
        presence_territory = None
    pois_id = list(ramdb.iter_pois_id(categories_slug = categories_slug,
        competence_territories_id = competence_territories_id, presence_territory = presence_territory,
        term = data.get('term')))
    if not pois_id:
        return None, None
    pois_iter = (
        ramdb.pois_by_id[poi_id]
        for poi_id in pois_id
        )
    return params_and_pois_iter_to_csv((params, pois_iter), state = state)


def params_to_pois_directory_data(params, state = default_state):
    from . import model, ramdb
    return struct(
        dict(
            category = str_to_slug_to_category,
            filter = str_to_filter,
            term = str_to_slug,
            territory = pipe(
                str_to_postal_distribution_to_geolocated_territory,
                test(lambda territory: territory.__class__.__name__ in model.communes_kinds,
                    error = N_(u'In "directory" mode, territory must be a commune')),
                test_exists(error = N_(u'In "directory" mode, a commune is required')),
                ),
            ),
        default = 'ignore',
        keep_empty = True,
        )(params, state = state)


def params_to_pois_layer_data(params, state = default_state):
    from . import ramdb
    return pipe(
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
                category = str_to_slug_to_category,
                filter = str_to_filter,
                page = pipe(
                    str_to_int,
                    test_greater_or_equal(1),
                    default(1),
                    ),
                term = str_to_slug,
                territory = str_to_postal_distribution_to_geolocated_territory,
                ),
            default = 'ignore',
            keep_empty = True,
            ),
        rename_item('bbox', 'bounding_box'),
        rename_item('page', 'page_number'),
        )(params, state = state)


def params_to_pois_list_data(params, state = default_state):
    from . import ramdb
    return pipe(
        struct(
            dict(
                category = str_to_slug_to_category,
                filter = str_to_filter,
                page = pipe(
                    str_to_int,
                    test_greater_or_equal(1),
                    default(1),
                    ),
                term = str_to_slug,
                territory = str_to_postal_distribution_to_geolocated_territory,
                ),
            default = 'ignore',
            keep_empty = True,
            ),
        rename_item('page', 'page_number'),
        )(params, state = state)


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


str_to_filter = pipe(
    str_to_slug,
    test_in(['competence', 'presence']),
    )


str_to_postal_distribution_to_geolocated_territory = pipe(
    str_to_postal_distribution,
    postal_distribution_to_territory,
    test(lambda territory: territory.geo is not None, error = N_(u'Territory has no geographical coordinates')),
    )


def str_to_slug_to_category(value, state = default_state):
    from . import ramdb
    return pipe(
        str_to_category_slug,
        function(lambda slug: ramdb.categories_by_slug[slug]),
        test(lambda category: (category.tags_slug or set()).issuperset(state.category_tags_slug or []),
            error = N_(u'Missing required tags for category')),
        )(value, state = state)

