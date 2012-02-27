## -*- coding: utf-8 -*-


## Etalage -- Open Data POIs portal
## By: Emmanuel Raviart <eraviart@easter-eggs.com>
##
## Copyright (C) 2011, 2012 Easter-eggs
## http://gitorious.org/infos-pratiques/etalage
##
## This file is part of Etalage.
##
## Etalage is free software; you can redistribute it and/or modify
## it under the terms of the GNU Affero General Public License as
## published by the Free Software Foundation, either version 3 of the
## License, or (at your option) any later version.
##
## Etalage is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Affero General Public License for more details.
##
## You should have received a copy of the GNU Affero General Public License
## along with this program.  If not, see <http://www.gnu.org/licenses/>.


<%!
import urlparse

import markupsafe
from biryani import strings

from etalage import conf, model, ramdb, urls
%>\


<%inherit file="/site.mako"/>


<%def name="container_content()" filter="trim">
        <h2>${poi.name}</h2>
        <%self:fields poi="${poi}"/>
</%def>


<%def name="css()" filter="trim">
    <%parent:css/>
    <link rel="stylesheet" href="${conf['leaflet.css']}">
<!--[if lte IE 8]>
    <link rel="stylesheet" href="${conf['leaflet.ie.css']}">
<![endif]-->
    <link rel="stylesheet" href="/css/map.css">
</%def>


<%def name="field(field, depth = 0)" filter="trim">
<%
    if field.value is None:
        return ''
%>\
    ${getattr(self, 'field_{0}'.format(field.id.replace('-', '_')), field_default)(field, depth = depth)}
</%def>


<%def name="field_children(poi, depth = 0)" filter="trim">
<%
    children = sorted(
        (
            child
            for child in ramdb.pois_by_id.itervalues()
            if child.parent_id == poi._id
            ),
        key = lambda child: child.name,
        )
%>\
    % if children:
        % for child in children:
<%
            field = model.Field(id = 'link', label = ramdb.schemas_title_by_name[child.schema_name], value = child._id)
%>\
        <%self:field depth="${depth}" field="${field}"/>
        % endfor
    %endif
</%def>


<%def name="field_default(field, depth = 0)" filter="trim">
        <div class="field">
            <b class="field-label">${field.label} :</b>
            <%self:field_value depth="${depth}" field="${field}"/>
        </div>
</%def>


<%def name="field_last_update(poi, depth = 0)" filter="trim">
<%
    field = model.Field(id = 'text-inline', label = u"Dernière mise à jour", value = u' par '.join(
        unicode(fragment)
        for fragment in (
            poi.last_update_datetime.strftime('%Y-%m-%d %H:%M') if poi.last_update_datetime is not None else None,
            poi.last_update_organization,
            )
        if fragment
        ))
%>\
        <%self:field depth="${depth}" field="${field}"/>
</%def>


<%def name="field_value(field, depth = 0)" filter="trim">
<%
    if field.value is None:
        return ''
%>\
    ${getattr(self, 'field_value_{0}'.format(field.id.replace('-', '_')), field_value_default)(field, depth = depth)}
</%def>


<%def name="field_value_adr(field, depth = 0)" filter="trim">
            <address class="field-value">
    % for subfield in field.value:
<%
        if subfield.value is None:
            continue
%>\
        % if subfield.id == 'street-address':
            % for line in subfield.value.split('\n'):
                ${line}<br>
            % endfor
        % elif subfield.id == 'commune':
<%
            continue
%>\
        % elif subfield.id == 'postal-distribution':
                ${subfield.value}
        % endif
    % endfor
            </address>
</%def>


<%def name="field_value_autocompleter(field, depth = 0)" filter="trim">
<%
    slug_and_name_couples = []
    name = field.value
    slug = strings.slugify(name)
    category = ramdb.categories_by_slug.get(slug)
    if category is not None:
        name = category.name
%>\
            <span class="field-value">${name}</span>
</%def>


<%def name="field_value_autocompleters(field, depth = 0)" filter="trim">
<%
    slug_and_name_couples = []
    for name in field.value:
        slug = strings.slugify(name)
        category = ramdb.categories_by_slug.get(slug)
        if category is not None:
            name = category.name
        slug_and_name_couples.append((slug, name))
    slug_and_name_couples.sort()
    names = [
        name
        for slug, name in slug_and_name_couples
        ]
%>\
            <span class="field-value">${u', '.join(names)}</span>
</%def>


<%def name="field_value_boolean(field, depth = 0)" filter="trim">
            <span class="field-value">${u'Oui' if field.value and field.value != '0' else u'Non'}</span>
</%def>


<%def name="field_value_checkboxes(field, depth = 0)" filter="trim">
            <%self:field_value_autocompleters depth="${depth}" field="${field}"/>
</%def>


<%def name="field_value_date_range(field, depth = 0)" filter="trim">
<%
    begin_field = field.get_first_field('date-range-begin')
    begin = begin_field.value if field is not None else None
    end_field = field.get_first_field('date-range-end')
    end = end_field.value if field is not None else None
%>\
    % if begin is None:
            <span class="field-value">Jusqu'au ${end.strftime('%d/%m/%Y')}</span>
    % elif end is None:
            <span class="field-value">À partir du ${begin.strftime('%d/%m/%Y')}</span>
    % elif begin == end:
            <span class="field-value">Le ${begin.strftime('%d/%m/%Y')}</span>
    % else:
            <span class="field-value">Du ${begin.strftime('%d/%m/%Y')} au ${end.strftime('%d/%m/%Y')}</span>
    % endif
</%def>


<%def name="field_value_default(field, depth = 0)" filter="trim">
            <span class="field-value">${field.value}</span>
</%def>


<%def name="field_value_email(field, depth = 0)" filter="trim">
            <span class="field-value"><a href="mailto:${field.value}">${field.value}</a></span>
</%def>


<%def name="field_value_feed(field, depth = 0)" filter="trim">
<%
    import feedparser
    d = feedparser.parse(field.value)
%>\
            <div class="field-value offset1">
    % if d is None or 'status' not in d \
            or not d.version and d.status != 304 and d.status != 401 \
            or d.status >= 400:
                <em class="error">Erreur dans le flux d'actualité <a href="${field.value}" rel="external">${field.value}</a></em>
    % else:
                <strong>${d.feed.title}</strong>
                <a href="${field.value}" rel="external"><img alt="" src="http://cdn.comarquage.fr/images/misc/feed.png"></a>
                <ul>
        % for entry in d.entries[:10]:
                    <li class="feed-entry">${entry.title | n}
            % for content in (entry.get('content') or []):
                        <div>${content.value | n}</div>
            % endfor
                    </li>
        % endfor
        % if len(d.entries) > 10:
                    <li>...</li>
        % endif
                </ul>
    % endif
            </div>
</%def>


<%def name="field_value_geo(field, depth = 0)" filter="trim">
            <div class="field-value">
    % if field.value[2] <= 6:
                <div class="alert alert-error">
                    Cet organisme est positionné <strong>très approximativement</strong>.
                </div>
    % elif field.value[2] <= 6:
                <div class="alert alert-warning">
                    Cet organisme est positionné <strong>approximativement dans la rue</strong>.
                </div>
    % endif
                <div class="single-marker-map" id="map-poi" style="height: 500px;"></div>
                <script>
etalage.map.singleMarkerMap("map-poi", ${field.value[0]}, ${field.value[1]});
                </script>
                <div class="bigger-map-link">
                    Voir sur une carte plus grande avec
                    <a href="${u'http://www.openstreetmap.org/?mlat={0}&mlon={1}&zoom=15&layers=M'.format(
                            field.value[0], field.value[1])}" rel="external">OpenStreetMap</a>
                    ou
                    <a href="${u'http://maps.google.com/maps?q={0},{1}'.format(field.value[0], field.value[1]
                            )}" rel="external">Google Maps</a>
                </div>
            </div>
</%def>


<%def name="field_value_image(field, depth = 0)" filter="trim">
            <div class="field-value"><img alt="" src="${field.value}"></div>
</%def>


<%def name="field_value_link(field, depth = 0)" filter="trim">
<%
    target = ramdb.pois_by_id.get(field.value)
%>\
    % if target is None:
            <em class="field-value">Lien manquant</em>
    % else:
            <a class="field-value internal" href="${urls.get_url(ctx, 'organismes', target.slug, target._id
                    )}">${target.name}</a>
    % endif
</%def>


<%def name="field_value_links(field, depth = 0)" filter="trim">
    % if len(field.value) == 1:
<%
        single_field = model.Field(id = 'link', value = field.value[0])
%>\
<%self:field_value depth="${depth}" field="${single_field}"/>
    % else:
            <ul class="field-value">
        % for target_id in field.value:
<%
            target = ramdb.pois_by_id.get(target_id)
            if target is None:
                continue
%>\
                <li><a class="internal" href="${urls.get_url(ctx, 'organismes', target.slug, target._id
                        )}">${target.name}</a></li>
        % endfor
            </ul>
    % endif
</%def>


<%def name="field_value_organism_type(field, depth = 0)" filter="trim">
<%
    category_slug = ramdb.categories_slug_by_pivot_code.get(field.value)
    category = ramdb.categories_by_slug.get(category_slug) if category_slug is not None else None
    category_name = category.name if category is not None else field.value
%>\
            <span class="field-value">${category_name}</span>
</%def>


<%def name="field_value_select(field, depth = 0)" filter="trim">
            <%self:field_value_autocompleter depth="${depth}" field="${field}"/>
</%def>


<%def name="field_value_source(field, depth = 0)" filter="trim">
            <div class="field-value offset1">
    % for subfield in field.value:
        <%self:field depth="${depth + 1}" field="${subfield}"/>
    % endfor
            </div>
</%def>


<%def name="field_value_source_url(field, depth = 0)" filter="trim">
            <%self:field_value_url depth="${depth}" field="${field}"/>
</%def>


<%def name="field_value_tags(field, depth = 0)" filter="trim">
<%
    tags_name = [
        tag.name
        for tag in (
            ramdb.categories_by_slug.get(tag_slug)
            for tag_slug in sorted(field.value)
            )
        if tag is not None
        ]
%>\
            <span class="field-value">${u', '.join(tags_name)}</span>
</%def>


<%def name="field_value_territories(field, depth = 0)" filter="trim">
<%
    territories_title_markup = [
        territory.main_postal_distribution_str
            if territory.__class__.__name__ in model.communes_kinds
            else markupsafe.Markup(u'{0} <em>({1})</em>').format(
                territory.main_postal_distribution_str, territory.type_short_name_fr)
        for territory in (
            ramdb.territories_by_id[territory_id]
            for territory_id in field.value
            )
        if territory is not None
        ]
%>\
    % if territories_title_markup:
        % if len(territories_title_markup) == 1:
            <span class="field-value">${territories_title_markup[0] | n}</span>
        % else:
            <ul class="field-value">
            % for territory_title_markup in territories_title_markup:
                <li>${territory_title_markup | n}</li>
            % endfor
            </ul>
        % endif
    % endif
</%def>


<%def name="field_value_text_block(field, depth = 0)" filter="trim">
    % if u'\n' in field.value:
            <div class="field-value offset1">${markupsafe.Markup('<br>').join(field.value.split('\n'))}</div>
    % else:
            <span class="field-value">${field.value}</span>
    % endif
</%def>


<%def name="field_value_text_rich(field, depth = 0)" filter="trim">
            <div class="field-value offset1">${field.value | n}</div>
</%def>


<%def name="field_value_url(field, depth = 0)" filter="trim">
            <a class="field-value" href="${field.value}" rel="external">${field.value}</a>
</%def>


<%def name="fields(poi, depth = 0)" filter="trim">
    % for field in (poi.fields or []):
<%
        if conf['ignored_fields'] is not None and field.id in conf['ignored_fields']:
            ignored_field = conf['ignored_fields'][field.id]
            if ignored_field is None:
                # Always ignore a field with this ID>
                continue
            if strings.slugify(field.label) in ignored_field:
                # Ignore a field with this ID and this label
                continue
%>\
        <%self:field depth="${depth}" field="${field}"/>
    % endfor
        <%self:field_children depth="${depth}" poi="${poi}"/>
        <%self:field_last_update depth="${depth}" poi="${poi}"/>
</%def>


<%def name="footer_data_p_content()" filter="trim">
${parent.footer_data_p_content()}\
    % if conf.get('petitpois_url'):
 &mdash; <a class="label label-info" href="${urlparse.urljoin(conf['petitpois_url'], '/poi/view/{0}'.format(poi._id)
        )}" rel="external">Modifier la fiche</a>\
    % endif
 &mdash; <a class="internal" href="${urls.get_url(
        ctx, 'minisite', 'organismes', poi.slug, poi._id)}" rel="nofollow">Minisite</a>
</%def>


<%def name="scripts()" filter="trim">
    <%parent:scripts/>
    <script src="${conf['leaflet.js']}"></script>
<!--[if lt IE 10]>
    <script src="${conf['pie.js']}"></script>
<![endif]-->
    <script src="/js/map.js"></script>
    <script>
var etalage = etalage || {};
etalage.map.markersUrl = ${conf['markers_url'].rstrip('/') | n, js};
etalage.map.tileLayersOptions = ${conf['tile_layers'] | n, js};
    </script>
</%def>


<%def name="title_content()" filter="trim">
${poi.name} - ${parent.title_content()}
</%def>

