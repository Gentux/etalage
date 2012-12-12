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


etalage.bind = (function ($) {
    var $loadingGif;
    var isLoaded = false;

    function preloadLoadingGif() {
        image = new Image();
        image.src = etalage.miscUrl + 'please-wait.gif';
        image.alt = 'Chargement...';

        $loadingGif = $("<span>", {class: "loading"}).append($(image));
        $loadingGif.addClass('loading');

        isLoaded = true;
    }

    function loadingGif() {
        if (!isLoaded) {
            preloadLoadingGif();
        }

        $('a.internal').on('click', appendLoadingGif);
        $('#search-form').on('submit', appendLoadingGif);
    }

    function appendLoadingGif(event) {
        $('#search-form .control-group .controls').last().append($loadingGif);
        $loadingGif.data('activeUrl', document.location);

        setTimeout(function () {
            if (typeof($loadingGif) !== "undefined" &&
                    $loadingGif !== null &&
                    document.location == $loadingGif.data('activeUrl')) {
                $loadingGif.detach();
                clearTimeout();
            }
        }, 300);
    }

    function toggleCategories() {
        if (!isLoaded) {
            preloadLoadingGif();
        }

        $("#search-form input[name='category'][type='checkbox']").on('change', function(event) {
            var action = $("#search-form").attr('action');
            var queryString = $("#search-form").serialize();

            $('#search-form .form-actions').last().append($loadingGif);

            if (typeof rpc !== "undefined" && rpc !== null) {
                rpc.requestNavigateTo(action, queryString);
                return false;
            } else {
                document.location = action + "?" + queryString;
            }
        });
    }

    return {
        loadingGif: loadingGif,
        toggleCategories: toggleCategories
    };
})(jQuery);

