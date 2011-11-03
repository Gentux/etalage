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


__all__ = ['Poi', 'Statement']


log = logging.getLogger(__name__)


class Poi(representations.UserRepresentable, monpyjama.Wrapper):
    collection_name = 'pois'
    geo = None
    name = None
    statements = None

    def __init__(self, **attributes):
        if attributes:
            self.set_attributes(**attributes)

    def add_to_ramdb(self, indexes):
        indexes['pois_by_id'][self._id] = self

        for category_slug in (self.categories_slug or set()):
            indexes['pois_id_by_category_slug'].setdefault(category_slug, set()).add(self._id)
        del self.categories_slug

        for territory_id in (self.competence_territories_id or set()):
            indexes['pois_id_by_competence_territory_id'].setdefault(territory_id, set()).add(self._id)
        del self.competence_territories_id

        for territory_id in (self.territories_id or set()):
            indexes['pois_id_by_territory_id'].setdefault(territory_id, set()).add(self._id)
        del self.territories_id

        for word in strings.slugify(self.name).split(u'-'):
            indexes['pois_id_by_word'].setdefault(word, set()).add(self._id)

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
        statements = []
        for field_id in metadata['positions']:
            field_position = fields_position.get(field_id, 0)
            fields_position[field_id] = field_position + 1
            field_value = bson[field_id][field_position]
            field_metadata = metadata[field_id][field_position]
            statements.append(Statement(id = field_id, metadata = field_metadata, value = field_value))
        if statements:
            self.statements = statements

        return self

    def set_attributes(self, **attributes):
        for name, value in attributes.iteritems():
            if value is getattr(self.__class__, name, UnboundLocalError):
                if value is not getattr(self, name, UnboundLocalError):
                    delattr(self, name)
            else:
                setattr(self, name, value)


class Statement(representations.UserRepresentable):
    id = None # Petitpois id = format of value
    metadata = None # = Petitpois field metadata (contains label)
    value = None

    def __init__(self, **attributes):
        if attributes:
            self.set_attributes(**attributes)

    def set_attributes(self, **attributes):
        for name, value in attributes.iteritems():
            if value is getattr(self.__class__, name, UnboundLocalError):
                if value is not getattr(self, name, UnboundLocalError):
                    delattr(self, name)
            else:
                setattr(self, name, value)

