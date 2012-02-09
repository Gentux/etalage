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
<%namespace name="searchform" file="search-form.mako"/>
<%namespace name="indextabs" file="index-tabs.mako"/>


<%def name="container_content()" filter="trim">
        <form action="${urls.get_url(ctx, mode)}" class="form-horizontal internal" id="search-form" method="get">
            <%searchform:search_form_content/>
        </form>
        <%indextabs:index_tabs/>
##    % if errors is None:
        <%self:results/>
##    % endif
</%def>


<%def name="footer_data_p_content()" filter="trim">
${parent.footer_data_p_content()}
    % if conf.get('petitpois_url'):
 &mdash; <a class="label notice" href="${urlparse.urljoin(conf['petitpois_url'], '/poi/search'
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

