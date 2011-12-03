#! /usr/bin/env python
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


"""Web application based on "Etalage" hierarchical database of territories"""


try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages


classifiers = """\
Development Status :: 3 - Alpha
Environment :: Web Environment
Intended Audience :: Information Technology
License :: OSI Approved :: GNU Affero General Public License v3
Operating System :: OS Independent
Programming Language :: Python
Topic :: Scientific/Engineering
"""

doc_lines = __doc__.split('\n')


setup(
    name = 'Etalage',
    version = '0.1',

    author = 'Emmanuel Raviart',
    author_email = 'infos-pratiques-devel@listes.infos-pratiques.org',
    classifiers = [classifier for classifier in classifiers.split('\n') if classifier],
    description = doc_lines[0],
    keywords = 'data database directory etalab geographical organism open organization poi web',
    license = 'http://www.fsf.org/licensing/licenses/agpl-3.0.html',
    long_description = '\n'.join(doc_lines[2:]),
    url = 'http://gitorious.org/infos-pratiques/etalage',

    data_files = [
        ('share/locale/fr/LC_MESSAGES', ['etalage/i18n/fr/LC_MESSAGES/etalage.mo']),
        ],
    entry_points = """
        [paste.app_factory]
        main = etalage.application:make_app

        [paste.app_install]
        main = etalage.websetup:Installer
        """,
    include_package_data = True,
    install_requires = [
        "Biryani >= 0.9dev",
        "Dogpile >= 0.1",
        "Mako >= 0.3.6",
        "Suq-Monpyjama >= 0.8",
        "WebError >= 0.10",
        "WebOb >= 1.1",
        ],
    message_extractors = {'etalage': [
            ('**.py', 'python', None),
            ('templates/**.mako', 'mako', {'input_encoding': 'utf-8'}),
            ('static/**', 'ignore', None)]},
#    package_data = {'etalage': ['i18n/*/LC_MESSAGES/*.mo']},
    packages = find_packages(),
    paster_plugins = ['PasteScript'],
    setup_requires = ["PasteScript >= 1.6.3"],
    zip_safe = False,
    )
