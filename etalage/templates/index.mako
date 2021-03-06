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

from etalage import conf, model, ramdb, urls


def is_category_autocompleter_empty(categories):
    is_empty = False
    possible_pois_id = ramdb.intersection_set(
        model.Poi.ids_by_category_slug.get(category_slug)
        for category_slug in categories
        if model.Poi.ids_by_category_slug.get(category_slug)
        )
    if possible_pois_id is not None:
        categories_infos = sorted(
            (-count, category_slug)
            for count, category_slug in (
                (
                    len(set(model.Poi.ids_by_category_slug.get(category_slug, [])).intersection(possible_pois_id)),
                    category_slug,
                    )
                for category_slug in ramdb.iter_categories_slug(tags_slug = categories)
                if category_slug not in categories
                )
            if count > 0 and count != len(possible_pois_id)
            )
        if not categories_infos:
            is_empty = True
    return is_empty
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
    % if conf['petitpois_url']:
            <p class="pull-right">
                <a class="label label-info" href="${urlparse.urljoin(conf['petitpois_url'][0], '/poi/search')
                        }" rel="external">Ajouter une fiche</a>
            </p>
    % endif
</%def>


<%def name="index_tabs()" filter="trim">
<%
    modes_infos = (
        (u'carte', u'Carte', ctx.hide_map),
        (u'liste', u'Liste', ctx.hide_list),
        (u'annuaire', u'Annuaire', ctx.hide_directory),
        (u'gadget', u'Partage', ctx.hide_gadget),
        (u'export', u'Téléchargement', ctx.hide_export),
        )
    if len([mode_info[2] for mode_info in modes_infos if mode_info[2] is False]) <= 1:
        return ''
    url_args = dict(
        (model.Poi.rename_input_to_param(name), value)
        for name, value in inputs.iteritems()
        if name != 'page' and name not in model.Poi.get_visibility_params_names(ctx) and value is not None
        )
%>\
        <ul class="nav nav-tabs">
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
    <script src="/js/bind.js"></script>
    <script src="/js/categories.js"></script>
    <script src="/js/form.js"></script>
    <script src="/js/territories.js"></script>
<%
if errors is not None and errors.get('categories_slug'):
    category_tags_slug = ctx.category_tags_slug
elif categories_slug:
    ## Note: ``category_slug`` may be a category (and not a slug) when an error has occurred during
    ## categories_slug verification.
    category_tags_slug_set = set([
        category_slug if isinstance(category_slug, basestring) else (category_slug.slug if category_slug else None)
        for category_slug in categories_slug
        ])
    category_tags_slug = list(category_tags_slug_set.union(ctx.category_tags_slug or []))
else:
    category_tags_slug = []
%>
    <script>
var etalage = etalage || {};
etalage.categories.tags = ${category_tags_slug if not ctx.hide_checkboxes else ctx.base_categories_slug| n, js};
etalage.miscUrl = ${conf['images.misc.url'] | n, js};
etalage.territories.autocompleterUrl = ${urlparse.urljoin(conf['territoria_url'],
    '/api/v1/autocomplete-territory') | n, js};
etalage.territories.kinds = ${ctx.autocompleter_territories_kinds | n, js};
    % if ctx.base_territory is not None:
etalage.territories.base_territory = ${ctx.base_territory.main_postal_distribution_str | n, js};
    % endif
etalage.params = ${dict(
    (key, value)
    for key, value in inputs.iteritems()
    if errors is None or errors.get(key) is None
    ) | n, js};
    </script>
</%def>


<%def name="scripts_domready_content()" filter="trim">
    etalage.bind.loadingGif();
    etalage.categories.createAutocompleter($('#category'));
    etalage.territories.createAutocompleter($('#territory'));
    etalage.form.initSearchForm({
        error: ${errors is not None | n, js},
        isGadget: ${ctx.container_base_url is not None and ctx.gadget_id is not None | n, js},
        searchForm: $('#search-form')
    });
    <%parent:scripts_domready_content/>
</%def>


<%def name="search_form()" filter="trim">

        <div class="toolbar">
            <div class="toggle-search-form">
                <button class="btn btn-primary btn-search-form" data-toggle="collapse" data-target="#search-form-collapse">
                    ${_('Search')}
                    <i class="icon-plus-sign icon-white"> </i>
                </button>
<%
    url_args = dict(
        (model.Poi.rename_input_to_param(name), value)
        for name, value in inputs.iteritems()
        if name != 'page' and name not in model.Poi.get_visibility_params_names(ctx) and value is not None and \
            (errors is None or errors.get(key) is None)
        )
    url_args.update({
        'container_base_url': ctx.container_base_url,
        'gadget': ctx.gadget_id,
        })
%>\
                <a class="btn btn-warning btn-search-form" href="${urls.get_url(ctx, 'feed', **url_args)}" \
target="_blank" title="${_('RSS Feed')}">
                    <i class="icon-feed"></i>
                </a>
            </div>
        </div>

        <div class="collapse in" id="search-form-collapse">
            <form action="${urls.get_url(ctx, mode)}" class="form-horizontal internal" id="search-form" method="get">
                <%self:search_form_hidden/>
                <fieldset>
                    <%self:search_form_fields/>
                    <div class="control-group">
                        <div class="controls">
                            <button class="btn btn-primary" type="submit">
                                <i class="icon-search icon-white"></i> ${_('Search')}
                            </button>
                            <a class="btn btn-warning btn-atom-feed" href="${urls.get_url(ctx, 'feed', **url_args)}" \
target="_blank" title="${_('RSS Feed')}">
                                <i class="icon-feed"></i>
                            </a>
                        </div>
                    </div>
                </fieldset>
            </form>
        </div>
</%def>


<%def name="search_form_field_categories_slug()" filter="trim">
<%
    if ctx.hide_checkboxes == True:
        hide_category = is_category_autocompleter_empty(ctx.base_categories_slug or [])
    else:
        hide_category = False
%>
    % if model.Poi.is_search_param_visible(ctx, 'category') and not hide_category:
<%
        error = errors.get('categories_slug') if errors is not None else None
        if error and isinstance(error, dict):
            error_index, error_message = sorted(error.iteritems())[0]
        else:
            error_index = None
            error_message = error
%>\
                <div class="control-group${' error' if error else ''}">
                    <label class="control-label" for="category">Catégorie</label>
                    <div class="controls">
        % if categories_slug and not ctx.hide_checkboxes:
            % for category_index, category_slug in enumerate(categories_slug):
                % if error is None or category_index not in error:
<%
                    # Note: ``category_slug`` may be a category (and not a slug) when an error has occurred during
                    # categories_slug verification.
                    category = ramdb.category_by_slug[category_slug] \
                        if isinstance(category_slug, basestring) else category_slug
                    if category is None or category.slug in (ctx.base_categories_slug or []):
                        continue
%>\
                        <label class="checkbox"><input checked name="category" type="checkbox" value="${category.name}">
                            <span class="label label-success"><i class="icon-tag icon-white"></i>
                            ${category.name}</span></label>
                % endif
            % endfor
                        <input class="input-xlarge" id="category" name="category" type="text" \
value="${inputs['categories_slug'][error_index] if error_index is not None else ''}" \
${'disabled' if is_category_autocompleter_empty(categories_slug or []) else ''}>
        % elif categories_slug:
                        <input class="input-xlarge" id="category" name="category" type="text"\
value="${inputs['categories_slug'][0] if len(inputs['categories_slug']) > 0 else ''}">
        % else:
                        <input class="input-xlarge" id="category" name="category" type="text" value="">
        % endif
        % if error_message:
                        <span class="help-inline">${error_message}</span>
        % endif
                    </div>
                </div>
    % endif
</%def>


<%def name="search_form_field_term()" filter="trim">
    % if model.Poi.is_search_param_visible(ctx, 'term'):
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
</%def>


<%def name="search_form_field_territory()" filter="trim">
    % if model.Poi.is_search_param_visible(ctx, 'territory'):
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
</%def>


<%def name="search_form_fields()" filter="trim">
                <%self:search_form_field_categories_slug/>
                <%self:search_form_field_term/>
                <%self:search_form_field_territory/>
</%def>


<%def name="search_form_hidden()" filter="trim">
<%
    search_params_name = model.Poi.get_search_params_name(ctx)
%>\
    % for name, value in sorted(inputs.iteritems()):
<%
        name = model.Poi.rename_input_to_param(name)
        if name in search_params_name and model.Poi.is_search_param_visible(ctx, name):
            continue
        if name in model.Poi.get_visibility_params_names(ctx):
            continue
        if name in ('bbox', 'page'):
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
</%def>

