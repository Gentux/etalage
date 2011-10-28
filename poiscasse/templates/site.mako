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
from poiscasse import conf
%>


<%def name="css()" filter="trim">
    <link rel="stylesheet" href="${conf['leaflet.css']}" />
    <link rel="stylesheet" href="${conf['leaflet.ie.css']}" />
    <link rel="stylesheet" href="${conf['jquery-ui.css']}" />
</%def>


<%def name="head_content()" filter="trim">
    <%next:css/>
    <%next:meta/>
    <title>Open Data POIs portal</title>
    <%next:script/>
</%def>


<%def name="meta()" filter="trim">
    <meta charset="utf-8" />
</%def>


<%def name="script()" filter="trim">
    <script src="${conf['jquery.js']}"></script>
    <script src="${conf['jquery-ui.js']}"></script>
    <script src="${conf['leaflet.js']}"></script>
    <script src="/js/poiscasse.js"></script>
</%def>


<!DOCTYPE html>
<html lang="fr">
    <head>
        <%next:head_content/>
    </head>
    <body>
        ${capture(next.body) | n, trim}
    </body>
</html>

