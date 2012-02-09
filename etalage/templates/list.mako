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
import markupsafe

from etalage import urls
%>


<%inherit file="/index.mako"/>


<%def name="metas()" filter="trim">
    <%parent:metas/>
    <meta name="robots" content="noindex">
</%def>


<%def name="pagination()" filter="trim">
    % if pager.page_count > 1:
            <div class="pagination pagination-centered">
                <ul>
<%
        url_args = dict(
            (dict(categories = 'category').get(name, name), value)
            for name, value in params.iteritems()
            if name != 'page' and value is not None
            )
%>\
                    <li class="prev${' disabled' if pager.page_number <= 1 else ''}">
                        <a class="internal" href="${urls.get_url(ctx, mode, page = max(pager.page_number - 1, 1),
                                **url_args)}">&larr;</a>
                    </li>
        % for page_number in range(max(pager.page_number - 5, 1), pager.page_number):
                    <li>
                        <a class="internal" href="${urls.get_url(ctx, mode, page = page_number,
                                **url_args)}">${page_number}</a>
                    </li>
        % endfor
                    <li class="active">
                        <a class="internal" href="${urls.get_url(ctx, mode, page = pager.page_number, **url_args
                                )}">${pager.page_number}</a>
                    </li>
        % for page_number in range(pager.page_number + 1, min(pager.page_number + 5, pager.last_page_number) + 1):
                    <li>
                        <a class="internal" href="${urls.get_url(ctx, mode, page = page_number,
                                **url_args)}">${page_number}</a>
                    </li>
        % endfor
                    <li class="next${' disabled' if pager.page_number >= pager.last_page_number else ''}">
                        <a class="internal" href="${urls.get_url(ctx, mode,
                                page = min(pager.page_number + 1, pager.last_page_number), **url_args)}">&rarr;</a>
                    </li>
                </ul>
            </div>
    % endif
</%def>


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
        <table class="table table-bordered table-condensed table-striped">
            <thead>
                <tr>
                    <th>${_('Name')}</th>
                    <th>${_('Street Address')}</th>
                    <th>${_('Commune')}</th>
                </tr>
            </thead>
            <tbody>
        % for poi in pager.items:
                <tr>
                    <td>
                        <a class="internal" href="${urls.get_url(ctx, 'organismes', poi.slug, poi._id)}">${poi.name}</a>
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


<%def name="title_content()" filter="trim">
${_(u'List')} - ${parent.title_content()}
</%def>

