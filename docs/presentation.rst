Etalage presentation
====================

Etalage is a part of `Comarquage.fr`_ solution.

It is the cartographic front-end page. Providing a **widget** wich can be implemented on any web pages of any websites
despite technologies used.

.. _Comarquage.fr: http://www.comarquage.fr


Structure
---------

This project don't use any known framework. It's structure diverge from pylons/pyramid project byt everything used in
the project is writen within the project.

Metadata files:

* COPYING
* README.md

Then, distutils files:

* setup.cfg
* setup.py

In those two files, you'll find usefull informations, and most important the **entry point**
This **entry point** will be followed my Apache mod_wsgi::

    entry_points = """
        [paste.app_factory]
        main = etalage.application:make_app
        """,

This lead us in file `etalage/application.py` where the **make_app** method take configuration file in parameter and
ubild a WSGI Middlewares pipe.

.. FIXME Explain middleware pipes or find a link to add here

Environment
-----------

In the **make_app** method, you'll find a particular call to **load_environment**.

This functions consists of a big `biryani <http://gitorious.org/biryani>`_ converter wich transform raw configuration
variables into a clean dict with usable values. It'll ensure that every information needed is correctly given to the
process in order to run correctly.

A second converter is called in case some configuration variable had to be computed with previous ones.

In the same files you'll find logging, errors handler, templates and databases configurations, all set globally in
**Etalage modules**

* Errors are using the standard **weberror ErrorMiddleware**
* Logging configuration uses the standart **logging** module of python
* Templates uses `**Mako templates** <http://www.makotemplates.org/>`_
* Databases uses… see the next pages about databases.


Specific important files
------------------------

Some file are very important in the project, knowing them can save you a large amount of time !


development.ini
~~~~~~~~~~~~~~~

This is the *default* configuration files when you're in development mode. You'll need to adjust the content to make
**Etalage** works but it reflect the minimal setting requirements.


etalage/contexts.py
~~~~~~~~~~~~~~~~~~~

In this file is defined the **Context** class. This object is really important cause it will be pass in every call for
every method of the project.

In each **controllers**, the first instruction is to build a **Context** object calles **ctx** to acquire all request
data and application environement.

We use this object to store the `**Webob Request** <http://webob.readthedocs.org/en/latest/modules/webob.html>`_ itself
and other usefull resources like **translator** method or **session** based storage.


etalage/conv.py
~~~~~~~~~~~~~~~

Central system of **Etalage**. All converter are regrouped in this files, it means that a lot of specific code are
written in it and it need to perfectly understand what a **biryani converter** is to read it.

.. FIXME Refer to biryani pages


etalage/urls.py
~~~~~~~~~~~~~~~

You'll find **Etalage** router here. Once again, you don't have any framework in this project, the *router* too is
writen within the project and can be found here.


etalage/wsgihelpers.py
~~~~~~~~~~~~~~~~~~~~~~

Set of function used to build errors responses to clients.
