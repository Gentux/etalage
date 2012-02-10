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


<%def name="search_form_content()" filter="trim">
    % for name, value in sorted(params.iteritems()):
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
                        <input class="input-xlarge" id="category" name="category" type="text" value="${params['category'][error_index] \
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
                        <input class="input-xlarge" id="term" name="term" type="text" value="${params['term'] or ''}">
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
                        <input class="input-xlarge" id="territory" name="territory" type="text" value="${params['territory'] or ''}">
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
                            <input${' checked' if not params['filter'] else ''} name="filter" type="radio" value="">
                            Tous les organismes
                        </label>
                        <label class="radio">
                            <input${' checked' if params['filter'] == 'competence' else ''} name="filter" type="radio" value="competence">
                            Uniquement les organismes compétents pour le territoire
                        </label>
                        <label class="radio">
                            <input${' checked' if params['filter'] == 'presence' else ''} name="filter" type="radio" value="presence">
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
