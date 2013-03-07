/*
 * Etalage -- Open Data POIs portal
 * By: Emmanuel Raviart <eraviart@easter-eggs.com>
 *
 * Copyright (C) 2011, 2012 Easter-eggs
 * http://gitorious.org/infos-pratiques/etalage
 *
 * This file is part of Etalage.
 *
 * Etalage is free software; you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as
 * published by the Free Software Foundation, either version 3 of the
 * License, or (at your option) any later version.
 *
 * Etalage is distributed in the hope that it will be useful,
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
        $input.autocomplete({
            minLength: 0,
            open: function (event, ui) {
                return $(".ui-autocomplete").css("z-index", $(".leaflet-control-zoom").css("z-index") + 1);
            },
            source: function (request, response) {
                $.ajax({
                    url: '/api/v1/categories/autocomplete',
                    dataType: 'json',
                    data: {
                        tag: $.merge(
                            etalage.categories.tags || [],
                            $('input[name=category][type=checkbox]:checked').map(function() {
                                return $(this).val();
                            }).get()
                        ),
                        term: request.term || ''
                    },
                    success: function (data) {
                        response($.map(data.data.items, function(item) {
                            return {
                                label: item.tag + ' (' + item.count + ')',
                                value: item.tag
                            };
                        }));
                    },
                    traditional: true
                });
            }
        });

        $("#search-form input[name='category'][type='checkbox']").on('change', function(event) {
            $(this).closest('label').hide();

            etalage.categories.tags.splice($.inArray($(this).val(), etalage.categories.tags), 1)
        });
    }

    return {
        createAutocompleter: createAutocompleter
    };
})(jQuery);

