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
        <%self:search_form/>
        <%self:index_tabs/>
##    % if errors is None:
        <%self:results/>
##    % endif
</%def>


<%def name="footer_actions()" filter="trim">
    % if conf.get('petitpois_url'):
            <p class="pull-right">
                <a class="label label-info" href="${urlparse.urljoin(conf['petitpois_url'], '/poi/search'
        )}" rel="external">Ajouter une fiche</a>
            </p>
    % endif
</%def>


<%def name="index_tabs()" filter="trim">
        <ul class="nav nav-tabs">
<%
    modes_infos = (
        (u'carte', u'Carte', conf['hide_map']),
        (u'liste', u'Liste', False),
        (u'annuaire', u'Annuaire', conf['hide_directory'] or ctx.hide_directory),
        (u'gadget', u'Partage', conf['hide_gadget']),
        (u'export', u'Export', conf['hide_export']),
        )
    url_args = dict(
        (dict(categories = 'category').get(name, name), value)
        for name, value in inputs.iteritems()
        if name != 'page' and value is not None
        )
%>\
    % for tab_mode, tab_name, tab_hidden in modes_infos:
<%
        if tab_hidden:
            continue
%>\
            <li${' class="active"' if tab_mode == mode else '' | n}>
                <a class="internal" href="${urls.get_url(ctx, tab_mode, **url_args)}">${tab_name}</a>
            </li>
    % endfor
        </ul>
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
etalage.territories.kinds = ${conf['territories_kinds'] | n, js};
etalage.params = ${inputs | n, js};

$(function () {
    etalage.categories.createAutocompleter($('#category'));
    etalage.territories.createAutocompleter($('#territory'));
});
    </script>
</%def>


<%def name="search_form()" filter="trim">
        <form action="${urls.get_url(ctx, mode)}" class="form-horizontal internal" id="search-form" method="get">
            <%self:search_form_content/>
        </form>
</%def>


<%def name="search_form_content()" filter="trim">
    % for name, value in sorted(inputs.iteritems()):
<%
        if name in (
                'bbox',
                'category' if not ctx.hide_category else None,
                'filter' if ctx.show_filter else None,
                'page',
                'term' if not ctx.hide_term else None,
                'territory' if not ctx.hide_territory else None,
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
            <fieldset>
    % if not ctx.hide_category:
<%
        error = errors.get('categories') if errors is not None else None
        if error and isinstance(error, dict):
            error_index, error_message = sorted(error.iteritems())[0]
        else:
            error_index = None
            error_message = error
%>\
                <div class="control-group${' error' if error else ''}">
                    <label class="control-label" for="category">Catégorie</label>
                    <div class="controls">
    % if categories:
        % for category_index, category in enumerate(categories):
            % if error is None or category_index not in error:
                        <label class="checkbox"><input checked name="category" type="checkbox" value="${category.name}">
                            <span class="label label-success"><i class="icon-tag icon-white"></i>
                            ${category.name}</span></label>
            % endif
        % endfor
    % endif
                        <input class="input-xlarge" id="category" name="category" type="text" value="${inputs['category'][error_index] \
                                if error_index is not None else ''}">
        % if error_message:
                        <span class="help-inline">${error_message}</span>
        % endif
                    </div>
                </div>
    % endif
    % if not ctx.hide_term:
<%
        error = errors.get('term') if errors is not None else None
%>\
                <div class="control-group${' error' if error else ''}">
                    <label class="control-label" for="term">Intitulé</label>
                    <div class="controls">
                        <input class="input-xlarge" id="term" name="term" type="text" value="${inputs['term'] or ''}">
        % if error:
                        <span class="help-inline">${error}</span>
        % endif
                    </div>
                </div>
    % endif
    % if not ctx.hide_territory:
<%
        error = errors.get('territory') if errors is not None else None
%>\
                <div class="control-group${' error' if error else ''}">
                    <label class="control-label" for="territory">Territoire</label>
                    <div class="controls">
                        <input class="input-xlarge" id="territory" name="territory" type="text" value="${inputs['territory'] or ''}">
        % if error:
                        <span class="help-inline">${error}</span>
        % endif
                    </div>
                </div>
    % endif
    % if ctx.show_filter:
<%
        error = errors.get('filter') if errors is not None else None
%>\
                <div class="control-group${' error' if error else ''}">
                    <label class="control-label" for="filter">Afficher</label>
                    <div class="controls">
                        <label class="radio">
                            <input${' checked' if not inputs['filter'] else ''} name="filter" type="radio" value="">
                            Tous les organismes
                        </label>
                        <label class="radio">
                            <input${' checked' if inputs['filter'] == 'competence' else ''} name="filter" type="radio" value="competence">
                            Uniquement les organismes compétents pour le territoire
                        </label>
                        <label class="radio">
                            <input${' checked' if inputs['filter'] == 'presence' else ''} name="filter" type="radio" value="presence">
                            Uniquement les organismes présents sur le territoire
                        </label>
        % if error:
                        <p class="help-block">${error}</p>
        % endif
                    </div>
                </div>
    % endif
                <div class="form-actions">
                    <button class="btn btn-primary" type="submit"><i class="icon-search icon-white"></i> ${_('Search')}</button>
                </div>
            <fieldset>
</%def>

