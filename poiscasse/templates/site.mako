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
    <link rel="stylesheet" href="${conf['leaflet.css']}" />
<!--[if lte IE 8]>
    <link rel="stylesheet" href="${conf['leaflet.ie.css']}">
<![endif]-->
    <link rel="stylesheet" href="${conf['jquery-ui.css']}" />
</%def>


<%def name="metas()" filter="trim">
    <meta charset="utf-8" />
</%def>


<%def name="scripts()" filter="trim">
    <script src="${conf['jquery.js']}"></script>
    <script src="${conf['jquery-ui.js']}"></script>
    <script src="${conf['leaflet.js']}"></script>
    <script>
var etalage = etalage || {};
etalage.territoryAutocompleterUrl = ${urlparse.urljoin(conf['territoria_url'],
    '/api/v1/autocomplete-territory') | n, js};
    </script>
    <script src="/js/poiscasse.js"></script>
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

