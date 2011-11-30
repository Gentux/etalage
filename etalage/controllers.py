# -*- coding: utf-8 -*-


# Etalage -- Open Data POIs portal
# By: Emmanuel Raviart <eraviart@easter-eggs.com>
#     Romain Soufflet <rsoufflet@easter-eggs.com>
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


"""Controllers for territories"""


import datetime
import itertools
import logging
import math
import sys
import urlparse

from biryani import strings
import simplejson as json

from . import contexts, conv, pagers, ramdb, templates, urls, wsgihelpers


log = logging.getLogger(__name__)
N_ = lambda message: message


@wsgihelpers.wsgify
def about(req):
    ctx = contexts.Ctx(req)

    params = req.GET
    base_params = init_base(ctx, params)
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
                    conv.test_greater_or_equal(1),
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
def csv(req):
    ctx = contexts.Ctx(req)

    params = req.GET
    base_params = init_base(ctx, params)
    params = dict(
        category = params.get('category'),
        filter = params.get('filter'),
        term = params.get('term'),
        territory = params.get('territory'),
        )
    params.update(base_params)

    csv, errors = conv.params_to_pois_csv(params, state = ctx)
    if errors is not None:
        raise wsgihelpers.bad_request(ctx, explanation = ctx._('Error: {0}').format(errors))

    req.response.content_type = 'text/csv; charset=utf-8'
    req.response.content_disposition = 'attachment;filename=export.csv'
    return csv


@wsgihelpers.wsgify
@ramdb.ramdb_based
def export_directory_csv(req):
    ctx = contexts.Ctx(req)

    params = req.GET
    base_params = init_base(ctx, params)
    format = u'csv'
    mode = u'export'
    type = u'annuaire'
    params = dict(
        accept = params.get('accept'),
        category = params.get('category'),
        filter = params.get('filter'),
        submit = params.get('submit'),
        term = params.get('term'),
        territory = params.get('territory'),
        )
    params.update(base_params)

    accept, error = conv.pipe(conv.guess_bool, conv.default(False), conv.test_is(True))(params['accept'], state = ctx)
    if error is None:
        url_params = params.copy()
        del url_params['accept']
        del url_params['submit']
        raise wsgihelpers.redirect(ctx, location = urls.get_url(ctx, u'api/v1/{0}/{1}'.format(type, format),
            **url_params))

    errors = dict(
        accept = ctx._(u"You must accept license to be allowed to download data."),
        ) if params['submit'] else None
    return templates.render(ctx, '/export-accept-license.mako',
        export_title = ctx._(u"Directory Export in CSV Format"),
        errors = errors,
        format = format,
        mode = mode,
        params = params,
        type = type,
        )


@wsgihelpers.wsgify
@ramdb.ramdb_based
def export_directory_geojson(req):
    ctx = contexts.Ctx(req)

    params = req.GET
    base_params = init_base(ctx, params)
    format = u'geojson'
    mode = u'export'
    type = u'annuaire'
    params = dict(
        accept = params.get('accept'),
        category = params.get('category'),
        filter = params.get('filter'),
        submit = params.get('submit'),
        term = params.get('term'),
        territory = params.get('territory'),
        )
    params.update(base_params)

    accept, error = conv.pipe(conv.guess_bool, conv.default(False), conv.test_is(True))(params['accept'], state = ctx)
    if error is None:
        url_params = params.copy()
        del url_params['accept']
        del url_params['submit']
        raise wsgihelpers.redirect(ctx, location = urls.get_url(ctx, u'api/v1/{0}/{1}'.format(type, format),
            **url_params))

    errors = dict(
        accept = ctx._(u"You must accept license to be allowed to download data."),
        ) if params['submit'] else None
    return templates.render(ctx, '/export-accept-license.mako',
        export_title = ctx._(u"Directory Export in GeoJSON Format"),
        errors = errors,
        format = format,
        mode = mode,
        params = params,
        type = type,
        )


@wsgihelpers.wsgify
@ramdb.ramdb_based
def export_directory_kml(req):
    ctx = contexts.Ctx(req)

    params = req.GET
    base_params = init_base(ctx, params)
    format = u'kml'
    mode = u'export'
    type = u'annuaire'
    params = dict(
        accept = params.get('accept'),
        category = params.get('category'),
        filter = params.get('filter'),
        submit = params.get('submit'),
        term = params.get('term'),
        territory = params.get('territory'),
        )
    params.update(base_params)

    accept, error = conv.pipe(conv.guess_bool, conv.default(False), conv.test_is(True))(params['accept'], state = ctx)
    if error is None:
        url_params = params.copy()
        del url_params['accept']
        del url_params['submit']
        raise wsgihelpers.redirect(ctx, location = urls.get_url(ctx, u'api/v1/{0}/{1}'.format(type, format),
            **url_params))

    errors = dict(
        accept = ctx._(u"You must accept license to be allowed to download data."),
        ) if params['submit'] else None
    return templates.render(ctx, '/export-accept-license.mako',
        export_title = ctx._(u"Directory Export in KML Format"),
        errors = errors,
        format = format,
        mode = mode,
        params = params,
        type = type,
        )


@wsgihelpers.wsgify
@ramdb.ramdb_based
def export_geographical_coverage_csv(req):
    ctx = contexts.Ctx(req)

    params = req.GET
    base_params = init_base(ctx, params)
    format = u'csv'
    mode = u'export'
    type = u'couverture-geographique'
    params = dict(
        accept = params.get('accept'),
        category = params.get('category'),
        filter = params.get('filter'),
        submit = params.get('submit'),
        term = params.get('term'),
        territory = params.get('territory'),
        )
    params.update(base_params)

    accept, error = conv.pipe(conv.guess_bool, conv.default(False), conv.test_is(True))(params['accept'], state = ctx)
    if error is None:
        url_params = params.copy()
        del url_params['accept']
        del url_params['submit']
        # TODO
        raise wsgihelpers.redirect(ctx, location = urls.get_url(ctx, u'api/v1/{0}/{1}'.format(type, format),
            **url_params))

    errors = dict(
        accept = ctx._(u"You must accept license to be allowed to download data."),
        ) if params['submit'] else None
    # TODO
    return templates.render(ctx, '/export-accept-license.mako',
        export_title = ctx._(u"Geographical Coverage Export in CSV Format"),
        errors = errors,
        format = format,
        mode = mode,
        params = params,
        type = type,
        )


@wsgihelpers.wsgify
@ramdb.ramdb_based
def geojson(req):
    ctx = contexts.Ctx(req)

    params = req.GET
    base_params = init_base(ctx, params)
    params = dict(
        bbox = params.get('bbox'),
        category = params.get('category'),
        context = params.get('context'),
        current = params.get('current'),
        filter = params.get('filter'),
        jsonp = params.get('jsonp'),
        term = params.get('term'),
        territory = params.get('territory'),
        )
    params.update(base_params)

    data, errors = conv.pipe(
        conv.params_to_pois_layer_data,
        conv.default_pois_layer_data_bbox,
        )(params, state = ctx)
    if errors is not None:
        raise wsgihelpers.bad_request(ctx, explanation = ctx._('Error: {0}').format(errors))
    clusters, errors = conv.layer_data_to_clusters(data, state = ctx)
    if errors is not None:
        raise wsgihelpers.bad_request(ctx, explanation = ctx._('Error: {0}').format(errors))

    geojson = {
        'type': 'FeatureCollection',
        'properties': {
            'context': params.get('context'), # Parameter given in request that is returned as is.
            'date': unicode(datetime.datetime.utcnow()),
        },
        'features': [
            {
                'type': 'Feature',
                'bbox': [
                    cluster.left,
                    cluster.bottom,
                    cluster.right,
                    cluster.top,
                    ] if cluster.count > 1 else None,
                'geometry': {
                    'type': 'Point',
                    'coordinates': [cluster.center_longitude, cluster.center_latitude],
                    },
                'properties': {
                    'competent': cluster.competent,
                    'count': cluster.count,
                    'id': str(cluster.center_pois[0]._id),
                    'centerPois': [
                        {
                            'id': str(poi._id),
                            'name': poi.name,
                            'postalDistribution': poi.postal_distribution_str,
                            'streetAddress': poi.street_address,
                            }
                        for poi in cluster.center_pois
                        ],
                    },
                }
            for cluster in clusters
            ],
        }
    territory = data.get('territory')
    if territory is not None:
        geojson['features'].insert(0, {
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [territory.geo[1], territory.geo[0]],
                },
            'properties': {
                'home': True,
                'id': str(territory._id),
                },
            })

    response = json.dumps(
        geojson,
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

    params = req.params
    base_params = init_base(ctx, params)

    # Redirect to another page.
    url_args = ('carte',)
    url_kwargs = dict(params)
    if ctx.container_base_url is None or ctx.gadget_id is None:
        raise wsgihelpers.redirect(ctx, location = urls.get_url(ctx, *url_args, **url_kwargs))
    else:
        return templates.render(ctx, '/http-simulated-redirect.mako',
            url_args = url_args,
            url_kwargs = url_kwargs,
            )


@wsgihelpers.wsgify
@ramdb.ramdb_based
def index_directory(req):
    ctx = contexts.Ctx(req)

    params = req.GET
    base_params = init_base(ctx, params)
    mode = u'annuaire'
    params = dict(
        category = params.get('category'),
        filter = params.get('filter'),
        term = params.get('term'),
        territory = params.get('territory'),
        )
    params.update(base_params)

    data, errors = conv.params_to_pois_directory_data(params, state = ctx)
    if errors is not None:
        directory = None
        territory = None
    else:
        categories_slug = set(ctx.base_categories_slug or [])
        if data.get('category') is not None:
            categories_slug.add(data['category'].slug)
        territory = data['territory']
        related_territories_id = ramdb.get_territory_related_territories_id(territory)
        filter = data.get('filter')
        if filter == 'competence':
            competence_territories_id = related_territories_id
            presence_territory = None
        elif filter == 'presence':
            competence_territories_id = None
            presence_territory = territory
        else:
            competence_territories_id = None
            presence_territory = None
        pois_id_iter = ramdb.iter_pois_id(categories_slug = categories_slug,
            competence_territories_id = competence_territories_id, presence_territory = presence_territory,
            term = data.get('term'))
        pois = set(
            poi
            for poi in (
                ramdb.pois_by_id.get(poi_id)
                for poi_id in pois_id_iter
                )
            if poi is not None
            )
        territory_latitude_cos = math.cos(math.radians(territory.geo[0]))
        territory_latitude_sin = math.sin(math.radians(territory.geo[0]))
        distance_and_poi_couples = sorted(
            (
                (
                    6372.8 * math.acos(
                        math.sin(math.radians(poi.geo[0])) * territory_latitude_sin
                        + math.cos(math.radians(poi.geo[0])) * territory_latitude_cos
                            * math.cos(math.radians(poi.geo[1] - territory.geo[1]))
                        ),
                    poi,
                    )
                for poi in pois
                if poi.geo is not None
                ),
            key = lambda distance_and_poi: distance_and_poi[0],
            )
        directory = {}
        for distance, poi in distance_and_poi_couples:
            if poi.organism_type_slug is None:
                continue
            organism_type_pois = directory.get(poi.organism_type_slug)
            if organism_type_pois is not None and len(organism_type_pois) >= 3:
                continue
            if filter is None:
                if poi.competence_territories_id is None:
                    # When no filter is given, when a POI has no notion of competence territory, only show it when it is
                    # not too far away from center territory.
                    if distance > ctx.distance:
                        continue
                elif related_territories_id.isdisjoint(poi.competence_territories_id):
                    # In directory mode without filter, the incompetent organisms must not be shown.
                    continue
            if organism_type_pois is None:
                directory[poi.organism_type_slug] = [poi]
            else:
                organism_type_pois.append(poi)
    return templates.render(ctx, '/directory.mako',
        directory = directory,
        errors = errors,
        mode = mode,
        params = params,
        territory = territory,
        )


@wsgihelpers.wsgify
@ramdb.ramdb_based
def index_export(req):
    ctx = contexts.Ctx(req)

    params = req.GET
    base_params = init_base(ctx, params)
    mode = u'export'
    params = dict(
        category = params.get('category'),
        filter = params.get('filter'),
# TODO
        submit = params.get('submit'),
        term = params.get('term'),
        territory = params.get('territory'),
# TODO
        type_and_format = params.get('type_and_format'),
        )
    params.update(base_params)

    data, errors = conv.struct(
        dict(
            type_and_format = conv.pipe(
                conv.str_to_slug,
                conv.test_in([
                    'annuaire-csv',
                    'annuaire-geojson',
                    'annuaire-kml',
                    'couverture-geographique-csv',
                    ]),
                ),
            ),
        default = 'ignore',
        keep_empty = True,
        )(params, state = ctx)
    if errors is None:
        if params['submit']:
            if data.get('type_and_format') is not None:
                type, format = data['type_and_format'].rsplit(u'-', 1)

                # Form submitted. Redirect to another page.
                url_args = ('export', type, format)
                url_kwargs = dict(
                    category = params['category'],
                    filter = params['filter'],
                    term = params['term'],
                    territory = params['territory'],
                    )
                if ctx.container_base_url is None or ctx.gadget_id is None:
                    raise wsgihelpers.redirect(ctx, location = urls.get_url(ctx, *url_args, **url_kwargs))
                else:
                    return templates.render(ctx, '/http-simulated-redirect.mako',
                        url_args = url_args,
                        url_kwargs = url_kwargs,
                        )
            errors = dict(
                type_and_format = ctx._(u'Missing value'),
                )
    return templates.render(ctx, '/export.mako',
        errors = errors,
        mode = mode,
        params = params,
        )


@wsgihelpers.wsgify
@ramdb.ramdb_based
def index_list(req):
    ctx = contexts.Ctx(req)

    params = req.GET
    base_params = init_base(ctx, params)
    mode = u'liste'
    params = dict(
        category = params.get('category'),
        filter = params.get('filter'),
        page = params.get('page'),
        term = params.get('term'),
        territory = params.get('territory'),
        )
    params.update(base_params)

    data, errors = conv.params_to_pois_list_data(params, state = ctx)
    if errors is not None:
        pager = None
    else:
        categories_slug = set(ctx.base_categories_slug or [])
        if data.get('category') is not None:
            categories_slug.add(data['category'].slug)
        filter = data.get('filter')
        territory = data.get('territory')
        related_territories_id = ramdb.get_territory_related_territories_id(territory) \
            if territory is not None else None
        if filter == 'competence':
            competence_territories_id = related_territories_id
            presence_territory = None
        elif filter == 'presence':
            competence_territories_id = None
            presence_territory = territory
        else:
            competence_territories_id = None
            presence_territory = None
        pois_id_iter = ramdb.iter_pois_id(categories_slug = categories_slug,
            competence_territories_id = competence_territories_id, presence_territory = presence_territory,
            term = data.get('term'))
        pois = set(
            poi
            for poi in (
                ramdb.pois_by_id.get(poi_id)
                for poi_id in pois_id_iter
                )
            if poi is not None
            )
        pager = pagers.Pager(item_count = len(pois), page_number = data['page_number'])
        if territory is None:
            pois = sorted(pois, key = lambda poi: poi.name) # TODO: Use slug instead of name.
            pager.items = [
                poi
                for poi in itertools.islice(pois, pager.first_item_index, pager.last_item_number)
                ]
        else:
            territory_latitude_cos = math.cos(math.radians(territory.geo[0]))
            territory_latitude_sin = math.sin(math.radians(territory.geo[0]))
            incompetence_distance_and_poi_triples = sorted(
                (
                    (
                        # is not competent
                        poi.competence_territories_id is not None
                            and related_territories_id.isdisjoint(poi.competence_territories_id),
                        # distance
                        6372.8 * math.acos(
                            math.sin(math.radians(poi.geo[0])) * territory_latitude_sin
                            + math.cos(math.radians(poi.geo[0])) * territory_latitude_cos
                                * math.cos(math.radians(poi.geo[1] - territory.geo[1]))
                            ) if poi.geo is not None else (sys.float_info.max, poi),
                        # POI
                        poi,
                        )
                    for poi in pois
                    ),
                key = lambda incompetence_distance_and_poi_triple: incompetence_distance_and_poi_triple[:2],
                )
            pager.items = [
                poi
                for incompetence, distance, poi in itertools.islice(incompetence_distance_and_poi_triples,
                    pager.first_item_index, pager.last_item_number)
                ]
    return templates.render(ctx, '/list.mako',
        errors = errors,
        mode = mode,
        pager = pager,
        params = params,
        )


@wsgihelpers.wsgify
@ramdb.ramdb_based
def index_map(req):
    ctx = contexts.Ctx(req)

    params = req.GET
    base_params = init_base(ctx, params)
    mode = u'carte'
    params = dict(
        bbox = params.get('bbox'),
        category = params.get('category'),
        filter = params.get('filter'),
        term = params.get('term'),
        territory = params.get('territory'),
        )
    params.update(base_params)

    data, errors = conv.pipe(
        conv.params_to_pois_layer_data,
        conv.default_pois_layer_data_bbox,
        )(params, state = ctx)
    if errors is None:
        bbox = data['bbox']
        territory = data.get('territory')
    else:
        bbox = None
        territory = None
    return templates.render(ctx, '/map.mako',
        bbox = bbox,
        errors = errors,
        mode = mode,
        params = params,
        territory = territory,
        )


def init_base(ctx, params):
    base_params = dict(
        base_category = params.getall('base_category'),
        category_tag = params.getall('category_tag'),
        container_base_url = params.get('container_base_url'),
        distance = params.get('distance'),
        gadget = params.get('gadget'),
        hide_category = params.get('hide_category'),
        show_filter = params.get('show_filter'),
        )

    ctx.base_categories_slug, error = conv.uniform_sequence(
        conv.str_to_category_slug,
        )(base_params['base_category'], state = ctx)
    if error is not None:
        raise wsgihelpers.bad_request(ctx, explanation = ctx._('Base Categories Error: {0}').format(error))

    ctx.category_tags_slug, error = conv.uniform_sequence(
        conv.str_to_category_slug,
        )(base_params['category_tag'], state = ctx)
    if error is not None:
        raise wsgihelpers.bad_request(ctx, explanation = ctx._('Category Tags Error: {0}').format(error))

    container_base_url = base_params['container_base_url'] or None
    if container_base_url is None:
        container_hostname = None
    else:
        container_hostname = urlparse.urlsplit(container_base_url).hostname or None
    try:
        gadget_id = int(base_params['gadget'])
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

    ctx.distance, error = conv.pipe(
        conv.str_to_float,
        conv.test_between(0.0, 40075.16),
        conv.default(20.0),
        )(base_params['distance'], state = ctx)
    if error is not None:
        raise wsgihelpers.bad_request(ctx, explanation = ctx._('Distance Error: {0}').format(error))

    ctx.hide_category, error = conv.pipe(
        conv.guess_bool,
        conv.default(False),
        )(base_params['hide_category'], state = ctx)
    if error is not None:
        raise wsgihelpers.bad_request(ctx, explanation = ctx._('Hide Category Error: {0}').format(error))

    ctx.show_filter, error = conv.pipe(
        conv.guess_bool,
        conv.default(False),
        )(base_params['show_filter'], state = ctx)
    if error is not None:
        raise wsgihelpers.bad_request(ctx, explanation = ctx._('Show Filter Error: {0}').format(error))

    return base_params


@wsgihelpers.wsgify
@ramdb.ramdb_based
def kml(req):
    ctx = contexts.Ctx(req)

    params = req.GET
    base_params = init_base(ctx, params)
    params = dict(
        bbox = params.get('bbox'),
        category = params.get('category'),
        context = params.get('context'),
        current = params.get('current'),
        filter = params.get('filter'),
        term = params.get('term'),
        territory = params.get('territory'),
        )
    params.update(base_params)

    clusters, errors = conv.pipe(
        conv.params_to_pois_layer_data,
        conv.default_pois_layer_data_bbox,
        conv.layer_data_to_clusters,
        )(params, state = ctx)
    if errors is not None:
        raise wsgihelpers.bad_request(ctx, explanation = ctx._('Error: {0}').format(errors))

    req.response.content_type = 'application/vnd.google-earth.kml+xml; charset=utf-8'
    return templates.render(ctx, '/kml.mako',
        clusters = clusters,
        params = params,
        )


def make_router():
    """Return a WSGI application that dispatches requests to controllers """
    return urls.make_router(
        ('GET', '^/?$', index),
        ('GET', '^/a-propos/?$', about),
        ('GET', '^/annuaire/?$', index_directory),
        ('GET', '^/api/v1/annuaire/csv/?$', csv),
        ('GET', '^/api/v1/annuaire/geojson/?$', geojson),
        ('GET', '^/api/v1/annuaire/kml/?$', kml),
        ('GET', '^/api/v1/categories/autocomplete/?$', autocomplete_category),
        ('GET', '^/api/v1/couverture-geographique/csv/?$', csv), # TODO
        ('GET', '^/carte/?$', index_map),
        ('GET', '^/export/?$', index_export),
        ('GET', '^/export/annuaire/csv/?$', export_directory_csv),
        ('GET', '^/export/annuaire/geojson/?$', export_directory_geojson),
        ('GET', '^/export/annuaire/kml/?$', export_directory_kml),
        ('GET', '^/export/couverture-geographique/csv/?$', export_geographical_coverage_csv),
        ('GET', '^/liste/?$', index_list),
        ('GET', '^/organismes/(?P<poi_id>[a-z0-9]{24})/?$', poi),
        )


@wsgihelpers.wsgify
@ramdb.ramdb_based
def poi(req):
    ctx = contexts.Ctx(req)

    params = req.params
    base_params = init_base(ctx, params)
    params = dict(
        poi_id = req.urlvars.get('poi_id'),
        )
    params.update(base_params)

    poi, error = conv.pipe(
        conv.str_to_object_id,
        conv.id_to_poi,
        conv.exists,
        )(params['poi_id'], ctx)
    if error is not None:
        raise wsgihelpers.bad_request(ctx, explanation = ctx._('POI ID Error: {0}').format(error))

    return templates.render(ctx, '/poi.mako', poi = poi)

