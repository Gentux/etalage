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


<%inherit file="/index.mako"/>


<%def name="results()" filter="trim">
        <%call expr="self.internal_form(ctx, mode, id = 'export-form', method = 'get')">
            <fieldset>
                <legend>${_('Select export options')}</legend>
    % for name, value in sorted(params.iteritems()):
<%
        if name in (
                'submit',
                'type_and_format',
                ):
            continue
        if value is None or value == u'':
            continue
%>\
        % if isinstance(value, list):
            % for item_value in value:
                <input name="${name}" type="hidden" value="${item_value or ''}">
            % endfor
        % else:
                <input name="${name}" type="hidden" value="${value or ''}">
        % endif
    % endfor
<%
    error = errors.get('type_and_format') if errors is not None else None
%>\
                <div class="clearfix${' error' if error else ''}">
                    <label>${(u"Export Type")}</label>
                    <div class="input">
                        <ul class="inputs-list">
                            <li>
                                <label>
                                    <input type="radio" value="annuaire-csv" name="type_and_format">
                                    <span>Annuaire (format CSV) &mdash; Les informations détaillées,
                                        organisme par organisme</span>
                                </label>
                            </li>
                            <li>
                                <label>
                                    <input type="radio" value="couverture-geographique-csv" name="type_and_format">
                                    <span>Couverture géographique (format CSV) &mdash; Les organismes compétents,
                                        commune par commune</span>
                                </label>
                            </li>
                            <li>
                                <label>
                                    <input type="radio" value="annuaire-geojson" name="type_and_format">
                                    <span>GeoJSON &mdash; Pour récupérer les organismes en temps réel dans vos
                                        applications</span>
                                </label>
                            </li>
                            <li>
                                <label>
                                    <input type="radio" value="annuaire-kml" name="type_and_format">
                                    <span>KML &mdash; Pour visualiser les organismes dans certains sites et applications
                                        cartographiques</span>
                                </label>
                            </li>
                        </ul>
    % if error:
                        <span class="help-block">${error}</span>
    % endif
                    </div>
                </div>
                <div class="actions">
                    <input class="btn primary" name="submit" type="submit" value="${_(u'Select')}">
                </div>
            </fieldset>
        </%call>
</%def>

