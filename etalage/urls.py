# -*- coding: utf-8 -*-


# Etalage -- Open Data POIs portal
# By: Emmanuel Raviart <eraviart@easter-eggs.com>
#     Romain Soufflet <rsoufflet@easter-eggs.com>
#
# Copyright (C) 2011 Easter-eggs
# http://gitorious.org/infos-pratiques/etalage
#
# This file is part of Etalage.
#
# Etalage is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# Etalage is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


"""Helpers for URLs"""


import re
import urllib
import urlparse

from biryani import strings

from . import contexts, wsgihelpers


application_url = None # Set to req.application_url as soon as Wenoit application is called.


def get_base_url(ctx, full = False):
    base_url = application_url.rstrip('/')
    if not full:
        # When a full URL is not requested, remove scheme and network location from it.
        base_url = urlparse.urlsplit(base_url).path
    return base_url


def get_full_url(ctx, *path, **query):
    path = [
        urllib.quote(unicode(sub_fragment).encode('utf-8'), safe = ',/:').decode('utf-8')
        for fragment in path
        if fragment
        for sub_fragment in unicode(fragment).split(u'/')
        if sub_fragment
        ]
    query = dict(
        (str(name), strings.deep_encode(value))
        for name, value in sorted(query.iteritems())
        if value is not None
        )
    return u'{0}/{1}{2}'.format(get_base_url(ctx, full = True), u'/'.join(path),
        ('?' + urllib.urlencode(query, doseq = True)) if query else '')


def get_url(ctx, *path, **query):
    path = [
        urllib.quote(unicode(sub_fragment).encode('utf-8'), safe = ',/:').decode('utf-8')
        for fragment in path
        if fragment
        for sub_fragment in unicode(fragment).split(u'/')
        if sub_fragment
        ]
    query = dict(
        (str(name), strings.deep_encode(value))
        for name, value in sorted(query.iteritems())
        if value is not None
        )
    return u'{0}/{1}{2}'.format(get_base_url(ctx), u'/'.join(path),
        ('?' + urllib.urlencode(query, doseq = True)) if query else '')


def make_router(*routings):
    """Return a WSGI application that dispatches requests to controllers """
    routes = []
    for routing in routings:
        methods, regex, app = routing[:3]
        if isinstance(methods, basestring):
            methods = (methods,)
        vars = routing[3] if len(routing) >= 4 else {}
        routes.append((methods, re.compile(regex), app, vars))

    @wsgihelpers.wsgify
    def router(req):
        """Dispatch request to controllers."""
        split_path_info = req.path_info.split('/')
        assert not split_path_info[0], split_path_info
        for methods, regex, app, vars in routes:
            if methods is None or req.method in methods:
                match = regex.match(req.path_info)
                if match is not None:
                    req.urlvars = dict(
                        (name, value.decode('utf-8') if value is not None else None)
                        for name, value in match.groupdict().iteritems()
                        )
                    req.urlvars.update(vars)
                    req.script_name += req.path_info[:match.end()]
                    req.path_info = req.path_info[match.end():]
                    return req.get_response(app)
        ctx = contexts.Ctx(req)
        _ = ctx.translator.ugettext
        return wsgihelpers.not_found(ctx, explanation = _("Page not found: {0}").format(req.path_info))

    return router

