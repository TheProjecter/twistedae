# -*- coding: utf-8 -*-
#
# Copyright 2009 Tobias Rodäbel
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Simple appserver implementation."""

import mongodb.datastore_mongo_stub
import google.appengine.api.apiproxy_stub_map
import google.appengine.api.datastore_file_stub
import google.appengine.tools.dev_appserver
import logging
import os
import sys
import twisted.internet.reactor
import twisted.python.hook
import twisted.python.threadpool
import twisted.web.http
import twisted.web.resource
import twisted.web.server
import twisted.web.static
import twisted.web.wsgi

# The default port
PORT = 8080

logging.basicConfig(
    format='%(levelname)-8s %(asctime)s %(filename)s:%(lineno)s] %(message)s',
    level=logging.DEBUG)

_pool = twisted.python.threadpool.ThreadPool()


def start():
    """Starts the thread pool."""

    twisted.internet.reactor.addSystemEventTrigger('after', 'shutdown', stop)
    _pool.start()


def stop():
    """Will be called when terminating."""

    logging.info("Server terminating")
    _pool.stop()


def requestLogHook(factory, request):
    """Writes log info for requests."""

    format = r'%(ip)s "%(method)s %(path)s %(protocol)s" %(code)s'
    ip       = request.getClientIP()
    method   = request.method
    path     = request.path
    protocol = request.clientproto
    code     = request.code

    logging.info(format % locals())

twisted.python.hook.addPost(twisted.web.http.HTTPFactory,
                            "log", requestLogHook)


def getWSGIResource(name):
    """Returns a suitable WSGI resource."""

    mod = __import__(name)
    res = twisted.web.wsgi.WSGIResource(
                        twisted.internet.reactor, _pool, getattr(mod, name))
    return res


def applyConfigToWSGIResource(conf, resource):
    """Applies the configuration to the resource."""

    # Register handlers for static files
    for handler in conf.handlers:
        static_dir = handler.static_dir
        script = handler.script
        if static_dir != None:
            resource.putChild(static_dir, twisted.web.static.File(static_dir))
        elif script != None:
            base, ext = os.path.splitext(os.path.basename(script))
            resource.putChild('', getWSGIResource(base))


def setupDatastore(app_id, datastore, history, require_indexes, trusted):
    """Sets up datastore."""

    tmp_dir = os.environ['TMPDIR']
    if not os.path.exists(tmp_dir):
        os.mkdir(tmp_dir)

    datastore_path = os.path.join(tmp_dir, datastore)
    history_path = os.path.join(tmp_dir, history)

    google.appengine.api.apiproxy_stub_map.apiproxy = \
                    google.appengine.api.apiproxy_stub_map.APIProxyStubMap()

    # We use the SDK's file datastore implementation.
    datastore = google.appengine.api.datastore_file_stub.DatastoreFileStub(
        app_id, datastore_path, history_path, require_indexes=require_indexes,
        trusted=trusted)
    #datastore = mongodb.datastore_mongo_stub.DatastoreMongoStub(
    #    app_id, datastore_path, history_path, require_indexes=require_indexes)
    google.appengine.api.apiproxy_stub_map.apiproxy.RegisterStub(
        'datastore_v3', datastore)


def main():
    """The main function the appserver sctipt uses to serve our application."""

    # Checking command line arguments
    # TODO: We need a better command line interface here
    if len(sys.argv) < 2:
        sys.stderr.write("usage: %s <path>\n" % os.path.basename(sys.argv[0]))
        sys.exit(1)

    # Point the current working direcotry to the given path
    os.chdir(sys.argv[1])
    sys.path.insert(0, os.getcwd())

    logging.info("Server: twistedae")

    # Start the thread pool
    start()

    root = twisted.web.resource.Resource()

    # Read the configuration (app.yaml) of a specific application
    conf, matcher = google.appengine.tools.dev_appserver.LoadAppConfig('.', {})

    # Setup application
    os.environ['APPLICATION_ID'] = conf.application
    setupDatastore(conf.application,
                   'dev_appserver.datastore',
                   'dev_appserver.datastore.history',
                   False, False)
    applyConfigToWSGIResource(conf, root)

    # Setup site
    site = twisted.web.server.Site(root)

    # Serve our application
    twisted.internet.reactor.listenTCP(PORT, site)
    twisted.internet.reactor.run()


# TODO: We'll see later whether we need paste or not
def app_factory(global_config, **local_conf):
    """Application factory for paste."""
