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
import urlparse

from poiscasse import conf
%>


<%def name="css()" filter="trim">
    <link rel="stylesheet" href="${conf['leaflet.css']}">
<!--[if lte IE 8]>
    <link rel="stylesheet" href="${conf['leaflet.ie.css']}">
<![endif]-->
    <link rel="stylesheet" href="${conf['jquery-ui.css']}">

    <link rel="stylesheet" href="/css/poi.css">
    <link rel="stylesheet" href="/css/site.css">
</%def>


<%def name="metas()" filter="trim">
    <meta charset="utf-8">
</%def>


<%def name="scripts()" filter="trim">
    <script src="${conf['jquery.js']}"></script>
    <script src="${conf['jquery-ui.js']}"></script>
    <script src="${conf['leaflet.js']}"></script>
<!--[if lt IE 10]>
    <script src="${conf['pie.js']}"></script>
<![endif]-->

    <script src="/js/categories.js"></script>
    <script src="/js/map.js"></script>
    <script src="/js/territories.js"></script>
    <script src="/js/poiscasse.js"></script>
    % if ctx.container_base_url is not None and ctx.gadget_id is not None:
    <script src="${conf['easyxdm.js']}"></script>
    <script>
easyXDM.DomHelper.requiresJSON('${conf['json2.js']}');
var rpc = new easyXDM.Rpc({
    swf: '${conf['easyxdm.swf']}'
},
{
    remote: {
        adjustHeight: {},
        requestNavigateTo: {}
    }
});
    </script>
    % endif
    <script>
var etalage = etalage || {};
etalage.map.organismsUrl = 'http://localhost:5001/api/v1/geojson/organismes/';
etalage.territories.autocompleterUrl = ${urlparse.urljoin(conf['territoria_url'],
    '/api/v1/autocomplete-territory') | n, js};


    % if ctx.container_base_url is not None and ctx.gadget_id is not None:
$(function () {
    $('#search-form').submit(function () {
        console.log('submit');
        return false;
    });
    etalage.init();
});
    % endif
    </script>
</%def>


<%def name="title()" filter="trim">
Open Data POIs Portal
</%def>


<%def name="trackers()" filter="trim">
</%def>


<!DOCTYPE html>
<html lang="fr">
<head>
    <%self:metas/>
    <title>${self.title()}</title>
    <%self:css/>
    <%self:scripts/>
</head>
<body>
    ${capture(next.body) | n, trim}
    <%self:trackers/>
</body>
</html>

