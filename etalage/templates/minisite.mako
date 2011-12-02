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


<%inherit file="/site.mako"/>


<%def name="container_content()" filter="trim">
        <div class="page-header">
            <h1>Génération d'une page Minisite</h1>
        </div>
        <form action="${urls.get_url(ctx, 'minisite', 'organismes', data['poi'].slug, data['poi']._id)}">
            <fieldset>
                <legend>${data['poi'].name}</legend>
<%
    error = errors.get('encoding') if errors is not None else None
    encoding_and_label_couples = [
        (u'cp1252', u'CP1252'),
        (u'iso-8859-1', u'ISO-8859-1'),
        (u'iso-8859-15', u'ISO-8859-15'),
        (u'', u'UTF-8'),
        ]
    print str((params,))
%>\
                <div class="clearfix${' error' if error else ''}">
                    <label for="encoding">Encodage</label>
                    <div class="input">
                        <select class="span6" name="encoding">
    % for encoding, label in encoding_and_label_couples:
                            <option${' selected' if params['encoding'] == encoding else ''} value="${\
                                    encoding}">${label}</option>
    % endfor
                        </select>
    % if error:
                        <span class="help-inline">${error}</span>
    % endif
                    </div>
                </div>
                <div class="actions">
                    <input class="btn primary" type="submit" value="Générer">
                </div>
            </fieldset>
        </form>
    % if data.get('url'):
        <h3>URL du fragment de page Minisite</h3>
        <pre>${data['url']}</pre>
    % endif
    % if not errors:
        <div class="page-header">
            <h1>Contenu du fragment de page Minisite</h1>
        </div>

        <!-- Début du contenu « Étalage - Comarquage.fr »récupéré et inséré dans la page -->

        ${data['fragment'] | n, unicode}

        <!-- Fin du contenu « Étalage - Comarquage.fr » récupéré et inséré dans la page -->
    % endif
</%def>


<%def name="metas()" filter="trim">
    <parent:metas/>
    <meta name="robots" content="nofollow,noindex">
</%def>


<%def name="title_content()" filter="trim">
Minisite - ${parent.title_content()}
</%def>

