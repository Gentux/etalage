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


"""Controllers for territories"""


from cStringIO import StringIO
import datetime
import json
import logging
import math
import urllib2
import urlparse
import zipfile

from biryani import strings

from . import conf, contexts, conv, model, pagers, ramdb, templates, urls, wsgihelpers


log = logging.getLogger(__name__)
N_ = lambda message: message


@wsgihelpers.wsgify
def about(req):
    ctx = contexts.Ctx(req)

    params = req.GET
    init_base(ctx, params)
    return templates.render(ctx, '/about.mako')


@wsgihelpers.wsgify
@ramdb.ramdb_based
def autocomplete_category(req):
    ctx = contexts.Ctx(req)

    headers = []
    params = req.GET
    inputs = dict(
        context = params.get('context'),
        jsonp = params.get('jsonp'),
        page = params.get('page'),
        page_max_size = params.get('page_max_size'),
        tag = params.getall('tag'),
        term = params.get('term'),
        )
    data, errors = conv.pipe(
        conv.struct(
            dict(
                page = conv.pipe(
                    conv.input_to_int,
                    conv.test_greater_or_equal(1),
                    conv.default(1),
                    ),
                page_max_size = conv.pipe(
                    conv.input_to_int,
                    conv.default(conf['pager.page_max_size']),
                    ),
                tag = conv.uniform_sequence(conv.input_to_tag_slug),
                term = conv.make_input_to_slug(separator = u' ', transform = strings.upper),
                ),
            default = 'drop',
            drop_none_values = False,
            ),
        conv.rename_item('page', 'page_number'),
        conv.rename_item('tag', 'tags_slug'),
        )(inputs, state = ctx)
    if errors is not None:
        return wsgihelpers.respond_json(
            ctx,
            dict(
                apiVersion = '1.0',
                context = inputs['context'],
                error = dict(
                    code = 400,  # Bad Request
                    errors = [
                        dict(
                            location = key,
                            message = error,
                            )
                        for key, error in sorted(errors.iteritems())
                        ],
                    # message will be automatically defined.
                    ),
                method = req.script_name,
                params = inputs,
                url = req.url.decode('utf-8'),
                ),
            headers = headers,
            jsonp = inputs['jsonp'],
            )

    possible_pois_id = ramdb.intersection_set(
        model.Poi.ids_by_category_slug[category_slug]
        for category_slug in (data['tags_slug'] or [])
        )
    if possible_pois_id is None:
        categories_infos = sorted(
            (-len(model.Poi.ids_by_category_slug.get(category_slug, [])), category_slug)
            for category_slug in ramdb.iter_categories_slug(tags_slug = data['tags_slug'], term = data['term'])
            if category_slug not in (data['tags_slug'] or [])
            )
    else:
        categories_infos = sorted(
            (-count, category_slug)
            for count, category_slug in (
                (
                    len(set(model.Poi.ids_by_category_slug.get(category_slug, [])).intersection(possible_pois_id)),
                    category_slug,
                    )
                for category_slug in ramdb.iter_categories_slug(tags_slug = data['tags_slug'], term = data['term'])
                if category_slug not in (data['tags_slug'] or [])
                )
            if count > 0 and count != len(possible_pois_id)
            )
    pager = pagers.Pager(
        item_count = len(categories_infos),
        page_number = data['page_number'],
        page_max_size = data.get('page_max_size') or conf['pager.page_max_size'],
        )
    pager.items = [
        dict(
            count = -category_infos[0],
            tag = ramdb.category_by_slug[category_infos[1]].name,
            )
        for category_infos in categories_infos[pager.first_item_index:pager.last_item_number]
        ]
    return wsgihelpers.respond_json(
        ctx,
        dict(
            apiVersion = '1.0',
            context = inputs['context'],
            data = dict(
                currentItemCount = len(pager.items),
                items = pager.items,
                itemsPerPage = pager.page_size,
                pageIndex = pager.page_number,
                startIndex = pager.first_item_index,
                totalItems = pager.item_count,
                totalPages = pager.page_count,
                ),
            method = req.script_name,
            params = inputs,
            url = req.url.decode('utf-8'),
            ),
        headers = headers,
        jsonp = inputs['jsonp'],
        )


@wsgihelpers.wsgify
@ramdb.ramdb_based
def csv(req):
    ctx = contexts.Ctx(req)

    if conf['hide_export']:
        return wsgihelpers.not_found(ctx, explanation = ctx._(u'Export disabled by configuration'))

    params = req.GET
    inputs = init_base(ctx, params)
    inputs.update(model.Poi.extract_search_inputs_from_params(ctx, params))
    inputs['format'] = u'csv'

    csv_bytes_by_name, errors = conv.pipe(
        conv.inputs_to_pois_csv_infos,
        conv.csv_infos_to_csv_bytes,
        )(inputs, state = ctx)
    if errors is not None:
        return wsgihelpers.bad_request(ctx, explanation = ctx._('Error: {0}').format(errors))
    if not csv_bytes_by_name:
        return wsgihelpers.no_content(ctx)
    if len(csv_bytes_by_name) == 1:
        csv_filename, csv_bytes = csv_bytes_by_name.items()[0]
        req.response.content_type = 'text/csv; charset=utf-8'
        req.response.content_disposition = 'attachment;filename={0}'.format(csv_filename)
        return csv_bytes
    zip_file = StringIO()
    with zipfile.ZipFile(zip_file, 'w') as zip_archive:
        for csv_filename, csv_bytes in csv_bytes_by_name.iteritems():
            zip_archive.writestr(csv_filename, csv_bytes)
    req.response.content_type = 'application/zip'
    req.response.content_disposition = 'attachment;filename=export.zip'
    return zip_file.getvalue()


def data_to_render_list_data(ctx, data, inputs, page_max_size = None):
    if page_max_size is None:
        page_max_size = conf['pager.page_max_size']
    non_territorial_search_data = model.Poi.extract_non_territorial_search_data(ctx, data)
    base_territory = data.get('base_territory')
    territory = data['territory']
    competence_territories_id = None
    presence_territory = None
    if conf['handle_competence_territories']:
        if territory and territory.__class__.__name__ not in model.communes_kinds:
            presence_territory = territory
        if territory:
            competence_territories_id = ramdb.get_territory_related_territories_id(territory)
        if base_territory and competence_territories_id is None:
            competence_territories_id = ramdb.get_territory_related_territories_id(base_territory)
    else:
        if territory and territory.__class__.__name__ not in model.communes_kinds:
            presence_territory = territory
        elif base_territory:
            presence_territory = data['base_territory']

    pois_id_iter = model.Poi.iter_ids(
        ctx,
        competence_territories_id = competence_territories_id,
        presence_territory = presence_territory,
        **non_territorial_search_data)

    poi_by_id = dict(
        (poi._id, poi)
        for poi in (
            model.Poi.instance_by_id.get(poi_id)
            for poi_id in pois_id_iter
            )
        if poi is not None
        )
    pager = pagers.Pager(
        item_count = len(poi_by_id),
        page_number = data['page_number'] if data['poi_index'] is None else (
            data['poi_index'] / page_max_size
            ) + 1,
        page_max_size = page_max_size,
        )
    pager.items = model.Poi.sort_and_paginate_pois_list(
        ctx,
        pager,
        poi_by_id,
        related_territories_id = competence_territories_id,
        territory = territory or data.get('base_territory'),
        sort_key = data['sort_key'],
        **non_territorial_search_data
        )

    return pager


@wsgihelpers.wsgify
@ramdb.ramdb_based
def excel(req):
    ctx = contexts.Ctx(req)

    if conf['hide_export']:
        return wsgihelpers.not_found(ctx, explanation = ctx._(u'Export disabled by configuration'))

    params = req.GET
    inputs = init_base(ctx, params)
    inputs.update(model.Poi.extract_search_inputs_from_params(ctx, params))
    inputs['format'] = u'csv'

    excel_bytes, errors = conv.pipe(
        conv.inputs_to_pois_csv_infos,
        conv.csv_infos_to_excel_bytes,
        )(inputs, state = ctx)
    if errors is not None:
        return wsgihelpers.bad_request(ctx, explanation = ctx._('Error: {0}').format(errors))
    if not excel_bytes:
        return wsgihelpers.no_content(ctx)
    req.response.content_type = 'application/vnd.ms-excel'
    req.response.content_disposition = 'attachment;filename=export.xls'
    return excel_bytes


@wsgihelpers.wsgify
@ramdb.ramdb_based
def export_directory_csv(req):
    ctx = contexts.Ctx(req)

    if conf['hide_export']:
        return wsgihelpers.not_found(ctx, explanation = ctx._(u'Export disabled by configuration'))

    params = req.GET
    inputs = init_base(ctx, params)
    inputs.update(model.Poi.extract_search_inputs_from_params(ctx, params))
    inputs.update(dict(
        accept = params.get('accept'),
        submit = params.get('submit'),
        ))

    format = u'csv'
    mode = u'export'
    type = u'annuaire'

    accept, error = conv.pipe(conv.guess_bool, conv.default(False), conv.test_is(True))(inputs['accept'], state = ctx)
    if error is None:
        url_params = dict(
            (model.Poi.rename_input_to_param(input_name), value)
            for input_name, value in inputs.iteritems()
            )
        del url_params['accept']
        del url_params['submit']
        return wsgihelpers.redirect(
            ctx,
            location = urls.get_url(ctx, u'api/v1/{0}/{1}'.format(type, format), **url_params),
            )

    data, errors = conv.merge(
        model.Poi.make_inputs_to_search_data(),
        conv.struct(
            dict(
                accept = conv.test(
                    lambda value: not inputs['submit'],
                    error = N_(u"You must accept license to be allowed to download data."),
                    handle_none_value = True,
                    ),
                ),
            default = 'drop',
            drop_none_values = False,
            ),
        )(inputs, state = ctx)
    return templates.render(
        ctx,
        '/export-accept-license.mako',
        export_title = ctx._(u"Directory Export in CSV Format"),
        errors = errors,
        format = format,
        inputs = inputs,
        mode = mode,
        type = type,
        **model.Poi.extract_non_territorial_search_data(ctx, data))


@wsgihelpers.wsgify
@ramdb.ramdb_based
def export_directory_excel(req):
    ctx = contexts.Ctx(req)

    if conf['hide_export']:
        return wsgihelpers.not_found(ctx, explanation = ctx._(u'Export disabled by configuration'))

    params = req.GET
    inputs = init_base(ctx, params)
    inputs.update(model.Poi.extract_search_inputs_from_params(ctx, params))
    inputs.update(dict(
        accept = params.get('accept'),
        submit = params.get('submit'),
        ))

    format = u'excel'
    mode = u'export'
    type = u'annuaire'

    accept, error = conv.pipe(conv.guess_bool, conv.default(False), conv.test_is(True))(inputs['accept'], state = ctx)
    if error is None:
        url_params = dict(
            (model.Poi.rename_input_to_param(input_name), value)
            for input_name, value in inputs.iteritems()
            )
        del url_params['accept']
        del url_params['submit']
        return wsgihelpers.redirect(
            ctx,
            location = urls.get_url(ctx, u'api/v1/{0}/{1}'.format(type, format), **url_params),
            )

    data, errors = conv.merge(
        model.Poi.make_inputs_to_search_data(),
        conv.struct(
            dict(
                accept = conv.test(
                    lambda value: not inputs['submit'],
                    error = N_(u"You must accept license to be allowed to download data."),
                    handle_none_value = True,
                    ),
                ),
            default = 'drop',
            drop_none_values = False,
            ),
        )(inputs, state = ctx)
    return templates.render(
        ctx,
        '/export-accept-license.mako',
        export_title = ctx._(u"Directory Export in Excel Format"),
        errors = errors,
        format = format,
        inputs = inputs,
        mode = mode,
        type = type,
        **model.Poi.extract_non_territorial_search_data(ctx, data))


@wsgihelpers.wsgify
@ramdb.ramdb_based
def export_directory_geojson(req):
    ctx = contexts.Ctx(req)

    if conf['hide_export']:
        return wsgihelpers.not_found(ctx, explanation = ctx._(u'Export disabled by configuration'))

    params = req.GET
    inputs = init_base(ctx, params)
    inputs.update(model.Poi.extract_search_inputs_from_params(ctx, params))
    inputs.update(dict(
        accept = params.get('accept'),
        submit = params.get('submit'),
        ))

    format = u'geojson'
    mode = u'export'
    type = u'annuaire'

    accept, error = conv.pipe(conv.guess_bool, conv.default(False), conv.test_is(True))(inputs['accept'], state = ctx)
    if error is None:
        url_params = dict(
            (model.Poi.rename_input_to_param(input_name), value)
            for input_name, value in inputs.iteritems()
            )
        del url_params['accept']
        del url_params['submit']
        return wsgihelpers.redirect(
            ctx,
            location = urls.get_url(ctx, u'api/v1/{0}/{1}'.format(type, format), **url_params),
            )

    data, errors = conv.merge(
        model.Poi.make_inputs_to_search_data(),
        conv.struct(
            dict(
                accept = conv.test(
                    lambda value: not inputs['submit'],
                    error = N_(u"You must accept license to be allowed to download data."),
                    handle_none_value = True,
                    ),
                ),
            default = 'drop',
            drop_none_values = False,
            ),
        )(inputs, state = ctx)
    return templates.render(
        ctx,
        '/export-accept-license.mako',
        export_title = ctx._(u"Directory Export in GeoJSON Format"),
        errors = errors,
        format = format,
        inputs = inputs,
        mode = mode,
        type = type,
        **model.Poi.extract_non_territorial_search_data(ctx, data))


@wsgihelpers.wsgify
@ramdb.ramdb_based
def export_directory_kml(req):
    ctx = contexts.Ctx(req)

    if conf['hide_export']:
        return wsgihelpers.not_found(ctx, explanation = ctx._(u'Export disabled by configuration'))

    params = req.GET
    inputs = init_base(ctx, params)
    inputs.update(model.Poi.extract_search_inputs_from_params(ctx, params))
    inputs.update(dict(
        accept = params.get('accept'),
        submit = params.get('submit'),
        ))

    format = u'kml'
    mode = u'export'
    type = u'annuaire'

    accept, error = conv.pipe(conv.guess_bool, conv.default(False), conv.test_is(True))(inputs['accept'], state = ctx)
    if error is None:
        url_params = dict(
            (model.Poi.rename_input_to_param(input_name), value)
            for input_name, value in inputs.iteritems()
            )
        del url_params['accept']
        del url_params['submit']
        return wsgihelpers.redirect(
            ctx,
            location = urls.get_url(ctx, u'api/v1/{0}/{1}'.format(type, format), **url_params),
            )

    data, errors = conv.merge(
        model.Poi.make_inputs_to_search_data(),
        conv.struct(
            dict(
                accept = conv.test(
                    lambda value: not inputs['submit'],
                    error = N_(u"You must accept license to be allowed to download data."),
                    handle_none_value = True,
                    ),
                ),
            default = 'drop',
            drop_none_values = False,
            ),
        )(inputs, state = ctx)
    return templates.render(
        ctx,
        '/export-accept-license.mako',
        export_title = ctx._(u"Directory Export in KML Format"),
        errors = errors,
        format = format,
        inputs = inputs,
        mode = mode,
        type = type,
        **model.Poi.extract_non_territorial_search_data(ctx, data))


@wsgihelpers.wsgify
@ramdb.ramdb_based
def export_geographical_coverage_csv(req):
    ctx = contexts.Ctx(req)

    if conf['hide_export']:
        return wsgihelpers.not_found(ctx, explanation = ctx._(u'Export disabled by configuration'))

    params = req.GET
    inputs = init_base(ctx, params)
    inputs.update(model.Poi.extract_search_inputs_from_params(ctx, params))
    inputs.update(dict(
        accept = params.get('accept'),
        submit = params.get('submit'),
        ))

    format = u'csv'
    mode = u'export'
    type = u'couverture'

    accept, error = conv.pipe(conv.guess_bool, conv.default(False), conv.test_is(True))(inputs['accept'], state = ctx)
    if error is None:
        url_params = dict(
            (model.Poi.rename_input_to_param(input_name), value)
            for input_name, value in inputs.iteritems()
            )
        del url_params['accept']
        del url_params['submit']
        return wsgihelpers.redirect(
            ctx,
            location = urls.get_url(ctx, u'api/v1/{0}/{1}'.format(type, format), **url_params),
            )

    data, errors = conv.merge(
        model.Poi.make_inputs_to_search_data(),
        conv.struct(
            dict(
                accept = conv.test(
                    lambda value: not inputs['submit'],
                    error = N_(u"You must accept license to be allowed to download data."),
                    handle_none_value = True,
                    ),
                ),
            default = 'drop',
            drop_none_values = False,
            ),
        )(inputs, state = ctx)
    return templates.render(
        ctx,
        '/export-accept-license.mako',
        export_title = ctx._(u"Geographical Coverage Export in CSV Format"),
        errors = errors,
        format = format,
        inputs = inputs,
        mode = mode,
        type = type,
        **model.Poi.extract_non_territorial_search_data(ctx, data))


@wsgihelpers.wsgify
@ramdb.ramdb_based
def export_geographical_coverage_excel(req):
    ctx = contexts.Ctx(req)

    if conf['hide_export']:
        return wsgihelpers.not_found(ctx, explanation = ctx._(u'Export disabled by configuration'))

    params = req.GET
    inputs = init_base(ctx, params)
    inputs.update(model.Poi.extract_search_inputs_from_params(ctx, params))
    inputs.update(dict(
        accept = params.get('accept'),
        submit = params.get('submit'),
        ))

    format = u'excel'
    mode = u'export'
    type = u'couverture'

    accept, error = conv.pipe(conv.guess_bool, conv.default(False), conv.test_is(True))(inputs['accept'], state = ctx)
    if error is None:
        url_params = dict(
            (model.Poi.rename_input_to_param(input_name), value)
            for input_name, value in inputs.iteritems()
            )
        del url_params['accept']
        del url_params['submit']
        return wsgihelpers.redirect(
            ctx,
            location = urls.get_url(ctx, u'api/v1/{0}/{1}'.format(type, format), **url_params),
            )

    data, errors = conv.merge(
        model.Poi.make_inputs_to_search_data(),
        conv.struct(
            dict(
                accept = conv.test(
                    lambda value: not inputs['submit'],
                    error = N_(u"You must accept license to be allowed to download data."),
                    handle_none_value = True,
                    ),
                ),
            default = 'drop',
            drop_none_values = False,
            ),
        )(inputs, state = ctx)
    return templates.render(
        ctx,
        '/export-accept-license.mako',
        export_title = ctx._(u"Geographical Coverage Export in Excel Format"),
        errors = errors,
        format = format,
        inputs = inputs,
        mode = mode,
        type = type,
        **model.Poi.extract_non_territorial_search_data(ctx, data))


@wsgihelpers.wsgify
@ramdb.ramdb_based
def feed(req):
    ctx = contexts.Ctx(req)

    params = req.GET
    inputs = init_base(ctx, params)
    inputs.update(model.Poi.extract_search_inputs_from_params(ctx, params))

    data, errors = conv.inputs_to_atom_feed_data(inputs, state = ctx)
    non_territorial_search_data = model.Poi.extract_non_territorial_search_data(ctx, data)
    if errors is not None:
        return wsgihelpers.bad_request(ctx, explanation = ctx._('Error: {0}').format(errors))
    else:
        base_territory = data.get('base_territory')
        territory = data['territory']
        competence_territories_id = None
        presence_territory = None
        if conf['handle_competence_territories']:
            if territory and territory.__class__.__name__ not in model.communes_kinds:
                presence_territory = territory
            if territory:
                competence_territories_id = ramdb.get_territory_related_territories_id(territory)
            if base_territory and competence_territories_id is None:
                competence_territories_id = ramdb.get_territory_related_territories_id(base_territory)
        else:
            if territory and territory.__class__.__name__ not in model.communes_kinds:
                presence_territory = territory
            elif base_territory:
                presence_territory = data['base_territory']

        pois_id_iter = model.Poi.iter_ids(
            ctx,
            competence_territories_id = competence_territories_id,
            presence_territory = presence_territory,
            **non_territorial_search_data)
        poi_by_id = dict(
            (poi._id, poi)
            for poi in (
                model.Poi.instance_by_id.get(poi_id)
                for poi_id in pois_id_iter
                )
            if poi is not None
            )
        pager = pagers.Pager(item_count = len(poi_by_id), page_number = 1)
        pager.items = model.Poi.sort_and_paginate_pois_list(
            ctx,
            pager,
            poi_by_id,
            related_territories_id = competence_territories_id,
            territory = territory or data.get('base_territory'),
            sort_key = 'last_update_datetime',
            **non_territorial_search_data
            )
        data['feed_id'] = urls.get_full_url(ctx, **inputs)
        data['feed_url'] = data['feed_id']
        data['feed_updated'] = pager.items[0].last_update_datetime if pager.items else datetime.datetime.utcnow()
        data['author_name'] = u"Easter-eggs"
        data['author_email'] = conf['email_to']

    req.response.content_type = 'application/atom+xml; charset=utf-8'
    return templates.render(
        ctx,
        '/feed-atom.mako',
        data = data,
        errors = errors,
        inputs = inputs,
        pager = pager,
        **non_territorial_search_data)


@wsgihelpers.wsgify
@ramdb.ramdb_based
def geographical_coverage_csv(req):
    ctx = contexts.Ctx(req)

    if conf['hide_export']:
        return wsgihelpers.not_found(ctx, explanation = ctx._(u'Export disabled by configuration'))

    params = req.GET
    inputs = init_base(ctx, params)
    inputs.update(model.Poi.extract_search_inputs_from_params(ctx, params))
    inputs['format'] = u'csv'

    csv_bytes_by_name, errors = conv.pipe(
        conv.inputs_to_geographical_coverage_csv_infos,
        conv.csv_infos_to_csv_bytes,
        )(inputs, state = ctx)
    if errors is not None:
        return wsgihelpers.bad_request(ctx, explanation = ctx._('Error: {0}').format(errors))
    if not csv_bytes_by_name:
        return wsgihelpers.no_content(ctx)
    if len(csv_bytes_by_name) == 1:
        csv_filename, csv_bytes = csv_bytes_by_name.items()[0]
        req.response.content_type = 'text/csv; charset=utf-8'
        req.response.content_disposition = 'attachment;filename={0}'.format(csv_filename)
        return csv_bytes
    zip_file = StringIO()
    with zipfile.ZipFile(zip_file, 'w') as zip_archive:
        for csv_filename, csv_bytes in csv_bytes_by_name.iteritems():
            zip_archive.writestr(csv_filename, csv_bytes)
    req.response.content_type = 'application/zip'
    req.response.content_disposition = 'attachment;filename=export.zip'
    return zip_file.getvalue()


@wsgihelpers.wsgify
@ramdb.ramdb_based
def geographical_coverage_excel(req):
    ctx = contexts.Ctx(req)

    if conf['hide_export']:
        return wsgihelpers.not_found(ctx, explanation = ctx._(u'Export disabled by configuration'))

    params = req.GET
    inputs = init_base(ctx, params)
    inputs.update(model.Poi.extract_search_inputs_from_params(ctx, params))
    inputs['format'] = u'excel'

    excel_bytes, errors = conv.pipe(
        conv.inputs_to_geographical_coverage_csv_infos,
        conv.csv_infos_to_excel_bytes,
        )(inputs, state = ctx)
    if errors is not None:
        return wsgihelpers.bad_request(ctx, explanation = ctx._('Error: {0}').format(errors))
    if not excel_bytes:
        raise wsgihelpers.no_content(ctx)
    req.response.content_type = 'application/vnd.ms-excel'
    req.response.content_disposition = 'attachment;filename=export.xls'
    return excel_bytes


@wsgihelpers.wsgify
@ramdb.ramdb_based
def geojson(req):
    ctx = contexts.Ctx(req)

    params = req.GET
    inputs = init_base(ctx, params)
    inputs.update(model.Poi.extract_search_inputs_from_params(ctx, params))
    inputs.update(dict(
        bbox = params.get('bbox'),
        context = params.get('context'),
        current = params.get('current'),
        enable_cluster = params.get('enable_cluster'),
        jsonp = params.get('jsonp'),
        ))

    data, errors = conv.pipe(
        conv.inputs_to_pois_layer_data,
        conv.default_pois_layer_data_bbox,
        )(inputs, state = ctx)
    if errors is not None:
        raise wsgihelpers.bad_request(ctx, explanation = ctx._('Error: {0}').format(errors))
    clusters, errors = conv.layer_data_to_clusters(data, state = ctx)
    if errors is not None:
        raise wsgihelpers.bad_request(ctx, explanation = ctx._('Error: {0}').format(errors))

    geojson = {
        'type': 'FeatureCollection',
        'properties': {
            'context': inputs['context'],  # Parameter given in request that is returned as is.
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
                    'iconUrl': cluster.icon_url,
                    'id': str(cluster.center_pois[0]._id),
                    'centerPois': [
                        {
                            'id': str(poi._id),
                            'name': poi.name,
                            'postalDistribution': poi.postal_distribution_str,
                            'slug': poi.slug,
                            'streetAddress': poi.street_address,
                            }
                        for poi in cluster.center_pois
                        ],
                    },
                }
            for cluster in clusters
            ],
        }
    territory = data['territory']
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
    if inputs['jsonp']:
        req.response.content_type = 'application/javascript; charset=utf-8'
        return u'{0}({1})'.format(inputs['jsonp'], response)
    else:
        req.response.content_type = 'application/json; charset=utf-8'
        return response


@wsgihelpers.wsgify
@ramdb.ramdb_based
def index(req):
    ctx = contexts.Ctx(req)

    params = req.params
    init_base(ctx, params)

    # Redirect to another page.
    enabled_tabs = [
        tab_name
        for tab_key, tab_name in (
            (u'map', u'carte'),
            (u'list', u'liste'),
            (u'directory', u'annuaire'),
            (u'gadget', u'partage'),
            (u'export', u'export'),
            )
        if not getattr(ctx, "hide_{0}".format(tab_key))
        ]
    if not len(enabled_tabs):
        enabled_tabs = [u'carte']  # Ensure there is at least one visible tab
    url_args = (conf['default_tab'] if conf['default_tab'] in enabled_tabs else enabled_tabs[0],)
    url_kwargs = dict(params)
    if ctx.container_base_url is None or ctx.gadget_id is None:
        raise wsgihelpers.redirect(ctx, location = urls.get_url(ctx, *url_args, **url_kwargs))
    else:
        return templates.render(
            ctx,
            '/http-simulated-redirect.mako',
            url_args = url_args,
            url_kwargs = url_kwargs,
            )


@wsgihelpers.wsgify
@ramdb.ramdb_based
def index_directory(req):
    ctx = contexts.Ctx(req)

    if conf['hide_directory']:
        return wsgihelpers.not_found(ctx, explanation = ctx._(u'Directory page disabled by configuration'))

    params = req.GET
    inputs = init_base(ctx, params)
    inputs.update(model.Poi.extract_search_inputs_from_params(ctx, params))
    mode = u'annuaire'

    data, errors = conv.inputs_to_pois_directory_data(inputs, state = ctx)
    if errors is not None:
        directory = None
        territory = None
        if errors.get('territory') and errors['territory'] == ctx._(u'In "directory" mode, a commune is required'):
            del errors['territory']
    else:
        territory = data['territory']
        related_territories_id = ramdb.get_territory_related_territories_id(territory)
        if conf['handle_competence_territories']:
            competence_territories_id = ramdb.get_territory_related_territories_id(territory)
            presence_territory = territory if territory.__class__.__name__ not in model.communes_kinds else None
        else:
            # Note: This section should never be called. In directory mode, the incompetent organisms must not be shown.
            presence_territory = data['base_territory'] if data.get('base_territory') is not None else None
            competence_territories_id = related_territories_id

        pois_id_iter = model.Poi.iter_ids(
            ctx,
            competence_territories_id = competence_territories_id,
            presence_territory = presence_territory,
            **model.Poi.extract_non_territorial_search_data(ctx, data))
        pois = set(
            poi
            for poi in (
                model.Poi.instance_by_id.get(poi_id)
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
                        round(
                            math.sin(math.radians(poi.geo[0])) * territory_latitude_sin
                            + math.cos(math.radians(poi.geo[0])) * territory_latitude_cos
                            * math.cos(math.radians(poi.geo[1] - territory.geo[1])),
                            13,
                            )
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
            if poi.theme_slug is None:
                continue
            theme_pois = directory.get(poi.theme_slug)
            if theme_pois is not None and len(theme_pois) >= 3 and territory.__class__.__name__ in model.communes_kinds:
                continue
            if territory.__class__.__name__ in model.communes_kinds:
                if poi.competence_territories_id is None:
                    # When a POI has no notion of competence territory, only show it when it is not too far away from
                    # center territory.
                    if distance > ctx.distance:
                        continue
                elif related_territories_id.isdisjoint(poi.competence_territories_id):
                    # In directory mode, the incompetent organisms must not be shown.
                    continue
            if theme_pois is None:
                directory[poi.theme_slug] = [poi]
            else:
                theme_pois.append(poi)
    return templates.render(
        ctx,
        '/directory.mako',
        directory = directory,
        errors = errors,
        inputs = inputs,
        mode = mode,
        territory = territory,
        **model.Poi.extract_non_territorial_search_data(ctx, data))


@wsgihelpers.wsgify
@ramdb.ramdb_based
def index_export(req):
    ctx = contexts.Ctx(req)

    if conf['hide_export']:
        return wsgihelpers.not_found(ctx, explanation = ctx._(u'Export disabled by configuration'))

    params = req.GET
    inputs = init_base(ctx, params)
    inputs.update(model.Poi.extract_search_inputs_from_params(ctx, params))
    inputs.update(dict(
        submit = params.get('submit'),
        type_and_format = params.get('type_and_format'),
        ))
    mode = u'export'

    data, errors = conv.merge(
        model.Poi.make_inputs_to_search_data(),
        conv.struct(
            dict(
                type_and_format = conv.pipe(
                    conv.input_to_slug,
                    conv.test_in([
                        'annuaire-csv',
                        'annuaire-excel',
                        'annuaire-geojson',
                        'annuaire-kml',
                        'couverture-csv',
                        'couverture-excel',
                        ]),
                    ),
                ),
            default = 'drop',
            drop_none_values = False,
            ),
        )(inputs, state = ctx)
    if errors is None:
        if inputs['submit']:
            if data['type_and_format'] is not None:
                type, format = data['type_and_format'].rsplit(u'-', 1)

                # Form submitted. Redirect to another page.
                url_args = ('export', type, format)
                search_params_name = model.Poi.get_search_params_name(ctx)
                url_kwargs = dict(
                    (param_name, value)
                    for param_name, value in (
                        (model.Poi.rename_input_to_param(input_name), value)
                        for input_name, value in inputs.iteritems()
                        )
                    if param_name in search_params_name
                    )
                if ctx.container_base_url is None or ctx.gadget_id is None:
                    raise wsgihelpers.redirect(ctx, location = urls.get_url(ctx, *url_args, **url_kwargs))
                else:
                    return templates.render(
                        ctx,
                        '/http-simulated-redirect.mako',
                        url_args = url_args,
                        url_kwargs = url_kwargs,
                        )
            errors = dict(
                type_and_format = ctx._(u'Missing value'),
                )
    return templates.render(
        ctx,
        '/export.mako',
        errors = errors,
        inputs = inputs,
        mode = mode,
        **model.Poi.extract_non_territorial_search_data(ctx, data))


@wsgihelpers.wsgify
@ramdb.ramdb_based
def index_gadget(req):
    ctx = contexts.Ctx(req)

    if conf['hide_gadget']:
        return wsgihelpers.not_found(ctx, explanation = ctx._(u'Gadget page disabled by configuration'))

    params = req.GET
    inputs = init_base(ctx, params)
    inputs.update(model.Poi.extract_search_inputs_from_params(ctx, params))
    mode = u'gadget'

    data, errors = conv.inputs_to_pois_list_data(inputs, state = ctx)

    return templates.render(
        ctx,
        '/gadget.mako',
        errors = errors,
        inputs = inputs,
        mode = mode,
        **data)


@wsgihelpers.wsgify
@ramdb.ramdb_based
def index_list(req):
    ctx = contexts.Ctx(req)

    params = req.GET
    inputs = init_base(ctx, params)
    inputs.update(model.Poi.extract_search_inputs_from_params(ctx, params))
    inputs.update(dict(
        page = params.get('page'),
        poi_index = params.get('poi_index'),
        sort_key = params.get('sort_key'),
        ))
    mode = u'liste'

    data, errors = conv.inputs_to_pois_list_data(inputs, state = ctx)
    non_territorial_search_data = model.Poi.extract_non_territorial_search_data(ctx, data)
    if errors is not None:
        pager = None
    else:
        pager = data_to_render_list_data(ctx, data, inputs)

    return templates.render(
        ctx,
        '/list.mako',
        errors = errors,
        inputs = inputs,
        mode = mode,
        pager = pager,
        **non_territorial_search_data)


@wsgihelpers.wsgify
@ramdb.ramdb_based
def index_list_api(req):
    ctx = contexts.Ctx(req)

    params = req.GET
    inputs = init_base(ctx, params)
    inputs.update(model.Poi.extract_search_inputs_from_params(ctx, params))
    inputs.update(dict(
        jsonp = params.get('jsonp'),
        page = params.get('page'),
        page_max_size = params.get('page_max_size'),
        ))

    data, errors = conv.inputs_to_pois_list_data(inputs, state = ctx)
    if errors is not None:
        pager = None
    else:
        pager = data_to_render_list_data(ctx, data, inputs, page_max_size = data['page_max_size'])

    return wsgihelpers.respond_json(
        ctx,
        dict(
            apiVersion = '1.0',
            data = dict(
                currentItemCount = len(pager.items),
                items = conv.uniform_sequence(conv.poi_to_bson)(pager.items, state = ctx)[0],
                itemsPerPage = pager.page_size,
                pageIndex = pager.page_number,
                startIndex = pager.first_item_index,
                totalItems = pager.item_count,
                totalPages = pager.page_count,
                ) if pager is not None else None,
            errors = errors,
            method = req.script_name,
            params = inputs,
            url = req.url.decode('utf-8'),
            ),
        jsonp = inputs['jsonp'],
        )


@wsgihelpers.wsgify
@ramdb.ramdb_based
def index_map(req):
    ctx = contexts.Ctx(req)

    if conf['hide_map']:
        return wsgihelpers.not_found(ctx, explanation = ctx._(u'Map page disabled by configuration'))

    params = req.GET
    inputs = init_base(ctx, params)
    inputs.update(model.Poi.extract_search_inputs_from_params(ctx, params))
    inputs.update(dict(
        bbox = params.get('bbox'),
        ))
    mode = u'carte'

    data, errors = conv.pipe(
        conv.inputs_to_pois_layer_data,
        conv.default_pois_layer_data_bbox,
        )(inputs, state = ctx)

    if errors is None:
        bbox = data['bbox']
        territory = data['territory']
    else:
        bbox = None
        territory = None
    return templates.render(
        ctx,
        '/map.mako',
        bbox = bbox,
        errors = errors,
        inputs = inputs,
        mode = mode,
        territory = territory,
        **model.Poi.extract_non_territorial_search_data(ctx, data))


def init_base(ctx, params):
    inputs = dict(
        base_category = params.getall('base_category'),
        base_territory = params.get('base_territory'),
        category_tag = params.getall('category_tag'),
        container_base_url = params.get('container_base_url'),
        custom_css_url = params.get('custom_css'),
        distance = params.get('distance'),
        gadget = params.get('gadget'),
        territory_kind = params.getall('territory_kind'),
        )

    ctx.container_base_url = container_base_url = inputs['container_base_url'] or None
    gadget_id, error = conv.input_to_int(inputs['gadget'])
    ctx.gadget_id = gadget_id
    container_hostname = (urlparse.urlsplit(container_base_url).hostname or None) if container_base_url else None
    if error is not None or gadget_id is None:
        gadget_id = None
        if container_base_url is not None:
            # Ignore container site when no gadget ID is given.
            container_base_url = None
    elif conf['subscribers.require_subscription'] and container_base_url is not None:
        subscriber = model.Subscriber.find_one({'sites.domain_name': container_hostname})
        if subscriber is None and (
                container_hostname is None or not container_hostname.endswith(conf['subscribers.gadget_valid_domains'])
                ):
            raise wsgihelpers.bad_request(
                ctx,
                explanation = ctx._('The gadget ID "{0}" doesn\'t exist.').format(gadget_id),
                message = ctx._('Rebuild component and copy the generated JavaScript into your website.'),
                title = ctx._('Invalid Gadget ID'),
                )
        elif subscriber is not None:
            for site in (subscriber.sites or []):
                for subscription in (site.subscriptions or []):
                    if subscription.type == 'etalage' and subscription.id == gadget_id:
                        # Note: We can get some specific options for this subscriber with subscription.options here
                        break
                else:
                    continue
                break
            else:
                raise wsgihelpers.bad_request(
                    ctx,
                    comment = ctx._('Rebuild component and copy the generated JavaScript into your website.'),
                    explanation = ctx._('The gadget ID "{0}" is used by another component.'),
                    title = ctx._('Invalid Gadget ID'),
                    )
            if gadget_id is not None and container_base_url is None and subscription.url is not None:
                # When in gadget mode but without a container_base_url, we are accessed through the noscript iframe or
                # by a search engine. We need to retrieve the URL of page containing gadget to do a JavaScript
                # redirection (in publication.mako).
                container_base_url = subscription.url or None

    for param_visibility_name in model.Poi.get_visibility_params_names(ctx):
        inputs[param_visibility_name] = conf.get(param_visibility_name) or params.get(param_visibility_name)
        param_visibility, error = conv.pipe(
            conv.guess_bool,
            conv.default(False),
            )(inputs[param_visibility_name], state = ctx)
        if error is not None:
            raise wsgihelpers.bad_request(ctx, explanation = ctx._('Error for "{0}" parameter: {1}').format(
                param_visibility_name, error))
        setattr(ctx, param_visibility_name, param_visibility)

    ctx.base_categories_slug, error = conv.uniform_sequence(
        conv.input_to_tag_slug,
        )(inputs['base_category'], state = ctx)
    if error is not None:
        raise wsgihelpers.bad_request(ctx, explanation = ctx._('Base Categories Error: {0}').format(error))

    ctx.category_tags_slug, error = conv.uniform_sequence(
        conv.input_to_tag_slug,
        )(inputs['category_tag'], state = ctx)
    if error is not None:
        raise wsgihelpers.bad_request(ctx, explanation = ctx._('Category Tags Error: {0}').format(error))

    ctx.base_territory, error = conv.input_to_postal_distribution_to_geolocated_territory(
        inputs['base_territory'],
        state = ctx,
        )
    if error is not None:
        raise wsgihelpers.bad_request(ctx, explanation = ctx._('Base Territory Error: {0}').format(error))
    if ctx.subscriber is not None:
        subscriber_territory = ctx.subscriber.territory
        if subscriber_territory._id not in ctx.base_territory.ancestors_id:
            return wsgihelpers.not_found(ctx, explanation = ctx._(u'Unknown territory'))
    if ctx.base_territory is None and ctx.subscriber is not None and ctx.subscriber.territory is not None:
        ctx.base_territory = model.Territory.get_variant_class(
            ctx.subscriber.territory['kind']).get(ctx.subscriber.territory['code'])
        if ctx.base_territory is None:
            return wsgihelpers.not_found(ctx, explanation = ctx._(u'Unknown territory'))

    ctx.custom_css_url, error = conv.pipe(
        conv.cleanup_line,
        conv.empty_to_none,
        conv.make_input_to_url(),
        )(inputs['custom_css_url'], state = ctx)
    if error is not None:
        ctx.custom_css_url = None

    ctx.distance, error = conv.pipe(
        conv.input_to_float,
        conv.test_between(0.0, 40075.16),
        conv.default(20.0),
        )(inputs['distance'], state = ctx)
    if error is not None:
        raise wsgihelpers.bad_request(ctx, explanation = ctx._('Distance Error: {0}').format(error))

    ctx.autocompleter_territories_kinds = [
        territory_kind
        for territory_kind in inputs['territory_kind']
        if territory_kind in conf['autocompleter_territories_kinds']
        ] or conf['autocompleter_territories_kinds']

    return inputs


@wsgihelpers.wsgify
@ramdb.ramdb_based
def kml(req):
    ctx = contexts.Ctx(req)

    params = req.GET
    inputs = init_base(ctx, params)
    inputs.update(model.Poi.extract_search_inputs_from_params(ctx, params))
    inputs.update(dict(
        bbox = params.get('bbox'),
        context = params.get('context'),
        current = params.get('current'),
        ))

    clusters, errors = conv.pipe(
        conv.inputs_to_pois_layer_data,
        conv.default_pois_layer_data_bbox,
        conv.layer_data_to_clusters,
        )(inputs, state = ctx)
    if errors is not None:
        raise wsgihelpers.bad_request(ctx, explanation = ctx._('Error: {0}').format(errors))

    req.response.content_type = 'application/vnd.google-earth.kml+xml; charset=utf-8'
    return templates.render(
        ctx,
        '/kml.mako',
        clusters = clusters,
        inputs = inputs,
        )


def make_router():
    """Return a WSGI application that dispatches requests to controllers """
    return urls.make_router(
        ('GET', '^/?$', index),
        ('GET', '^/a-propos/?$', about),
        ('GET', '^/annuaire/?$', index_directory),
        ('GET', '^/api/v1/annuaire/csv/?$', csv),
        ('GET', '^/api/v1/annuaire/excel/?$', excel),
        ('GET', '^/api/v1/annuaire/geojson/?$', geojson),
        ('GET', '^/api/v1/annuaire/kml/?$', kml),
        ('GET', '^/api/v1/categories/autocomplete/?$', autocomplete_category),
        ('GET', '^/api/v1/couverture/csv/?$', geographical_coverage_csv),
        ('GET', '^/api/v1/couverture/excel/?$', geographical_coverage_excel),
        ('GET', '^/api/v1/liste/?$', index_list_api),
        ('GET', '^/api/v1/organismes/?$', poi_api),
        ('GET', '^/api/v1/organismes/(?P<poi_id>[a-z0-9]{24})/?$', poi_api),
        ('GET', '^/api/v1/organismes/(?P<slug>[^/]+)/(?P<poi_id>[a-z0-9]{24})/?$', poi_api),
        ('GET', '^/carte/?$', index_map),
        ('GET', '^/export/?$', index_export),
        ('GET', '^/export/annuaire/csv/?$', export_directory_csv),
        ('GET', '^/export/annuaire/excel/?$', export_directory_excel),
        ('GET', '^/export/annuaire/geojson/?$', export_directory_geojson),
        ('GET', '^/export/annuaire/kml/?$', export_directory_kml),
        ('GET', '^/export/couverture/csv/?$', export_geographical_coverage_csv),
        ('GET', '^/export/couverture/excel/?$', export_geographical_coverage_excel),
        ('GET', '^/feed/?$', feed),
        ('GET', '^/fragment/organismes/(?P<poi_id>[a-z0-9]{24})/?$', poi_embedded),
        ('GET', '^/fragment/organismes/(?P<slug>[^/]+)/(?P<poi_id>[a-z0-9]{24})/?$', poi_embedded),
        ('GET', '^/gadget/?$', index_gadget),
        ('GET', '^/liste/?$', index_list),
        ('GET', '^/minisite/organismes/(?P<poi_id>[a-z0-9]{24})/?$', minisite),
        ('GET', '^/minisite/organismes/(?P<slug>[^/]+)/(?P<poi_id>[a-z0-9]{24})/?$', minisite),
        ('GET', '^/organismes/?$', poi),
        ('GET', '^/organismes/(?P<poi_id>[a-z0-9]{24})/?$', poi),
        ('GET', '^/organismes/(?P<slug>[^/]+)/(?P<poi_id>[a-z0-9]{24})/?$', poi),
        )


@wsgihelpers.wsgify
@ramdb.ramdb_based
def minisite(req):
    ctx = contexts.Ctx(req)

    if conf['hide_minisite']:
        return wsgihelpers.not_found(ctx, explanation = ctx._(u'Minisite disabled by configuration'))

    params = req.params
    inputs = init_base(ctx, params)
    inputs.update(dict(
        encoding = params.get('encoding') or u'',
        poi_id = req.urlvars.get('poi_id'),
        slug = req.urlvars.get('slug'),
        ))

    data, errors = conv.pipe(
        conv.struct(
            dict(
                poi_id = conv.pipe(
                    conv.input_to_object_id,
                    conv.id_to_poi,
                    conv.not_none,
                    ),
                encoding = conv.pipe(
                    conv.input_to_slug,
                    conv.translate({u'utf-8': None}),
                    conv.test_in([u'cp1252', u'iso-8859-1', u'iso-8859-15']),
                    ),
                ),
            default = 'drop',
            drop_none_values = False,
            ),
        conv.rename_item('poi_id', 'poi'),
        )(inputs, state = ctx)

    if errors is not None and errors.get('poi_id'):
        return wsgihelpers.bad_request(ctx, explanation = ctx._('Error: {0}').format(errors['poi_id']))

    data['url'] = url = urls.get_full_url(
        ctx,
        'fragment',
        'organismes',
        data['poi'].slug,
        data['poi']._id,
        encoding = data['encoding'],
        )
    try:
        fragment = urllib2.urlopen(url).read().decode(data['encoding'] or 'utf-8')
    except:
        errors = dict(fragment = ctx._('Access to organism failed'))
    else:
        data['fragment'] = fragment
    return templates.render(ctx, '/minisite.mako', errors = errors, inputs = inputs, **data)


def data_to_render_poi(ctx, data, inputs):
    non_territorial_search_data = model.Poi.extract_non_territorial_search_data(ctx, data)
    base_territory = data.get('base_territory')
    territory = data['territory']
    competence_territories_id = None
    presence_territory = None
    if conf['handle_competence_territories']:
        if territory and territory.__class__.__name__ not in model.communes_kinds:
            presence_territory = territory
        if territory:
            competence_territories_id = ramdb.get_territory_related_territories_id(territory)
        if base_territory and competence_territories_id is None:
            competence_territories_id = ramdb.get_territory_related_territories_id(base_territory)
    else:
        if territory and territory.__class__.__name__ not in model.communes_kinds:
            presence_territory = territory
        elif base_territory:
            presence_territory = data['base_territory']

    pois_id_iter = model.Poi.iter_ids(
        ctx,
        competence_territories_id = competence_territories_id,
        presence_territory = presence_territory,
        **non_territorial_search_data
        )

    poi_by_id = dict(
        (poi._id, poi)
        for poi in (
            model.Poi.instance_by_id.get(poi_id)
            for poi_id in pois_id_iter
            )
        if poi is not None
        )

    pager = pagers.Pager(
        item_count = len(poi_by_id),
        page_number = data['page_number'] if data['poi_index'] is None else (
            data['poi_index'] / conf['pager.page_max_size']
            ) + 1,
        page_max_size = conf['pager.page_max_size'],
        )
    pager.items = model.Poi.sort_and_paginate_pois_list(
        ctx,
        pager,
        poi_by_id,
        related_territories_id = competence_territories_id,
        territory = territory or data.get('base_territory'),
        sort_key = data['sort_key'],
        **non_territorial_search_data
        )
    return pager.items[min((data['poi_index'] - 1) % conf['pager.page_max_size'], len(pager.items) - 1)]


@wsgihelpers.wsgify
@ramdb.ramdb_based
def poi(req):
    ctx = contexts.Ctx(req)

    params = req.params
    inputs = init_base(ctx, params)
    inputs.update(model.Poi.extract_search_inputs_from_params(ctx, params))
    inputs.update(dict(
        bbox = params.get('bbox'),
        page = params.get('page'),
        poi_id = req.urlvars.get('poi_id'),
        poi_index = params.get('poi_index'),
        slug = req.urlvars.get('slug'),
        ))

    data, errors = conv.pipe(
        conv.merge(
            conv.inputs_to_pois_list_data,
            conv.struct(
                dict(
                    poi_id = conv.pipe(
                        conv.input_to_object_id,
                        conv.id_to_poi,
                        ),
                    ),
                default = 'drop',
                drop_none_values = False,
                ),
            ),
        conv.rename_item('poi_id', 'poi'),
        )(inputs, state = ctx)
    if errors is not None:
        return wsgihelpers.bad_request(ctx, explanation = ctx._('Error: {0}').format(errors))
    if data['poi'] is None and data['poi_index'] is None:
        return wsgihelpers.bad_request(ctx, explanation = ctx._('Invalid POI ID'))

    if data['poi'] is None:
        data['poi'] = data_to_render_poi(ctx, data, inputs)
    else:
        slug = data['poi'].slug
        if inputs['slug'] != slug:
            if ctx.container_base_url is None or ctx.gadget_id is None:
                raise wsgihelpers.redirect(ctx, location = urls.get_url(ctx, 'organismes', slug, data['poi']._id))
            # In gadget mode, there is no need to redirect.

    return templates.render(
        ctx,
        '/poi.mako',
        data = data,
        inputs = inputs,
        poi = data['poi'],
        )


@wsgihelpers.wsgify
@ramdb.ramdb_based
def poi_api(req):
    ctx = contexts.Ctx(req)

    params = req.params
    inputs = init_base(ctx, params)
    inputs.update(model.Poi.extract_search_inputs_from_params(ctx, params))
    inputs.update(dict(
        bbox = params.get('bbox'),
        jsonp = params.get('jsonp'),
        page = params.get('page'),
        poi_id = req.urlvars.get('poi_id'),
        poi_index = params.get('poi_index'),
        slug = req.urlvars.get('slug'),
        ))

    data, errors = conv.pipe(
        conv.merge(
            conv.inputs_to_pois_list_data,
            conv.struct(
                dict(
                    poi_id = conv.pipe(
                        conv.input_to_object_id,
                        conv.id_to_poi,
                        ),
                    ),
                default = 'drop',
                drop_none_values = False,
                ),
            ),
        conv.rename_item('poi_id', 'poi'),
        )(inputs, state = ctx)
    if errors is not None:
        return wsgihelpers.bad_request(ctx, explanation = ctx._('Error: {0}').format(errors))
    if data['poi'] is None and data['poi_index'] is None:
        return wsgihelpers.bad_request(ctx, explanation = ctx._('Invalid POI ID'))

    if data['poi'] is None:
        data['poi'] = data_to_render_poi(ctx, data, inputs)
    else:
        slug = data['poi'].slug
        if inputs['slug'] != slug:
            if ctx.container_base_url is None or ctx.gadget_id is None:
                raise wsgihelpers.redirect(
                    ctx,
                    location = urls.get_url(ctx, 'api/v1/organismes', slug, data['poi']._id),
                    )
            # In gadget mode, there is no need to redirect.

    data['fields'], errors = conv.uniform_sequence(conv.field_to_bson)(data['poi'].generate_all_fields(), state = ctx)
    data['poi'], errors = conv.poi_to_bson(data['poi'], state = ctx)
    return wsgihelpers.respond_json(
        ctx,
        dict(
            apiVersion = '1.0',
            data = data,
            method = req.script_name,
            params = inputs,
            url = req.url.decode('utf-8'),
            ),
        jsonp = inputs['jsonp'],
        )


@wsgihelpers.wsgify
@ramdb.ramdb_based
def poi_embedded(req):
    ctx = contexts.Ctx(req)

    if conf['hide_minisite']:
        return wsgihelpers.not_found(ctx, explanation = ctx._(u'Minisite disabled by configuration'))

    params = req.params
    inputs = init_base(ctx, params)
    inputs.update(model.Poi.extract_search_inputs_from_params(ctx, params))
    inputs.update(dict(
        encoding = params.get('encoding') or u'',
        poi_id = req.urlvars.get('poi_id'),
        slug = req.urlvars.get('slug'),
        ))

    poi, error = conv.pipe(
        conv.input_to_object_id,
        conv.id_to_poi,
        conv.not_none,
        )(inputs['poi_id'], state = ctx)
    if error is not None:
        raise wsgihelpers.bad_request(ctx, explanation = ctx._('POI ID Error: {0}').format(error))

    encoding, error = conv.pipe(
        conv.input_to_slug,
        conv.translate({u'utf-8': None}),
        conv.test_in([u'cp1252', u'iso-8859-1', u'iso-8859-15']),
        )(inputs['encoding'], state = ctx)
    if error is not None:
        raise wsgihelpers.bad_request(ctx, explanation = ctx._('Encoding Error: {0}').format(error))

    text = templates.render(ctx, '/poi-embedded.mako', inputs = inputs, poi = poi)
    if encoding is None:
        req.response.content_type = 'text/plain; charset=utf-8'
        return text
    else:
        req.response.content_type = 'text/plain; charset={0}'.format(encoding)
        return text.encode(encoding, errors = 'xmlcharrefreplace')
