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


"""Objects for POIs"""


from copy import copy
import datetime
import itertools
import logging
import math
import sys
import urlparse
import urllib

import bson
from biryani import strings
from suq import representations
import webob.multidict

from . import conf, conv, ramdb, urls


__all__ = ['Cluster', 'Field', 'get_first_field', 'iter_fields', 'Poi', 'pop_first_field']

log = logging.getLogger(__name__)


class Cluster(representations.UserRepresentable):
    bottom = None  # South latitude of rectangle enclosing all POIs of cluster
    center_latitude = None  # Copy of center_pois[*].geo[0] for quick access
    center_longitude = None  # Copy of center_pois[*].geo[1] for quick access
    center_pois = None  # POIs at the center of cluster, sharing the same coordinates
     # False = Not competent for current territory, None = Competent for any territory or unknown territory,
     # True = Competent for current territory
    competent = False
    count = None  # Number of POIs in cluster
    left = None  # West longitude of rectangle enclosing all POIs of cluster
    right = None  # East longitude of rectangle enclosing all POIs of cluster
    top = None  # North latitude of rectangle enclosing all POIs of cluster


class Field(representations.UserRepresentable):
    id = None  # Petitpois id = format of value
    kind = None
    label = None
    relation = None
    type = None
    value = None

    def __init__(self, **attributes):
        if attributes:
            self.set_attributes(**attributes)

    def get_first_field(self, id, label = None):
        # Note: Only for composite fields.
        return get_first_field(self.value, id, label = label)

    @property
    def is_composite(self):
        return self.id in ('adr', 'date-range', 'source')

    def iter_csv_fields(self, ctx, counts_by_label, parent_ref = None):
        """Iter fields, entering inside composite fields."""
        if self.value is not None:
            if self.is_composite:
                same_label_index = counts_by_label.get(self.label, 0)
                ref = (parent_ref or []) + [self.label, same_label_index]
                field_counts_by_label = {}
                for field in self.value:
                    for subfield_ref, subfield in field.iter_csv_fields(ctx, field_counts_by_label,
                            parent_ref = ref):
                        yield subfield_ref, subfield
                if field_counts_by_label:
                    # Some subfields were not empty, so increment number of exported fields having the same label.
                    counts_by_label[self.label] = same_label_index + 1
            elif self.id in ('autocompleters', 'checkboxes'):
                field_attributes = self.__dict__.copy()
                field_attributes['value'] = u'\n'.join(self.value)
                field = Field(**field_attributes)
                same_label_index = counts_by_label.get(field.label, 0)
                yield (parent_ref or []) + [field.label, same_label_index], field
                counts_by_label[field.label] = same_label_index + 1
            elif self.id == 'commune':
                field_attributes = self.__dict__.copy()
                field_attributes['label'] = u'Code Insee commune'  # Better than "Commune"
                field = Field(**field_attributes)
                same_label_index = counts_by_label.get(field.label, 0)
                yield (parent_ref or []) + [field.label, same_label_index], field
                counts_by_label[field.label] = same_label_index + 1
            elif self.id == 'geo':
                for field in (
                        Field(id = 'float', value = self.value[0], label = u'Latitude'),
                        Field(id = 'float', value = self.value[1], label = u'Longitude'),
                        Field(id = 'int', value = self.value[2], label = u'Précision'),
                        ):
                    for subfield_ref, subfield in field.iter_csv_fields(ctx, counts_by_label, parent_ref = parent_ref):
                        yield subfield_ref, subfield
            elif self.id == 'links':
                field_attributes = self.__dict__.copy()
                field_attributes['value'] = u'\n'.join(
                    unicode(object_id)
                    for object_id in self.value
                    )
                field = Field(**field_attributes)
                same_label_index = counts_by_label.get(field.label, 0)
                yield (parent_ref or []) + [field.label, same_label_index], field
                counts_by_label[field.label] = same_label_index + 1
            elif self.id == 'poi-last-update':
                last_update_field = copy(self)
                last_update_field.value = last_update_field.value.strftime('%d/%m/%Y')
                last_update_label_index = counts_by_label.get(self.label, 0)
                yield (parent_ref or []) + [self.label, last_update_label_index], last_update_field
                counts_by_label[self.label] = last_update_label_index + 1
            elif self.id == 'postal-distribution':
                postal_code, postal_routing = conv.check(conv.split_postal_distribution)(self.value, state = ctx)
                for field in (
                        Field(id = 'postal-code', value = postal_code, label = u'Code postal'),
                        Field(id = 'postal-routing', value = postal_routing, label = u'Localité'),
                        ):
                    for subfield_ref, subfield in field.iter_csv_fields(ctx, counts_by_label, parent_ref = parent_ref):
                        yield subfield_ref, subfield
            elif self.id == 'street-address':
                for item_value in self.value.split('\n'):
                    item_value = item_value.strip()
                    item_field_attributes = self.__dict__.copy()
                    item_field_attributes['id'] = 'street-address-lines'  # Change ID to avoid infinite recursion.
                    # item_field_attributes['label'] = u'Adresse'  # Better than "N° et libellé de voie"?
                    item_field_attributes['value'] = item_value
                    item_field = Field(**item_field_attributes)
                    for subfield_ref, subfield in item_field.iter_csv_fields(ctx, counts_by_label,
                            parent_ref = parent_ref):
                        yield subfield_ref, subfield
            elif self.id == 'territories':
                territories = [
                    territory
                    for territory in (
                        ramdb.territory_by_id.get(territory_id)
                        for territory_id in self.value
                        )
                    if territory is not None
                    ]
                if territories:
                    field_attributes = self.__dict__.copy()
                    field_attributes['value'] = u'\n'.join(
                        territory.main_postal_distribution_str
                        for territory in territories
                        )
                    field = Field(**field_attributes)
                    same_label_index = counts_by_label.get(field.label, 0)
                    yield (parent_ref or []) + [field.label, same_label_index], field
                    counts_by_label[field.label] = same_label_index + 1
            elif self.id == 'territory':
                territory = ramdb.territory_by_id.get(self.value)
                if territory is not None:
                    field_attributes = self.__dict__.copy()
                    field_attributes['value'] = territory.main_postal_distribution_str
                    field = Field(**field_attributes)
                    same_label_index = counts_by_label.get(field.label, 0)
                    yield (parent_ref or []) + [field.label, same_label_index], field
                    counts_by_label[field.label] = same_label_index + 1
            elif isinstance(self.value, list):
                for item_value in self.value:
                    item_field_attributes = self.__dict__.copy()
                    item_field_attributes['value'] = item_value
                    item_field = Field(**item_field_attributes)
                    for subfield_ref, subfield in item_field.iter_csv_fields(ctx, counts_by_label,
                            parent_ref = parent_ref):
                        yield subfield_ref, subfield
            else:
                # Note: self.value is now always a single value, not a list.
                same_label_index = counts_by_label.get(self.label, 0)
                yield (parent_ref or []) + [self.label, same_label_index], self
                counts_by_label[self.label] = same_label_index + 1

    @property
    def linked_pois_id(self):
        if self.id not in ('link', 'links'):
            return None
        if self.value is None:
            return None
        if isinstance(self.value, list):
            return self.value
        if isinstance(self.value, basestring):
            # When field is a CSV field, links are a linefeed-separated list of IDs
            return [
                bson.objectid.ObjectId(id_str)
                for id_str in self.value.split()
                ]
        return [self.value]

    @classmethod
    def load(cls, id, metadata, value):
        if len(metadata) != (1 if 'kind' in metadata else 0) \
                + (1 if 'label' in metadata else 0) \
                + (1 if 'relation' in metadata else 0) \
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
                fields.append(cls.load(field_id, field_metadata, field_value))
            value = fields or None
        elif id == 'territories':
            # Replace each kind-code with the corresponding territory ID.
            if value is not None:
                value = [
                    territory_id
                    for territory_id in (
                        ramdb.territory_id_by_kind_code.get((territory_kind_code['kind'],
                            territory_kind_code['code']))
                        for territory_kind_code in value
                        )
                    if territory_id is not None
                    ]
        return cls(
            id = id,
            kind = metadata.get('kind'),
            label = metadata['label'],
            relation = metadata.get('relation'),
            type = metadata.get('type'),
            value = value,
            )

    def set_attributes(self, **attributes):
        """Set given attributes and return a boolean stating whether existing attributes have changed."""
        changed = False
        for name, value in attributes.iteritems():
            if value is getattr(self.__class__, name, UnboundLocalError):
                if value is not getattr(self, name, UnboundLocalError):
                    delattr(self, name)
                    changed = True
            elif value is not getattr(self, name, UnboundLocalError):
                setattr(self, name, value)
                changed = True
        return changed


class Poi(representations.UserRepresentable):
    _id = None
    # IDs of territories for which POI is fully competent. None when POI has no notion of competence territory
    competence_territories_id = None
    fields = None
    geo = None
    ids_by_category_slug = {}
    ids_by_competence_territory_id = {}
    ids_by_begin_datetime = []
    ids_by_end_datetime = []
    ids_by_last_update_datetime = []
    ids_by_parent_id = {}  # class attribute
    ids_by_presence_territory_id = {}
    ids_by_word = {}
    indexed_ids = set()
    instance_by_id = {}
    last_update_datetime = None
    last_update_organization = None
    name = None
    parent_id = None
    petitpois_url = None  # class attribute defined in subclass. URL of Petitpois site
    postal_distribution_str = None
    schema_name = None
    slug_by_id = {}
    street_address = None
    subclass_by_database_and_schema_name = {}
    theme_slug = None

    def __init__(self, **attributes):
        if attributes:
            self.set_attributes(**attributes)

    @classmethod
    def clear_indexes(cls):
        cls.indexed_ids.clear()
        cls.instance_by_id.clear()
        cls.ids_by_parent_id.clear()
        cls.ids_by_category_slug.clear()
        cls.ids_by_competence_territory_id.clear()
        cls.ids_by_presence_territory_id.clear()
        cls.ids_by_word.clear()
        cls.slug_by_id.clear()
        cls.subclass_by_database_and_schema_name.clear()

    @classmethod
    def extract_non_territorial_search_data(cls, ctx, data):
        return dict(
            categories_slug = data['categories_slug'],
            term = data['term'],
            )

    @classmethod
    def extract_search_inputs_from_params(cls, ctx, params):
        return dict(
            categories_slug = params.getall('category'),
            term = params.get('term'),
            territory = params.get('territory'),
            )

    def generate_all_fields(self):
        """Return all fields of POI including dynamic ones (ie linked fields, etc)."""
        fields = self.fields[:] if self.fields is not None else []

        # Add children POIs as linked fields.
        children = sorted(
            (
                self.instance_by_id[child_id]
                for child_id in self.ids_by_parent_id.get(self._id, set())
                ),
            key = lambda child: (child.schema_name, child.name),
            )
        for child in children:
            fields.append(Field(id = 'link', label = ramdb.schema_title_by_name[child.schema_name],
                value = child._id))

        # Add last-update field.
        fields.append(Field(id = 'last-update', label = u"Dernière mise à jour", value = u' par '.join(
            unicode(fragment)
            for fragment in (
                self.last_update_datetime.strftime('%Y-%m-%d %H:%M') if self.last_update_datetime is not None else None,
                self.last_update_organization,
                )
            if fragment
            )))

        return fields

    def get_first_field(self, id, label = None):
        return get_first_field(self.fields, id, label = label)

    def get_full_url(self, ctx, params_prefix = 'cmq_'):
        if ctx.container_base_url is None:
            return urls.get_full_url(ctx, 'organismes', self.slug, self._id)
        else:
            parsed_container_base_url = urlparse.urlparse(ctx.container_base_url)
            params = dict([
                ('{0}path'.format(params_prefix), urls.get_url(ctx, 'organismes', self.slug, self._id))
                ])
            params.update(dict(urlparse.parse_qsl(parsed_container_base_url.query)))
            return urlparse.urljoin(
                '{0}://{1}{2}'.format(
                    parsed_container_base_url.scheme,
                    parsed_container_base_url.netloc,
                    parsed_container_base_url.path
                    ),
                '?{0}#{0}'.format(urllib.urlencode(params)),
                )

    @classmethod
    def get_search_params_name(cls, ctx):
        return set(
            cls.rename_input_to_param(name)
            for name in cls.extract_search_inputs_from_params(ctx, webob.multidict.MultiDict()).iterkeys()
            )

    @classmethod
    def get_visibility_params_names(cls, ctx):
        visibility_params = list(cls.get_search_params_name(ctx))
        visibility_params.extend(['checkboxes', 'directory', 'export', 'gadget', 'legend', 'list', 'map', 'minisite'])
        return [
            'hide_{0}'.format(visibility_param)
            for visibility_param in visibility_params
            ]

    def index(self, indexed_poi_id):
        poi_bson = self.bson
        metadata = poi_bson['metadata']
        for category_slug in (metadata.get('categories-index') or set()):
            self.ids_by_category_slug.setdefault(category_slug, set()).add(indexed_poi_id)

        if conf['index.date.field']:
            for date_range_index, date_range_metadata in enumerate(metadata.get('date-range') or []):
                if date_range_metadata['label'] == conf['index.date.field']:
                    date_range_values = poi_bson['date-range'][date_range_index]
                    date_range_begin = date_range_values.get('date-range-begin', [None])[0]
                    date_range_end = date_range_values.get('date-range-end', [None])[0]

                    if date_range_begin is not None:
                        for index, (begin_datetime, poi_id) in enumerate(self.ids_by_begin_datetime):
                            if begin_datetime is not None and begin_datetime > date_range_begin:
                                break
                    else:
                        index = 0
                    self.ids_by_begin_datetime.insert(index, (date_range_begin, indexed_poi_id))
                    if date_range_end is not None:
                        for index, (end_datetime, poi_id) in enumerate(self.ids_by_end_datetime):
                            if end_datetime is not None and end_datetime < date_range_end:
                                break
                    else:
                        index = 0
                    self.ids_by_end_datetime.insert(index, (date_range_end, indexed_poi_id))

            if not metadata.get('date-range'):
                self.ids_by_begin_datetime.append((None, indexed_poi_id))
                self.ids_by_end_datetime.append((None, indexed_poi_id))
        self.ids_by_last_update_datetime.append((self.last_update_datetime, indexed_poi_id))

        for i, territory_metadata in enumerate(metadata.get('territories') or []):
            # Note: Don't fail when territory doesn't exist, because Etalage can be configured to ignore some kinds
            # of territories (cf conf['territories_kinds']).
            self.competence_territories_id = set(
                territory_id
                for territory_id in (
                    ramdb.territory_id_by_kind_code.get((territory_kind_code['kind'], territory_kind_code['code']))
                    for territory_kind_code in poi_bson['territories'][i]
                    )
                if territory_id is not None
                )
            for territory_id in self.competence_territories_id:
                self.ids_by_competence_territory_id.setdefault(territory_id, set()).add(indexed_poi_id)
            break
        if not self.competence_territories_id:
            self.ids_by_competence_territory_id.setdefault(None, set()).add(indexed_poi_id)

        poi_territories_id = set(
            territory_id
            for territory_id in (
                ramdb.territory_id_by_kind_code.get((territory_kind_code['kind'], territory_kind_code['code']))
                for territory_kind_code in metadata['territories-index']
                if territory_kind_code['kind'] not in (u'Country', u'InternationalOrganization')
                )
            if territory_id is not None
            ) if metadata.get('territories-index') is not None else None
        for territory_id in (poi_territories_id or set()):
            self.ids_by_presence_territory_id.setdefault(territory_id, set()).add(indexed_poi_id)

        for word in strings.slugify(self.name).split(u'-'):
            self.ids_by_word.setdefault(word, set()).add(indexed_poi_id)
        self.slug_by_id[indexed_poi_id] = strings.slugify(self.name)

    @classmethod
    def index_pois(cls):
        for self in cls.instance_by_id.itervalues():
            # Note: self._id is not added to cls.indexed_ids by method self.index(self._id) to allow
            # customizations where not all POIs are indexed (Passim for example).
            cls.indexed_ids.add(self._id)
            self.index(self._id)
            del self.bson
        if conf['index.date.field']:
            cls.ids_by_begin_datetime = sorted(
                cls.ids_by_begin_datetime,
                key = lambda t: t[0] or datetime.datetime(datetime.MINYEAR, 1, 1),
                )
            cls.ids_by_end_datetime = sorted(
                cls.ids_by_end_datetime,
                key = lambda t: t[0] or datetime.datetime(datetime.MAXYEAR, 1, 1),
                reverse = True
                )

        cls.ids_by_last_update_datetime = sorted(cls.ids_by_last_update_datetime, key = lambda t: t[0], reverse = True)

    @classmethod
    def is_search_param_visible(cls, ctx, name):
        param_visibility_name = 'hide_{0}'.format(name)
        return getattr(ctx, param_visibility_name, False) \
            if param_visibility_name.startswith('show_') \
            else not getattr(ctx, param_visibility_name, False)

    def iter_csv_fields(self, ctx):
        counts_by_label = {}

        id_field = Field(id = 'poi-id', value = self._id, label = u'Identifiant')
        for subfield_ref, subfield in id_field.iter_csv_fields(ctx, counts_by_label):
            yield subfield_ref, subfield

        last_update_field = Field(
            id = 'poi-last-update',
            value = self.last_update_datetime,
            label = u'Date de dernière modification'
            )
        for subfield_ref, subfield in last_update_field.iter_csv_fields(ctx, counts_by_label):
            yield subfield_ref, subfield

        if self.fields is not None:
            for field in self.fields:
                for subfield_ref, subfield in field.iter_csv_fields(ctx, counts_by_label):
                    yield subfield_ref, subfield

    @classmethod
    def iter_ids(cls, ctx, categories_slug = None, competence_territories_id = None, competence_type = None,
            presence_territory = None, term = None):
        intersected_sets = []

        if competence_territories_id is not None:
            competence_territories_sets = []
            if competence_type in (None, 'by_territory'):
                competence_territories_sets.extend(
                    cls.ids_by_competence_territory_id.get(competence_territory_id)
                    for competence_territory_id in competence_territories_id
                    )
            if competence_type in (None, 'by_nature'):
                competence_territories_sets.append(cls.ids_by_competence_territory_id.get(None))
            territory_competent_pois_id = ramdb.union_set(competence_territories_sets)
            if not territory_competent_pois_id:
                return set()
            intersected_sets.append(territory_competent_pois_id)

        if presence_territory is not None:
            territory_present_pois_id = cls.ids_by_presence_territory_id.get(presence_territory._id)
            if not territory_present_pois_id:
                return set()
            intersected_sets.append(territory_present_pois_id)

        if ctx.base_categories_slug is not None:
            base_categories_sets = []
            base_categories_slug = copy(ctx.base_categories_slug or [])
            for category_slug in set(base_categories_slug or []):
                if category_slug is not None:
                    category_pois_id = cls.ids_by_category_slug.get(category_slug)
                    if category_pois_id:
                        base_categories_sets.append(category_pois_id)
            intersected_sets.append(ramdb.union_set(base_categories_sets))

        for category_slug in set(categories_slug or []):
            if category_slug is not None:
                category_pois_id = cls.ids_by_category_slug.get(category_slug)
                if not category_pois_id:
                    return set()
                intersected_sets.append(category_pois_id)

        if conf['index.date.field']:
            current_datetime = datetime.datetime.utcnow()
            ids_by_begin_datetime_set = set()
            for poi_begin_datetime, poi_id in cls.ids_by_begin_datetime:
                if poi_begin_datetime is None or current_datetime >= poi_begin_datetime:
                    ids_by_begin_datetime_set.add(poi_id)
                else:
                    break
            ids_by_end_datetime_set = set()
            for poi_end_datetime, poi_id in cls.ids_by_end_datetime:
                if poi_end_datetime is None or current_datetime <= poi_end_datetime:
                    ids_by_end_datetime_set.add(poi_id)
                else:
                    break
            intersected_sets.append(ramdb.intersection_set([ids_by_begin_datetime_set, ids_by_end_datetime_set]))

        # We should filter on term *after* having looked for competent organizations. Otherwise, when no organization
        # matching term is found, the nearest organizations will be used even when there are competent organizations
        # (that don't match the term).
        if term:
            prefixes = strings.slugify(term).split(u'-')
            pois_id_by_prefix = {}
            for prefix in prefixes:
                if prefix in pois_id_by_prefix:
                    # TODO? Handle pois with several words sharing the same prefix?
                    continue
                pois_id_by_prefix[prefix] = ramdb.union_set(
                    pois_id
                    for word, pois_id in cls.ids_by_word.iteritems()
                    if word.startswith(prefix)
                    ) or set()
            intersected_sets.extend(pois_id_by_prefix.itervalues())

        found_pois_id = ramdb.intersection_set(intersected_sets)
        if found_pois_id is None:
            return cls.indexed_ids
        return found_pois_id

    @classmethod
    def load(cls, poi_bson):
        metadata = poi_bson['metadata']
        last_update = metadata['last-update']
        if poi_bson.get('geo') is None:
            geo = None
        else:
            geo = poi_bson['geo'][0]
            if len(geo) > 2 and geo[2] == 0:
                # Don't use geographical coordinates with a 0 accuracy because their coordinates may be None.
                geo = None
        self = cls(
            _id = poi_bson['_id'],
            geo = geo,
            last_update_datetime = last_update['date'],
            last_update_organization = last_update['organization'],
            name = metadata['title'],
            schema_name = metadata['schema-name'],
            )

        if conf['theme_field'] is None:
            theme_field_id = None
            theme_field_name = None
        else:
            theme_field_id = conf['theme_field']['id']
            theme_field_name = conf['theme_field'].get('name')
        fields_position = {}
        fields = []
        for field_id in metadata['positions']:
            field_position = fields_position.get(field_id, 0)
            fields_position[field_id] = field_position + 1
            field_metadata = metadata[field_id][field_position]
            field_value = poi_bson[field_id][field_position]
            field = Field.load(field_id, field_metadata, field_value)
            if field.id == u'adr' and self.postal_distribution_str is None:
                for sub_field in (field.value or []):
                    if sub_field.id == u'postal-distribution':
                        self.postal_distribution_str = sub_field.value
                    elif sub_field.id == u'street-address':
                        self.street_address = sub_field.value
            elif field.id == u'link' and field.relation == u'parent':
                assert self.parent is None, str(self)
                self.parent_id = field.value

            if field_id == theme_field_id and (
                    theme_field_name is None or theme_field_name == strings.slugify(field.label)):
                if field.id == u'organism-type':
                    organism_type_slug = ramdb.category_slug_by_pivot_code.get(field.value)
                    if organism_type_slug is None:
                        log.warning('Ignoring organism type "{0}" without matching category.'.format(field.value))
                    else:
                        self.theme_slug = organism_type_slug
                else:
                    theme_slug = strings.slugify(field.value)
                    if theme_slug in ramdb.category_by_slug:
                        self.theme_slug = theme_slug
                    else:
                        log.warning('Ignoring theme "{0}" without matching category.'.format(field.value))

            fields.append(field)
        if fields:
            self.fields = fields

        # Temporarily store bson in poi because it is needed by index_pois.
        self.bson = poi_bson

        cls.instance_by_id[self._id] = self
        if self.parent_id is not None:
            cls.ids_by_parent_id.setdefault(self.parent_id, set()).add(self._id)
        return self

    @classmethod
    def load_pois(cls):
        from . import model
        for db, petitpois_url in zip(model.dbs, conf['petitpois_url']):
            for poi_bson in db.pois.find({'metadata.deleted': {'$exists': False}}):
                if (db.name, poi_bson['metadata']['schema-name']) not in cls.subclass_by_database_and_schema_name:
                    schema = db.schemas.find_one({'name': poi_bson['metadata']['schema-name']})
                    cls.subclass_by_database_and_schema_name[(db.name, poi_bson['metadata']['schema-name'])] = type(
                        'PoiWithPetitpois',
                        (cls,),
                        dict(
                            icon_url = schema.get('icon_url'),
                            petitpois_url = petitpois_url,
                            ),
                        )
                cls.subclass_by_database_and_schema_name[(db.name, poi_bson['metadata']['schema-name'])].load(poi_bson)

    @classmethod
    def make_inputs_to_search_data(cls):
        return conv.pipe(
            conv.struct(
                dict(
                    base_territory = conv.input_to_postal_distribution_to_geolocated_territory,
                    categories_slug = conv.uniform_sequence(conv.input_to_category_slug),
                    term = conv.input_to_slug,
                    territory = conv.input_to_postal_distribution_to_geolocated_territory,
                    ),
                default = 'drop',
                keep_none_values = True,
                ),
            conv.test_territory_in_base_territory,
            )

    @property
    def parent(self):
        if self.parent_id is None:
            return None
        return self.instance_by_id.get(self.parent_id)

    @classmethod
    def rename_input_to_param(cls, input_name):
        return dict(
            categories_slug = u'category',
            ).get(input_name, input_name)

    def set_attributes(self, **attributes):
        """Set given attributes and return a boolean stating whether existing attributes have changed."""
        changed = False
        for name, value in attributes.iteritems():
            if value is getattr(self.__class__, name, UnboundLocalError):
                if value is not getattr(self, name, UnboundLocalError):
                    delattr(self, name)
                    changed = True
            elif value is not getattr(self, name, UnboundLocalError):
                setattr(self, name, value)
                changed = True
        return changed

    @property
    def slug(self):
        return strings.slugify(self.name)

    @classmethod
    def sort_and_paginate_pois_list(cls, ctx, pager, poi_by_id, related_territories_id = None, reverse = False,
            territory = None, sort_key = None, **other_search_data):
        if territory is None:
            if sort_key is not None and sort_key == 'organism-type':
                key = lambda poi: ([
                    ramdb.category_by_slug.get(ramdb.category_slug_by_pivot_code.get(field.value)) or field.value
                    for field in poi.fields
                    if field.id == 'organism-type'
                    ] or [''])[0]
            elif sort_key is not None and sort_key == 'last_update_datetime':
                key = lambda poi: getattr(poi, sort_key, poi.name) if sort_key is not None else poi.name
                reverse = True
            elif sort_key == 'name':
                key = lambda poi: Poi.slug_by_id.get(poi._id)
            else:
                key = lambda poi: getattr(poi, sort_key, Poi.slug_by_id.get(poi._id)) \
                        if sort_key is not None else Poi.slug_by_id.get(poi._id)
            pois = sorted(poi_by_id.itervalues(), key = key, reverse = reverse)
            return [
                poi
                for poi in itertools.islice(pois, pager.first_item_index, pager.last_item_number)
                ]
        territory_latitude_cos = math.cos(math.radians(territory.geo[0]))
        territory_latitude_sin = math.sin(math.radians(territory.geo[0]))

        if sort_key is None:
            key = lambda incompetence_distance_and_poi_triple: incompetence_distance_and_poi_triple[:2]
        elif sort_key == 'organism-type':
            key = lambda incompetence_distance_and_poi_triple: (
                ([
                    ramdb.category_by_slug.get(ramdb.category_slug_by_pivot_code.get(field.value)) or field.value
                    for field in incompetence_distance_and_poi_triple[2].fields
                    if field.id == 'organism-type'
                    ] or [''])[0],
                incompetence_distance_and_poi_triple[1],
                )
        else:
            key = lambda incompetence_distance_and_poi_triple: (
                getattr(incompetence_distance_and_poi_triple[2], sort_key, None),
                incompetence_distance_and_poi_triple[1],
                )
        incompetence_distance_and_poi_triples = sorted(
            (
                (
                    # is not competent
                    poi.competence_territories_id is not None
                        and related_territories_id.isdisjoint(poi.competence_territories_id),
                    # distance
                    6372.8 * math.acos(
                        round(
                            math.sin(math.radians(poi.geo[0])) * territory_latitude_sin
                            + math.cos(math.radians(poi.geo[0])) * territory_latitude_cos
                            * math.cos(math.radians(poi.geo[1] - territory.geo[1])),
                            13,
                        )) if poi.geo is not None else (sys.float_info.max, poi),
                    # POI
                    poi,
                    )
                for poi in poi_by_id.itervalues()
                ),
            key = key,
            reverse = reverse,
            )
        return [
            poi
            for incompetence, distance, poi in itertools.islice(incompetence_distance_and_poi_triples,
                pager.first_item_index, pager.last_item_number)
            ]


def get_first_field(fields, id, label = None):
    for field in iter_fields(fields, id, label = label):
        return field
    return None


def iter_fields(fields, id, label = None):
    if fields is not None:
        for field in fields:
            if field.id == id and (label is None or field.label == label):
                yield field


def pop_first_field(fields, id, label = None):
    for field in iter_fields(fields, id, label = label):
        fields.remove(field)
        return field
    return None
