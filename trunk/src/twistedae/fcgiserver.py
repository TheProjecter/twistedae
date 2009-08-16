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
"""Simple FastCGI server implementation."""

import google.appengine.tools.dev_appserver
import logging
import os
import sys
import twistedae.appserver
import flup.server.fcgi_fork


def getWSGIApplication(conf):
    """Returns a master WSGI application object."""

    apps = []

    for handler in conf.handlers:
        script = handler.script
        if script != None:
            base, ext = os.path.splitext(os.path.basename(script))
            mod = __import__(base)
            apps += [getattr(mod, v) for v in mod.__dict__
                     if isinstance(getattr(mod, v),
                                   google.appengine.ext.webapp.WSGIApplication)]

    master = google.appengine.ext.webapp.WSGIApplication([], debug=True)

    for a in apps:
        for k in ['_handler_map', '_pattern_map', '_url_mapping']:
            o = getattr(master, k)
            if isinstance(o, dict):
                o.update(getattr(a, k))
            elif isinstance(o, list):
                o += getattr(a, k)

    return master


def main():
    """Initializes the server."""

    os.chdir(os.environ['APP_PATH'])
    sys.path.insert(0, os.environ['APP_PATH'])
    conf, matcher = google.appengine.tools.dev_appserver.LoadAppConfig('.', {})
    os.environ['APPLICATION_ID'] = conf.application
    twistedae.appserver.setupStubs(conf)

    app = getWSGIApplication(conf)

    environ = dict(
        SERVER_NAME='WSGIServer',
        SERVER_PORT=8081,
        SERVER_PROTOCOL='wsgi'
    )

    config = dict(
        environ=environ,
        bindAddress=('127.0.0.1', 8081),
        multiprocess=False
    )

    flup.server.fcgi_fork.WSGIServer(app, **config).run()
