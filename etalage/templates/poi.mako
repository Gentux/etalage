## -*- coding: utf-8 -*-


## Etalage -- Open Data POIs portal
## By: Emmanuel Raviart <eraviart@easter-eggs.com>
##     Romain Soufflet <rsoufflet@easter-eggs.com>
##
## Copyright (C) 2011 Easter-eggs
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
import markupsafe
from biryani import strings

from etalage import model, ramdb
%>\


<%inherit file="/site.mako"/>\


<%def name="container_content()" filter="trim">
        <h2>${poi.name}</h2>
        % for field in (poi.fields or []):
        <%self:field field="${field}"/>
        % endfor
</%def>


<%def name="field(field)" filter="trim">
<%
    if field.value is None:
        return ''
%>\
<div class="field">
    <span class="field-label">${field.label} :</span>
    <%self:field_value field="${field}"/>
</div>
</%def>


<%def name="field_value(field)" filter="trim">
<%
    if field.value is None:
        return ''
%>\
    % if field.id == 'autocompleters':
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
    % elif field.id == 'adr':
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
    % elif field.id == 'email':
    <span class="field-value"><a href="mailto:${field.value}">${field.value}</a></span>
    % elif field.id == 'feed':
    <div class="field-value">
<%
        import feedparser
        d = feedparser.parse(field.value)
%>\
        % if d is None or 'status' not in d \
            or not d.version and d.status != 304 and d.status != 401 \
            or d.status >= 400:
        <em class="error">Erreur dans le flux d'actualité <a href="${field.value}" rel="external">${field.value}</a></em>
        % else:
        <strong>${d.feed.title}</strong>
        <a href="${field.value}" rel="external"><img alt="" src="http://cdn.comarquage.fr/images/misc/feed.png" /></a>
        % endif
        <ul>
        % for entry in d.entries[:10]:
            <li class="feed-entry">${entry.title | n}
            % for content in entry.content:
                <div>${content.value | n}</div>
            % endfor
            </li>
        % endfor
        % if len(d.entries) > 10:
            <li>...</li>
        % endif
        </ul>
    </div>
    % elif field.id == 'geo':
        <div class="field-value">
            <div class="single-marker-map" id="map-poi" style="height: 500px;"></div>
            <script type="text/javascript">
var etalage = etalage || {};
etalage.map.singleMarkerMap("map-poi", ${field.value[0]}, ${field.value[1]});
            </script>
            <div class="bigger-map-link">
                Voir sur une carte plus grande avec
                <a href="${u'http://www.openstreetmap.org/?mlat={0}&mlon={1}&zoom=15&layers=M'\
.format(field.value[0], field.value[1])}" rel="external">OpenStreetMap</a>
                ou
                <a href="${u'http://maps.google.com/maps?q={0},{1}'.format(field.value[0], field.value[1])}" \
rel="external">Google Maps</a>
            </div>
        </div>
    % elif field.id == 'image':
        <img class="field-value" alt="" src="${field.value}" />
    % elif field.id == 'link':
<%
        target = ramdb.pois_by_id.get(field.value)
%>\
        % if target is None:
    <em class="field-value">Lien manquant</em>
        % else:
    <a class="field-value" href="/poi/${target._id}">${target.name}</a>
        % endif
    % elif field.id == 'links':
        % if len(field.value) == 1:
<%
            single_field = model.Field(id = 'link', value = field.value[0])
%>\
<%self:field_value field="${single_field}"/>
        % else:
    <ul class="field-value">
            % for target_id in field.value:
<%
                target = ramdb.pois_by_id.get(target_id)
                if target is None:
                    continue
%>\
        <li><a href="/poi/${target._id}">${target.name}</a></li>
            % endfor
    </ul>
        % endif
    % elif field.id == 'organism-type':
    <span class="field-value">${field.value.title}</span>
    % elif field.id == 'source':
    <div class="field-value">
        % for subfield in field.value:
            <%self:field field="${subfield}"/>
        % endfor
    </div>
    % elif field.id == 'tags':
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
    % elif field.id == 'territories':
<%
        territories_main_postal_distribution_str = [
            territory.main_postal_distribution_str
            for territory in (
                model.Territory.find_one(dict(code = territory_kind_code['code'], kind = territory_kind_code['kind']))
                for territory_kind_code in field.value
                )
            if territory is not None
            ]
%>\
    <span class="field-value">${u', '.join(territories_main_postal_distribution_str)}</span>
    % elif field.id == 'text-block':
    <div class="field-value">${markupsafe.Markup('<br>').join(field.value.split('\n'))}</div>
    % elif field.id == 'text-rich':
    <div class="field-value">${field.value | n}</div>
    % elif field.id in ('source-url', 'url'):
    <a class="field-value" href="${field.value}" rel="external">${field.value}</a>
    % else:
<%
        if field.id not in ('fax', 'name', 'org', 'source-organization', 'tel'):
            print 'Unknown ID for field {0}'.format(field)
%>\
    <span class="field-value">${field.value}</span>
    % endif
</%def>


<%def name="title_content()" filter="trim">
${poi.name} - ${parent.title_content()}
</%def>

