## -*- coding: utf-8 -*-


## PoisCasse -- Open Data POIs portal
## By: Emmanuel Raviart <eraviart@easter-eggs.com>
##     Romain Soufflet <rsoufflet@easter-eggs.com>
##
## Copyright (C) 2011 Easter-eggs
## http://gitorious.org/infos-pratiques/poiscasse
##
## This file is part of PoisCasse.
##
## PoisCasse is free software; you can redistribute it and/or modify
## it under the terms of the GNU Affero General Public License as
## published by the Free Software Foundation, either version 3 of the
## License, or (at your option) any later version.
##
## PoisCasse is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Affero General Public License for more details.
##
## You should have received a copy of the GNU Affero General Public License
## along with this program.  If not, see <http://www.gnu.org/licenses/>.


<%!
import markupsafe
import uuid

from poiscasse import model, ramdb
%>\


<%def name="field(id, value, label, label_plural = None)" filter="trim">
<%
    if value is None:
        return ''
%>\
<div class="field">
    % if label_plural is not None and isinstance(value, (list, set, tuple)) and len(value) > 1:
    <span class="field-label">${label_plural} :</span>
    % else:
    <span class="field-label">${label} :</span>
    % endif
    <%self:field_value id="${id}" value="${value}"/>
</div>
</%def>


<%def name="field_value(id, value)" filter="trim">
    % if id == 'activities':
<%
    activities_code = value
    activities_title = [
        title
        for slug, title in sorted(
            (activity.slug, activity.title)
            for activity in Activity.find(dict(code = {'$in': list(value)}))
            )
        ]
%>\
    <span class="field-value">${u', '.join(activities_title)}</span>
    % elif id == 'adr':
    <div class="field-value">
        <div class="adr">
        % if 'street-address' in value:
            % for line in value['street-address'][0].split('\n'):
            ${line}<br />
            % endfor
        % endif
            ${(value.get('postal-distribution') or [''])[0]}
        </div>
    </div>
    % elif id == 'email':
    <span class="field-value"><a href="mailto:${value}">${value}</a></span>
    % elif id == 'emails':
        % if len(value) == 1:
<%self:field_value id="email" value="${value[0]}"/>
        % else:
    <ul class="field-value">
            % for email in value:
        <li>${email}</li>
            % endfor
    </ul>
        % endif
    % elif id == 'fax':
    <span class="field-value">${value}</span>
    % elif id == 'faxes':
        % if len(value) == 1:
<%self:field_value id="fax" value="${value[0]}"/>
        % else:
    <ul class="field-value">
            % for fax in value:
        <li>${fax}</li>
            % endfor
    </ul>
        % endif
    % elif id == 'feed':
    <div class="field-value">
<%
        import feedparser
        d = feedparser.parse(value)
%>\
        % if d is None or 'status' not in d \
            or not d.version and d.status != 304 and d.status != 401 \
            or d.status >= 400:
        <em class="error">Erreur dans le flux d'actualité <a href="${value}" rel="external">${value}</a></em>
        % else:
        <strong>${d.feed.title}</strong>
        <a href="${value}" rel="external"><img alt="" src="http://cdn.comarquage.fr/images/misc/feed.png" /></a>
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
    % elif id == 'geo':
        <div class="field-value">
            <div class="single-marker-map" id="map-poi" style="height: 500px;"></div>
            <script type="text/javascript">
var etalage = etalage || {};
etalage.map.singleMarkerMap("map-poi", ${value[0]}, ${value[1]});
            </script>
            <div class="bigger-map-link">
                Voir sur une carte plus grande avec
                <a href="${u'http://www.openstreetmap.org/?mlat={0}&mlon={1}&zoom=15&layers=M'\
.format(value[0], value[1])}" rel="external">OpenStreetMap</a>
                ou
                <a href="${u'http://maps.google.com/maps?q={0},{1}'.format(value[0], value[1])}" \
rel="external">Google Maps</a>
            </div>
        </div>
    % elif id == 'image':
        <img class="field-value" alt="" src="${value}" />
    % elif id == 'link':
<%
        target = ramdb.ram_pois_by_id.get(value)
%>\
        % if target is None:
    <em class="field-value">Lien manquant</em>
        % else:
    <a class="field-value" href="/poi/${target._id}">${target.name}</a>
        % endif
    % elif id == 'links':
        % if len(value) == 1:
<%self:field_value id="link" value="${value[0]}"/>
        % else:
    <ul class="field-value">
            % for target in value:
<%
                target = ramdb.ram_pois_by_id.get(value)
                if target is None:
                    continue
%>\
        <li><a href="/poi/${target._id}">${target.name}</a></li>
            % endfor
    </ul>
        % endif
    % elif id == 'org':
    <span class="field-value">${value}</span>
    % elif id == 'organism-type':
    <span class="field-value">${value.title}</span>
    % elif id == 'tags':
<%
    tags_code = value
    tags_title = [
        title
        for slug, title in sorted(
            (tag.slug, tag.title)
            for tag in Tag.find(dict(code = {'$in': list(value)}))
            )
        ]
%>\
    <span class="field-value">${u', '.join(tags_title)}</span>
    % elif id == 'tel':
    <span class="field-value">${value}</span>
    % elif id == 'tels':
        % if len(value) == 1:
<%self:field_value id="tel" value="${value[0]}"/>
        % else:
    <ul class="field-value">
            % for tel in value:
        <li>${tel}</li>
            % endfor
    </ul>
        % endif
    % elif id == 'territories':
<%
        territories_title = [
            title
            for slug, title in sorted(
                ## FIXME : Ne pas utiliser ncc
                (territory.ncc, territory.name)
                for territory in (
                    model.Territory.find_one(dict(code = territory_kind_code['code'], kind = territory_kind_code['kind']))
                    for territory_kind_code in value
                    )
                if territory is not None
                )
            ]
%>\
    <span class="field-value">${u', '.join(territories_title)}</span>
    % elif id == 'text-block':
    <div class="field-value">${markupsafe.Markup('<br />').join(value.split('\n'))}</div>
    % elif id == 'text-rich':
    <div class="field-value">${value | n}</div>
    % elif id == 'url':
    <a class="field-value" href="${value}" rel="external">${value}</a>
    % elif id == 'urls':
        % if len(value) == 1:
<%self:field_value id="url" value="${value[0]}"/>
        % else:
    <ul class="field-value">
            % for url in value:
        <li><a href="${url}" rel="external">${url}</a></li>
            % endfor
    </ul>
        % endif
    % else:
    <span class="field-value">${value}</span>
    % endif
</%def>

