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


<%def name="breadcrumb_content()" filter="trim">
            <%parent:breadcrumb_content/>
            <li class="active">${_(u'Redirection')}</li>
</%def>


<%def name="container_content()" filter="trim">
        <div class="alert alert-block alert-info">
            <h2 class="alert-heading">${_("Redirection in progress...")}</h2>
            ${_(u"You'll be redirected to page")}
            <a class="internal" href="${urls.get_url(ctx, *url_args, **url_kwargs)}">${urls.get_url(
                    ctx, *url_args, **url_kwargs)}</a>.
        </div>
</%def>


<%def name="scripts_domready_content()" filter="trim">
    <%parent:scripts_domready_content/>
    etalage.rpc.requestNavigateTo(${urls.get_url(ctx, *url_args, **url_kwargs) | n, js});
</%def>


<%def name="title_content()" filter="trim">
${_(u'Redirection')} - ${parent.title_content()}
</%def>

