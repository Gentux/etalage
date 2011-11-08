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
import urlparse
import uuid

from etalage import conf, urls
%>


<%def name="body_content()" filter="trim">
    <div class="container-fluid">
        <%self:container_content/>
    </div>
</%def>


<%def name="container_content()" filter="trim">
</%def>


<%def name="css()" filter="trim">
    <link rel="stylesheet" href="${conf['bootstrap.css']}">
    <link rel="stylesheet" href="${conf['jquery-ui.css']}">
    % if ctx.container_base_url is not None and ctx.gadget_id is not None:
    <link rel="stylesheet" href="/css/gadget.css">
    % endif
</%def>


<%def name="internal_a(ctx, *args, **kwargs)" filter="trim">
<%
    class_ = u' '.join(
        fragment
        for fragment in (
            kwargs.pop('class_', None),
            'internal',
            )
        if fragment
        )
    id = kwargs.pop('id', None)
    if id is None:
        id = u'a-{0}'.format(uuid.uuid4())
%>\
    <a class="${class_}" href="${urls.get_url(ctx, *args, **kwargs)}" id="${id}">${caller.body()}</a>
    % if ctx.container_base_url is not None and ctx.gadget_id is not None:
    <script>
$('a#${id}').data('navigation', ${urls.get_navigation_params(ctx, *args, **kwargs) | n, js})
    </script>
    % endif
</%def>


<%def name="internal_form(ctx, *args, **kwargs)" filter="trim">
<%
    class_ = u' '.join(
        fragment
        for fragment in (
            kwargs.pop('class_', None),
            'internal',
            )
        if fragment
        )
    id = kwargs.pop('id', None)
    if id is None:
        id = u'form-{0}'.format(uuid.uuid4())
    method = kwargs.pop('method', 'get')
%>\
    <form class="${class_}" action="${urls.get_url(ctx, *args, **kwargs)}" id="${id}" method="${method}">${caller.body(
        )}</form>
    % if ctx.container_base_url is not None and ctx.gadget_id is not None:
    <script>
$('form#${id}').data('navigation', ${urls.get_navigation_params(ctx, *args, **kwargs) | n, js})
    </script>
    % endif
</%def>


<%def name="metas()" filter="trim">
    <meta charset="utf-8">
</%def>


<%def name="scripts()" filter="trim">
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

$(function () {
    rpc.adjustHeight($('body', document).height());

    $('form.internal').submit(function (event) {
        rpc.requestNavigateTo($(this).data('navigation').concat($(this).serializeArray()).concat({
            name: 'submit',
            value: 'Submit'
        }));
        return false;
    });

    $('a.internal').click(function () {
        rpc.requestNavigateTo($(this).data('navigation'));
        return false;
    });
});
    </script>
    % endif
</%def>


<%def name="title_content()" filter="trim">
Open Data POIs Portal
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

