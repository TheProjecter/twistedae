========================================
twistedae - Google App Engine on Twisted
========================================

The twistedae project aims at running the Google App Engine SDK on top of the
Twisted framework. Concurrent request handling is just one of the benefits. It
delivers the parts for building your own scalable app engine while staying
compatible with Google's API. This allows the development of applications that
can either run in your own or in Google's cloud.

At this point the project is a proof of concept. It basically replaces the
SDK's BaseHTTPServer with twisted.web and includes 10gen's datastore stub for
MongoDB. With twistedae it is totally unnecessary to patch the Google App
Engine SDK.


Running the server out of the box
---------------------------------

Build and run the server by typing the following commands::

  $ python bootstrap.py
  $ ./bin/buildout

Run the application server::

  $ ./bin/appserver parts/demo/

Alternatively you can use twistd to start the service::

  $ ./bin/twistd -ny src/twistedae/service.py

Then access the application using a web browser with the following URL::

  http://localhost:8080/


Testing
-------

Run unit tests by typing::

  $ bin/trial twistedae.tests.service


Installing
----------

To install twistedae type::

  $ python setup.py install
