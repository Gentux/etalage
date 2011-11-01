## -*- coding: utf-8 -*-


## PoisCasse -- Open Data POIs portal
## By: Emmanuel Raviart <eraviart@easter-eggs.com>
##     Romain Soufflet <rsoufflet@easter-eggs.com>
##
## Copyright (C) 2011 Easter-eggs
## http://gitorious.org/infos-pratiques/poiscasse
##
## This file is part of PoisCasse.
##
## PoisCasse is free software; you can redistribute it and/or modify
## it under the terms of the GNU Affero General Public License as
## published by the Free Software Foundation, either version 3 of the
## License, or (at your option) any later version.
##
## PoisCasse is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Affero General Public License for more details.
##
## You should have received a copy of the GNU Affero General Public License
## along with this program.  If not, see <http://www.gnu.org/licenses/>.


<%!
from poiscasse import ramdb, urls
%>


<%inherit file="/index.mako"/>


<%def name="results()" filter="trim">
    % if not directory:
        <div>
            <em>Aucun organisme trouvé.</em>
        </div>
    % else:
        <div>
        % for category_slug, pois_id in sorted(directory.iteritems()):
<%
            category = ramdb.categories_by_slug[category_slug]
%>\
            <h3>${category.name}</h3>
            % if not pois_id:
            <div>
                <em>Aucun organisme trouvé.</em>
            </div>
            % else:
            <ul>
                % for poi_id in pois_id:
<%
                    ram_poi = ramdb.ram_pois_by_id[poi_id]
%>\
                <li>
                    <a href="${urls.get_url(ctx, 'organismes', poi_id)}">${ram_poi.name}</a>
                </li>
                % endfor
            </ul>
            % endif
            <ul>
            </ul>
        % endfor
        </div>
    % endif
</%def>

