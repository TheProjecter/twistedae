=====================================
twistedae - Twisted Google App Engine
=====================================

The twistedae project aims at providing a full-featured and productive stack to
run Google App Engine applications. It delivers the parts for building your own
scalable App Engine while staying compatible with Google's API.


The Stack
---------

The key components are::

  * Google App Engine SDK - http://code.google.com/appengine
  * mongoDB - http://www.mongodb.org
  * memcached - http://www.danga.com/memcached/
  * RabbitMQ - http://www.rabbitmq.com
  * FastCGI - http://www.fastcgi.com
  * nginx - http://nginx.net/
  * Supervisor - http://supervisord.org

All these components will be automatically installed by zc.buildout into an
isolated directory tree on your development machine. If you want to remove the
twistedae development environment you just have to delete this single
directory.


Copyright and license
---------------------

Copyright 2009 Tobias Rodäbel

This software is released under the Apache License, Version 2.0. You may obtain
a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0


Running the cloud out of the box
--------------------------------

Build and the whole stack by typing the following commands::

  $ python bootstrap.py
  $ ./bin/buildout

Configure the demo application::

  $ ./bin/apptool parts/demo/

Run the supervisor daemon, which starts and controls all services at once::

  $ ./bin/supervisord

You can access the application using a web browser with the following URL::

  http://localhost:8080/


Loading some data into the demo application
-------------------------------------------

The appcfg tool (original script from the SDK) can upload and download data to
and from your application's datastore.

An already prepared configuration is placed in the demo application source
directory and can be tested by typing::

  $ bin/appcfg upload_data --config_file=src/demo/note_loader.py --filename=src/demo/notes.csv --kind=Note --url=http://localhost:8080/remote_api parts/demo/


Google's development application server
---------------------------------------

You may recognize the dev_appserver script in the bin directory after building
the environment. It's included to check whether your application runs with the
installed original SDK.

It can be used as expected::

  $ bin/dev_appserver parts/demo


Testing
-------

Stop all appserver processes before running the test suite. The tests expect
following services up and running::

  * memcached
  * mongod
  * intid
  * rabbitmq

Run unit tests by typing::

  $ bin/nosetests
