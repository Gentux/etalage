# -*- coding: utf-8 -*-


# PoisCasse -- Open Data POIs portal
# By: Emmanuel Raviart <eraviart@easter-eggs.com>
#     Romain Soufflet <rsoufflet@easter-eggs.com>
#
# Copyright (C) 2011 Easter-eggs
# http://gitorious.org/infos-pratiques/poiscasse
#
# This file is part of PoisCasse.
#
# PoisCasse is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# PoisCasse is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


"""Objects for RAM-based POIs"""


import logging

from biryani import strings
from suq import representations

from . import conv


__all__ = ['RamPoi']


log = logging.getLogger(__name__)


class RamPoi(representations.UserRepresentable):
    _id = None
    from_bson = staticmethod(conv.check(conv.bson_to_ram_poi))
    geo = None
    name = None
    to_bson = conv.check(conv.ram_poi_to_bson)

    def __init__(self, **attributes):
        if attributes:
            self.set_attributes(**attributes)

    def add_to_ramdb(self, indexes, categories_slug, territories_kind_code):
        indexes['ram_pois_by_id'][self._id] = self
        for category_slug in (categories_slug or set()):
            indexes['pois_id_by_category_slug'].setdefault(category_slug, set()).add(self._id)
        for territory_kind_code in (territories_kind_code or set()):
            indexes['pois_id_by_territory_kind_code'].setdefault(territory_kind_code, set()).add(self._id)
        for word in strings.slugify(self.name).split(u'-'):
            indexes['pois_id_by_word'].setdefault(word, set()).add(self._id)

    def set_attributes(self, **attributes):
        for name, value in attributes.iteritems():
            if value is getattr(self.__class__, name, UnboundLocalError):
                if value is not getattr(self, name, UnboundLocalError):
                    delattr(self, name)
            else:
                setattr(self, name, value)

