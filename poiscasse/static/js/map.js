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


etalage.map = (function ($) {
    var leafletMap;

    function createMap(mapDiv) {
        var icon;

        leafletMap = new L.Map(mapDiv, {
            scrollWheelZoom: false
        }).addLayer(
            new L.TileLayer(etalage.map.tileUrlTemplate, {
                attribution: 'Cartel CC-By-SA par <a href="http://openstreetmap.org/">OpenStreetMap</a>',
                maxZoom: 18
            })
        );

        if (window.PIE) {
            $(".leaflet-control, .leaflet-control-zoom, .leaflet-control-zoom-in, .leaflet-control-zoom-out").each(function() {
                // Apply CSS3 border-radius for IE to zoom controls.
                PIE.attach(this);
            });
        }

        // Text settings
        leafletMap.attributionControl.setPrefix('Carte par <a href="http://leaflet.cloudmade.com">Leaflet</a>');
        $(".leaflet-control-zoom-in").attr("title", "Zoomer");
        $(".leaflet-control-zoom-out").attr("title", "Dézoomer");

        // Icon settings
        icon = new L.Icon(etalage.map.markersUrl + '/map-icons-collection-2.0/numeric/redblank.png');
        icon.iconAnchor = new L.Point(14, 24);
        icon.iconSize = new L.Point(27, 27);
        icon.shadowSize = new L.Point(51, 27);
        icon.shadowUrl = etalage.map.markersUrl + '/misc/shadow.png';

        var geojson = new L.GeoJSON();
        geojson.on('featureparse', function(e) {
            e.layer.options.icon = icon;

            if (e.properties.id && e.properties.name)  {
                e.layer.bindPopup('<a href="/organismes/' + e.properties.id + '">' +  e.properties.name + "</a>");
            }
        });
        leafletMap.addLayer(geojson);
        leafletMap._geojsonLayer = geojson;

        if (window.PIE) {
            leafletMap.on("layeradd", function(event) {
                if (event.layer._wrapper && event.layer._opened === true && event.layer._content) {
                    // Apply CSS3 border-radius for IE to popup.
                    PIE.attach(event.layer._wrapper);
                }
            });
        }

        fetchPois();
    }

    function getBBox(features) {
        var featureLatLng, coordinates = [];

        $.each(features, function() {
            featureLatLng = new L.LatLng(this.geometry.coordinates[1], this.geometry.coordinates[0]);
            coordinates.push(featureLatLng);
        });

        return new L.LatLngBounds(coordinates);
    }

    function singleMarkerMap(mapDiv, latitude, longitude) {
        var icon, latLng, map, marker;

        map = new L.Map(mapDiv, {
            scrollWheelZoom: false
        }).addLayer(
            new L.TileLayer(etalage.map.tileUrlTemplate, {
                attribution: 'Carte CC-By-SA par <a href="http://openstreetmap.org/">OpenStreetMap</a>',
                maxZoom: 18
            })
        );

        icon = new L.Icon("http://cdn.comarquage.fr/images/markers/map-icons-collection-2.0/numeric/redblank.png");
        icon.iconAnchor = new L.Point(14, 24);
        icon.iconSize = new L.Point(27, 27);
        icon.shadowSize = new L.Point(51, 27);
        icon.shadowUrl = "http://cdn.comarquage.fr/images/markers/misc/shadow.png";

        latLng = new L.LatLng(latitude, longitude);
        marker = new L.Marker(latLng);
        marker.options.icon = icon;
        map.addLayer(marker);

        map.setView(latLng, map.getMaxZoom() - 3);

        return map;
    }

    function fetchPois() {
        $.ajax({
            url: etalage.map.geoJsonUrl,
            dataType: "json",
            data: {
                term: $("#term").val(),
                territory: $("#territory").val()
            },
            success: function(data) {
                leafletMap._geojsonLayer.addGeoJSON(data);
                leafletMap.fitBounds(etalage.map.getBBox(data.features));
            }
        });
    }

    return {
        createMap: createMap,
        geoJsonUrl: null,
        getBBox: getBBox,
        markersUrl: null,
        singleMarkerMap: singleMarkerMap,
        tileUrlTemplate: null
    };
})(jQuery);

