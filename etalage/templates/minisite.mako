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
from etalage import conf, urls
%>


<%inherit file="/site.mako"/>


<%def name="container_content()" filter="trim">
        <div class="page-header">
            <h1>Génération d'une page Minisite</h1>
        </div>
        <div class="alert alert-info">
            <strong>Note :</strong> Une page <em>Minisite</em> est destinée à être intégrée dans une page d'un autre
            serveur web.
        </div>
        <form action="${urls.get_url(ctx, 'minisite', 'organismes', poi.slug, poi._id)}">
            <fieldset>
                <legend>${poi.name}</legend>
<%
    error = errors.get('encoding') if errors is not None else None
    encoding_and_label_couples = [
        (u'cp1252', u'CP1252'),
        (u'iso-8859-1', u'ISO-8859-1'),
        (u'iso-8859-15', u'ISO-8859-15'),
        (u'', u'UTF-8'),
        ]
%>\
                <div class="control-group${' error' if error else ''}">
                    <label class="control-label" for="encoding">Encodage</label>
                    <div class="controls">
                        <select name="encoding">
    % for encoding, label in encoding_and_label_couples:
                            <option${' selected' if inputs['encoding'] == encoding else ''} value="${\
                                    encoding}">${label}</option>
    % endfor
                        </select>
    % if error:
                        <span class="help-inline">${error}</span>
    % else:
                        <span class="help-inline">Encodage des caractères utilisé par le serveur hébergeant la page
                            <em>Minisite</em></span>
    % endif
                    </div>
                </div>
                <div class="form-actions">
                    <button class="btn btn-primary" type="submit" value="generate"><i class="icon-ok icon-white"></i> ${_('Generate')}</button>
                </div>
            </fieldset>
        </form>
    % if url:
        <h3>URL du fragment de page Minisite</h3>
        <pre>${url}</pre>
    % endif
    % if not errors:
        <hr>
        <h3>Résultat</h3>
        <div class="tabbable">
            <ul class="nav nav-tabs">
                <li class="active"><a data-toggle="tab" href="#show-preview">Aperçu</a></li>
                <li><a data-toggle="tab" href="#show-source-code">Code Source</a></li>
            </ul>
            <div class="tab-content">
                <div class="active tab-pane" id="show-preview">
                    <div class="fixed-width">

        <!-- Début du contenu « Étalage - Comarquage.fr »récupéré et inséré dans la page -->

        ${fragment | n, unicode}

        <!-- Fin du contenu « Étalage - Comarquage.fr » récupéré et inséré dans la page -->

                    </div>
                </div>
                <div class="tab-pane" id="show-source-code">
                    <pre class="prettyprint linenums">
        ${fragment}
                    </pre>
                </div>
            </div>
        </div>
    % endif
</%def>


<%def name="metas()" filter="trim">
    <parent:metas/>
    <meta name="robots" content="nofollow,noindex">
</%def>


<%def name="scripts()" filter="trim">
    <%parent:scripts/>
    <script src="${conf['bootstrap.js']}"></script>
    <script src="${conf['prettify.js']}"></script>
    <script>
$(function () {
    prettyPrint();
});
    </script>
</%def>


<%def name="title_content()" filter="trim">
Minisite - ${parent.title_content()}
</%def>

