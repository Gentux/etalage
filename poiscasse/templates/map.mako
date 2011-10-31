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
%>


<%inherit file="/site.mako"/>


<%
    territory = u'{pd[0]} {pd[1]}'.format(pd = postal_distribution) if postal_distribution else u''

    url_params = urllib.urlencode({
        "category": category_slug or '',
        "term": term or '',
        "territory": territory,
        })
%>
<fieldset>
    <form action="${'/map' if mode == 'map' else '/'}" id="search-form" method="get">
        <label for="category">Catégorie</label>
        <input id="category" name="category" type="text" value="${category_slug or ''}"/>

        <br>

        <label for="term">Intitulé</label>
        <input id="term" name="term" type="text" value="${term or ''}">

        <br>

        <label for="territory">Territoire</label>
        <input id="territory" name="territory" type="text" value="${territory}">

        <br>

        <input id="submit" name="submit" type="submit" value"Rechercher">
    </form>
</fieldset>

<div>
    Résultat de ${((page_number - 1) * page_size) + 1} à ${page_number * page_size} <br>
    Nombre de résultat par page : ${page_size}
    % if page_number > 1:
    <a href='/map?page=${page_number - 1}&${url_params}'>Précédent</a>
    % endif
    % if page_number < pois_count / page_size:
    <a href='/map?page=${page_number + 1}&${url_params}'>Suivant</a>
    % endif
    <a href='/list?page=${page_number}&${url_params}'>Voir dans une liste</a>
</div>

<div id="map" style="height: 400px;">
</div>

