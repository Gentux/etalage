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


import itertools
import logging
import urlparse

from biryani import strings

from . import contexts, conf, conv, model, pois, ramdb, templates, urls, wsgihelpers


log = logging.getLogger(__name__)


@wsgihelpers.wsgify
def about(req):
    ctx = contexts.Ctx(req)

    params = req.GET
    init_ctx(ctx, params)
    return templates.render(ctx, '/about.mako')


@wsgihelpers.wsgify
@ramdb.ramdb_based
def index(req):
    ctx = contexts.Ctx(req)

    params = req.GET
    init_ctx(ctx, params)
    params = dict(
        base_category = params.get('base_category'),
        category = params.get('category'),
        page = params.get('page'),
        term = params.get('term'),
        territory = params.get('territory'),
        )

    base_category_slug, error = conv.str_to_slug(params['base_category'], state = ctx)
    if error is not None:
        raise wsgihelpers.not_found(ctx, explanation = ctx._('Base Category Error: {0}').format(error))

    category_slug, error = conv.str_to_slug(params['category'], state = ctx)
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
    for poi_id in itertools.islice(
            ramdb.iter_pois_id(categories_slug = [base_category_slug, category_slug], term = term,
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

    return templates.render(ctx, '/index.mako',
        category_slug = category_slug,
        page_number = page_number,
        page_size = page_size,
        pois_count = len(ramdb.ram_pois_by_id),
        term = params['term'],
        pois_infos = pois_infos,
        )


def init_ctx(ctx, params):
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
        ('GET', '^/?$', index),
        ('GET', '^/a-propos/?$', about),
        ('GET', '^/poi/(?P<poi_id>[a-z0-9]{24})/?$', poi),
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


#@wsgihelpers.wsgify
#@ramdb.ramdb_based
#def territory(req):
#    ctx = contexts.Ctx(req)

#    params = req.GET
#    params = dict(
#        postal_distribution = req.urlvars.get('postal_distribution'),
#        type = req.urlvars.get('type'),
#        )

#    territory_kind, error = conv.pipe(
#        conv.str_to_slug,
#        conv.slug_plural_fr_to_territory_kind,
#        conv.exists,
#        )(params['type'], state = ctx)
#    if error is not None:
#        raise wsgihelpers.not_found(ctx, explanation = ctx._('Territory Type Error: {0}').format(error))

#    territory, error = conv.pipe(
#        conv.str_to_postal_distribution,
#        conv.make_postal_distribution_to_territory_id(guess = True, kinds = [territory_kind]),
#        conv.id_to_territory,
#        conv.exists,
#        )(params['postal_distribution'], state = ctx)
#    if error is not None:
#        raise wsgihelpers.not_found(ctx, explanation = ctx._('Territory Error: {0}').format(error))

#    territory_full_url = urls.get_full_url(ctx, territory.ref)
#    if req.url != territory_full_url:
#        raise wsgihelpers.redirect(ctx, location = territory_full_url)

#    return templates.render(ctx, '/territory.mako', territory = territory)

