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
import urlparse

from etalage import conf, urls
%>


<%inherit file="/site.mako"/>


<%def name="container_content()" filter="trim">
        <form action="${urls.get_url(ctx, mode)}" class="internal" id="search-form" method="get">
            <fieldset>
    % for name, value in sorted(params.iteritems()):
<%
        if name in (
                'category' if not ctx.hide_category else None,
                'filter',
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
                <div class="clearfix${' error' if error else ''}">
                    <label for="category">Catégorie</label>
                    <div class="input">
                        <input class="span6" id="category" name="category" type="text" value="${params['category'] or ''}">
        % if error:
                        <span class="help-inline">${error}</span>
        % endif
                    </div>
                </div>
    % endif
<%
    error = errors.get('term') if errors is not None else None
%>\
                <div class="clearfix${' error' if error else ''}">
                    <label for="term">Intitulé</label>
                    <div class="input">
                        <input class="span6" id="term" name="term" type="text" value="${params['term'] or ''}">
    % if error:
                        <span class="help-inline">${error}</span>
    % endif
                    </div>
                </div>
<%
    error = errors.get('territory') if errors is not None else None
%>\
                <div class="clearfix${' error' if error else ''}">
                    <label for="territory">Territoire</label>
                    <div class="input">
                        <input class="span6" id="territory" name="territory" type="text" value="${params['territory'] or ''}">
    % if error:
                        <span class="help-inline">${error}</span>
    % endif
                    </div>
                </div>
<%
    error = errors.get('filter') if errors is not None else None
%>\
                <div class="clearfix${' error' if error else ''}">
                    <label for="filter">Afficher</label>
                    <div class="input">
                        <ul class="inputs-list">
                            <li>
                                <label>
                                    <input${' checked' if not params['filter'] else ''} name="filter" type="radio" value="">
                                    <span>Tous les organismes</span>
                                </label>
                            </li>
                            <li>
                                <label>
                                    <input${' checked' if params['filter'] == 'competence' else ''} name="filter" type="radio" value="competence">
                                    <span>Uniquement les organismes compétents pour le territoire</span>
                                </label>
                            </li>
                            <li>
                                <label>
                                    <input${' checked' if params['filter'] == 'presence' else ''} name="filter" type="radio" value="presence">
                                    <span>Uniquement les organismes présents sur le territoire</span>
                                </label>
                            </li>
                        </ul>
    % if error:
                        <span class="help-inline">${error}</span>
    % endif
                    </div>
                </div>
                <div class="actions">
                    <input class="btn primary" type="submit" value="${_('Search')}">
                </div>
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
        ## There is a bug in the tabs CSS above that requires a style="clear: left;".
        ## Remove the div below once it is repaired.
        <div style="clear: left;">
##    % if errors is None:
        <%self:results/>
##    % endif
        </div>
</%def>


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
                        <a class="internal" href="${urls.get_url(ctx, mode, page = pager.page_number - 1, **url_args
                                )}">&larr; ${_(u"Previous")}</a>
                    </li>
        % for page_number in range(max(pager.page_number - 5, 1), pager.page_number):
                    <li>
                        <a class="internal" href="${urls.get_url(ctx, mode, class_ = 'page', page = page_number,
                                **url_args)}">${page_number}</a>
                    </li>
        % endfor
                    <li class="active">
                        <a class="internal" href="${urls.get_url(ctx, mode, page = pager.page_number, **url_args
                                )}">${pager.page_number}</a>
                    </li>
        % for page_number in range(pager.page_number + 1, min(pager.page_number + 5, pager.last_page_number) + 1):
                    <li>
                        <a class="internal" href="${urls.get_url(ctx, mode, class_ = 'page', page = page_number,
                                **url_args)}">${page_number}</a>
                    </li>
        % endfor
                    <li class="next${' disabled' if pager.page_number >= pager.last_page_number else ''}">
                        <a class="internal" href="${urls.get_url(ctx, mode, page = pager.page_number + 1, **url_args
                                )}">${_(u"Next")} &rarr;</a>
                    </li>
                </ul>
            </div>
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

