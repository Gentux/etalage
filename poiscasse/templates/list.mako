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
from poiscasse import urls
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
                        <a href="${urls.get_url(ctx, page = pager.page_number - 1, **url_args)}">&larr; ${\
                                _(u"Previous")}</a>
                    </li>
        % for page_number in range(max(pager.page_number - 5, 1), pager.page_number):
                    <li>
                        <a class="page" href="${urls.get_url(ctx, page = page_number, **url_args)}">${page_number}</a>
                    </li>
        % endfor
                    <li class="active">
                        <a href="${urls.get_url(ctx, page = pager.page_number, **url_args)}">${pager.page_number}</a>
                    </li>
        % for page_number in range(pager.page_number + 1, min(pager.page_number + 5, pager.last_page_number) + 1):
                    <li>
                        <a class="page" href="${urls.get_url(ctx, page = page_number, **url_args)}">${page_number}</a>
                    </li>
        % endfor
                    <li class="next${' disabled' if pager.page_number >= pager.last_page_number else ''}">
                        <a href="${urls.get_url(ctx, page = pager.page_number + 1, **url_args)}">${\
                                _(u"Next")} &rarr;</a>
                    </li>
                </ul>
            </div>
    % endif
</%def>


<%def name="results()" filter="trim">
    <%self:pagination/>
    <table style="border: solid black 1px;">
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

