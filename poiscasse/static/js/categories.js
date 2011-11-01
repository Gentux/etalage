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


etalage.categories = (function ($) {
    function createAutocompleter($input) {
        $($input).autocomplete({
            source: function(request, response) {
                $.ajax({
                    url: '/api/v1/autocomplete-category',
                    dataType: 'json',
                    data: {
                        tag: etalage.categories.tags || '',
                        term: request.term || ''
                    },
                    success: function (data) {
                        response($.map(data.data.items, function(label) {
                            return {
                                label: label
                            };
                        }));
                    },
                    traditional: true
                });
            }
        });
    }

    return {
        createAutocompleter: createAutocompleter
    };
})(jQuery);

