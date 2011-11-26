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
        leafletMap = new L.Map(mapDiv, {
            scrollWheelZoom: false
        }).addLayer(
            new L.TileLayer(etalage.map.tileUrlTemplate, {
                attribution: 'Données cartographiques CC-By-SA'
                    + ' <a href="http://openstreetmap.org/" rel="external">OpenStreetMap</a>',
                maxZoom: 18
            })
        );
        leafletMap.attributionControl.setPrefix(null); // Remove Leaflet attribution.
        leafletMap.on('moveend', function (e) {
            try {
                var bounds = leafletMap.getBounds();
            } catch(err) {
                // Method getBounds fails when map center or zoom level are not yet set.
                return;
            }
            // When map is larger than 360 degrees, fix min and max longitude returned by getBounds().
            var northEast = bounds.getNorthEast();
            var southWest = bounds.getSouthWest();
            var lowestX = leafletMap.layerPointToContainerPoint(leafletMap.latLngToLayerPoint(new L.LatLng(0, -180))).x;
            var zeroX = leafletMap.layerPointToContainerPoint(leafletMap.latLngToLayerPoint(new L.LatLng(0, 0))).x;
            // highestX = lowestX + 2 * (zeroX - lowestX) = 2 * zeroX - lowestX
            var east = 2 * zeroX - lowestX > leafletMap.getSize().x ?  northEast.lng : 180;
            var west = lowestX < 0 ? southWest.lng : -180;
            fetchPois({
                bbox: [west, southWest.lat, east, northEast.lat].join(",")
            });
        });

        if (window.PIE) {
            $('.leaflet-control, .leaflet-control-zoom, .leaflet-control-zoom-in, .leaflet-control-zoom-out').each(
                function () {
                    // Apply CSS3 border-radius for IE to zoom controls.
                    PIE.attach(this);
                }
            );
        }

        // Text settings
        $('.leaflet-control-zoom-in').attr('title', 'Zoomer');
        $('.leaflet-control-zoom-out').attr('title', 'Dézoomer');

        // Icon settings
        var redBlankIcon = new L.Icon(etalage.map.markersUrl + '/misc/redblank.png');
        redBlankIcon.iconAnchor = new L.Point(14, 24);
        redBlankIcon.iconSize = new L.Point(27, 27);
        redBlankIcon.shadowSize = new L.Point(51, 27);
        redBlankIcon.shadowUrl = etalage.map.markersUrl + '/misc/shadow.png';

        var redMultipleIcon = new L.Icon(etalage.map.markersUrl + '/misc/redmultiple.png');
        redMultipleIcon.iconAnchor = new L.Point(14, 24);
        redMultipleIcon.iconSize = new L.Point(27, 27);
        redMultipleIcon.shadowSize = new L.Point(51, 27);
        redMultipleIcon.shadowUrl = etalage.map.markersUrl + '/misc/shadow.png';

        var geojsonLayer = new L.GeoJSON();
        geojsonLayer.on('featureparse', function (e) {
            var properties = e.properties;
            etalage.map.layerByPoiId[properties.id] = e.layer;
            var $div = $('<div/>').append(
                $('<a/>', {
                    'class': 'internal',
                    href: '/organismes/' + properties.id
                }).text(properties.name)
            );
            if (properties.streetAddress) {
                $.each(properties.streetAddress.split('\n'), function (index, line) {
                    $div.append($('<div/>').text(line));
                });
            }
            if (properties.postalDistribution) {
                $div.append($('<div/>').text(properties.postalDistribution));
            }
            if (properties.count > 1) {
                e.layer.options.icon = redMultipleIcon;
                var bbox = e.bbox;
                var $a = $('<a/>', {
                    'class': 'bbox',
                    href: '/carte?' + $.param($.extend({bbox: bbox.join(",")}, etalage.map.geojsonParams || {}), true)
                });
                if (properties.count == 2) {
                    $a.text('Ainsi qu\'un autre organisme à proximité');
                } else {
                    $a.text('Ainsi que ' + (properties.count - 1) + ' autres organismes à proximité');
                }
                $div.append($('<div/>').append($('<em/>').append($a)));
            } else {
                e.layer.options.icon = redBlankIcon;
            }
            e.layer.bindPopup($div.html())
            .on('click', function (e) {
                $('a.bbox', e.target._popup._contentNode).on('click', function () {
                    leafletMap.fitBounds(new L.LatLngBounds(new L.LatLng(bbox[1], bbox[0]),
                        new L.LatLng(bbox[3], bbox[2])));
                    return false;
                });
                $('a.internal', e.target._popup._contentNode).on('click', function () {
                    rpc.requestNavigateTo($(this).attr('href'));
                    return false;
                });
            });
        });
        leafletMap.addLayer(geojsonLayer);
        etalage.map.geojsonLayer = geojsonLayer;

        if (window.PIE) {
            leafletMap.on('layeradd', function (e) {
                if (e.layer._wrapper && e.layer._opened === true && e.layer._content) {
                    // Apply CSS3 border-radius for IE to popup.
                    PIE.attach(e.layer._wrapper);
                }
            });
        }

        etalage.map.layerByPoiId = {};
        setGeoJSONData(geojsonData);
        var bbox = etalage.map.getBBox(geojsonData.features);
        if (bbox._northEast && bbox._southWest) {
            leafletMap.fitBounds(bbox);
        } else {
            // No POI found.
            if (etalage.map.center !== null) {
                leafletMap.setView(etalage.map.center, leafletMap.getMaxZoom() - 3);
            }
        }
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

        $.each(features, function () {
            featureLatLng = new L.LatLng(this.geometry.coordinates[1], this.geometry.coordinates[0]);
            coordinates.push(featureLatLng);
        });

        return new L.LatLngBounds(coordinates);
    }

    function setGeoJSONData(data) {
        var geojsonLayer = etalage.map.geojsonLayer;
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
                    geojsonLayer.addGeoJSON(feature);
                }
            }
        }
        // Delete obsolete POIs layers.
        for (var poiId in obsoleteLayerByPoiId) {
            if (obsoleteLayerByPoiId.hasOwnProperty(poiId)) {
                geojsonLayer.removeLayer(obsoleteLayerByPoiId[poiId]);
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
                attribution: 'Données cartographiques CC-By-SA'
                    + ' <a href="http://openstreetmap.org/" rel="external">OpenStreetMap</a>',
                maxZoom: 18
            })
        );

        icon = new L.Icon(etalage.map.markersUrl + '/misc/redblank.png');
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
        center: null,
        createMap: createMap,
        geojsonLayer: null,
        geojsonParams: null,
        geojsonUrl: null,
        getBBox: getBBox,
        layerByPoiId: null,
        markersUrl: null,
        singleMarkerMap: singleMarkerMap,
        tileUrlTemplate: null
    };
})(jQuery);

