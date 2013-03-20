## -*- coding: utf-8 -*-


## Etalage -- Open Data POIs portal
## By: Emmanuel Raviart <eraviart@easter-eggs.com>
##
## Copyright (C) 2011, 2012 Easter-eggs
## http://gitorious.org/infos-pratiques/etalage
##
## This file is part of Etalage.
##
## Etalage is free software; you can redistribute it and/or modify
## it under the terms of the GNU Affero General Public License as
## published by the Free Software Foundation, either version 3 of the
## License, or (at your option) any later version.
##
## Etalage is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Affero General Public License for more details.
##
## You should have received a copy of the GNU Affero General Public License
## along with this program.  If not, see <http://www.gnu.org/licenses/>.


<%!
from datetime import datetime

from etalage import conf, urls
%>


<%namespace file="/site.mako" name="site"/>


<?xml version="1.0" encoding="UTF-8"?>
<feed xml:lang="fr" xmlns="http://www.w3.org/2005/Atom">
    <id>${data['feed_id']}</id>
    <title><%site:title_content/></title>
    <updated>${datetime.strftime(data['feed_updated'], '%Y-%m-%dT%H:%M:%S')}.00Z</updated>
    <link href="${data['feed_url']}" rel="self" />
    <author>
        <name>${data['author_name']}</name>
        <email>${data['author_email']}</email>
        <uri>${data['feed_url']}</uri>
    </author>
% for poi in pager.items:
    <entry>
        <id>${poi.get_full_url(ctx, params_prefix = 'cmq_')}</id>
        <title>${poi.name}</title>
        <link rel="alternate" type="text/html" href="${poi.get_full_url(ctx, params_prefix = 'cmq_')}" />
        <published>${datetime.strftime(poi.last_update_datetime, '%Y-%m-%dT%H:%M:%S')}.00Z</published>
        <updated>${datetime.strftime(poi.last_update_datetime, '%Y-%m-%dT%H:%M:%S')}.00Z</updated>
    % if getattr(poi, 'last_update_organization') or getattr(poi, 'last_update_organization'):
        <author>
            <name>${poi.last_update_organization}</name>
        </author>
    % endif
    </entry>
% endfor
</feed>
