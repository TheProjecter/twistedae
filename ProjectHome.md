# Important: twistedae is now renamed to TyphoonAE http://typhoonae.googlecode.com, because we want to avoid confusion with the great Twisted framework http://twistedmatrix.com. #

The twistedae project aims at providing a full-featured and productive serving environment to
run [Google App Engine](http://code.google.com/appengine) (Python) applications. It delivers the parts for building your own scalable App Engine while staying compatible with Google's API.

(_Important note:_ The current development status is **pre-alpha**. At this point it is not guaranteed that any GAE application will run completely error-free on twistedae. So, stay patient please!)

See the [Product Roadmap](RoadMap.md) for further details on planned features.


## The Stack ##

The key components are:

  * Google App Engine SDK http://code.google.com/appengine
  * mongoDB http://www.mongodb.org
  * memcached http://www.danga.com/memcached/
  * RabbitMQ http://www.rabbitmq.com
  * FastCGI http://www.fastcgi.com
  * nginx http://nginx.net/
  * Supervisor http://supervisord.org

All these components will be automatically installed by [zc.buildout](http://www.buildout.org) into an isolated directory tree on your development machine. If you want to remove the twistedae development environment you just have to delete this single directory.

For some good reasons why using zc.buildout you may want to read [this post](http://renesd.blogspot.com/2008/05/buildout-tutorial-buildout-howto.html) or watch [this talk](http://us.pycon.org/2009/conference/schedule/event/48/).

The configuration above is tested on OS X Leopard, Snow Leopard with Python 2.6.2 and Debian Lenny. Several parts can be replaced by editing the [buildout.cfg](http://code.google.com/p/twistedae/source/browse/trunk/buildout.cfg) file. _But you should really know what you're doing._

## Architecture Overview ##

![http://twistedae.googlecode.com/svn/trunk/doc/twistedae.gif](http://twistedae.googlecode.com/svn/trunk/doc/twistedae.gif)