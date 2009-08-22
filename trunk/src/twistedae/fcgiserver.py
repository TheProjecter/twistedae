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

import logging
import optparse
import os
import sys
import twistedae


def main():
    """Initializes the server."""

    usage = "usage: %prog [options]"
    op = optparse.OptionParser(usage=usage)
    op.add_option("-d", "--debug", action="store_true", dest="debug",
                  help="run a single fcgi server process in debug mode",
                  default=False)
    op.add_option("--unrestricted", action="store_true", dest="unrestricted",
                  help="run the server without GAE restrictions",
                  default=False)

    (options, args) = op.parse_args()

    logging.basicConfig(
        format='%(levelname)-8s %(asctime)s %(filename)s:%(lineno)s] '
               '%(message)s',
        level=logging.DEBUG)

    app_root = os.environ['APP_ROOT']
    os.chdir(app_root)
    sys.path.append(app_root)

    conf = twistedae.getAppConfig()
    twistedae.setupStubs(conf)

    twistedae.setupRuntimeEnvironment(app_root)

    app = twistedae.getWSGIApplication(conf, options.unrestricted)

    environ = dict(
        APPLICATION_ID=conf.application,
        PATH_TRANSLATED='unknown',
        SERVER_NAME='twistedae',
        SERVER_PORT='8080',
        SERVER_PROTOCOL='HTTP/1.1',
        SERVER_SOFTWARE='twistedae',
        USER=os.getlogin(),
    )

    config = dict(
        environ=environ,
        bindAddress=('127.0.0.1', 8081),
        multiprocess=False
    )

    logging.info("Server starting")

    if not options.debug:
        import flup.server.fcgi_fork
        server_module = flup.server.fcgi_fork
    else:
        import flup.server.fcgi_single
        server_module = flup.server.fcgi_single

    server_module.WSGIServer(app, **config).run()
