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

        $loadingGif = $(image);
        $loadingGif.addClass('loading');

        isLoaded = true;
    }

    function loadingGif() {
        if (!isLoaded) {
            preloadLoadingGif();
        }

        $('a.internal').bind('click', function(event) {
            $('#search-form .form-actions').last().append($loadingGif);
        });

        $('#search-form').bind('submit', function(event) {
            $('#search-form .form-actions').last().append($loadingGif);
        });
    }

    function toggleCategories() {
        if (!isLoaded) {
            preloadLoadingGif();
        }

        $("#search-form input[name='category'][type='checkbox']").bind('change', function(event) {
            var pathname = window.location.pathname;
            var queryString = $("#search-form").serialize();

            $('#search-form .form-actions').last().append($loadingGif);

            document.location = pathname + "?" + queryString;
        });
    }

    return {
        loadingGif: loadingGif,
        toggleCategories: toggleCategories,
    };
})(jQuery);
