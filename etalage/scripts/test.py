#! /usr/bin/env python
# -*- coding: utf-8 -*-


import logging
import os
import sys
import time

import paste.deploy

from etalage import conv, environment, model, ramdb


app_name = os.path.splitext(os.path.basename(__file__))[0]
log = logging.getLogger(app_name)


def main(argv = None):
    if argv is None:
        argv = sys.argv
    arguments = argv[1:]
    logging.basicConfig(level = logging.DEBUG, stream = sys.stdout)
    site_conf = paste.deploy.appconfig('config:%s' % os.path.abspath(arguments[0]))
    environment.load_environment(site_conf.global_conf, site_conf.local_conf)

    print 'poi_by_id:', len(ramdb.poi_by_id)
    print 'pois_id_by_presence_territory_id:', len(ramdb.pois_id_by_presence_territory_id)
    print 'pois_id_by_word:', len(ramdb.pois_id_by_word)
    print 'Categories:', len(ramdb.category_by_slug)
    print 'pois_id_by_category_slug:', len(ramdb.pois_id_by_category_slug)

    print "model.Poi.iter_ids()"
    print "===================="
    print
    start_time = time.time()
    print len(list(model.Poi.iter_ids()))
    print time.time() - start_time
    print

    print "model.Poi.iter_ids(categories_slug = [u'mairie'])"
    print "================================================="
    print
    start_time = time.time()
    print len(model.Poi.iter_ids(categories_slug = [u'mairie']))
    print time.time() - start_time
    print

    print "model.Poi.iter_ids(term = u'Mairie')"
    print "===================================="
    print
    start_time = time.time()
    print len(model.Poi.iter_ids(term = u'Mairie'))
    print time.time() - start_time
    print

    print "model.Poi.iter_ids(presence_territory = conv(u'92 HAUTS DE SEINE'))"
    print "==================================================================="
    print
    start_time = time.time()
    print len(list(model.Poi.iter_ids(presence_territory = conv.check(
        conv.input_to_postal_distribution_to_geolocated_territory)(u'92 HAUTS DE SEINE'))))
    print time.time() - start_time
    print

    print "model.Poi.iter_ids(categories_slug = [u'mairie'], term = u'Mairie')"
    print "==================================================================="
    print
    start_time = time.time()
    print len(model.Poi.iter_ids(categories_slug = [u'mairie'], term = u'Mairie'))
    print time.time() - start_time
    print

    print "model.Poi.iter_ids(categories_slug = [u'mairie'], term = u'Préf')"
    print "================================================================="
    print
    start_time = time.time()
    print len(model.Poi.iter_ids(categories_slug = [u'mairie'], term = u'Préf'))
    print time.time() - start_time
    print

    print "model.Poi.iter_ids(categories_slug = ['mairie'], presence_territory = '92 HAUTS DE SEINE', term = 'Mairie')"
    print "==========================================================================================================="
    print
    start_time = time.time()
    print len(list(model.Poi.iter_ids(
        categories_slug = [u'mairie'],
        presence_territory = conv.check(conv.input_to_postal_distribution_to_geolocated_territory)(
            u'92 HAUTS DE SEINE'),
        term = u'Mairie',
        )))
    print time.time() - start_time
    print

    print "conv.pois_to_csv(ramdb.poi_by_id.itervalues())"
    print "=============================================="
    print
    start_time = time.time()
    conv.pois_to_csv(ramdb.poi_by_id.itervalues())
    print time.time() - start_time
    return 0


if __name__ == "__main__":
    sys.exit(main())
