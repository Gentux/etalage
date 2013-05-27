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
from etalage import conf
%>


<%def name="body_content()" filter="trim">
    % if ctx.container_base_url is None or ctx.gadget_id is None:
    <%self:topbar/>
    <%self:site_header/>
    % endif
    <div class="container-fluid"><div class="row-fluid">
        <%self:container_content/>
        <%self:footer/>
    </div></div>
</%def>


<%def name="container_content()" filter="trim">
</%def>


<%def name="css()" filter="trim">
    <link rel="stylesheet" href="${conf['bootstrap.css']}">
    <link rel="stylesheet" href="${conf['bootstrap-responsive.css']}">
    <link rel="stylesheet" href="${conf['jquery-ui.css']}">
    <link rel="stylesheet" href="/css/site.css">
    % if ctx.container_base_url is not None and ctx.gadget_id is not None:
    <link rel="stylesheet" href="/css/gadget.css">
    % else:
    <link rel="stylesheet" href="/css/standalone.css">
    <link rel="stylesheet" href="/css/responsive.css">
    % endif
    % if getattr(ctx, 'custom_css_url', None):
    <link rel="stylesheet" href="${ctx.custom_css_url}">
    % endif
</%def>

<%def name="feeds()" filter="trim">
    <link rel="alternate" type="application/atom+xml" href="/feed">
</%def>

<%def name="footer()" filter="trim">
        <footer class="footer">
            <%self:footer_content/>
        </footer>
</%def>


<%def name="footer_content()" filter="trim">
            <%self:footer_actions/>
            <%self:footer_service/>
            <p>
                <%self:footer_data_p_content/>
            </p>
            <p>
                Logiciel :
                <a href="http://gitorious.org/infos-pratiques/etalage" rel="external">Etalage</a>
                &mdash;
                <span>Copyright © 2011, 2012, 2013 <a href="http://www.easter-eggs.com/" rel="external"
                        title="Easter-eggs, société de services en logiciels libres">Easter-eggs</a></span>
                &mdash;
                Licence libre
                <a href="http://www.gnu.org/licenses/agpl.html" rel="external">${_(
                    'GNU Affero General Public License')}</a>
            </p>
</%def>


<%def name="footer_actions()" filter="trim">
</%def>


<%def name="footer_data_p_content()" filter="trim">
                Page réalisée en <a href="http://www.comarquage.fr/" rel="external"
                        title="Comarquage.fr">co-marquage</a>
                &mdash;
                Données :
                <a href="http://www.data.gouv.fr/Licence-Ouverte-Open-Licence" rel="external">Licence ouverte</a>
</%def>


<%def name="footer_service()" filter="trim">
</%def>


<%def name="metas()" filter="trim">
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</%def>


<%def name="scripts()" filter="trim">
<!--[if lt IE 9]>
    <script src="//html5shim.googlecode.com/svn/trunk/html5.js"></script>
<![endif]-->
    <script src="${conf['jquery.js']}"></script>
    <script src="${conf['jquery-ui.js']}"></script>
    <script src="${conf['bootstrap.js']}"></script>
    % if ctx.container_base_url is not None and ctx.gadget_id is not None:
    <script src="${conf['easyxdm.js']}"></script>
    <script>
easyXDM.DomHelper.requiresJSON("${conf['json2.js']}");
var etalage = etalage || {};
if (!etalage.easyXDM) {
    etalage.easyXDM = easyXDM.noConflict("etalage");
}
    </script>
    <script src="/js/gadget.js"></script>
    <script>
var swfUrl = ${conf['easyxdm.swf'] | n, js};
if (swfUrl.search(/\/\//) === 0) {
    swfUrl = document.location.protocol + swfUrl;
}
etalage.rpc = new etalage.easyXDM.Rpc({
    swf: swfUrl
},
{
    remote: {
        adjustHeight: {},
        requestNavigateTo: {}
    }
});
    </script>
    % endif
</%def>


<%def name="scripts_domready()" filter="trim">
    <script>
$(function () {
    <%self:scripts_domready_content/>
});
    </script>
</%def>


<%def name="scripts_domready_content()" filter="trim">
    % if ctx.container_base_url is not None and ctx.gadget_id is not None:
    initGadget();
    % endif
</%def>


<%def name="site_header()" filter="trim">
</%def>


<%def name="title_content()" filter="trim">
Étalage - Comarquage.fr
</%def>


<%def name="topbar()" filter="trim">
    <div class="navbar navbar-inverse navbar-fixed-top">
        <div class="navbar-inner">
            <div class="container-fluid">
                <a class="brand" href="${conf['brand_url']}">${conf['brand_name']}</a>
                <ul class="nav">
                    <li><a href="http://petitpois.comarquage.fr/">Annuaire</a></li>
                    <li><a href="http://cosmetic3.comarquage.fr/">Droits et démarches</a></li>
                </ul>
            </div>
        </div>
    </div>
</%def>


<%def name="trackers()" filter="trim">
    % if conf.get('markers.piwik.id'):
    <!-- Piwik -->
    <script type="text/javascript">
var pkBaseURL = (("https:" == document.location.protocol) ? ${conf['markers.piwik.ssl_host'] | n, js} : ${conf['markers.piwik.host'] | n, js});
document.write(unescape("%3Cscript src='" + pkBaseURL + "piwik.js' type='text/javascript'%3E%3C/script%3E"));
    </script><script type="text/javascript">
try {
    var piwikTracker = Piwik.getTracker(pkBaseURL + "piwik.php", ${conf['markers.piwik.id']});
    % if ctx.container_base_url is not None:
    piwikTracker.setCustomVariable(2, "container_base_url", ${ctx.container_base_url | n, js}, "visit");
    % endif
    piwikTracker.trackPageView();
    piwikTracker.enableLinkTracking();
} catch( err ) {}
    </script><noscript><p><img src="${conf['markers.piwik.host']}/piwik.php?idsite=${conf['markers.piwik.id']}" style="border:0" alt="" /></p></noscript>
    <!-- End Piwik Tracking Code -->
    % endif
</%def>


<!DOCTYPE html>
<html lang="${ctx.lang[0][:2]}">
<head>
    <%self:metas/>
    <title>${self.title_content()}</title>
    <%self:feeds/>
    <%self:css/>
    <%self:scripts/>
    <%self:scripts_domready/>
</head>
<body>
    <%self:body_content/>
    <%self:trackers/>
</body>
</html>

