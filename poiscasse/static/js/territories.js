/*
 * PoisCasse -- Open Data POIs portal
 * By: Emmanuel Raviart <eraviart@easter-eggs.com>
 *     Romain Soufflet <rsoufflet@easter-eggs.com>
 *
 * Copyright (C) 2011 Easter-eggs
 * http://gitorious.org/infos-pratiques/poiscasse
 *
 * This file is part of PoisCasse.
 *
 * PoisCasse is free software; you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as
 * published by the Free Software Foundation, either version 3 of the
 * License, or (at your option) any later version.
 *
 * PoisCasse is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
*/


var etalage = etalage || {};


etalage.territories = (function ($) {
    function createAutocompleter($input) {
        $($input).autocomplete({
            source: function(request, response) {
                $.ajax({
                    url: etalage.territories.autocompleterUrl + '?jsonp=?',
                    dataType: 'jsonp',
                    data: {
                        term: request.term
                    },
                    success: function (data) {
                        response($.map(data.data.items, function(item) {
                            var label = item.main_postal_distribution;
                            if (item.main_postal_distribution != item.nearest_postal_distribution) {
                                label += ' (' + item.nearest_postal_distribution + ')';
                            }
                            if (item.type_name != 'Arrondissement municipal' && item.type_name != 'Commune'
                                    && item.type_name != 'Commune associée') {
                                label += ' (' + item.type_name + ')';
                            }
                            return {
                                label: label,
                                value: item.main_postal_distribution
                            };
                        }));
                    }
                });
            }
        });
    }

    return {
        createAutocompleter: createAutocompleter
    };
})(jQuery);

