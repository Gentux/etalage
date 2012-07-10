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


import logging

from biryani import strings
from suq import monpyjama, representations

from . import conv, ramdb


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
        for name, value in attributes.iteritems():
            if value is getattr(self.__class__, name, UnboundLocalError):
                if value is not getattr(self, name, UnboundLocalError):
                    delattr(self, name)
            else:
                setattr(self, name, value)


class Poi(representations.UserRepresentable, monpyjama.Wrapper):
    collection_name = 'pois'
    # IDs of territories for which POI is fully competent. None when POI has no notion of competence territory
    competence_territories_id = None
    fields = None
    geo = None
    last_update_datetime = None
    last_update_organization = None
    name = None
    organism_type_slug = None
    parent_id = None
    pois_id_by_parent_id = {}  # class attribute
    postal_distribution_str = None
    schema_name = None
    street_address = None

    def __init__(self, **attributes):
        if attributes:
            self.set_attributes(**attributes)

    @classmethod
    def clear_indexes(cls):
        ramdb.indexed_pois_id.clear()
        ramdb.poi_by_id.clear()
        cls.pois_id_by_parent_id.clear()
        ramdb.pois_id_by_category_slug.clear()
        ramdb.pois_id_by_competence_territory_id.clear()
        ramdb.pois_id_by_presence_territory_id.clear()
        ramdb.pois_id_by_word.clear()

    @classmethod
    def extract_non_territorial_search_data(cls, ctx, data):
        categories_slug = set(ctx.base_categories_slug or [])
        if data['categories'] is not None:
            categories_slug.update(
                category.slug
                for category in data['categories']
                )
        return dict(
            categories_slug = categories_slug,
            term = data['term'],
            )

    @classmethod
    def extract_search_inputs_from_params(cls, ctx, params):
        return dict(
            categories = params.getall('category'),
            filter = params.get('filter'),
            term = params.get('term'),
            territory = params.get('territory'),
            )

    def generate_all_fields(self):
        """Return all fields of POI including dynamic ones (ie linked fields, etc)."""
        fields = self.fields[:] if self.fields is not None else []

        # Add children POIs as linked fields.
        children = sorted(
            (
                ramdb.poi_by_id[child_id]
                for child_id in self.pois_id_by_parent_id.get(self._id, set())
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

    def index(self, indexed_poi_id):
        poi_bson = self.bson
        metadata = poi_bson['metadata']

        for category_slug in (metadata.get('categories-index') or set()):
            ramdb.pois_id_by_category_slug.setdefault(category_slug, set()).add(indexed_poi_id)

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
                ramdb.pois_id_by_competence_territory_id.setdefault(territory_id, set()).add(indexed_poi_id)
            break

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
            ramdb.pois_id_by_presence_territory_id.setdefault(territory_id, set()).add(indexed_poi_id)

        for word in strings.slugify(self.name).split(u'-'):
            ramdb.pois_id_by_word.setdefault(word, set()).add(indexed_poi_id)

    @classmethod
    def index_pois(cls):
        for self in ramdb.poi_by_id.itervalues():
            # Note: self._id is not added to ramdb.indexed_pois_id by method self.index(self._id) to allow
            # customizations where not all POIs are indexed (Passim for example).
            ramdb.indexed_pois_id.add(self._id)
            self.index(self._id)
            del self.bson

    def iter_csv_fields(self, ctx):
        counts_by_label = {}

        id_field = Field(id = 'poi-id', value = self._id, label = u'Identifiant')
        for subfield_ref, subfield in id_field.iter_csv_fields(ctx, counts_by_label):
            yield subfield_ref, subfield

        if self.fields is not None:
            for field in self.fields:
                for subfield_ref, subfield in field.iter_csv_fields(ctx, counts_by_label):
                    yield subfield_ref, subfield

    @classmethod
    def iter_ids(cls, ctx, categories_slug = None, competence_territories_id = None, presence_territory = None,
            term = None):
        intersected_sets = []

        if competence_territories_id is not None:
            territory_competent_pois_id = ramdb.union_set(
                ramdb.pois_id_by_competence_territory_id.get(competence_territory_id)
                for competence_territory_id in competence_territories_id
                )
            if not territory_competent_pois_id:
                return set()
            intersected_sets.append(territory_competent_pois_id)

        if presence_territory is not None:
            territory_present_pois_id = ramdb.pois_id_by_presence_territory_id.get(presence_territory._id)
            if not territory_present_pois_id:
                return set()
            intersected_sets.append(territory_present_pois_id)

        for category_slug in set(categories_slug or []):
            if category_slug is not None:
                category_pois_id = ramdb.pois_id_by_category_slug.get(category_slug)
                if not category_pois_id:
                    return set()
                intersected_sets.append(category_pois_id)

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
                    for word, pois_id in ramdb.pois_id_by_word.iteritems()
                    if word.startswith(prefix)
                    ) or set()
            intersected_sets.extend(pois_id_by_prefix.itervalues())

        found_pois_id = ramdb.intersection_set(intersected_sets)
        if found_pois_id is None:
            return ramdb.indexed_pois_id
        return found_pois_id

    @classmethod
    def load(cls, poi_bson):
        metadata = poi_bson['metadata']
        last_update = metadata['last-update']
        self = cls(
            _id = poi_bson['_id'],
            geo = poi_bson['geo'][0] if poi_bson.get('geo') is not None else None,
            last_update_datetime = last_update['date'],
            last_update_organization = last_update['organization'],
            name = metadata['title'],
            schema_name = metadata['schema-name'],
            )

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
            elif field.id == u'organism-type':
                organism_type_slug = ramdb.category_slug_by_pivot_code.get(field.value)
                if organism_type_slug is None:
                    log.warning('Ignoring organism type "{0}" without matching category.'.format(field.value))
                else:
                    self.organism_type_slug = organism_type_slug
            fields.append(field)
        if fields:
            self.fields = fields

        # Temporarily store bson in poi because it is needed by index_pois.
        self.bson = poi_bson

        ramdb.poi_by_id[self._id] = self
        if self.parent_id is not None:
            cls.pois_id_by_parent_id.setdefault(self.parent_id, set()).add(self._id)
        return self

    @classmethod
    def load_pois(cls):
        for poi_bson in cls.get_collection().find({'metadata.deleted': {'$exists': False}}):
            cls.load(poi_bson)

    @classmethod
    def make_inputs_to_search_data(cls):
        return conv.struct(
            dict(
                categories = conv.uniform_sequence(conv.input_to_slug_to_category),
                filter = conv.input_to_filter,
                term = conv.input_to_slug,
                territory = conv.input_to_postal_distribution_to_geolocated_territory,
                ),
            default = 'drop',
            keep_none_values = True,
            )
    @property
    def parent(self):
        if self.parent_id is None:
            return None
        return ramdb.poi_by_id.get(self.parent_id)

    def set_attributes(self, **attributes):
        for name, value in attributes.iteritems():
            if value is getattr(self.__class__, name, UnboundLocalError):
                if value is not getattr(self, name, UnboundLocalError):
                    delattr(self, name)
            else:
                setattr(self, name, value)

    @property
    def slug(self):
        return strings.slugify(self.name)


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
