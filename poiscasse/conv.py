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


"""Conversion functions"""


from biryani.baseconv import *
from biryani.objectconv import *
from biryani.frconv import *
from biryani import states, strings

from territoria2.conv import str_to_postal_distribution


default_state = states.default_state


def bson_to_poi(bson, state = default_state):
    from . import pois
    return make_dict_to_object(pois.Poi)(bson, state = state)


def bson_to_ram_poi(bson, state = default_state):
    from . import rampois
    return make_dict_to_object(rampois.RamPoi)(bson, state = state)


ram_poi_to_bson = object_to_clean_dict


str_to_slug = make_str_to_slug()
