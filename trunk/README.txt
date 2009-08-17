=====================================
twistedae - Twisted Google App Engine
=====================================

The twistedae project aims at providing a full-featured and productive stack to
run GAE applications. It delivers the parts for building your own scalable App
Engine while staying compatible with Google's API.


The Stack
---------

The default configuration is built upon following services::

  * mongoDB
  * memcached
  * nginx
  * FastCGI
  * supervisor


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

Run the supervisor daemon, which starts and controls all services at once::

  $ ./bin/supervisord

You can access the application using a web browser with the following URL::

  http://localhost:8080/


Testing
-------

Run unit tests by typing (running supervisord required)::

  $ bin/nosetests
