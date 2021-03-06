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


etalage.form = (function ($) {
    function initSearchForm(options) {
        if (! options.error) {
            $(".collapse").collapse();
            $("button.btn-search-form").on("click", function() {
                $(".btn-search-form").hide();
                if (options.isGadget) {
                    adjustFrameHeight(5);
                }
            });

            $("a.btn-atom-feed").on("click", function (event) {
                $searchForm = options.searchForm || $(this).closest('form');
                feed_url = $(this).attr("href");
                if (feed_url.search(/\?/) > 0) {
                    $(this).attr("href", feed_url.substr(0, feed_url.search(/\?/)) + '?' + $searchForm.serialize());
                }
            });
        } else {
            $(".btn-search-form").hide();
        }
    }

    return {
        initSearchForm: initSearchForm
    };
})(jQuery);
