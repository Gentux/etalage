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

from etalage import model, ramdb, urls
%>


<%inherit file="/index.mako"/>


<%def name="results()" filter="trim">
    % if errors is not None:
        % if territory is None:
        <div class="alert alert-info">
            Pour accéder à l'annuaire, vous devez <strong>préciser un territoire</strong> dans le formulaire ci-dessus.
        </div>
        % endif
    % else:
        <h2>Annuaire ${territory.name_with_hinge}</h2>
        % if not directory:
        <div>
            <em>Aucun organisme trouvé.</em>
        </div>
        % else:
        <div>
            % for category_slug, pois in sorted(directory.iteritems()):
                % if pois:
<%
                    category = ramdb.category_by_slug[category_slug]
                    url_args = dict(
                        (name, value)
                        for name, value in inputs.iteritems()
                        if name != 'categories' and name not in model.Poi.get_visibility_params_names(ctx) and\
                            value is not None
                        )
                    url_args['category'] = category.name
%>\
            <h3>
                ${category.name}
                <small>(<a class="internal" href="${urls.get_url(ctx, 'carte', **url_args)}">carte</a>,
                <a class="internal" href="${urls.get_url(ctx, 'liste', **url_args)}">liste</a>)</small>
            </h3>
            <ul>
                    % for poi in pois:
                <li>
                    <a class="internal" href="${urls.get_url(ctx, 'organismes', poi.slug, poi._id)}">${poi.name}</a>
                        % if poi.street_address:
                    <div>${markupsafe.Markup(u'<br>').join((poi.street_address).split(u'\n'))}</div>
                        % endif
                        % if poi.postal_distribution_str:
                    <div>${poi.postal_distribution_str}</div>
                        % endif
                </li>
                    % endfor
            </ul>
                % endif
            % endfor
        </div>
        % endif
    % endif
</%def>


<%def name="title_content()" filter="trim">
${_(u'Directory')} - ${parent.title_content()}
</%def>

