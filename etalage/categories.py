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


"""Objects for RAM-based POIs"""


import logging

from biryani import strings
from suq import representations

from . import conv


__all__ = ['Category']


log = logging.getLogger(__name__)


class Category(representations.UserRepresentable):
    name = None
    tags_slug = None

    def __init__(self, **attributes):
        if attributes:
            self.set_attributes(**attributes)

    def add_to_ramdb(self, indexes):
        slug = self.slug
        indexes['categories_by_slug'][slug] = self
        for word in slug.split(u'-'):
            indexes['categories_slug_by_word'].setdefault(word, set()).add(slug)
        for tag_slug in (self.tags_slug or set()):
            indexes['categories_slug_by_tag_slug'].setdefault(tag_slug, set()).add(slug)

    def set_attributes(self, **attributes):
        for name, value in attributes.iteritems():
            if value is getattr(self.__class__, name, UnboundLocalError):
                if value is not getattr(self, name, UnboundLocalError):
                    delattr(self, name)
            else:
                setattr(self, name, value)

    @property
    def slug(self):
        return strings.slugify(self.name) or None

