## -*- coding: utf-8 -*-


## Etalage -- Open Data POIs portal
## By: Emmanuel Raviart <eraviart@easter-eggs.com>
##     Romain Soufflet <rsoufflet@easter-eggs.com>
##
## Copyright (C) 2011 Easter-eggs
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
import markupsafe

from etalage import urls
%>


<%inherit file="/index.mako"/>


<%def name="results()" filter="trim">
    % if errors is None:
        % if pager.item_count == 0:
        <div>
            <em>Aucun organisme trouvé.</em>
        </div>
        % else:
        <div>
            Organismes ${pager.first_item_number} à ${pager.last_item_number} sur ${pager.item_count}
        </div>
        % endif
        <%self:pagination/>
        <table class="zebra-striped">
            <thead>
                <tr>
                    <th>Name</th>
                    <th>Street Address</th>
                    <th>Postal Code & Commune</th>
                </tr>
            </thead>
            <tbody>
        % for poi in pager.items:
                <tr>
                    <td>
                        <a class="internal" href="${urls.get_url(ctx, 'organismes', poi._id)}">${poi.name}</a>
                    </td>
                    <td>${markupsafe.Markup(u'<br>').join((poi.street_address or u'').split(u'\n'))}</td>
                    <td>${poi.postal_distribution_str or ''}</td>
                </tr>
        % endfor
            </tbody>
        </table>
        <%self:pagination/>
    % endif
</%def>


<%def name="scripts()" filter="trim">
    <%parent:scripts/>
    <script>
etalage.pager = ${dict(
    # Name of items follow Google JSON Style Guide http://google-styleguide.googlecode.com/svn/trunk/jsoncstyleguide.xml
    currentItemCount = pager.page_size,
    itemsPerPage = pager.page_max_size,
    pageIndex = pager.page_number,
    startIndex = pager.first_item_number,
    totalItems = pager.item_count,
    totalPages = pager.page_count,
    ) if errors is None else None | n, js};
    </script>
</%def>


<%def name="title_content()" filter="trim">
${_(u'List')} - ${parent.title_content()}
</%def>

