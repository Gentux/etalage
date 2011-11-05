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
from etalage import urls
%>


<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
    <Document>
        <name>Organismes</name>
    % for poi in pager.items:
<%
        if poi.geo is None:
            continue
%>\
        <Placemark>
            <name>${poi.name}</name>
            <description>${urls.get_full_url(ctx, 'organismes', str(poi._id))}</description>
            <Point>
                <coordinates>${poi.geo[1]},${poi.geo[0]}</coordinates>
            </Point>
        % for field in (poi.fields or []):
<%
            if field.value is None:
                continue
%>\
            % if field.id == 'adr':
            <address>${u', '.join(
                    strip_fragment
                    for strip_fragment in (
                        fragment.strip()
                        for subfield in field.value
                        if subfield.value is not None and subfield.id != 'commune'
                        for fragment in subfield.value.split('\n')
                        )
                    if strip_fragment
                    )}</address>
            % elif field.id == 'fax':
            <phoneNumber>fax: ${field.value}</phoneNumber>
            % elif field.id == 'tel':
            <phoneNumber>tel: ${field.value}</phoneNumber>
            % endif
        % endfor
        </Placemark>
    % endfor
    <Document>
</kml>