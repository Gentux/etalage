/*
 * Etalage -- Open Data POIs portal
 * By: Emmanuel Raviart <eraviart@easter-eggs.com>
 *     Romain Soufflet <rsoufflet@easter-eggs.com>
 *
 * Copyright (C) 2011 Easter-eggs
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


etalage.map = (function ($) {
    var leafletMap;

    function createMap(mapDiv, geojsonData) {
        var icon;

        leafletMap = new L.Map(mapDiv, {
            scrollWheelZoom: false
        }).addLayer(
            new L.TileLayer(etalage.map.tileUrlTemplate, {
                attribution: 'Fond de carte <a href="http://openstreetmap.org/">OpenStreetMap</a>',
                maxZoom: 18
            })
        );
        leafletMap.on('moveend', function(e) {
            try {
                var bounds = leafletMap.getBounds();
            } catch(err) {
                // Method getBounds fails when map center or zoom level are not yet set.
                return;
            }
            fetchPois({
                bbox: [
                    bounds.getSouthWest().lng, bounds.getSouthWest().lat,
                    bounds.getNorthEast().lng, bounds.getNorthEast().lat
                ].join(","),
            });
        });

        if (window.PIE) {
            $('.leaflet-control, .leaflet-control-zoom, .leaflet-control-zoom-in, .leaflet-control-zoom-out').each(
                function() {
                    // Apply CSS3 border-radius for IE to zoom controls.
                    PIE.attach(this);
                }
            );
        }

        // Text settings
        leafletMap.attributionControl.setPrefix('Carte par <a href="http://leaflet.cloudmade.com">Leaflet</a>');
        $('.leaflet-control-zoom-in').attr('title', 'Zoomer');
        $('.leaflet-control-zoom-out').attr('title', 'Dézoomer');

        // Icon settings
        icon = new L.Icon(etalage.map.markersUrl + '/map-icons-collection-2.0/numeric/redblank.png');
        icon.iconAnchor = new L.Point(14, 24);
        icon.iconSize = new L.Point(27, 27);
        icon.shadowSize = new L.Point(51, 27);
        icon.shadowUrl = etalage.map.markersUrl + '/misc/shadow.png';

        var geojson = new L.GeoJSON();
        geojson.on('featureparse', function(e) {
            etalage.map.layerByPoiId[e.properties.id] = e.layer;
            e.layer.options.icon = icon;
            e.layer
                .bindPopup('<a class="internal" href="/organismes/' + e.properties.id + '">'
                    + e.properties.name + '</a>')
                .on('click', function (e) {
                    $('a.internal', e.target._popup._contentNode).on('click', function () {
                        rpc.requestNavigateTo($(this).attr('href'));
                        return false;
                    });
                });
        });
        leafletMap.addLayer(geojson);
        etalage.map.geojson = geojson;

        if (window.PIE) {
            leafletMap.on('layeradd', function(e) {
                if (e.layer._wrapper && e.layer._opened === true && e.layer._content) {
                    // Apply CSS3 border-radius for IE to popup.
                    PIE.attach(e.layer._wrapper);
                }
            });
        }

        etalage.map.layerByPoiId = {};
        setGeoJSONData(geojsonData);
        leafletMap.fitBounds(etalage.map.getBBox(geojsonData.features));
    }

    function fetchPois(params) {
        var context = (new Date()).getTime();
        $.ajax({
            url: etalage.map.geojsonUrl,
            dataType: 'json',
            data: $.extend({
                context: context
            }, etalage.map.geojsonParams || {}, params || {}),
            success: function (data) {
                if (parseInt(data.properties.context) !== context) {
                    return;
                }
                setGeoJSONData(data);
            },
            traditional: true
        });
    }

    function getBBox(features) {
        var featureLatLng, coordinates = [];

        $.each(features, function() {
            featureLatLng = new L.LatLng(this.geometry.coordinates[1], this.geometry.coordinates[0]);
            coordinates.push(featureLatLng);
        });

        return new L.LatLngBounds(coordinates);
    }

    function setGeoJSONData(data) {
        var geojson = etalage.map.geojson;
        var layerByPoiId = etalage.map.layerByPoiId;
        // Retrieve existing POIs layers.
        var obsoleteLayerByPoiId = {};
        for (var poiId in layerByPoiId) {
            if (layerByPoiId.hasOwnProperty(poiId)) {
                obsoleteLayerByPoiId[poiId] = layerByPoiId[poiId];
            }
        }
        // Add only new POIs layers.
        if (data.features) {
            var feature, poiId;
            for (var i = 0, len = data.features.length; i < len; i++) {
                feature = data.features[i];
                poiId = feature.properties.id;
                delete obsoleteLayerByPoiId[poiId];
                if (!(poiId in layerByPoiId)) {
                    geojson.addGeoJSON(feature);
                }
            }
        }
        // Delete obsolete POIs layers.
        for (var poiId in obsoleteLayerByPoiId) {
            if (obsoleteLayerByPoiId.hasOwnProperty(poiId)) {
                geojson.removeLayer(obsoleteLayerByPoiId[poiId]);
                delete layerByPoiId[poiId];
            }
        }
    }

    function singleMarkerMap(mapDiv, latitude, longitude) {
        var icon, latLng, map, marker;

        map = new L.Map(mapDiv, {
            scrollWheelZoom: false
        }).addLayer(
            new L.TileLayer(etalage.map.tileUrlTemplate, {
                attribution: 'Fond de carte <a href="http://openstreetmap.org/">OpenStreetMap</a>',
                maxZoom: 18
            })
        );

        icon = new L.Icon(etalage.map.markersUrl + '/map-icons-collection-2.0/numeric/redblank.png');
        icon.iconAnchor = new L.Point(14, 24);
        icon.iconSize = new L.Point(27, 27);
        icon.shadowSize = new L.Point(51, 27);
        icon.shadowUrl = etalage.map.markersUrl + '/misc/shadow.png';

        latLng = new L.LatLng(latitude, longitude);
        marker = new L.Marker(latLng);
        marker.options.icon = icon;
        map.addLayer(marker);

        map.setView(latLng, map.getMaxZoom() - 3);

        return map;
    }

    return {
        createMap: createMap,
        geojson: null,
        geojsonParams: null,
        geojsonUrl: null,
        getBBox: getBBox,
        layerByPoiId: null,
        markersUrl: null,
        singleMarkerMap: singleMarkerMap,
        tileUrlTemplate: null
    };
})(jQuery);

