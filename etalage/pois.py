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


"""Objects for POIs"""


import logging

from biryani import strings
from suq import monpyjama, representations

from . import conv, ramdb


__all__ = ['Field', 'Poi']


log = logging.getLogger(__name__)


class Field(representations.UserRepresentable):
    id = None # Petitpois id = format of value
    kind = None
    label = None
    type = None
    value = None

    def __init__(self, **attributes):
        if attributes:
            self.set_attributes(**attributes)

    @classmethod
    def from_bson(cls, id, metadata, value, state = conv.default_state):
        if len(metadata) != (1 if 'kind' in metadata else 0) \
                + (1 if 'label' in metadata else 0) \
                + (1 if 'type' in metadata else 0) \
                + (1 + len(metadata['positions']) if 'positions' in metadata else 0):
            log.warning('Unexpected attributes in field metadata {0} for value {1}'.format(metadata, value))
        if 'positions' in metadata:
            fields_position = {}
            fields = []
            for field_id in metadata['positions']:
                field_position = fields_position.get(field_id, 0)
                fields_position[field_id] = field_position + 1
                field_metadata = metadata[field_id][field_position]
                field_value = value[field_id][field_position]
                fields.append(Field.from_bson(field_id, field_metadata, field_value, state = state))
            value = fields or None
        return cls(
            id = id,
            kind = metadata.get('kind'),
            label = metadata['label'],
            type = metadata.get('type'),
            value = value,
            )

    @property
    def is_composite(self):
        return self.id in ('adr', 'source')

    def iter_csv_fields(self, ctx, counts_by_label, parent_ref = None):
        """Iter fields, entering inside composite fields."""
        if self.value is not None:
            if self.is_composite:
                same_label_index = counts_by_label.get(self.label, 0)
                ref = (parent_ref or []) + [self.label, same_label_index]
                if self.value is not None:
                    field_counts_by_label = {}
                    for field in self.value:
                        for subfield_ref, subfield in field.iter_csv_fields(ctx, field_counts_by_label,
                                parent_ref = ref):
                            yield subfield_ref, subfield
                    if field_counts_by_label:
                        # Some subfields were not empty, so increment number of exported fields having the same label.
                        counts_by_label[self.label] = same_label_index + 1
            elif self.id == 'postal-distribution':
                postal_code, postal_routing = conv.check(conv.split_postal_distribution)(self.value, state = ctx)
                for field in (
                        Field(id = 'postal-code', value = postal_code, label = u'Code postal'),
                        Field(id = 'postal-routing', value = postal_routing, label = u'Commune'),
                        ):
                    for subfield_ref, subfield in field.iter_csv_fields(ctx, counts_by_label, parent_ref = parent_ref):
                        yield subfield_ref, subfield
            elif self.id == 'geo':
                for field in (
                        Field(id = 'float', value = self.value[0], label = u'Latitude'),
                        Field(id = 'float', value = self.value[1], label = u'Longitude'),
                        Field(id = 'int', value = self.value[2], label = u'Précision'),
                        ):
                    for subfield_ref, subfield in field.iter_csv_fields(ctx, counts_by_label, parent_ref = parent_ref):
                        yield subfield_ref, subfield
            elif self.id == 'street-address' and u'\n' in self.value:
                for item_value in self.value.split('\n'):
                    item_value = item_value.strip()
                    item_field_attributes = self.__dict__.copy()
                    item_field_attributes['label'] = u'Adresse' # Better than "Rue, Voie, Chemin"
                    item_field_attributes['value'] = item_value
                    item_field = Field(**item_field_attributes)
                    for subfield_ref, subfield in item_field.iter_csv_fields(ctx, counts_by_label,
                            parent_ref = parent_ref):
                        yield subfield_ref, subfield
            elif isinstance(self.value, list):
                for item_value in self.value:
                    item_field_attributes = self.__dict__.copy()
                    item_field_attributes['value'] = item_value
                    item_field = Field(**item_field_attributes)
                    for subfield_ref, subfield in item_field.iter_csv_fields(ctx, counts_by_label,
                            parent_ref = parent_ref):
                        yield subfield_ref, subfield
            elif self.id == 'commune':
                field_attributes = self.__dict__.copy()
                field_attributes['label'] = u'Code Insee commune' # Better than "Commune"
                field = Field(**field_attributes)
                same_label_index = counts_by_label.get(field.label, 0)
                yield (parent_ref or []) + [field.label, same_label_index], field
                counts_by_label[field.label] = same_label_index + 1
            else:
                same_label_index = counts_by_label.get(self.label, 0)
                yield (parent_ref or []) + [self.label, same_label_index], self
                counts_by_label[self.label] = same_label_index + 1

    def set_attributes(self, **attributes):
        for name, value in attributes.iteritems():
            if value is getattr(self.__class__, name, UnboundLocalError):
                if value is not getattr(self, name, UnboundLocalError):
                    delattr(self, name)
            else:
                setattr(self, name, value)


class Poi(representations.UserRepresentable, monpyjama.Wrapper):
    collection_name = 'pois'
    fields = None
    geo = None
    name = None

    def __init__(self, **attributes):
        if attributes:
            self.set_attributes(**attributes)

    @classmethod
    def from_bson(cls, bson, state = conv.default_state):
        if bson is None:
            return None

        metadata = bson['metadata']
        self = cls(
            _id = bson['_id'],
            geo = bson['geo'][0] if bson.get('geo') is not None else None,
            name = metadata['title'],
            )

        self.categories_slug = metadata.get('categories-index')

        for i, territory_metadata in enumerate(metadata.get('territories') or []):
            if strings.slugify(territory_metadata['label']) == u'territoires-de-competence':
                competence_territories_id = set(
                    ramdb.territories_id_by_kind_code[(territory_kind_code['kind'], territory_kind_code['code'])]
                    for territory_kind_code in bson['territories'][i]
                    )
                break
        else:
            competence_territories_id = None
        self.competence_territories_id = competence_territories_id

        self.territories_id = set(
            ramdb.territories_id_by_kind_code[(territory_kind_code['kind'], territory_kind_code['code'])]
            for territory_kind_code in metadata['territories-index']
            if territory_kind_code['kind'] not in (u'Country', u'InternationalOrganization', u'MetropoleOfCountry')
            ) if metadata.get('territories-index') is not None else None

        fields_position = {}
        fields = []
        for field_id in metadata['positions']:
            field_position = fields_position.get(field_id, 0)
            fields_position[field_id] = field_position + 1
            field_metadata = metadata[field_id][field_position]
            field_value = bson[field_id][field_position]
            fields.append(Field.from_bson(field_id, field_metadata, field_value, state = state))
        if fields:
            self.fields = fields

        return self

    def iter_csv_fields(self, ctx):
        counts_by_label = {}

        id_field = Field(id = 'poi-id', value = self._id, label = u'ID')
        for subfield_ref, subfield in id_field.iter_csv_fields(ctx, counts_by_label):
            yield subfield_ref, subfield

        if self.fields is not None:
            for field in self.fields:
                for subfield_ref, subfield in field.iter_csv_fields(ctx, counts_by_label):
                    yield subfield_ref, subfield

    def set_attributes(self, **attributes):
        for name, value in attributes.iteritems():
            if value is getattr(self.__class__, name, UnboundLocalError):
                if value is not getattr(self, name, UnboundLocalError):
                    delattr(self, name)
            else:
                setattr(self, name, value)

