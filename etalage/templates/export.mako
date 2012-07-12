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
from etalage import model, urls
%>


<%inherit file="/index.mako"/>


<%def name="types_and_formats_radios()" filter="trim">
                        <label class="radio">
                            <input type="radio" value="annuaire-excel" name="type_and_format">
                            Annuaire (format Excel) &mdash; Les informations détaillées,
                            organisme par organisme
                        </label>
                        <label class="radio">
                            <input type="radio" value="annuaire-csv" name="type_and_format">
                            Annuaire (format CSV) &mdash; Les informations détaillées,
                            organisme par organisme
                        </label>
                        <label class="radio">
                            <input type="radio" value="couverture-excel" name="type_and_format">
                            Couverture géographique (format Excel) &mdash; Les informations détailléees des
                            organismes compétents, commune par commune
                        </label>
                        <label class="radio">
                            <input type="radio" value="couverture-csv" name="type_and_format">
                            Couverture géographique (format CSV) &mdash; Les informations détailléees des
                            organismes compétents, commune par commune
                        </label>
##                        <label class="radio">
##                            <input type="radio" value="annuaire-geojson" name="type_and_format">
##                            GeoJSON &mdash; Pour récupérer les organismes en temps réel dans vos applications
##                        </label>
##                        <label class="radio">
##                            <input type="radio" value="annuaire-kml" name="type_and_format">
##                            KML &mdash; Pour visualiser les organismes dans certains sites et applications
##                                cartographiques
##                        </label>
</%def>


<%def name="results()" filter="trim">
        <form action="${urls.get_url(ctx, mode)}" class="form-horizontal internal" id="export-form" method="get">
            <fieldset>
                <legend>${_('Select export options')}</legend>
    % for name, value in sorted(inputs.iteritems()):
<%
        name = model.Poi.rename_input_to_param(name)
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
                <div class="control-group${' error' if error else ''}">
                    <label class="control-label">${_(u"Export Type")}</label>
                    <div class="controls">
                        <%self:types_and_formats_radios/>
    % if error:
                        <p class="help-block">${error}</p>
    % endif
                    </div>
                </div>
                <div class="form-actions">
                    <button class="btn btn-primary" name="submit" type="submit" value="select"><i class="icon-ok icon-white"></i> ${_('Select')}</button>
                </div>
            </fieldset>
        </form>
</%def>


<%def name="title_content()" filter="trim">
${_(u'Export')} - ${parent.title_content()}
</%def>

