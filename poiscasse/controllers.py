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

from biryani import strings
from territoria2 import territories

from . import contexts, conf, conv, model, ramdb, templates, urls, wsgihelpers


log = logging.getLogger(__name__)


@wsgihelpers.wsgify
def about(req):
    ctx = contexts.Ctx(req)
    return templates.render(ctx, '/about.mako')


@wsgihelpers.wsgify
@ramdb.ramdb_based
def index(req):
    ctx = contexts.Ctx(req)

    params = req.GET
    params = dict(
        category = params.get('category'),
        page = params.get('page'),
        term = params.get('q'),
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
        found_territories = list(territories.Territory.find({
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
            territory = (territory_dict['kind'], territory_dict['code'])
    else:
        territory = None

    page_size = 20
    pois_infos = []
    for poi_id in itertools.islice(
            ramdb.iter_pois_id(category_slug = category, term = term, territory_kind_code = territory),
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
        page_number = page_number,
        page_size = page_size,
        pois_count = len(ramdb.ram_pois_by_id),
        term = params['term'],
        pois_infos = pois_infos,
        )


def make_router():
    """Return a WSGI application that dispatches requests to controllers """
    return urls.make_router(
        ('GET', '^/?$', index),
        ('GET', '^/a-propos/?$', about),
        )


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

