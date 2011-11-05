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
from etalage import urls
%>


<%inherit file="/index.mako"/>


<%def name="pagination()" filter="trim">
    % if pager.page_count > 1:
            <div class="pagination">
                <ul>
<%
        url_args = dict(
            (name, value)
            for name, value in params.iteritems()
            if name != 'page' and value is not None
            )
%>\
                    <li class="prev${' disabled' if pager.page_number <= 1 else ''}">
                        <a href="${urls.get_url(ctx, mode, page = pager.page_number - 1, **url_args)}">&larr; ${\
                                _(u"Previous")}</a>
                    </li>
        % for page_number in range(max(pager.page_number - 5, 1), pager.page_number):
                    <li>
                        <a class="page" href="${urls.get_url(ctx, mode, page = page_number, **url_args)}">${\
                                page_number}</a>
                    </li>
        % endfor
                    <li class="active">
                        <a href="${urls.get_url(ctx, mode, page = pager.page_number, **url_args)}">${\
                                pager.page_number}</a>
                    </li>
        % for page_number in range(pager.page_number + 1, min(pager.page_number + 5, pager.last_page_number) + 1):
                    <li>
                        <a class="page" href="${urls.get_url(ctx, mode, page = page_number, **url_args)}">${\
                                page_number}</a>
                    </li>
        % endfor
                    <li class="next${' disabled' if pager.page_number >= pager.last_page_number else ''}">
                        <a href="${urls.get_url(ctx, mode, page = pager.page_number + 1, **url_args)}">${\
                                _(u"Next")} &rarr;</a>
                    </li>
                </ul>
            </div>
    % endif
</%def>


<%def name="results()" filter="trim">
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
                    <th>Place</th>
                </tr>
            </thead>
            <tbody>
    % for poi in pager.items:
                <tr>
                    <td><a data-rel="external" href="/organismes/${poi._id}">${poi.name}</a></td>
                    <td>${poi.geo}</td>
                </tr>
    % endfor
            </tbody>
        </table>
        <%self:pagination/>
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
