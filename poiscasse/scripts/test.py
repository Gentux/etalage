#! /usr/bin/env python
# -*- coding: utf-8 -*-


import logging
import os
import pprint
import sys
import time

from bson.objectid import ObjectId
import paste.deploy

from poiscasse import conv, environment, model, ramdb


app_name = os.path.splitext(os.path.basename(__file__))[0]
log = logging.getLogger(app_name)


def main(argv = None):
    if argv is None:
        argv = sys.argv
    arguments = argv[1:]
    logging.basicConfig(level = logging.DEBUG, stream = sys.stdout)
    site_conf = paste.deploy.appconfig('config:%s' % os.path.abspath(arguments[0]))
    environment.load_environment(site_conf.global_conf, site_conf.local_conf)

    print 'ram_pois_by_id:', len(ramdb.ram_pois_by_id)
    print 'pois_id_by_territory_kind_code:', len(ramdb.pois_id_by_territory_kind_code)
    print 'pois_id_by_word:', len(ramdb.pois_id_by_word)
    print 'Categories:', len(ramdb.categories_by_slug)
    print 'pois_id_by_category_slug:', len(ramdb.pois_id_by_category_slug)

    print "ramdb.iter_pois_id()"
    print "===================="
    print
    start_time = time.time()
    print len(list(ramdb.iter_pois_id()))
    print time.time() - start_time
    print

    print "ramdb.iter_pois_id(category_slug = u'mairie')"
    print "============================================="
    print
    start_time = time.time()
    print len(ramdb.iter_pois_id(category_slug = u'mairie'))
    print time.time() - start_time
    print

    print "ramdb.iter_pois_id(term = u'Mairie')"
    print "===================================="
    print
    start_time = time.time()
    print len(ramdb.iter_pois_id(term = u'Mairie'))
    print time.time() - start_time
    print

    print "ramdb.iter_pois_id(territory_kind_code = (u'DepartmentOfFrance', u'92'))"
    print "========================================================================"
    print
    start_time = time.time()
    print len(ramdb.iter_pois_id(territory_kind_code = (u'DepartmentOfFrance', u'92')))
    print time.time() - start_time
    print

    print "ramdb.iter_pois_id(category_slug = u'mairie', term = u'Mairie')"
    print "==============================================================="
    print
    start_time = time.time()
    print len(ramdb.iter_pois_id(category_slug = u'mairie', term = u'Mairie'))
    print time.time() - start_time
    print

    print "ramdb.iter_pois_id(category_slug = u'mairie', term = u'Préf')"
    print "============================================================="
    print
    start_time = time.time()
    print len(ramdb.iter_pois_id(category_slug = u'mairie', term = u'Préf'))
    print time.time() - start_time
    print

    print "ramdb.iter_pois_id(category_slug = u'mairie', term = u'Mairie', territory_kind_code = (u'DepartmentOfFrance', u'92'))"
    print "====================================================================================================================="
    print
    start_time = time.time()
    print len(ramdb.iter_pois_id(category_slug = u'mairie', term = u'Mairie', territory_kind_code = (u'DepartmentOfFrance', u'92')))
    print time.time() - start_time
    print

    return 0


if __name__ == "__main__":
    sys.exit(main())
