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
import urlparse

from etalage import conf, urls
%>


<%inherit file="/site.mako"/>


<%def name="container_content()" filter="trim">
        <form action="${urls.get_url(ctx, mode)}" class="horizontal-form internal" id="search-form" method="get">
    % for name, value in sorted(params.iteritems()):
<%
        if name in (
                'bbox',
                'category' if not ctx.hide_category else None,
                'filter' if ctx.show_filter else None,
                'page',
                'term',
                'territory',
                ):
            continue
        if value is None or value == u'':
            continue
%>\
        % if isinstance(value, list):
            % for item_value in value:
            <input name="${name}" type="hidden" value="${item_value or ''}">
            % endfor
        % else:
            <input name="${name}" type="hidden" value="${value or ''}">
        % endif
    % endfor
    % if not ctx.hide_category:
<%
        error = errors.get('category') if errors is not None else None
%>\
            <fieldset class="control-group${' error' if error else ''}">
                <label class="control-label" for="category">Catégorie</label>
                <div class="controls">
                    <input class="input-xlarge" id="category" name="category" type="text" value="${params['category'] or ''}">
        % if error:
                    <span class="help-inline">${error}</span>
        % endif
                </div>
            </fieldset>
    % endif
<%
    error = errors.get('term') if errors is not None else None
%>\
            <fieldset class="control-group${' error' if error else ''}">
                <label class="control-label" for="term">Intitulé</label>
                <div class="controls">
                    <input class="input-xlarge" id="term" name="term" type="text" value="${params['term'] or ''}">
    % if error:
                    <span class="help-inline">${error}</span>
    % endif
                </div>
            </fieldset>
<%
    error = errors.get('territory') if errors is not None else None
%>\
            <fieldset class="control-group${' error' if error else ''}">
                <label class="control-label" for="territory">Territoire</label>
                <div class="controls">
                    <input class="input-xlarge" id="territory" name="territory" type="text" value="${params['territory'] or ''}">
    % if error:
                    <span class="help-inline">${error}</span>
    % endif
                </div>
            </fieldset>
    % if ctx.show_filter:
<%
        error = errors.get('filter') if errors is not None else None
%>\
            <fieldset class="control-group${' error' if error else ''}">
                <label class="control-label" for="filter">Afficher</label>
                <div class="controls">
                    <div class="control-list">
                        <label>
                            <input${' checked' if not params['filter'] else ''} name="filter" type="radio" value="">
                            <span>Tous les organismes</span>
                        </label>
                        <label>
                            <input${' checked' if params['filter'] == 'competence' else ''} name="filter" type="radio" value="competence">
                            <span>Uniquement les organismes compétents pour le territoire</span>
                        </label>
                        <label>
                            <input${' checked' if params['filter'] == 'presence' else ''} name="filter" type="radio" value="presence">
                            <span>Uniquement les organismes présents sur le territoire</span>
                        </label>
                    </div>
        % if error:
                    <p class="help-text">${error}</p>
        % endif
                </div>
            </fieldset>
    % endif
            <fieldset class="form-actions">
                <input class="btn primary" type="submit" value="${_('Search')}">
            </fieldset>
        </form>
        <ul class="tabs">
<%
    modes_infos = (
        (u'carte', u'Carte'),
        (u'liste', u'Liste'),
        (u'annuaire', u'Annuaire'),
        (u'export', u'Export'),
        )
%>\
    % for tab_mode, tab_name in modes_infos:
            <li${' class="active"' if tab_mode == mode else '' | n}>
                <a class="internal" href="${urls.get_url(ctx, tab_mode, **params)}">${tab_name}</a>
            </li>
    % endfor
        </ul>
##    % if errors is None:
        <%self:results/>
##    % endif
</%def>


<%def name="footer_data_p_content()" filter="trim">
${parent.footer_data_p_content()}
    % if conf.get('petitpois_url'):
 &mdash; <a class="btn" href="${urlparse.urljoin(conf['petitpois_url'], '/poi/search'
        )}" rel="external">Ajouter une fiche</a>
    % endif
</%def>


<%def name="scripts()" filter="trim">
    <%parent:scripts/>
    <script src="/js/categories.js"></script>
    <script src="/js/territories.js"></script>
    <script>
var etalage = etalage || {};
etalage.categories.tags = ${ctx.category_tags_slug | n, js};
etalage.territories.autocompleterUrl = ${urlparse.urljoin(conf['territoria_url'],
    '/api/v1/autocomplete-territory') | n, js};
etalage.params = ${params | n, js};

$(function () {
    etalage.categories.createAutocompleter($('#category'));
    etalage.territories.createAutocompleter($('#territory'));
});
    </script>
</%def>

