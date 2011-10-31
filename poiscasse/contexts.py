# -*- coding: utf-8 -*-


# PoisCasse -- Open Data POIs portal
# By: Emmanuel Raviart <eraviart@easter-eggs.com>
#     Romain Soufflet <rsoufflet@easter-eggs.com>
#
# Copyright (C) 2011 Easter-eggs
# http://gitorious.org/infos-pratiques/poiscasse
#
# This file is part of PoisCasse.
#
# PoisCasse is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# PoisCasse is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


"""Context loaded and saved in WSGI requests"""


from gettext import NullTranslations, translation
import os

import webob

from . import conf


__all__ = ['Ctx', 'null_ctx']


class Ctx(object):
    _parent = None
    default_values = dict(
        _lang = None,
        _scopes = UnboundLocalError,
        _translator = None,
        base_categories_slug = None,
        category_tags_slug = None,
        container_base_url = None,
        controller_name = None,
        gadget_id = None,
        req = None,
        )
    env_keys = ('_lang', '_scopes', '_translator')

    def __init__(self, req = None):
        if req is not None:
            self.req = req
            poiscasse_env = req.environ.get('poiscasse', {})
            for key in object.__getattribute__(self, 'env_keys'):
                value = poiscasse_env.get(key)
                if value is not None:
                    setattr(self, key, value)

    def __getattribute__(self, name):
        try:
            return object.__getattribute__(self, name)
        except AttributeError:
            parent = object.__getattribute__(self, '_parent')
            if parent is None:
                default_values = object.__getattribute__(self, 'default_values')
                if name in default_values:
                    return default_values[name]
                raise
            return getattr(parent, name)

    @property
    def _(self):
        return self.translator.ugettext

    def blank_req(self, path, environ = None, base_url = None, headers = None, POST = None, **kw):
        env = environ.copy() if environ else {}
        poiscasse_env = env.setdefault('poiscasse', {})
        for key in env_keys:
            value = getattr(self, key)
            if value is not None:
                poiscasse_env[key] = value
        return webob.Request.blank(path, environ = env, base_url = base_url, headers = headers, POST = POST, **kw)

    def get_containing(self, name, depth = 0):
        """Return the n-th (n = ``depth``) context containing attribute named ``name``."""
        ctx_dict = object.__getattribute__(self, '__dict__')
        if name in ctx_dict:
            if depth <= 0:
                return self
            depth -= 1
        parent = ctx_dict.get('_parent')
        if parent is None:
            return None
        return parent.get_containing(name, depth = depth)

    def get_inherited(self, name, default = UnboundLocalError, depth = 1):
        ctx = self.get_containing(name, depth = depth)
        if ctx is None:
            if default is UnboundLocalError:
                raise AttributeError('Attribute %s not found in %s' % (name, self))
            return default
        return object.__getattribute__(ctx, name)

    def iter(self):
        yield self
        parent = object.__getattribute__(self, '_parent')
        if parent is not None:
            for ancestor in parent.iter():
                yield ancestor

    def iter_containing(self, name):
        ctx_dict = object.__getattribute__(self, '__dict__')
        if name in ctx_dict:
            yield self
        parent = ctx_dict.get('_parent')
        if parent is not None:
            for ancestor in parent.iter_containing(name):
                yield ancestor

    def iter_inherited(self, name):
        for ctx in self.iter_containing(name):
            yield object.__getattribute__(ctx, name)

    def lang_del(self):
        del self._lang
        if self.req is not None and self.req.environ.get('poiscasse') is not None \
                and '_lang' in self.req.environ['poiscasse']:
            del self.req.environ['poiscasse']['_lang']

    def lang_get(self):
        if self._lang is None:
#            self._lang = self.req.accept_language.best_matches('en-US') if self.req is not None else []
            self._lang = ['fr-FR']
            if self.req is not None:
                self.req.environ.setdefault('poiscasse', {})['_lang'] = self._lang
        return self._lang

    def lang_set(self, lang):
        self._lang = lang
        if self.req is not None:
            self.req.environ.setdefault('poiscasse', {})['_lang'] = self._lang
        # Reinitialize translator for new languages.
        if self._translator is not None:
            # Don't del self._translator, because attribute _translator can be defined in a parent.
            self._translator = None
            if self.req is not None and self.req.environ.get('poiscasse') is not None \
                    and '_translator' in self.req.environ['poiscasse']:
                del self.req.environ['poiscasse']['_translator']

    lang = property(lang_get, lang_set, lang_del)

    def new(self, **kwargs):
        ctx = Ctx()
        ctx._parent = self
        for name, value in kwargs.iteritems():
            setattr(ctx, name, value)
        return ctx

    @property
    def parent(self):
        return object.__getattribute__(self, '_parent')

    def scopes_del(self):
        del self._scopes
        if self.req is not None and self.req.environ.get('wenoit_poiscasse') is not None \
                and '_scopes' in self.req.environ['wenoit_poiscasse']:
            del self.req.environ['wenoit_poiscasse']['_scopes']

    def scopes_get(self):
        return self._scopes

    def scopes_set(self, scopes):
        self._scopes = scopes
        if self.req is not None:
            self.req.environ.setdefault('wenoit_poiscasse', {})['_scopes'] = scopes

    scopes = property(scopes_get, scopes_set, scopes_del)

    @property
    def session(self):
        return self.req.environ.get('beaker.session') if self.req is not None else None

    @property
    def translator(self):
        """Get a valid translator object from one or several languages names."""
        if self._translator is None:
            lang = self.lang
            if not lang:
                return NullTranslations()
            if not isinstance(lang, list):
                lang = [lang]
            translator = translation(conf['package_name'], conf['i18n_dir'], languages = lang,
                fallback = NullTranslations())
            self._translator = translator
        return self._translator


null_ctx = Ctx()
null_ctx.lang = 'fr-FR'

