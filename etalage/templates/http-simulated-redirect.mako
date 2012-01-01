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


<%doc>Redirection page that, in gadget mode, replaces a HTTP redirect</%doc>


<%!
from etalage import urls
%>

<%inherit file="/site.mako"/>


<%def name="container_content()" filter="trim">
        <h2>${_("Redirection in progress...")}</h2>
        <div class="alert-message info">
            <p>
                ${_(u"You'll be redirected to page")}
                <a class="internal" href="${urls.get_url(ctx, *url_args, **url_kwargs)}">${urls.get_url(
                    ctx, *url_args, **url_kwargs)}</a>.
            </p>
        </div>
</%def>


<%def name="scripts()" filter="trim">
        <%parent:scripts/>
        <script type="text/javascript">
rpc.requestNavigateTo(${urls.get_url(ctx, *url_args, **url_kwargs) | n, js});
        </script>
</%def>


<%def name="title_content()" filter="trim">
${_(u'Redirection')} - ${parent.title_content()}
</%def>

