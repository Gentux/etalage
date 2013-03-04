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

from etalage import conf, conv, model, ramdb, urls
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
            (model.Poi.rename_input_to_param(name), value)
            for name, value in inputs.iteritems()
            if name != 'page' and name not in model.Poi.get_visibility_params_names(ctx) and value is not None
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
        <%self:pagination/>
        <%self:results_table/>
        <%self:pagination/>
        % endif
    % endif
</%def>


<%def name="results_table()" filter="trim">
<%
        data, errors = conv.inputs_to_pois_list_data(inputs, state = ctx)
        related_territories_id = ramdb.get_territory_related_territories_id(
            data['territory']
            ) if data.get('territory') is not None else None
%>
        <table class="table table-bordered table-condensed table-striped">
            <thead>
                <tr>
<%
        url_args = dict(
            (model.Poi.rename_input_to_param(name), value)
            for name, value in inputs.iteritems()
            if name != 'page' and name not in model.Poi.get_visibility_params_names(ctx) and value is not None
            )
        url_args['sort_key'] = ''
%>\
                    <th>
                        <a class="internal" href="${urls.get_url(ctx, mode, page = pager.page_number, **url_args)}">
                            <i class="icon icon-chevron-down"> </i>
                        </a>
                    </th>
                    <th>
<%
        url_args['sort_key'] = 'name'
%>\
                        <a class="internal" href="${urls.get_url(ctx, mode, page = pager.page_number, **url_args)}">
                            ${_('Name')}
                            <i class="icon icon-chevron-down"> </i>
                        </a>
                    </th>
                    <th>
<%
        url_args['sort_key'] = ''
%>\
                        <a class="internal" href="${urls.get_url(ctx, mode, page = pager.page_number, **url_args)}">
                            ${_('Street Address')}
                            <i class="icon icon-chevron-down"> </i>
                        </a>
                    </th>
                    <th>
<%
        url_args['sort_key'] = ''
%>\
                        <a class="internal" href="${urls.get_url(ctx, mode, page = pager.page_number, **url_args)}">
                            ${_('Commune')}
                            <i class="icon icon-chevron-down"> </i>
                        </a>
                    </th>
                </tr>
            </thead>
            <tbody>
        % for poi in pager.items:
                <tr>
                    <td>
            % if related_territories_id is None or poi.competence_territories_id is None:
                <img class="legend-icon" src="${conf['images.markers.url'].rstrip('/')}/misc/blueblank.png">
            % elif not related_territories_id.isdisjoint(poi.competence_territories_id):
                <img class="legend-icon" src="${conf['images.markers.url'].rstrip('/')}/misc/greenvalid.png">
            % else:
                <img class="legend-icon" src="${conf['images.markers.url'].rstrip('/')}/misc/redinvalid.png">
            % endif
                    </td>
                    <td>
                        <a class="internal" href="${urls.get_url(ctx, 'organismes', poi.slug, poi._id)}">${poi.name}</a>
                    </td>
                    <td>${markupsafe.Markup(u'<br>').join((poi.street_address or u'').split(u'\n'))}</td>
                    <td>${poi.postal_distribution_str or ''}</td>
                </tr>
        % endfor
            </tbody>
        </table>
</%def>


<%def name="title_content()" filter="trim">
${_(u'List')} - ${parent.title_content()}
</%def>

