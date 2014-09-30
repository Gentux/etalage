Base de données
===============


**Etalage** implement a proof of concept of databases loaded in RAM. This has the inconvenient to be very slow at
startup and consume lots of memory.

But, in the other hand, it grant us with a high speed research trhough data and all related actions are verry fast too.


MongoDB
-------

.. FIXME Add links href

The standard data source for **etalage** is the `Petitpois <https://gitorious.org/infos-pratiques/petitpois.git>`_
*POIs* collection and the `Territoria2 <https://gitorious.org/infos-pratiques/territoria.git>`_ *territories*
collections. Both collections are stored within a `**MongoDB** <https://www.mongodb.org/>`_ Database.

Those two collections are entirely browsed in **etalage.ramdb.load** method, called in the **load_environment** at
startup.

RAMDB
-----

Browsed data are partially stored in **python dict**. You can found the following indexes in **Etalage**

Categories related indexes:

* categories_slug_by_tag_slug
* categories_slug_by_word
* category_by_slug
* category_slug_by_pivot_code

Territories related indexes:

* schema_title_by_name
* territories_id_by_ancestor_id
* territories_id_by_postal_distribution
* territory_by_id
* territory_id_by_kind_code

POIs related indexes:

* ids_by_category_slug
* ids_by_competence_territory_id
* ids_by_begin_datetime
* ids_by_end_datetime
* ids_by_last_update_datetime
* ids_by_parent_id
* ids_by_presence_territory_id
* ids_by_word
* slug_by_id

And two specials **dict**:

* indexed_ids : A set of all ids, used to verify if a POI is correctly loaded
* instance_by_id : Data are directly stored in that dict in case the database is small enough to enter in RAM
