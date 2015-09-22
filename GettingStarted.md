# Before you install #

## Python interpreter ##

It is possible to run twistedae's Python parts with Python 2.5.x and 2.6.x, but
it is recommended to use a version which is supported by the Google App Engine
SDK. See http://code.google.com/intl/de/appengine/docs/python/overview.html for
further information.

It is advisable to install twistedae into a
[virtualenv](http://pypi.python.org/pypi/virtualenv) in order to obtain
isolation from any “system” packages you’ve got installed in your Python
version.

## Google App Engine SDK ##

You don't have to install the Google App Engine SDK, because
[zc.buildout](http://pypi.python.org/pypi/zc.buildout) will install it for you.

## Other requirements ##

Most of the required libraries and programs will be installed by zc.buildout.
See the [buildout.cfg](http://code.google.com/p/twistedae/source/browse/trunk/buildout.cfg) file.

The buildout needs Python and the tools contained in /bin and /usr/bin of a
standard installation of the Linux operating environment. You should ensure
that these directories are on your PATH and following programs can be found:

  * Python 2.5.2+ (3.x is not supported!)
  * gcc and g++
  * make

(_Note:_ On Debian Lenny libncurses5-dev and libssl-dev are required.)

# Installation #

  * Check out the sources:
```
  $ svn checkout http://twistedae.googlecode.com/svn/trunk/ twistedae
```

  * Build the stack:
```
  $ python bootstrap.py
  $ ./bin/buildout
```

  * Configure the demo application:
```
  $ ./bin/apptool parts/demo/
```

  * Let the cloud fly:
```
  $ ./bin/supervisord
```

  * Access the application using a web browser with the following URL: http://localhost:8080/

  * Run the supervisor console:
```
  $ ./bin/supervisorctl -c etc/supervisord.conf -u admin -p admin
```

When all services are up and running, the supervisor console shows something
like this:
```
  appserver                        RUNNING    pid 74751, uptime 0:00:18
  memcached                        RUNNING    pid 74750, uptime 0:00:18
  mongod                           RUNNING    pid 74748, uptime 0:00:18
  nginx                            RUNNING    pid 74753, uptime 0:00:18
  rabbitmq                         RUNNING    pid 74749, uptime 0:00:18
  taskworker                       RUNNING    pid 74782, uptime 0:00:12
```