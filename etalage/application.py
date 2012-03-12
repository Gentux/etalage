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
import urllib

from beaker.middleware import SessionMiddleware
from paste.cascade import Cascade
from paste.urlparser import StaticURLParser
from weberror.errormiddleware import ErrorMiddleware

from . import conf, controllers, environment, urls, wsgihelpers


percent_encoding_re = re.compile('%[\dA-Fa-f]{2}')


@wsgihelpers.wsgify.middleware
def environment_setter(req, app):
    """WSGI middleware that sets request-dependant environment."""
    urls.application_url = req.application_url
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

    # Repair badly encoded query in request URL.
    app = request_query_encoding_fixer(app)

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


@wsgihelpers.wsgify.middleware
def request_query_encoding_fixer(req, app):
    """WSGI middleware that repairs a badly encoded query in request URL."""
    query_string = req.query_string
    if query_string is not None:
        try:
            urllib.unquote(query_string).decode('utf-8')
        except UnicodeDecodeError:
            req.query_string = percent_encoding_re.sub(
                lambda match: urllib.quote(urllib.unquote(match.group(0)).decode('iso-8859-1').encode('utf-8')),
                query_string)
    return req.get_response(app)

