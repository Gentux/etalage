# -*- coding: utf-8 -*-


# Etalage -- Open Data POIs portal
# By: Emmanuel Raviart <eraviart@easter-eggs.com>
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


"""Environment configuration"""


import logging
import os
import sys

import mako.lookup
import pymongo
from suq import monpyjama
from etalage import ramdb

import etalage
from . import conv, model, templates


app_dir = os.path.dirname(os.path.abspath(__file__))


def load_environment(global_conf, app_conf):
    """Configure the application environment."""
    conf = etalage.conf # Empty dictionary
    conf.update({
        'app_conf': app_conf,
        'app_dir': app_dir,
        'cache_dir': os.path.join(os.path.dirname(app_dir), 'cache'),
        'categories_collection': 'categories',
        'data_updates_collection': 'data_updates',
        'database': 'souk',
        'debug': False,
        'global_conf': global_conf,
        'i18n_dir': os.path.join(app_dir, 'i18n'),
        'log_level': 'WARNING',
        'organism_types_collection': 'organism_types',
        'pois_collection': 'pois',
        'package_name': 'etalage',
        'static_files': True, # Whether this application serves its own static files
        'static_files_dir': os.path.join(app_dir, 'static'),
        'territories_collection': 'territories',
        })
    conf.update(global_conf)
    conf.update(app_conf)
    conf['debug'] = conv.check(conv.pipe(conv.guess_bool, conv.default(False)))(conf['debug'])
    conf['log_level'] = getattr(logging, conf['log_level'].upper())
    conf['static_files'] = conv.check(conv.pipe(conv.guess_bool, conv.default(False)))(conf['static_files'])

    # Configure logging.
    logging.basicConfig(level = conf['log_level'], stream = sys.stdout)

    errorware = conf.setdefault('errorware', {})
    errorware['debug'] = conf['debug']
    if not errorware['debug']:
        errorware['error_email'] = conf['email_to']
        errorware['error_log'] = conf.get('error_log', None)
        errorware['error_message'] = conf.get('error_message', 'An internal server error occurred')
        errorware['error_subject_prefix'] = conf.get('error_subject_prefix', 'Etalage Error: ')
        errorware['from_address'] = conf['from_address']
        errorware['smtp_server'] = conf.get('smtp_server', 'localhost')

    # Connect to MongoDB database.
    monpyjama.Wrapper.db = model.db = pymongo.Connection()[conf['database']]
    # Initialize ramdb database from MongoDB.
    ramdb.load()

    # Create the Mako TemplateLookup, with the default auto-escaping.
    templates.lookup = mako.lookup.TemplateLookup(
        default_filters = ['h'],
        directories = [os.path.join(app_dir, 'templates')],
#        error_handler = handle_mako_error,
        input_encoding = 'utf-8', 
        module_directory = os.path.join(conf['cache_dir'], 'templates'),
#        strict_undefined = True,
        )

