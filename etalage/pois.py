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


__all__ = ['Cluster', 'Field', 'Poi']


log = logging.getLogger(__name__)


class Cluster(representations.UserRepresentable):
    bottom = None # South latitude of rectangle enclosing all POIs of cluster
    center_latitude = None # Copy of center_pois[*].geo[0] for quick access
    center_longitude = None # Copy of center_pois[*].geo[1] for quick access
    center_pois = None # POIs at the center of cluster, sharing the same coordinates
    # False = Not competent for current territory, None = Competent for any territory or unknown territory,
    # True = Competent for current territory
    competent = False
    count = None # Number of POIs in cluster
    left = None # West longitude of rectangle enclosing all POIs of cluster
    right = None # East longitude of rectangle enclosing all POIs of cluster
    top = None # North latitude of rectangle enclosing all POIs of cluster


class Field(representations.UserRepresentable):
    id = None # Petitpois id = format of value
    kind = None
    label = None
    relation = None
    type = None
    value = None

    def __init__(self, **attributes):
        if attributes:
            self.set_attributes(**attributes)

    @property
    def is_composite(self):
        return self.id in ('adr', 'source')

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
            elif self.id == 'commune':
                field_attributes = self.__dict__.copy()
                field_attributes['label'] = u'Code Insee commune' # Better than "Commune"
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
            elif self.id == 'postal-distribution':
                postal_code, postal_routing = conv.check(conv.split_postal_distribution)(self.value, state = ctx)
                for field in (
                        Field(id = 'postal-code', value = postal_code, label = u'Code postal'),
                        Field(id = 'postal-routing', value = postal_routing, label = u'Commune'),
                        ):
                    for subfield_ref, subfield in field.iter_csv_fields(ctx, counts_by_label, parent_ref = parent_ref):
                        yield subfield_ref, subfield
            elif self.id == 'street-address':
                for item_value in self.value.split('\n'):
                    item_value = item_value.strip()
                    item_field_attributes = self.__dict__.copy()
                    item_field_attributes['id'] = 'street-address-lines' # Change ID to avoid infinite recursion.
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
    # IDs of territories for which POI is fully competent. None when POI has no notion of competence territory
    competence_territories_id = None
    fields = None
    geo = None
    last_update_datetime = None
    last_update_organization = None
    name = None
    organism_type_slug = None
    parent_id = None
    postal_distribution_str = None
    street_address = None

    def __init__(self, **attributes):
        if attributes:
            self.set_attributes(**attributes)

    def iter_csv_fields(self, ctx):
        counts_by_label = {}

        id_field = Field(id = 'poi-id', value = self._id, label = u'ID')
        for subfield_ref, subfield in id_field.iter_csv_fields(ctx, counts_by_label):
            yield subfield_ref, subfield

        if self.fields is not None:
            for field in self.fields:
                for subfield_ref, subfield in field.iter_csv_fields(ctx, counts_by_label):
                    yield subfield_ref, subfield

    @property
    def parent(self):
        if self.parent_id is None:
            return None
        return ramdb.pois_by_id.get(self.parent_id)

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
