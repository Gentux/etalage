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


"""Controllers for territories"""


import base64
import datetime
import itertools
import logging
import re

from biryani import strings
import bson
from Crypto.Cipher import Blowfish
from poiscasse import ramdb

from . import conf, contexts, conv, model, templates, urls, wsgihelpers


decrypted_access_token_re = re.compile(
    '(?P<random>[\da-f]{4,})&(?P<client_id>[^&]+)&(?P<user_id>[\da-f]{24})?&(?P<expiration>.*?)&(?P<scope>.*?)$')
log = logging.getLogger(__name__)
N_ = lambda message: message


@wsgihelpers.wsgify
def about(req):
    ctx = contexts.Ctx(req)

    return templates.render(ctx, '/about.mako')


@wsgihelpers.wsgify
@ramdb.ramdb_based
def autocomplete_postal_distribution(req):
    ctx = contexts.Ctx(req)
    ctx.controller_name = 'autocomplete_territory'

    headers = []
    params = req.GET
    params = dict(
        context = params.get('context'),
        distinct = params.get('distinct'),
        jsonp = params.get('jsonp'),
        kind = params.getall('kind'),
        latitude = params.get('latitude'),
        longitude = params.get('longitude'),
        page = params.get('page'),
        parent = params.getall('parent'),
        term = params.get('term'),
        )
    data, errors = conv.pipe(
        conv.struct(
            dict(
                kind = conv.uniform_sequence(conv.str_to_territory_kind),
                latitude = conv.str_to_float,
                longitude = conv.str_to_float,
                distinct = conv.pipe(conv.guess_bool, conv.default(False)),
                page = conv.pipe(
                    conv.str_to_int,
                    conv.make_greater_or_equal(1),
                    conv.default(1),
                    ),
                parent = conv.uniform_sequence(conv.str_to_ref_to_territory_id),
                term = conv.make_str_to_slug(separator = u' ', transform = strings.upper),
                ),
            default = 'ignore',
            ),
        conv.rename_item('kind', 'kinds'),
        conv.rename_item('page', 'page_number'),
        conv.rename_item('parent', 'ancestors_id'),
        )(params, state = ctx)
    if errors is not None:
        raise wsgihelpers.respond_json(ctx,
            dict(
                apiVersion = '1.0',
                context = params['context'],
                error = dict(
                    code = 400, # Bad Request
                    errors = [
                        dict(
                            location = key,
                            message = error,
                            )
                        for key, error in sorted(errors.iteritems())
                        ],
                    # message will be automatically defined.
                    ),
                method = ctx.controller_name,
                params = params,
                ),
            headers = headers,
            jsonp = params['jsonp'],
            )

    postal_distributions_json = []
    page_size = 20
    for postal_distribution, territories_id in itertools.islice(
            ramdb.iter_best_postal_distributions_and_territories_id_couple(
                ancestors_id = data.get('ancestors_id'),
                distinct = data['distinct'],
                kinds = data.get('kinds'),
                latitude = data.get('latitude'),
                limit = data['page_number'] * page_size,
                longitude = data.get('longitude'),
                term = data.get('term'),
                ),
            (data['page_number'] - 1) * page_size,
            data['page_number'] * page_size,
            ):
        territories_json = []
        for territory_id in territories_id:
            territory = ramdb.territories_by_id[territory_id]
            territories_json.append(dict(
                id = str(territory._id),
                path = urls.get_url(ctx, territory.ref),
                ref = territory.ref,
                type_name = territory.type_short_name_fr,
                ))
        postal_distributions_json.append(dict(
            territories = territories_json,
            postal_distribution = model.postal_distribution_to_str(postal_distribution),
            ))
    return wsgihelpers.respond_json(ctx,
        dict(
            apiVersion = '1.0',
            context = params['context'],
            data = dict(
                currentItemCount = len(postal_distributions_json),
                items = postal_distributions_json,
                itemsPerPage = page_size,
                pageIndex = data['page_number'],
                startIndex = (data['page_number'] - 1) * page_size + 1,
                # totalItems = pager.item_count,
                # totalPages = pager.page_count,
                ),
            method = ctx.controller_name,
            params = params,
            ),
        headers = headers,
        jsonp = params['jsonp'],
        )


@wsgihelpers.wsgify
@ramdb.ramdb_based
def autocomplete_territory(req):
    ctx = contexts.Ctx(req)
    ctx.controller_name = 'autocomplete_territory'

    headers = []
    params = req.GET
    params = dict(
        context = params.get('context'),
        jsonp = params.get('jsonp'),
        kind = params.getall('kind'),
        latitude = params.get('latitude'),
        longitude = params.get('longitude'),
        page = params.get('page'),
        parent = params.getall('parent'),
        term = params.get('term'),
        )
    data, errors = conv.pipe(
        conv.struct(
            dict(
                kind = conv.uniform_sequence(conv.str_to_territory_kind),
                latitude = conv.str_to_float,
                longitude = conv.str_to_float,
                page = conv.pipe(
                    conv.str_to_int,
                    conv.make_greater_or_equal(1),
                    conv.default(1),
                    ),
                parent = conv.uniform_sequence(conv.str_to_ref_to_territory_id),
                term = conv.pipe(
                    conv.make_str_to_slug(separator = u' ', transform = strings.upper),
                    conv.shrink_postal_routing,
                    ),
                ),
            default = 'ignore',
            ),
        conv.rename_item('kind', 'kinds'),
        conv.rename_item('page', 'page_number'),
        conv.rename_item('parent', 'ancestors_id'),
        )(params, state = ctx)
    if errors is not None:
        raise wsgihelpers.respond_json(ctx,
            dict(
                apiVersion = '1.0',
                context = params['context'],
                error = dict(
                    code = 400, # Bad Request
                    errors = [
                        dict(
                            location = key,
                            message = error,
                            )
                        for key, error in sorted(errors.iteritems())
                        ],
                    # message will be automatically defined.
                    ),
                method = ctx.controller_name,
                params = params,
                ),
            headers = headers,
            jsonp = params['jsonp'],
            )

    territories_infos = []
    page_size = 20
    for territory_id in itertools.islice(
            ramdb.iter_best_territories_id(
                ancestors_id = data.get('ancestors_id'),
                kinds = data.get('kinds'),
                latitude = data.get('latitude'),
                limit = data['page_number'] * page_size,
                longitude = data.get('longitude'),
                term = data.get('term'),
                ),
            (data['page_number'] - 1) * page_size,
            data['page_number'] * page_size,
            ):
        territory = ramdb.territories_by_id[territory_id]
        territories_infos.append(dict(
            id = str(territory._id),
            main_postal_distribution = model.postal_distribution_to_str(territory.main_postal_distribution),
            nearest_postal_distribution = territory.get_nearest_postal_distribution_str(data.get('term')),
            path = urls.get_url(ctx, territory.ref),
            ref = territory.ref,
            type_name = territory.type_short_name_fr,
            ))
    return wsgihelpers.respond_json(ctx,
        dict(
            apiVersion = '1.0',
            context = params['context'],
            data = dict(
                currentItemCount = len(territories_infos),
                items = territories_infos,
                itemsPerPage = page_size,
                pageIndex = data['page_number'],
                startIndex = (data['page_number'] - 1) * page_size + 1,
                # totalItems = pager.item_count,
                # totalPages = pager.page_count,
                ),
            method = ctx.controller_name,
            params = params,
            ),
        headers = headers,
        jsonp = params['jsonp'],
        )


@wsgihelpers.wsgify
def delete(req):
    ctx = contexts.Ctx(req)
    client_id, scopes, user_id = get_access_token_infos(ctx, check = True, scope = conf['oauth.cards_web_hook_scope'])

    if client_id != model.wenoit_server.client_id:
        raise wsgihelpers.bad_request(ctx, explanation = ctx._('Unregistered Wenoit server with client ID: {0}').format(
            client_id))

    model.init_cards_env()

    card_id, error = conv.pipe(
        conv.str_to_object_id,
        conv.exists,
        )(req.GET.get('id'), state = ctx)
    if error is not None:
        raise wsgihelpers.bad_request(ctx, explanation = ctx._('Card ID Error: {0}').format(error))

    model.delete(ctx, card_id)

    raise wsgihelpers.no_content(ctx)


def get_access_token_infos(ctx, check = False, possible_scopes = None, required_scopes = None, scope = None):
    scopes = ctx.scopes
    if scopes is UnboundLocalError:
        access_token = None
        # Try to retrieve an OAuth access token stored in request header.
        authorization = ctx.req.authorization
        if authorization is not None and authorization[0].lower() == 'bearer':
            access_token = authorization[1].strip() or None
        if access_token is None and 'oauth_token' in ctx.req.GET:
            # Try to retrieve an OAuth access token stored in URL query.
            access_token = ctx.req.GET.get('oauth_token')
        if access_token is None and ctx.req.method in ('DELETE', 'POST', 'PUT') \
                and ctx.req.content_type == 'application/x-www-form-urlencoded' \
                and 'oauth_token' in ctx.req.POST:
            # Try to retrieve an OAuth access token stored in (URL-encoded) request body.
            access_token = ctx.req.POST.get('oauth_token')
        access_infos = parse_access_token(ctx, access_token, check = check)
        scopes = None
        if access_infos is not None:
            client_id = access_infos['client_id']
            assert client_id is not None
            scopes = access_infos['scopes']
            user_id = access_infos.get('user_id')
        ctx.scopes = scopes
    if possible_scopes is not None and not any(
                scope in (scopes or [])
                for scope in possible_scopes
                ) \
            or required_scopes is not None and not all(
                scope in (scopes or [])
                for scope in required_scopes
                ) \
            or scope is not None and scope not in (scopes or []):
        if check:
            raise wsgihelpers.unauthorized(ctx, headers = [
                (
                    'WWW-Authenticate',
                    'OAuth2 error="insufficient_scope", error_description="Missing requested scope"',
                    ),
                ])
        else:
            return None, None, None
    return client_id, scopes, user_id


@wsgihelpers.wsgify
@ramdb.ramdb_based
def index(req):
    ctx = contexts.Ctx(req)

    params = req.GET
    params = dict(
        ancestor_type = req.urlvars.get('type'),
        ancestor_postal_distribution = req.urlvars.get('postal_distribution'),
        kind = params.getall('kind'),
        latitude = params.get('latitude'),
        longitude = params.get('longitude'),
        page = params.get('page'),
        q = params.get('q'),
        )

    if params['ancestor_postal_distribution'] is None or params['ancestor_type'] is None:
        ancestor = None
    else:
        ancestor_kind, error = conv.pipe(
            conv.str_to_slug,
            conv.slug_plural_fr_to_territory_kind,
            )(params['ancestor_type'], state = ctx)
        if error is not None:
            raise wsgihelpers.not_found(ctx, explanation = ctx._('Territory Type Error: {0}').format(error))

        ancestor, error = conv.pipe(
            conv.str_to_postal_distribution,
            conv.make_postal_distribution_to_territory_id(guess = True, kinds = [ancestor_kind]),
            conv.id_to_territory,
            )(params['ancestor_postal_distribution'], state = ctx)
        if error is not None:
            raise wsgihelpers.not_found(ctx, explanation = ctx._('Territory Error: {0}').format(error))

    latitude, error = conv.str_to_float(params['latitude'], state = ctx)
    if error is not None:
        raise wsgihelpers.not_found(ctx, explanation = ctx._('Latitude Error: {0}').format(error))

    longitude, error = conv.str_to_float(params['longitude'], state = ctx)
    if error is not None:
        raise wsgihelpers.not_found(ctx, explanation = ctx._('Longitude Error: {0}').format(error))

    page_number, error = conv.pipe(
        conv.str_to_int,
        conv.make_greater_or_equal(1),
        conv.default(1),
        )(params['page'], state = ctx)
    if error is not None:
        raise wsgihelpers.not_found(ctx, explanation = ctx._('Page Number Error: {0}').format(error))

    simple_term, error = conv.pipe(
        conv.make_str_to_slug(separator = u' ', transform = strings.upper),
        conv.shrink_postal_routing,
        )(params['q'], state = ctx)
    if error is not None:
        raise wsgihelpers.not_found(ctx, explanation = ctx._('Postal Distribution Error: {0}').format(error))

    kinds, error = conv.pipe(
        conv.uniform_sequence(conv.str_to_territory_kind),
        conv.default(model.communes_kinds + [u'Special']),
        )(params['kind'], state = ctx)
    if error is not None:
        raise wsgihelpers.not_found(ctx, explanation = ctx._('Types Error: {0}').format(error))

    page_size = 20
    territories_infos = []
    for territory_id in itertools.islice(
            ramdb.iter_best_territories_id(
                ancestors_id = [ancestor._id] if ancestor is not None else None,
                kinds = kinds,
                latitude = latitude,
                longitude = longitude,
                limit = page_number * page_size,
                term = params['q'],
                ),
            (page_number - 1) * page_size,
            page_number * page_size,
            ):
        territory = ramdb.territories_by_id[territory_id]
        territories_infos.append(dict(
            main_postal_distribution = model.postal_distribution_to_str(territory.main_postal_distribution),
            nearest_postal_distribution = territory.get_nearest_postal_distribution_str(simple_term),
            territory = territory,
            ref = territory.ref,
            type_name = territory.type_short_name_fr,
            ))

    return templates.render(ctx, '/select-territory.mako',
        ancestor = ancestor,
        kinds = kinds,
        latitude = latitude,
        longitude = longitude,
        page_number = page_number,
        page_size = page_size,
        term = params['q'],
        territories_infos = territories_infos,
        )


def make_router():
    """Return a WSGI application that dispatches requests to controllers """
    return urls.make_router(
        ('DELETE', '^/?$', delete),
        ('GET', '^/?$', index),
        ('POST', '^/?$', update),
        ('GET', '^/a-propos/?$', about),
        ('GET', '^/api/v1/autocomplete-postal-distribution/?$', autocomplete_postal_distribution),
        ('GET', '^/api/v1/autocomplete-territory/?$', autocomplete_territory),
        ('GET', '^/(?P<type>[^/]+)/(?P<postal_distribution>.[^/]+)/territoires/?$', index),
        (('GET', 'POST'), '^(/(?P<type>[^/]+)/(?P<postal_distribution>.[^/]+))?/types-de-territoires/?$',
            select_territory_types),
        ('GET', '^/(?P<type>[^/]+)(/(?P<postal_distribution>.[^/]+))?/?$', territory),
        )


def parse_access_token(ctx, access_token, check = False):
    if access_token is None:
        if check:
            log.error('Invalid OAuth request: Missing access token')
            raise wsgihelpers.unauthorized(ctx, headers = [
                (
                    'WWW-Authenticate',
                    'OAuth2 error="invalid_request", error_description="Missing access token"',
                    ),
                ])
        else:
            return None
    shared_secret = conf['oauth.client_secret']
    try:
        message = Blowfish.new(shared_secret).decrypt(base64.urlsafe_b64decode(str(access_token)))
    except ValueError:
        # ValueError: Input strings must be a multiple of 8 in length
        if check:
            log.error('Invalid format for OAuth access token: {0}'.format(str(access_token)))
            raise wsgihelpers.unauthorized(ctx, headers = [
                (
                    'WWW-Authenticate',
                    'OAuth2 error="invalid_token", error_description="Invalid format for token"',
                    ),
                ])
        else:
            return None
    match = decrypted_access_token_re.match(message)
    if match is None:
        if check:
            log.error('Invalid format for OAuth access token: {0}'.format(message))
            raise wsgihelpers.unauthorized(ctx, headers = [
                (
                    'WWW-Authenticate',
                    'OAuth2 error="invalid_token", error_description="Invalid format for token"',
                    ),
                ])
        else:
            return None
    if match.group('expiration') < datetime.datetime.now().isoformat():
        if check:
            raise wsgihelpers.unauthorized(ctx, headers = [
                (
                    'WWW-Authenticate',
                    'OAuth2 error="invalid_token", error_description="Access token has expired"',
                    ),
                ])
        else:
            return None
    return dict(
        client_id = match.group('client_id'),
        scopes = set(match.group('scope').split()),
        user_id = match.group('user_id') or None,
        )


@wsgihelpers.wsgify
@ramdb.ramdb_based
def select_territory_types(req):
    ctx = contexts.Ctx(req)

    params = req.params
    params = dict(
        ancestor_postal_distribution = req.urlvars.get('postal_distribution'),
        ancestor_type = req.urlvars.get('type'),
        kind = params.getall('kind'),
        latitude = params.get('latitude'),
        longitude = params.get('longitude'),
        submit_button = params.get('submit-button'),
        q = params.get('q'),
        )

    if params['ancestor_postal_distribution'] is None or params['ancestor_type'] is None:
        ancestor = None
    else:
        ancestor_kind, error = conv.pipe(
            conv.str_to_slug,
            conv.slug_plural_fr_to_territory_kind,
            )(params['ancestor_type'], state = ctx)
        if error is not None:
            raise wsgihelpers.not_found(ctx, explanation = ctx._('Territory Type Error: {0}').format(error))

        ancestor, error = conv.pipe(
            conv.str_to_postal_distribution,
            conv.make_postal_distribution_to_territory_id(guess = True, kinds = [ancestor_kind]),
            conv.id_to_territory,
            )(params['ancestor_postal_distribution'], state = ctx)
        if error is not None:
            raise wsgihelpers.not_found(ctx, explanation = ctx._('Territory Error: {0}').format(error))

    data, errors = conv.pipe(
        conv.struct(
            dict(
                kind = conv.uniform_sequence(conv.str_to_territory_kind),
                ),
            default = 'ignore',
            keep_empty = True,
            ),
        conv.rename_item('kind', 'kinds'),
        )(params, state = ctx)
    if errors is not None:
        raise wsgihelpers.bad_request(ctx, explanation = ctx._('Parameters Errors: {0}').format(errors))

    if params['submit_button']:
        index_params = dict(
            kind = None \
                if data.get('kinds') is None or set(data['kinds']) == set(model.communes_kinds) \
                else sorted(data['kinds']),
            latitude = params['latitude'] or None,
            longitude = params['longitude'] or None,
            q = params['q'] or None,
            )
        index_url = urls.get_url(ctx, ancestor.ref, 'territoires', **index_params) if ancestor is not None \
            else urls.get_url(ctx, **index_params)
        raise wsgihelpers.redirect(ctx, location = index_url)

    return templates.render(ctx, '/select-territory-types.mako', ancestor = ancestor, data = data, params = params)


@wsgihelpers.wsgify
@ramdb.ramdb_based
def territory(req):
    ctx = contexts.Ctx(req)

    params = req.GET
    params = dict(
        postal_distribution = req.urlvars.get('postal_distribution'),
        type = req.urlvars.get('type'),
        )

    territory_kind, error = conv.pipe(
        conv.str_to_slug,
        conv.slug_plural_fr_to_territory_kind,
        conv.exists,
        )(params['type'], state = ctx)
    if error is not None:
        raise wsgihelpers.not_found(ctx, explanation = ctx._('Territory Type Error: {0}').format(error))

    territory, error = conv.pipe(
        conv.str_to_postal_distribution,
        conv.make_postal_distribution_to_territory_id(guess = True, kinds = [territory_kind]),
        conv.id_to_territory,
        conv.exists,
        )(params['postal_distribution'], state = ctx)
    if error is not None:
        raise wsgihelpers.not_found(ctx, explanation = ctx._('Territory Error: {0}').format(error))

    territory_full_url = urls.get_full_url(ctx, territory.ref)
    if req.url != territory_full_url:
        raise wsgihelpers.redirect(ctx, location = territory_full_url)

    return templates.render(ctx, '/territory.mako', territory = territory)


@wsgihelpers.wsgify
def update(req):
    ctx = contexts.Ctx(req)
    client_id, scopes, user_id = get_access_token_infos(ctx, check = True, scope = conf['oauth.cards_web_hook_scope'])

    if client_id != model.wenoit_server.client_id:
        raise wsgihelpers.bad_request(ctx, explanation = ctx._('Unregistered Wenoit server with client ID: {0}').format(
            client_id))

    model.init_cards_env()

    card, errors = conv.pipe(
        conv.str_to_json,
        conv.make_test(lambda card_json: card_json.get('id') == req.GET.get('id'),
            error = N_("ID in URL ({0}) doesn't match the ID of attached card.").format(req.GET.get('id'))),
        conv.api1_json_to_card,
        conv.exists,
        )(req.body, state = ctx)
    if errors is not None:
        raise wsgihelpers.bad_request(ctx, explanation = ctx._('Card Errors: {0}').format(errors))

    model.update(ctx, card)

    raise wsgihelpers.no_content(ctx)

