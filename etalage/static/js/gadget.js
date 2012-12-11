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


function adjustFrameHeight(seconds) {
    var frameNewHeight = $("html").height();
    if (seconds) {
        // Adjust frame height for a few seconds ("* 5" is because of 200 ms timeout).
        adjustFrameHeightCount = seconds * 5;
    }


    if (frameNewHeight != etalage.frameHeight) {
        etalage.rpc.adjustHeight(frameNewHeight);
        etalage.frameHeight = frameNewHeight;
    }
    if (etalage.adjustFrameHeightCount-- >= 0) {
        setTimeout(function() {
            adjustFrameHeight();
        }, 200);
    }
}


function initGadget(options) {
    // Adjust frame height for 5 seconds.
    etalage.adjustFrameHeightCount = 5 * 5;
    etalage.frameHeight = null;

    if (!etalage.easyXDM) {
        etalage.easyXDM = easyXDM.noConflict("etalage");
        etalage.easyXDM.DomHelper.requiresJSON(options.json2Url);
    }

    etalage.rpc = new etalage.easyXDM.Rpc({
        swf: options.swfUrl
    },
    {
        remote: {
            adjustHeight: {},
            requestNavigateTo: {}
        }
    });

    adjustFrameHeight();

    $("form.internal").on("submit", function (event) {
        etalage.rpc.requestNavigateTo($(this).attr("action"), $(this).serialize());
        return false;
    });

    $("a.internal").on("click", function () {
        etalage.rpc.requestNavigateTo($(this).attr("href"));
        return false;
    });

    $("a[href][rel=bookmark]").attr("target", "_top");
    $("a[href][rel=mobile]").attr("target", "_top");
    $("a[href][rel=external]").attr("target", "_top");
}
