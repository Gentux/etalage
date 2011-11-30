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

    function createMap(mapDiv, bbox) {
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
        leafletMap
            .on('dragend', function (e) {
                fetchPois();
            })
            .on('zoomend', function (e) {
                try {
                    leafletMap.getBounds();
                } catch(err) {
                    // Method getBounds fails when map center or zoom level are not yet set.
                    return;
                }
                etalage.map.geojsonLayer.clearLayers();
                etalage.map.layerByPoiId = {};
                fetchPois();
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
        var blueBlankIcon = new L.Icon(etalage.map.markersUrl + '/misc/blueblank.png');
        blueBlankIcon.iconAnchor = new L.Point(14, 24);
        blueBlankIcon.iconSize = new L.Point(27, 27);
        blueBlankIcon.shadowSize = new L.Point(51, 27);
        blueBlankIcon.shadowUrl = etalage.map.markersUrl + '/misc/shadow.png';

        var blueMultipleIcon = new L.Icon(etalage.map.markersUrl + '/misc/bluemultiple.png');
        blueMultipleIcon.iconAnchor = new L.Point(14, 24);
        blueMultipleIcon.iconSize = new L.Point(27, 27);
        blueMultipleIcon.shadowSize = new L.Point(51, 27);
        blueMultipleIcon.shadowUrl = etalage.map.markersUrl + '/misc/shadow.png';

        var greenValidIcon = new L.Icon(etalage.map.markersUrl + '/misc/greenvalid.png');
        greenValidIcon.iconAnchor = new L.Point(14, 24);
        greenValidIcon.iconSize = new L.Point(27, 27);
        greenValidIcon.shadowSize = new L.Point(51, 27);
        greenValidIcon.shadowUrl = etalage.map.markersUrl + '/misc/shadow.png';

        var greenMultipleIcon = new L.Icon(etalage.map.markersUrl + '/misc/greenmultiple.png');
        greenMultipleIcon.iconAnchor = new L.Point(14, 24);
        greenMultipleIcon.iconSize = new L.Point(27, 27);
        greenMultipleIcon.shadowSize = new L.Point(51, 27);
        greenMultipleIcon.shadowUrl = etalage.map.markersUrl + '/misc/shadow.png';

        var homeIcon = new L.Icon(etalage.map.markersUrl + '/map-icons-collection-2.0/icons/home.png');
        homeIcon.iconAnchor = new L.Point(14, 24);
        homeIcon.iconSize = new L.Point(27, 27);
        homeIcon.shadowSize = new L.Point(51, 27);
        homeIcon.shadowUrl = etalage.map.markersUrl + '/misc/shadow.png';

        var redInvalidIcon = new L.Icon(etalage.map.markersUrl + '/misc/redinvalid.png');
        redInvalidIcon.iconAnchor = new L.Point(14, 24);
        redInvalidIcon.iconSize = new L.Point(27, 27);
        redInvalidIcon.shadowSize = new L.Point(51, 27);
        redInvalidIcon.shadowUrl = etalage.map.markersUrl + '/misc/shadow.png';

        var redMultipleIcon = new L.Icon(etalage.map.markersUrl + '/misc/redmultiple.png');
        redMultipleIcon.iconAnchor = new L.Point(14, 24);
        redMultipleIcon.iconSize = new L.Point(27, 27);
        redMultipleIcon.shadowSize = new L.Point(51, 27);
        redMultipleIcon.shadowUrl = etalage.map.markersUrl + '/misc/shadow.png';

        var geojsonLayer = new L.GeoJSON();
        geojsonLayer.on('featureparse', function (e) {
            var properties = e.properties;
            etalage.map.layerByPoiId[properties.id] = e.layer;

            if (properties.home) {
                e.layer.options.icon = homeIcon;
            } else {
                if (properties.count > 1) {
                    if (properties.competent === true) {
                        e.layer.options.icon = greenMultipleIcon;
                    } else if (properties.competent === false) {
                        e.layer.options.icon = redMultipleIcon;
                    } else {
                        e.layer.options.icon = blueMultipleIcon;
                    }
                } else {
                    if (properties.competent === true) {
                        e.layer.options.icon = greenValidIcon;
                    } else if (properties.competent === false) {
                        e.layer.options.icon = redInvalidIcon;
                    } else {
                        e.layer.options.icon = blueBlankIcon;
                    }
                }

                var nearbyPoiCount = properties.count - properties.centerPois.length;
                var poi;
                var $popupDiv = $('<div/>');
                if (properties.count == 1 || nearbyPoiCount > 0) {
                    poi = properties.centerPois[0];
                    $popupDiv.append(
                        $('<a/>', {
                            'class': 'internal',
                            href: '/organismes/' + poi.id
                        }).append($('<strong/>').text(poi.name))
                    );
                    if (poi.streetAddress) {
                        $.each(poi.streetAddress.split('\n'), function (index, line) {
                            $popupDiv.append($('<div/>').text(line));
                        });
                    }
                    if (poi.postalDistribution) {
                        $popupDiv.append($('<div/>').text(poi.postalDistribution));
                    }
                } else {
                    var $ul = $('<ul/>');
                    var $li;
                    $.each(properties.centerPois, function (index, poi) {
                        $li = $('<li>').append(
                            $('<a/>', {
                                'class': 'internal',
                                href: '/organismes/' + poi.id
                            }).append($('<strong/>').text(poi.name))
                        );
                        if (poi.streetAddress) {
                            $.each(poi.streetAddress.split('\n'), function (index, line) {
                                $li.append($('<div/>').text(line));
                            });
                        }
                        if (poi.postalDistribution) {
                            $li.append($('<div/>').text(poi.postalDistribution));
                        }
                        $ul.append($li);
                    });
                    $popupDiv.append($ul);
                }

                if (nearbyPoiCount > 0) {
                    var bbox = e.bbox;
                    var $a = $('<a/>', {
                        'class': 'bbox',
                        href: '/carte?' + $.param($.extend({bbox: bbox.join(",")}, etalage.map.geojsonParams || {}), true)
                    });
                    var $em = $('<em/>');
                    if (properties.count == 2) {
                        $em.text('Ainsi qu\'1 autre organisme à proximité');
                    } else {
                        $em.text('Ainsi que ' + (properties.count - 1) + ' autres organismes à proximité');
                    }
                    $popupDiv.append($('<div/>').append($a.append($em)));
                }

                e.layer
                    .bindPopup($popupDiv.html())
                    .on('click', function (e) {
                        etalage.map.currentPoiId = properties.id;
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
                leafletMap.on('layerremove', function (e) {
                    if (e.layer._closeButton) {
                        delete etalage.map.currentPoiId;
                    }
                });
            }
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
        if (bbox) {
            leafletMap.fitBounds(new L.LatLngBounds(new L.LatLng(bbox[1], bbox[0]), new L.LatLng(bbox[3], bbox[2])));
            fetchPois();
        } else {
            // No POI found.
            if (etalage.map.center !== null) {
                leafletMap.setView(etalage.map.center, leafletMap.getMaxZoom() - 3);
            }
        }
    }

    function fetchPois() {
        var context = (new Date()).getTime();
        // When map is larger than 360 degrees, fix min and max longitude returned by getBounds().
        var bounds = leafletMap.getBounds();
        var northEast = bounds.getNorthEast();
        var southWest = bounds.getSouthWest();
        var lowestX = leafletMap.layerPointToContainerPoint(leafletMap.latLngToLayerPoint(new L.LatLng(0, -180))).x;
        var zeroX = leafletMap.layerPointToContainerPoint(leafletMap.latLngToLayerPoint(new L.LatLng(0, 0))).x;
        // highestX = lowestX + 2 * (zeroX - lowestX) = 2 * zeroX - lowestX
        var east = 2 * zeroX - lowestX > leafletMap.getSize().x ?  northEast.lng : 180;
        var west = lowestX < 0 ? southWest.lng : -180;
        $.ajax({
            url: etalage.map.geojsonUrl,
            dataType: 'json',
            data: $.extend({
                bbox: [west, southWest.lat, east, northEast.lat].join(","),
                context: context
            }, etalage.map.geojsonParams || {}, etalage.map.currentPoiId ? {current: etalage.map.currentPoiId} : {}),
            success: function (data) {
                if (parseInt(data.properties.context) !== context) {
                    return;
                }
                setGeoJSONData(data);
            },
            traditional: true
        });
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
        currentPoiId: null,
        geojsonLayer: null,
        geojsonParams: null,
        geojsonUrl: null,
        layerByPoiId: null,
        markersUrl: null,
        singleMarkerMap: singleMarkerMap,
        tileUrlTemplate: null
    };
})(jQuery);

