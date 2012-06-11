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


"""Environment configuration"""


from ConfigParser import SafeConfigParser
import logging
import os
import sys

from biryani import strings
import mako.lookup
import pkg_resources
import pymongo
from suq import monpyjama
from etalage import ramdb

import etalage
from . import conv, model, templates


app_dir = os.path.dirname(os.path.abspath(__file__))


def load_environment(global_conf, app_conf):
    """Configure the application environment."""
    conf = etalage.conf # Empty dictionary
    conf.update(strings.deep_decode(global_conf))
    conf.update(strings.deep_decode(app_conf))
    conf.update(conv.check(conv.struct(
        {
            'app_conf': conv.set_value(app_conf),
            'app_dir': conv.set_value(app_dir),
            'cache_dir': conv.default(os.path.join(os.path.dirname(app_dir), 'cache')),
            'categories_collection': conv.default('categories'),
            'custom_static_files_dir': conv.default(None),
            'custom_templates_dir': conv.default(None),
            'data_updates_collection': conv.default('data_updates'),
            'database': conv.default('souk'),
            'debug': conv.pipe(conv.guess_bool, conv.default(False)),
            'default_tab': conv.pipe(
                conv.cleanup_line,
                conv.test_in(['carte', 'liste']),
                conv.default('carte'),
                ),
            'global_conf': conv.set_value(global_conf),
            'hide_directory': conv.pipe(conv.guess_bool, conv.default(False)),
            'hide_export': conv.pipe(conv.guess_bool, conv.default(False)),
            'hide_gadget': conv.pipe(conv.guess_bool, conv.default(False)),
            'hide_map': conv.pipe(conv.guess_bool, conv.default(False)),
            'hide_minisite': conv.pipe(conv.guess_bool, conv.default(False)),
            'i18n_dir': conv.default(os.path.join(app_dir, 'i18n')),
            'ignored_fields': conv.pipe(
                conv.function(lambda lines: lines.split(u'\n')),
                conv.uniform_sequence(conv.pipe(
                    conv.function(lambda line: line.split(None, 1)),
                    conv.uniform_sequence(conv.input_to_slug),
                    conv.function(lambda seq: dict(zip(['id', 'name'], seq))),
                    )),
                conv.id_name_dict_list_to_ignored_fields,
                ),
            'log_level': conv.pipe(
                conv.default('WARNING'),
                conv.function(lambda log_level: getattr(logging, log_level.upper())),
                ),
            'organism_types_collection': conv.default('organism_types'),
            'package_name': conv.default('etalage'),
            'pois_collection': conv.default('pois'),
            'plugins_conf_file': conv.default(None),
            'realm': conv.default(u'Etalage'),
            # Whether this application serves its own static files.
            'static_files': conv.pipe(conv.guess_bool, conv.default(True)),
            'static_files_dir': conv.default(os.path.join(app_dir, 'static')),
            'territories_collection': conv.default('territories'),
            'territories_kinds': conv.pipe(
                conv.function(lambda kinds: kinds.split()),
                conv.uniform_sequence(
                    conv.test_in(model.Territory.public_kinds),
                    constructor = lambda kinds: sorted(set(kinds)),
                    ),
                conv.default([
                    # u'AbstractCommuneOfFrance',
                    u'ArrondissementOfCommuneOfFrance',
                    u'ArrondissementOfFrance',
                    u'AssociatedCommuneOfFrance',
                    # u'CantonalFractionOfCommuneOfFrance',
                    u'CantonOfFrance',
                    u'CommuneOfFrance',
                    # u'Country',
                    u'DepartmentOfFrance',
                    u'IntercommunalityOfFrance',
                    # u'InternationalOrganization',
                    u'MetropoleOfCountry',
                    u'Mountain',
                    u'OverseasCollectivityOfFrance',
                    u'PaysOfFrance',
                    u'RegionalNatureParkOfFrance',
                    u'RegionOfFrance',
                    # u'Special',
                    u'UrbanAreaOfFrance',
                    u'UrbanTransportsPerimeterOfFrance',
                    ]),
                ),
            'tile_layers': conv.pipe(
                conv.function(eval),
                conv.function(strings.deep_decode),
                conv.test_isinstance(list),
                conv.uniform_sequence(
                    conv.pipe(
                        conv.test_isinstance(dict),
                        conv.struct(dict(
                            attribution = conv.pipe(
                                conv.test_isinstance(basestring),
                                conv.not_none,
                                ),
                            name = conv.pipe(
                                conv.test_isinstance(basestring),
                                conv.not_none,
                                ),
                            subdomains = conv.test_isinstance(basestring),
                            url = conv.pipe(
                                conv.test_isinstance(basestring),
                                conv.make_input_to_url(full = True),
                                conv.not_none,
                                ),
                            )),
                        ),
                    ),
                conv.not_none,
                ),
            },
        default = 'drop',
        keep_none_values = True,
        ))(conf))

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

    # Initialize plugins.
    if conf['plugins_conf_file'] is not None:
        plugins_conf = SafeConfigParser(dict(here = os.path.dirname(conf['plugins_conf_file'])))
        plugins_conf.read(conf['plugins_conf_file'])
        for section in plugins_conf.sections():
            plugin_accessor = plugins_conf.get(section, 'use')
            plugin_constructor = pkg_resources.EntryPoint.parse('constructor = {0}'.format(plugin_accessor)).load(
                require = False)
            plugin_constructor(plugins_conf, section)

    # Initialize ramdb database from MongoDB.
    ramdb.load()

    # Create the Mako TemplateLookup, with the default auto-escaping.
    templates_dirs = []
    if conf['custom_templates_dir']:
        templates_dirs.append(conf['custom_templates_dir'])
    templates_dirs.append(os.path.join(app_dir, 'templates'))
    templates.lookup = mako.lookup.TemplateLookup(
        default_filters = ['h'],
        directories = templates_dirs,
#        error_handler = handle_mako_error,
        input_encoding = 'utf-8', 
        module_directory = os.path.join(conf['cache_dir'], 'templates'),
#        strict_undefined = True,
        )

