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
import urlparse

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
    conf = etalage.conf  # Empty dictionary
    conf.update(strings.deep_decode(global_conf))
    conf.update(strings.deep_decode(app_conf))
    conf.update(conv.check(conv.struct(
        {
            u'app_conf': conv.set_value(app_conf),
            u'app_dir': conv.set_value(app_dir),
            u'autocompleter_territories_kinds': conv.pipe(
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
            u'brand_name': conv.default(u'Comarquage.fr'),
            u'brand_url': conv.default(u'http://www.comarquage.fr/'),
            u'cache_dir': conv.default(os.path.join(os.path.dirname(app_dir), 'cache')),
            u'categories_collection': conv.default('categories'),
            u'cdn_url': conv.default('http://localhost:7000'),
            u'custom_static_files_dir': conv.default(None),
            u'custom_templates_dir': conv.default(None),
            u'data_updates_collection': conv.default('data_updates'),
            u'data_email': conv.pipe(
                conv.function(lambda lines: lines.split(u',')),
                conv.uniform_sequence(
                    conv.input_to_email,
                    ),
                ),
            u'database': conv.default('souk'),
            u'debug': conv.pipe(conv.guess_bool, conv.default(False)),
            u'default_tab': conv.pipe(
                conv.cleanup_line,
                conv.test_in(['carte', 'liste']),
                conv.default('carte'),
                ),
            u'gadget-integration.js': conv.default(urlparse.urljoin('http://localhost:7002/', 'integration.js')),
            u'global_conf': conv.set_value(global_conf),
            u'handle_competence_territories': conv.pipe(conv.guess_bool, conv.default(True)),
            u'hide_directory': conv.pipe(conv.guess_bool, conv.default(False)),
            u'hide_export': conv.pipe(conv.guess_bool, conv.default(False)),
            u'hide_gadget': conv.pipe(conv.guess_bool, conv.default(False)),
            u'hide_list': conv.pipe(conv.guess_bool, conv.default(False)),
            u'hide_map': conv.pipe(conv.guess_bool, conv.default(False)),
            u'hide_minisite': conv.pipe(conv.guess_bool, conv.default(False)),

            u'hide_category': conv.pipe(conv.guess_bool, conv.default(False)),
            u'hide_checkboxes': conv.pipe(conv.guess_bool, conv.default(False)),
            u'hide_legend': conv.pipe(conv.guess_bool, conv.default(False)),
            u'hide_territory': conv.pipe(conv.guess_bool, conv.default(False)),
            u'hide_term': conv.pipe(conv.guess_bool, conv.default(False)),
            u'i18n_dir': conv.default(os.path.join(app_dir, 'i18n')),
            u'i18n_dir_by_plugin_name': conv.set_value(None),  # set by plugins below
            u'ignored_fields': conv.pipe(
                conv.function(lambda lines: lines.split(u'\n')),
                conv.uniform_sequence(conv.pipe(
                    conv.function(lambda line: line.split(None, 1)),
                    conv.uniform_sequence(conv.input_to_slug),
                    conv.function(lambda seq: dict(zip(['id', 'name'], seq))),
                    )),
                conv.id_name_dict_list_to_ignored_fields,
                ),
            u'index.date.field': conv.default(None),
            u'log_level': conv.pipe(
                conv.default('WARNING'),
                conv.function(lambda log_level: getattr(logging, log_level.upper())),
                ),
            u'organism_types_collection': conv.default('organism_types'),
            u'package_name': conv.default('etalage'),
            u'pois_collection': conv.default('pois'),
            u'plugins_conf_file': conv.default(None),
            u'realm': conv.default(u'Etalage'),
            u'require_subscription': conv.pipe(conv.guess_bool, conv.default(False)),
            u'reset_on_poi_update': conv.pipe(conv.guess_bool, conv.default(False)),
            # Whether this application serves its own static files.
            u'static_files': conv.pipe(conv.guess_bool, conv.default(True)),
            u'static_files_dir': conv.default(os.path.join(app_dir, 'static')),
            u'territories_database': conv.pipe(
                conv.default(conf.get('database')),
                conv.default('souk'),
                ),
            u'territories_collection': conv.default('territories'),
            u'territories_kinds': conv.pipe(
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
            u'theme_field': conv.pipe(
                conv.function(lambda line: line.split(None, 1)),
                conv.uniform_sequence(conv.input_to_slug),
                conv.function(lambda seq: dict(zip(['id', 'name'], seq))),
                conv.default(dict(id = 'organism-type')),
                ),
            u'tile_layers': conv.pipe(
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
                                conv.make_input_to_url(),
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

    # CDN configuration
    conf.update(conv.check(conv.struct(
        {
            u'bootstrap.css': conv.default(urlparse.urljoin(conf['cdn_url'], '/bootstrap/2.2.1/css/bootstrap.min.css')),
            u'bootstrap.js': conv.default(urlparse.urljoin(conf['cdn_url'], '/bootstrap/2.2.1/js/bootstrap.min.js')),
            u'bootstrap-responsive.css': conv.default(
                urlparse.urljoin(conf['cdn_url'], '/bootstrap/2.2.1/css/bootstrap-responsive.min.css')
                ),
            u'easyxdm.js': conv.default(urlparse.urljoin(conf['cdn_url'], '/easyxdm/latest/easyXDM.min.js')),
            u'easyxdm.swf': conv.default(urlparse.urljoin(conf['cdn_url'], '/easyxdm/latest/easyxdm.swf')),
            u'jquery.js': conv.default(urlparse.urljoin(conf['cdn_url'], '/jquery/jquery-1.7.1.min.js')),
            u'jquery-ui.css': conv.default(
                urlparse.urljoin(conf['cdn_url'], '/jquery-ui/1.8.16/themes/smoothness/jquery-ui.css')
                ),
            u'jquery-ui.js': conv.default(urlparse.urljoin(conf['cdn_url'], '/jquery-ui/1.8.16/jquery-ui.min.js')),
            u'json2.js': conv.default(urlparse.urljoin(conf['cdn_url'], '/easyxdm/latest/json2.js')),
            u'leaflet.css': conv.default(urlparse.urljoin(conf['cdn_url'], '/leaflet/leaflet-0.5.1/leaflet.css')),
            u'leaflet.ie.css': conv.default(urlparse.urljoin(conf['cdn_url'], '/leaflet/leaflet-0.5.1/leaflet.ie.css')),
            u'leaflet.js': conv.default(urlparse.urljoin(conf['cdn_url'], '/leaflet/leaflet-0.5.1/leaflet.js')),
            u'pie.js': conv.default(urlparse.urljoin(conf['cdn_url'], '/css3pie/1.0beta5/PIE.js')),
            u'prettify.js': conv.default(urlparse.urljoin(conf['cdn_url'], '/google-code-prettify/187/prettify.js')),
            u'images.markers.url': conv.default(urlparse.urljoin(conf['cdn_url'], '/images/markers/')),
            u'images.misc.url': conv.default(urlparse.urljoin(conf['cdn_url'], '/images/misc/')),
            },
        default = conv.noop,
        ))(conf))

    # Configure logging.
    logging.basicConfig(level = conf['log_level'], stream = sys.stdout)

    errorware = conf.setdefault(u'errorware', {})
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
        conf['i18n_dir_by_plugin_name'] = {}
        for section in plugins_conf.sections():
            plugin_accessor = plugins_conf.get(section, 'use')
            plugin_constructor = pkg_resources.EntryPoint.parse('constructor = {0}'.format(plugin_accessor)).load(
                require = False)
            plugin_constructor(plugins_conf, section)
            plugin_package_name = plugins_conf.get(section, 'package_name')
            if plugin_package_name is not None:
                plugin_i18n_dir = plugins_conf.get(section, 'i18n_dir')
                if plugin_i18n_dir is not None:
                    conf['i18n_dir_by_plugin_name'][plugin_package_name] = plugin_i18n_dir

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
