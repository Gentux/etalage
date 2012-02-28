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


"""Conversion functions"""


from cStringIO import StringIO
import csv
import math

from biryani.baseconv import *
from biryani.bsonconv import *
from biryani.objectconv import *
from biryani.frconv import *
from biryani import states, strings
import bson
import xlwt
from territoria2.conv import split_postal_distribution, str_to_postal_distribution


default_state = states.default_state
N_ = lambda message: message


def csv_infos_to_csv_bytes(csv_infos_by_schema_name, state = default_state):
    from . import ramdb
    if csv_infos_by_schema_name is None:
        return None, None
    csv_bytes_by_name = {}
    for schema_name, csv_infos in csv_infos_by_schema_name.iteritems():
        csv_file = StringIO()
        writer = csv.writer(csv_file, delimiter = ',', quotechar = '"', quoting = csv.QUOTE_MINIMAL)
        writer.writerow([
            label.encode("utf-8")
            for label in csv_infos['columns_label']
            ])
        for row in csv_infos['rows']:
            writer.writerow([
                unicode(cell).encode('utf-8') if cell is not None else None
                for cell in row
                ])
        csv_filename = '{0}.csv'.format(strings.slugify(ramdb.schemas_title_by_name.get(schema_name, schema_name)))
        csv_bytes_by_name[csv_filename] = csv_file.getvalue()
    return csv_bytes_by_name or None, None


def csv_infos_to_excel_bytes(csv_infos_by_schema_name, state = default_state):
    from . import ramdb
    if csv_infos_by_schema_name is None:
        return None, None
    book = xlwt.Workbook(encoding = 'utf-8')
    for schema_name, csv_infos in csv_infos_by_schema_name.iteritems():
        sheet = book.add_sheet(ramdb.schemas_title_by_name.get(schema_name, schema_name)[:31])
        sheet_row = sheet.row(0)
        for column_index, label in enumerate(csv_infos['columns_label']):
            sheet_row.write(column_index, label)
        for row_index, row in enumerate(csv_infos['rows'], 1):
            if row_index % 1000 == 0:
                sheet.flush_row_data()
            sheet_row = sheet.row(row_index)
            for column_index, cell in enumerate(row):
                if cell is not None:
                    sheet_row.write(column_index,
                        unicode(cell) if isinstance(cell, bson.objectid.ObjectId) else cell,
                        )
        sheet.flush_row_data()
    excel_file = StringIO()
    book.save(excel_file)
    return excel_file.getvalue(), None


def default_pois_layer_data_bbox(data, state = default_state):
    """Compute bounding box and add it when it is missing from data. Return modified data."""
    from . import ramdb
    if data is None:
        return data, None
    if data['bbox'] is not None:
        return data, None
    data = data.copy()
    categories_slug = set(state.base_categories_slug or [])
    if data['categories'] is not None:
        categories_slug.update(
            category.slug
            for category in data['categories']
            )
    filter = data['filter']
    territory = data['territory']
    pois_by_id = ramdb.pois_by_id
    if territory is None:
        competence_territories_id = None
        presence_territory = None
        pois_id_iter = ramdb.iter_pois_id(categories_slug = categories_slug,
            competence_territories_id = competence_territories_id, presence_territory = presence_territory,
            term = data['term'])
        pois = [
            poi
            for poi in (
                pois_by_id[poi_id]
                for poi_id in pois_id_iter
                )
            if poi.geo is not None
            ]
        if not pois:
            data['bbox'] = [-180.0, -90.0, 180.0, 90.0]
            return data, None
        bottom = top = pois[0].geo[0]
        left = right = pois[0].geo[1]
    else:
        center_latitude = territory.geo[0]
        center_longitude = territory.geo[1]
        bottom = center_latitude
        left = center_longitude
        right = center_longitude
        top = center_latitude
        if filter == 'competence':
            competence_territories_id = ramdb.get_territory_related_territories_id(territory)
            presence_territory = None
            pois_id_iter = ramdb.iter_pois_id(categories_slug = categories_slug,
                competence_territories_id = competence_territories_id, presence_territory = presence_territory,
                term = data['term'])
            pois = [
                poi
                for poi in (
                    pois_by_id[poi_id]
                    for poi_id in pois_id_iter
                    )
                if poi.geo is not None
                ]
        elif filter == 'presence':
            competence_territories_id = None
            presence_territory = territory
            pois_id_iter = ramdb.iter_pois_id(categories_slug = categories_slug,
                competence_territories_id = competence_territories_id, presence_territory = presence_territory,
                term = data['term'])
            pois = [
                poi
                for poi in (
                    pois_by_id[poi_id]
                    for poi_id in pois_id_iter
                    )
                if poi.geo is not None
                ]
        else:
            # When no filter is given, use the bounding box of the territory (ie the bounding box enclosing every POI
            # present in the territory).
            competence_territories_id = None
            presence_territory = territory
            pois_id_iter = ramdb.iter_pois_id(categories_slug = categories_slug,
                competence_territories_id = competence_territories_id, presence_territory = presence_territory,
                term = data['term'])
            pois = [
                poi
                for poi in (
                    pois_by_id[poi_id]
                    for poi_id in pois_id_iter
                    )
                if poi.geo is not None
                ]
            if not pois:
                # When no POI has been found in territory, use the bounding box enclosing every competent POI.
                competence_territories_id = ramdb.get_territory_related_territories_id(territory)
                presence_territory = None
                pois_id_iter = ramdb.iter_pois_id(categories_slug = categories_slug,
                    competence_territories_id = competence_territories_id, presence_territory = presence_territory,
                    term = data['term'])
                pois = [
                    poi
                    for poi in (
                        pois_by_id[poi_id]
                        for poi_id in pois_id_iter
                        )
                    if poi.geo is not None
                    ]
                if not pois:
                    # When no present nor competent POI has been found, compute bounding box using given distance.
                    delta = math.degrees(state.distance / 6372.8)
                    data['bbox'] = [
                        center_longitude - delta, # left
                        center_latitude - delta, # bottom
                        center_longitude + delta, # left
                        center_latitude + delta, # top
                        ]
                    return data, None
    for poi in pois:
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
    data['bbox'] = [left, bottom, right, top]
    return data, None


def id_name_dict_list_to_ignored_fields(value, state = default_state):
    if not value:
        return None, None
    ignored_fields = {}
    for id_name_dict in value:
        id = id_name_dict['id']
        name = id_name_dict.get('name')
        if id in ignored_fields:
            ignored_field = ignored_fields[id]
            if ignored_field is not None:
                ignored_field.add(name)
        else:
            if name is None:
                ignored_fields[id] = None
            else:
                ignored_fields[id] = set([name])
    return ignored_fields, None


def id_to_poi(poi_id, state = default_state):
    import ramdb
    if poi_id is None:
        return poi_id, None
    poi = ramdb.pois_by_id.get(poi_id)
    if poi is None:
        return poi_id, state._("POI {0} doesn't exist").format(poi_id)
    return poi, None


def layer_data_to_clusters(data, state = default_state):
    from . import model, ramdb
    if data is None:
        return None, None
    left, bottom, right, top = data['bbox']
    center_latitude = (bottom + top) / 2.0
    center_latitude_cos = math.cos(math.radians(center_latitude))
    center_latitude_sin = math.sin(math.radians(center_latitude))
    center_longitude = (left + right) / 2.0
    categories_slug = set(state.base_categories_slug or [])
    if data['categories'] is not None:
        categories_slug.update(
            category.slug
            for category in data['categories']
            )
    filter = data['filter']
    territory = data['territory']
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
        term = data['term'])
    pois_by_id = ramdb.pois_by_id
    current = data['current']
    pois_iter = (
        poi
        for poi in (
            pois_by_id[poi_id]
            for poi_id in pois_id_iter
            )
        if poi.geo is not None and bottom <= poi.geo[0] <= top and left <= poi.geo[1] <= right and (
            current is None or poi._id != current._id)
        )
    distance_and_poi_couples = sorted(
        (
            (
                # distance from center of map
                6372.8 * math.acos(
                    math.sin(math.radians(poi.geo[0])) * center_latitude_sin
                    + math.cos(math.radians(poi.geo[0])) * center_latitude_cos
                        * math.cos(math.radians(poi.geo[1] - center_longitude))
                    ),
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
    if current is not None:
        pois.insert(0, current)
    horizontal_iota = (right - left) / 20.0
    vertical_iota = (top - bottom) / 15.0
#    vertical_iota = horizontal_iota = (right - left) / 30.0
    clusters = []
    for poi in pois:
        poi_latitude = poi.geo[0]
        poi_longitude = poi.geo[1]
        for cluster in clusters:
            if abs(poi_latitude - cluster.center_latitude) <= vertical_iota \
                    and abs(poi_longitude - cluster.center_longitude) <= horizontal_iota:
                cluster.count += 1
                if poi_latitude == cluster.center_latitude and poi_longitude == cluster.center_longitude:
                    cluster.center_pois.append(poi)
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
            cluster.competent = False # changed below
            cluster.count = 1
            cluster.bottom = cluster.top = cluster.center_latitude = poi_latitude
            cluster.left = cluster.right = cluster.center_longitude = poi_longitude
            cluster.center_pois = [poi]
            clusters.append(cluster)
        if cluster.competent is False:
            if related_territories_id is None or poi.competence_territories_id is None:
                cluster.competent = None
            elif not related_territories_id.isdisjoint(poi.competence_territories_id):
                cluster.competent = True
        elif cluster.competent is None and related_territories_id is not None \
                and poi.competence_territories_id is not None \
                and not related_territories_id.isdisjoint(poi.competence_territories_id):
            cluster.competent = True
    return clusters, None


def params_to_pois_csv_infos(params, state = default_state):
    from . import ramdb
    data, errors = pipe(
        rename_item('category', 'categories'), # Must be renamed before struct, to be able to use categories on errors
        struct(
            dict(
                categories = uniform_sequence(str_to_slug_to_category),
                filter = pipe(
                    str_to_filter,
                    default('presence'), # By default, export only POIs present on given territory.
                    ),
                term = str_to_slug,
                territory = str_to_postal_distribution_to_geolocated_territory,
                ),
            default = 'ignore',
            keep_missing_values = True,
            ),
        )(params, state = state)
    if errors is not None:
        return data, errors

    categories_slug = set(state.base_categories_slug or [])
    if data['categories'] is not None:
        categories_slug.update(
            category.slug
            for category in data['categories']
            )
    filter = data['filter']
    territory = data['territory']
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
    if data['categories'] is None and data['term'] is None and data['territory'] is None:
        # No criteria specified => Export every POI, even non indexed ones.
        pois_id = list(ramdb.pois_by_id.iterkeys())
    else:
        pois_id = list(ramdb.iter_pois_id(categories_slug = categories_slug,
            competence_territories_id = competence_territories_id, presence_territory = presence_territory,
            term = data['term']))
    return pois_id_to_csv_infos(pois_id, state = state)


def params_to_pois_directory_data(params, state = default_state):
    from . import model
    return pipe(
        rename_item('category', 'categories'), # Must be renamed before struct, to be able to use categories on errors
        struct(
            dict(
                categories = uniform_sequence(str_to_slug_to_category),
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
            keep_missing_values = True,
            ),
        )(params, state = state)


def params_to_pois_layer_data(params, state = default_state):
    return pipe(
        rename_item('category', 'categories'), # Must be renamed before struct, to be able to use categories on errors
        struct(
            dict(
                bbox = pipe(
                    function(lambda bbox: bbox.split(u',')),
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
                    ),
                categories = uniform_sequence(str_to_slug_to_category),
                current = pipe(
                    str_to_object_id,
                    id_to_poi,
                    test(lambda poi: poi.geo is not None, error = N_('POI has no geographical coordinates')),
                    ),
                filter = str_to_filter,
                term = str_to_slug,
                territory = str_to_postal_distribution_to_geolocated_territory,
                ),
            default = 'ignore',
            keep_missing_values = True,
            ),
        )(params, state = state)


def params_to_pois_list_data(params, state = default_state):
    return pipe(
        rename_item('category', 'categories'), # Must be renamed before struct, to be able to use categories on errors
        struct(
            dict(
                categories = uniform_sequence(str_to_slug_to_category),
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
            keep_missing_values = True,
            ),
        rename_item('page', 'page_number'),
        )(params, state = state)


def pois_id_to_csv_infos(pois_id, state = default_state):
    from . import ramdb
    if pois_id is None:
        return None, None

    csv_infos_by_schema_name = {}
    visited_pois_id = set(pois_id)
    while pois_id:
        remaining_pois_id = []
        for poi_id in pois_id:
            poi = ramdb.pois_by_id.get(poi_id)
            if poi is None:
                continue
            csv_infos = csv_infos_by_schema_name.get(poi.schema_name)
            if csv_infos is None:
                csv_infos_by_schema_name[poi.schema_name] = csv_infos = dict(
                    columns_label = [],
                    columns_ref = [],
                    rows = [],
                    )
            columns_label = csv_infos['columns_label']
            columns_index = {}
            columns_ref = csv_infos['columns_ref']
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
                row[column_index] = field.value
                for linked_poi_id in (field.linked_pois_id or []):
                    if linked_poi_id not in visited_pois_id:
                        visited_pois_id.add(linked_poi_id)
                        remaining_pois_id.append(linked_poi_id)
            csv_infos['rows'].append(row)
        pois_id = remaining_pois_id
    return csv_infos_by_schema_name or None, None


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

