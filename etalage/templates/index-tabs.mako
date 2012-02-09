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
from etalage import urls
%>


<%def name="index_tabs()" filter="trim">
        <ul class="nav nav-tabs">
<%
    modes_infos = (
        (u'carte', u'Carte'),
        (u'liste', u'Liste'),
        (u'annuaire', u'Annuaire'),
        (u'gadget', u'Partage'),
        (u'export', u'Export'),
        )
%>\
    % for tab_mode, tab_name in modes_infos:
<%
        if tab_mode == u'annuaire' and ctx.hide_directory:
            continue
%>\
            <li${' class="active"' if tab_mode == mode else '' | n}>
                <a class="internal" href="${urls.get_url(ctx, tab_mode, **params)}">${tab_name}</a>
            </li>
    % endfor
        </ul>
</%def>

