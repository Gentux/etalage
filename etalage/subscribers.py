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


"""Objects for subscribers, subscriptions, sites and users"""


from suq import monpyjama, representations

from . import conv, ramdb


class Site(representations.UserRepresentable):
    domain_name = None
    from_bson = staticmethod(conv.check(conv.bson_to_site))
    subscriptions = None
    to_bson = conv.check(conv.site_to_bson)
    url = None


class Subscriber(representations.UserRepresentable, monpyjama.Wrapper):
    collection_name = 'subscribers'
    emegalis = False
    from_bson = staticmethod(conv.check(conv.bson_to_subscriber))
    id = None
    organization = None  # Organism name
    sites = None
    territory_kind_code = None
    to_bson = conv.check(conv.subscriber_to_bson)
    users = None

    @property
    def territory(self):
        if self.territory_kind_code is None:
            return None
        territory_id = ramdb.territory_id_by_kind_code.get((self.territory_kind_code['kind'],
            self.territory_kind_code['code']))
        if territory_id is None:
            return None
        return ramdb.territory_by_id.get(territory_id)


class Subscription(representations.UserRepresentable):
    from_bson = staticmethod(conv.check(conv.bson_to_subscription))
    id = None
    options = None
    territory_kind_code = None
    to_bson = conv.check(conv.subscription_to_bson)
    type = None
    url = None

    @property
    def territory(self):
        if self.territory_kind_code is None:
            return None
        territory_id = ramdb.territory_id_by_kind_code.get((self.territory_kind_code['kind'],
            self.territory_kind_code['code']))
        if territory_id is None:
            return None
        return ramdb.territory_by_id.get(territory_id)


class User(representations.UserRepresentable):
    from_bson = staticmethod(conv.check(conv.bson_to_user))
    to_bson = conv.check(conv.user_to_bson)
