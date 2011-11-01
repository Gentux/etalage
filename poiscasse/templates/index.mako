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
import urllib
import urlparse

from poiscasse import conf
%>


<%inherit file="/site.mako"/>


<%def name="scripts()" filter="trim">
    <%parent:scripts/>
    <script src="/js/categories.js"></script>
    <script src="/js/territories.js"></script>
    <script>
var etalage = etalage || {};
etalage.categories.tags = ${ctx.category_tags_slug | n, js};
etalage.territories.autocompleterUrl = ${urlparse.urljoin(conf['territoria_url'],
    '/api/v1/autocomplete-territory') | n, js};
etalage.pager = ${dict(
    # Name of items follow Google JSON Style Guide http://google-styleguide.googlecode.com/svn/trunk/jsoncstyleguide.xml
    currentItemCount = pager.page_size,
    itemsPerPage = pager.page_max_size,
    pageIndex = pager.page_number,
    startIndex = pager.first_item_number,
    totalItems = pager.item_count,
    totalPages = pager.page_count,
    ) if errors is None else None | n, js};
etalage.params = ${params | n, js};

$(function () {
    etalage.categories.createAutocompleter($('#category'));
    etalage.territories.createAutocompleter($('#territory'));

    % if ctx.container_base_url is not None and ctx.gadget_id is not None:
    $('#search-form').submit(function () {
        return false;
    });
    % endif
});
    </script>
</%def>


<%def name="body_content()" filter="trim">
    <div class="container">
        <form action="${'/carte' if mode == 'map' else '/'}" id="search-form" method="get">
            <fieldset>
    % for name, value in params.iteritems():
<%
        if name in ('category', 'page', 'term', 'territory'):
            continue
%>\
                <input name="${name}" type="hidden" value="${value or ''}">
    % endfor
<%
    error = errors.get('category') if errors is not None else None
%>\
                <div class="clearfix${' error' if error else ''}">
                    <label for="category">Catégorie</label>
                    <div class="input">
                        <input id="category" name="category" type="text" value="${params['category'] or ''}">
    % if error:
                        <span class="help-inline">${error}</span>
    % endif
                    </div>
                </div>
<%
    error = errors.get('term') if errors is not None else None
%>\
                <div class="clearfix${' error' if error else ''}">
                    <label for="term">Intitulé</label>
                    <div class="input">
                        <input id="term" name="term" type="text" value="${params['term'] or ''}">
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
                        <input id="territory" name="territory" type="text" value="${params['territory'] or ''}">
    % if error:
                        <span class="help-inline">${error}</span>
    % endif
                    </div>
                </div>
                <div class="actions">
                    <input class="btn primary" type="submit" value="Rechercher">
                </div>
            </fieldset>
        </form>
<%
    url_params = urllib.urlencode(dict(
        (name, value)
        for name, value in params.iteritems()
        if name != 'page' and value is not None
        ))
%>\
    % if errors is None:
        % if pager.item_count == 0:
        <div>
            <em>Aucun organisme trouvé.</em>
        </div>
        % else:
        <div>
            Organismes ${pager.first_item_number} à ${pager.last_item_number} sur ${pager.item_count}<br>
            Nombre d'organismes par page : ${pager.page_size}
            % if pager.page_number > 1:
            <a href='/?page=${pager.page_number - 1}&${url_params}'>Précédent</a>
            % endif
            % if pager.page_number < pager.item_count / pager.page_size:
            <a href='/?page=${pager.page_number + 1}&${url_params}'>Suivant</a>
            % endif
            <a href='/carte?page=${pager.page_number}&${url_params}'>Voir sur une carte</a>
        </div>
        <%self:results/>
        % endif
    % endif
    </div>
</%def>

