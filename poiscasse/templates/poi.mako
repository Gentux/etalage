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
import simplejson
%>\

<%inherit file="/site.mako"/>\
<%namespace file="poi-lib.mako" import="*"/>


% if poi.metadata['positions']:
    % for field_id in poi.metadata['positions']:
${field(id = field_id, label = poi.metadata[field_id].pop(0)['label'], value = poi.__getattribute__(field_id).pop(0))}
##<%:field id="${field_id}" label="${poi.metadata['field_id'].pop(0)}" value="${poi.getattribute(field_id).pop(0)}"/>
    % endfor
% endif

