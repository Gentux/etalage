# -*- coding: utf-8 -*-


# Etalage -- Open Data POIs portal
# By: Emmanuel Raviart <eraviart@easter-eggs.com>
#
# Copyright (C) 2011, 2012 Easter-eggs
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


"""Middleware initialization"""


import re

from beaker.middleware import SessionMiddleware
from paste.cascade import Cascade
from paste.urlparser import StaticURLParser
from weberror.errormiddleware import ErrorMiddleware
import webob.exc

from . import conf, contexts, controllers, environment, urls, wsgihelpers


lang_re = re.compile(r'^/(?P<lang>en|fr)(?=/|$)')
percent_encoding_re = re.compile(r'%[\dA-Fa-f]{2}')


@wsgihelpers.wsgify.middleware
def reject_misencoded_requests(req, app, exception_class=None):
    """WSGI middleware that returns an HTTP error (bad request by default) if the request attributes
    are not encoded in UTF-8.
    """
    if exception_class is None:
        exception_class = webob.exc.HTTPBadRequest
    try:
        req.path_info
        req.script_name
        req.params
    except UnicodeDecodeError:
        return exception_class(u'The request URL and its parameters must be encoded in UTF-8.')
    return req.get_response(app)


@wsgihelpers.wsgify.middleware
def environment_setter(req, app):
    """WSGI middleware that sets request-dependant environment."""
    urls.application_url = req.application_url
    return app


@wsgihelpers.wsgify.middleware
def language_detector(req, app):
    """WSGI middleware that detect language symbol in requested URL or otherwise in Accept-Language header."""
    ctx = contexts.Ctx(req)
    match = lang_re.match(req.path_info)
    if match is None:
        ctx.lang = [
            # req.accept_language.best_match([('en-US', 1), ('en', 1), ('fr-FR', 1), ('fr', 1)],
            #    default_match = 'en').split('-', 1)[0],
            'fr',
            ]
    else:
        ctx.lang = [match.group('lang')]
        req.script_name += req.path_info[:match.end()]
        req.path_info = req.path_info[match.end():] or '/'
    return req.get_response(app)


def make_app(global_conf, **app_conf):
    """Create a WSGI application and return it

    ``global_conf``
        The inherited configuration for this application. Normally from
        the [DEFAULT] section of the Paste ini file.

    ``app_conf``
        The application's local configuration. Normally specified in
        the [app:<name>] section of the Paste ini file (where <name>
        defaults to main).
    """
    # Configure the environment and fill conf dictionary.
    environment.load_environment(global_conf, app_conf)

    # Dispatch request to controllers.
    app = controllers.make_router()

    # Keep sessions.
    app = SessionMiddleware(app, conf)

    # Init request-dependant environment
    app = environment_setter(app)
    app = language_detector(app)

    # Repair badly encoded query in request URL.
    app = reject_misencoded_requests(app)

    # CUSTOM MIDDLEWARE HERE (filtered by error handling middlewares)

    # Handle Python exceptions
    if not conf['debug']:
        app = ErrorMiddleware(app, global_conf, **conf['errorware'])

    if conf['static_files']:
        # Serve static files.
        cascaded_apps = []
        if conf['custom_static_files_dir'] is not None:
            cascaded_apps.append(StaticURLParser(conf['custom_static_files_dir']))
        cascaded_apps.append(StaticURLParser(conf['static_files_dir']))
        cascaded_apps.append(app)
        app = Cascade(cascaded_apps)

    return app
