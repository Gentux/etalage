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
from etalage import conf, model, urls
%>


<%inherit file="/index.mako"/>


<%def name="css()" filter="trim">
    <%parent:css/>
    <link rel="stylesheet" href="${conf['leaflet.css']}">
<!--[if lte IE 8]>
    <link rel="stylesheet" href="${conf['leaflet.ie.css']}">
<![endif]-->
    <link rel="stylesheet" href="/css/map.css">
</%def>


<%def name="results()" filter="trim">
    <div class="well" id="map" style="height: 400px;"></div>

    <div class="legend-text well">
        <p><strong>Légende</strong> :</p>
        <ul class="unstyled">
            <li>
                <img class="legend-icon" src="${conf['markers_url'].rstrip('/')}/misc/blueblank.png">
                L'organisme a une compétence géographique sur le territoire recherché (compétent par nature).
            </li>

            <li>
                <img class="legend-icon" src="${conf['markers_url'].rstrip('/')}/misc/greenvalid.png">
                L'organisme a une compétence administrative sur le territoire recherché.
            </li>

            <li>
                <img class="legend-icon" src="${conf['markers_url'].rstrip('/')}/misc/bluemultiple.png">
                Plusieurs organismes sont présents à cet endroit (idem pour vert et rouge).
            </li>

            <li>
                <img class="legend-icon" src="${conf['markers_url'].rstrip('/')}/misc/redinvalid.png">
                L'organisme n'est pas compétent sur le territoire recherché.
            </li>

            <li>
                <img class="legend-icon" src="${conf['markers_url'].rstrip('/')}/map-icons-collection-2.0/icons/home.png">
                Centre du territoire recherché.
            </li>
        </ul>
    </div>
</%def>


<%def name="scripts()" filter="trim">
    <%parent:scripts/>
    <script src="${conf['leaflet.js']}"></script>
<!--[if lt IE 10]>
    <script src="${conf['pie.js']}"></script>
<![endif]-->
    <script src="/js/map.js"></script>
    <script>
    % if territory is not None and territory.geo is not None:
etalage.map.center = new L.LatLng(${territory.geo[0] | n, js}, ${territory.geo[1] | n, js});
    % endif
etalage.map.geojsonParams = ${dict(
    (model.Poi.rename_input_to_param(name), value)
    for name, value in inputs.iteritems()
    if name not in ('bbox', 'context', 'jsonp') and value is not None
    )| n, js};
etalage.map.geojsonUrl = '/api/v1/annuaire/geojson';
etalage.map.markersUrl = ${conf['markers_url'].rstrip('/') | n, js};
etalage.map.tileLayersOptions = ${conf['tile_layers'] | n, js};


$(function () {
    etalage.map.createMap('map', ${bbox | n, js});
});
    </script>
</%def>


<%def name="title_content()" filter="trim">
${_(u'Map')} - ${parent.title_content()}
</%def>

