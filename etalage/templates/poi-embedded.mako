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

from etalage import conf
%>


<%namespace file="/poi.mako" name="pois"/>
<%namespace file="/site.mako" name="site"/>


        <script src="${conf['leaflet.js']}"></script>
<!--[if lt IE 10]>
        <script src="${conf['pie.js']}"></script>
<![endif]-->
        <script src="${urlparse.urljoin(req.url, '/js/map.js')}"></script>
        <script>
(function ($) {
    var $head = $('head');
    $head.append($('<link/>', {rel: 'stylesheet', href: ${conf['leaflet.css'] | n, js}}));
    if ($.browser.msie && $.browser.version.substr(0, 1) <= 8) {
        $head.append($('<link/>', {rel: 'stylesheet', href: ${conf['leaflet.ie.css'] | n, js}}));
    }
    etalage.map.markersUrl = ${conf['markers_url'].rstrip('/') | n, js};
    etalage.map.tileLayersOptions = ${conf['tile_layers'] | n, js};
})(jQuery);
        </script>
        <%pois:container_content/>
        <hr>
        <div>
            <%site:footer_content/>
        </div>
