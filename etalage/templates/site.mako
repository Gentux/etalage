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
from etalage import conf
%>


<%def name="body_content()" filter="trim">
    % if ctx.container_base_url is not None and ctx.gadget_id is not None:
    <div class="container-fluid">
        <%self:container_content/>
        <%self:footer/>
    </div>
    % else:
    <%self:topbar/>
    <div class="container">
        <%self:container_content/>
        <%self:footer/>
    </div>
    % endif
</%def>


<%def name="container_content()" filter="trim">
</%def>


<%def name="css()" filter="trim">
    <link rel="stylesheet" href="${conf['bootstrap.css']}">
    <link rel="stylesheet" href="${conf['jquery-ui.css']}">
##    <link rel="stylesheet" href="/css/site.css">
    % if ctx.container_base_url is not None and ctx.gadget_id is not None:
    <link rel="stylesheet" href="/css/gadget.css">
    % else:
    <link rel="stylesheet" href="/css/standalone.css">
    % endif
</%def>


<%def name="footer()" filter="trim">
        <footer>
            <p>Page réalisée en <a href="http://www.comarquage.fr/" rel="external">co-marquage</a>.
        </footer>
</%def>


<%def name="metas()" filter="trim">
    <meta charset="utf-8">
</%def>


<%def name="scripts()" filter="trim">
<!--[if lt IE 9]>
    <script src="http://html5shim.googlecode.com/svn/trunk/html5.js"></script>
<![endif]-->
    <script src="${conf['jquery.js']}"></script>
    <script src="${conf['jquery-ui.js']}"></script>
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


## Adjust frame height for 5 seconds.
var adjustFrameHeightCount = 5 * 5;
var frameHeight = null;

function adjustFrameHeight() {
    var frameNewHeight = $('body', document).height();
    if (frameNewHeight != frameHeight) {
        rpc.adjustHeight(frameNewHeight);
        frameHeight = frameNewHeight;
    }
    if (adjustFrameHeightCount-- >= 0) {
        setTimeout(adjustFrameHeight, 200);
    }
}


$(function () {
    adjustFrameHeight();

    $('form.internal').on('submit', function (event) {
        rpc.requestNavigateTo($(this).attr('action'), $(this).serializeArray().concat({
            name: 'submit',
            value: 'Submit'
        }));
        return false;
    });

    $('a.internal').on('click', function () {
        rpc.requestNavigateTo($(this).attr('href'));
        return false;
    });

    $('a[href][rel=bookmark]').attr('target', '_blank');
    $('a[href][rel=mobile]').attr('target', '_blank');
    $('a[href][rel=external]').attr('target', '_blank');
});
    </script>
    % endif
</%def>


<%def name="title_content()" filter="trim">
Étalage - Comarquage.fr
</%def>


<%def name="topbar()" filter="trim">
    <div class="topbar">
        <div class="topbar-inner">
            <div class="container">
                <a class="brand" href="http://www.comarquage.fr/">Comarquage.fr</a>
                <ul class="nav">
                    <li><a href="http://petitpois.comarquage.fr/">Annuaire</a></li>
                    <li><a href="http://cosmetic3.comarquage.fr/">Droits et démarches</a></li>
                </ul>
            </div>
        </div>
    </div>
</%def>


<%def name="trackers()" filter="trim">
</%def>


<!DOCTYPE html>
<html lang="fr">
<head>
    <%self:metas/>
    <title>${self.title_content()}</title>
    <%self:css/>
    <%self:scripts/>
</head>
<body>
    <%self:body_content/>
    <%self:trackers/>
</body>
</html>

