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


import datetime
import itertools
import logging
import simplejson as json
import urlparse

from biryani import strings

from . import contexts, conf, conv, model, pois, ramdb, templates, urls, wsgihelpers


log = logging.getLogger(__name__)
N_ = lambda message: message


@wsgihelpers.wsgify
def about(req):
    ctx = contexts.Ctx(req)

    params = req.GET
    init_ctx(ctx, params)
    return templates.render(ctx, '/about.mako')


@wsgihelpers.wsgify
@ramdb.ramdb_based
def autocomplete_category(req):
    ctx = contexts.Ctx(req)
    ctx.controller_name = 'autocomplete_category'

    headers = []
    params = req.GET
    params = dict(
        context = params.get('context'),
        jsonp = params.get('jsonp'),
        page = params.get('page'),
        tag = params.getall('tag'),
        term = params.get('term'),
        )
    data, errors = conv.pipe(
        conv.struct(
            dict(
                page = conv.pipe(
                    conv.str_to_int,
                    conv.make_greater_or_equal(1),
                    conv.default(1),
                    ),
                tag = conv.uniform_sequence(conv.str_to_category_slug),
                term = conv.make_str_to_slug(separator = u' ', transform = strings.upper),
                ),
            default = 'ignore',
            ),
        conv.rename_item('page', 'page_number'),
        conv.rename_item('tag', 'tags_slug'),
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

    page_size = 20
    categories_json = [
        ramdb.categories_by_slug[category_slug].name
        for category_slug in itertools.islice(
            sorted(ramdb.iter_categories_slug(
                tags_slug = data.get('tags_slug'),
                term = data.get('term'),
                )),
            (data['page_number'] - 1) * page_size,
            data['page_number'] * page_size,
            )
        ]
    return wsgihelpers.respond_json(ctx,
        dict(
            apiVersion = '1.0',
            context = params['context'],
            data = dict(
                currentItemCount = len(categories_json),
                items = categories_json,
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
def export_geojson(req):
    ctx = contexts.Ctx(req)

    params = req.GET
    init_ctx(ctx, params)
    params = dict(
        category = params.get('category'),
        jsonp = params.get('jsonp'),
        page = params.get('page'),
        term = params.get('term'),
        territory = params.get('territory'),
        )

    category, error = conv.str_to_slug(params['category'], state = ctx)
    if error is not None:
        raise wsgihelpers.not_found(ctx, explanation = ctx._('Category Error: {0}').format(error))

    page_number, error = conv.pipe(
        conv.str_to_int,
        conv.make_greater_or_equal(1),
        conv.default(1),
        )(params['page'], state = ctx)
    if error is not None:
        raise wsgihelpers.not_found(ctx, explanation = ctx._('Page Number Error: {0}').format(error))

    term, error = conv.str_to_slug(params['term'], state = ctx)
    if error is not None:
        raise wsgihelpers.not_found(ctx, explanation = ctx._('Research Terms Error: {0}').format(error))

    postal_distribution, error = conv.str_to_postal_distribution(params['territory'], state = ctx)
    if error is not None:
        raise wsgihelpers.not_found(ctx, explanation = ctx._('Territory Error: {0}').format(error))
    elif postal_distribution:
        found_territories = list(model.Territory.find({
            'main_postal_distribution.postal_code': postal_distribution[0],
            'main_postal_distribution.postal_routing': postal_distribution[1],
            }).limit(2))
        if not found_territories:
            error = u'Territoire inconnu'
            raise wsgihelpers.not_found(ctx, explanation = ctx._('Territory Error: {0}').format(error))
        elif len(found_territories) > 1:
            error = u'Territoire ambigu'
            raise wsgihelpers.not_found(ctx, explanation = ctx._('Territory Error: {0}').format(error))
        else:
            territory_dict = found_territories[0].new_kind_code()
            territory_kind_code = (territory_dict['kind'], territory_dict['code'])
    else:
        territory_kind_code = None

    page_size = 20
    pois_geojson = {
        "type": "FeatureCollection",
        "properties": {"date": unicode(datetime.datetime.now())},
        "features": [],
        }
    for poi_id in itertools.islice(
            ramdb.iter_pois_id(category_slug = category.slug, term = term, territory_kind_code = territory_kind_code),
            (page_number - 1) * page_size,
            page_number * page_size,
            ):
        poi = ramdb.ram_pois_by_id[poi_id]
        pois_geojson['features'].append({
            "geometry": {
                "type": "Point",
                "coordinates": [poi.geo[1], poi.geo[0]],
                },
            "type": "Feature",
            "properties": {
                "id": unicode(poi._id),
                "name": poi.name,
                },
            })

    response = json.dumps(
        pois_geojson,
        encoding = 'utf-8',
        ensure_ascii = False,
        )
    if params['jsonp']:
        req.response.content_type = 'application/javascript; charset=utf-8'
        return u'{0}({1})'.format(params['jsonp'], response)
    else:
        req.response.content_type = 'application/json; charset=utf-8'
        return response


@wsgihelpers.wsgify
@ramdb.ramdb_based
def index(req):
    ctx = contexts.Ctx(req)

    params = req.GET
    init_ctx(ctx, params)
    params = dict(
        category = params.get('category'),
        mode = req.urlvars.get('mode'),
        page = params.get('page'),
        term = params.get('term'),
        territory = params.get('territory'),
        )

    category, error = conv.pipe(
        conv.str_to_category_slug,
        conv.function(lambda slug: ramdb.categories_by_slug[slug]),
        conv.make_test(lambda category: (category.tags_slug or set()).issuperset(ctx.category_tags_slug or []),
            error = N_(u'Missing required tags to category')),
        )(params['category'], state = ctx)
    if error is not None:
        raise wsgihelpers.not_found(ctx, explanation = ctx._('Category Error: {0}').format(error))

    page_number, error = conv.pipe(
        conv.str_to_int,
        conv.make_greater_or_equal(1),
        conv.default(1),
        )(params['page'], state = ctx)
    if error is not None:
        raise wsgihelpers.not_found(ctx, explanation = ctx._('Page Number Error: {0}').format(error))

    term, error = conv.str_to_slug(params['term'], state = ctx)
    if error is not None:
        raise wsgihelpers.not_found(ctx, explanation = ctx._('Research Terms Error: {0}').format(error))

    ctx.postal_distribution, error = conv.str_to_postal_distribution(params['territory'], state = ctx)
    if error is not None:
        raise wsgihelpers.not_found(ctx, explanation = ctx._('Territory Error: {0}').format(error))
    elif ctx.postal_distribution:
        found_territories = list(model.Territory.find({
            'main_postal_distribution.postal_code': ctx.postal_distribution[0],
            'main_postal_distribution.postal_routing': ctx.postal_distribution[1],
            }).limit(2))
        if not found_territories:
            error = u'Territoire inconnu'
            raise wsgihelpers.not_found(ctx, explanation = ctx._('Territory Error: {0}').format(error))
        elif len(found_territories) > 1:
            error = u'Territoire ambigu'
            raise wsgihelpers.not_found(ctx, explanation = ctx._('Territory Error: {0}').format(error))
        else:
            territory_dict = found_territories[0].new_kind_code()
            territory_kind_code = (territory_dict['kind'], territory_dict['code'])
    else:
        territory_kind_code = None

    page_size = 20
    pois_infos = []
    categories_slug = set(ctx.base_categories_slug or [])
    if category is not None:
        categories_slug.add(category.slug)
    for poi_id in itertools.islice(
            ramdb.iter_pois_id(categories_slug = categories_slug, term = term,
                territory_kind_code = territory_kind_code),
            (page_number - 1) * page_size,
            page_number * page_size,
            ):
        poi = ramdb.ram_pois_by_id[poi_id]
        pois_infos.append(dict(
            _id = poi._id,
            geo = poi.geo,
            name = poi.name,
            ))

    template = '/map.mako' if params['mode'] == 'map' else '/index.mako'
    return templates.render(ctx, template,
        mode = params['mode'],
        page_number = page_number,
        page_size = page_size,
        params = params,
        pois_count = len(ramdb.ram_pois_by_id),
        pois_infos = pois_infos,
        )


def init_ctx(ctx, params):
    ctx.base_categories_slug, error = conv.uniform_sequence(
        conv.str_to_category_slug,
        )(params.getall('base_category'), state = ctx)
    if error is not None:
        raise wsgihelpers.bad_request(ctx, explanation = ctx._('Base Categories Error: {0}').format(error))

    ctx.category_tags_slug, error = conv.uniform_sequence(
        conv.str_to_category_slug,
        )(params.getall('category_tag'), state = ctx)
    if error is not None:
        raise wsgihelpers.bad_request(ctx, explanation = ctx._('Category Tags Error: {0}').format(error))

    container_base_url = params.get('container_base_url') or None
    if container_base_url is None:
        container_hostname = None
    else:
        container_hostname = urlparse.urlsplit(container_base_url).hostname or None
    try:
        gadget_id = int(params.get('gadget'))
    except (TypeError, ValueError):
        gadget_id = None
    if gadget_id is None:
        if container_base_url is not None:
            # Ignore container site when no gadget ID is given.
            container_base_url = None
            container_hostname = None
#    else:
#        subscriber = Subscriber.retrieve_by_subscription_id(ctx, gadget_id)
#        if subscriber is None:
#            ctx.front_office = True
#            return wsgihelpers.bad_request(ctx, body = htmlhelpers.modify_html(ctx, templates.render(ctx,
#                '/error-invalid-gadget-id.mako', gadget_id = gadget_id)))
#        for site in subscriber.sites or []:
#            for subscription in site.get('subscriptions') or []:
#                if subscription['id'] == gadget_id:
#                    break
#            else:
#                continue
#            break
#        else:
#            ctx.front_office = True
#            return wsgihelpers.bad_request(ctx, body = htmlhelpers.modify_html(ctx, templates.render(ctx,
#                '/error-invalid-gadget-id.mako', gadget_id = gadget_id)))
#        ctx.subscriber = subscriber
#        if gadget_id is not None and container_base_url is None and subscription.get('url') is not None:
#            # When in gadget mode but without a container_base_url, we are accessed through the noscript iframe or by a
#            # search engine. We need to retrieve the URL of page containing gadget to do a JavaScript redirection (in
#            # publication.mako).
#            container_base_url = subscription['url'] or None
#            container_hostname = urlparse.urlsplit(container_base_url).hostname or None
    ctx.container_base_url = container_base_url
    ctx.gadget_id = gadget_id

#    base_territory_type = req.urlvars.get('base_territory_type')
#    base_territory_code = req.urlvars.get('base_territory_code')
#    if base_territory_type is not None and base_territory_code is not None:
#        base_territory_kind = urls.territories_kind[base_territory_type]
#        ctx.base_territory = Territory.kind_to_class(base_territory_kind).get(base_territory_code)
#        if ctx.base_territory is None:
#            return wsgihelpers.not_found(ctx, body = htmlhelpers.modify_html(ctx, templates.render(ctx,
#                '/error-unknown-territory.mako', territory_code = base_territory_code,
#                territory_kind = base_territory_kind)))
#        if ctx.subscriber is not None:
#            subscriber_territory = ctx.subscriber.territory
#            if subscriber_territory._id not in ctx.base_territory.ancestors_id:
#                return wsgihelpers.not_found(ctx, body = htmlhelpers.modify_html(ctx, templates.render(ctx,
#                    '/error-invalid-territory.mako', parent_territory = subscriber_territory,
#                    territory = ctx.base_territory)))
#    if ctx.base_territory is None and user is not None and user.territory is not None:
#        ctx.base_territory = Territory.get_variant_class(user.territory['kind']).get(user.territory['code'])
#        if ctx.base_territory is None:
#            return wsgihelpers.not_found(ctx, body = htmlhelpers.modify_html(ctx, templates.render(ctx,
#                '/error-unknown-territory.mako', territory_code = user.territory['code'],
#                territory_kind = user.territory['kind'])))


def make_router():
    """Return a WSGI application that dispatches requests to controllers """
    return urls.make_router(
        ('GET', '^/(?P<mode>(list|map)/?)?$', index),
        ('GET', '^/a-propos/?$', about),
        ('GET', '^/api/v1/geojson/organismes/?$', export_geojson),
        ('GET', '^/api/v1/autocomplete-category/?$', autocomplete_category),
        ('GET', '^/organismes/(?P<poi_id>[a-z0-9]{24})/?$', poi),
        )


@wsgihelpers.wsgify
@ramdb.ramdb_based
def poi(req):
    ctx = contexts.Ctx(req)

    params = req.params
    init_ctx(ctx, params)
    params = dict(
        poi_id = req.urlvars.get('poi_id'),
        )

    poi_id, error = conv.str_to_object_id(params['poi_id'], ctx)
    if error is not None:
        raise wsgihelpers.not_found(ctx, explanation = ctx._('Poi ID Error: {0}').format(error))

    poi = pois.Poi.find_one({"_id": poi_id})
    return templates.render(ctx, '/poi.mako', poi = poi)
