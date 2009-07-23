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
"""Simple tcp server implementation."""

import google.appengine.tools.dev_appserver
import logging
import os
import sys
import twistedae.appserver
import twisted.application.internet
import twisted.application.service
import twisted.web.server

# The default port
PORT = 8080

# Setting up our twisted application
application = twisted.application.service.Application('twistedae')

# Disable standard python logging, because we use twited's logging module
logging.disable(logging.INFO)

# We need to start the appserver's thread pool
twistedae.appserver.start()

# Root resource
root = twisted.web.resource.Resource()

# Load and apply configuration
os.chdir(os.environ['APP_PATH'])
sys.path.insert(0, os.environ['APP_PATH'])
conf, matcher = google.appengine.tools.dev_appserver.LoadAppConfig('.', {})
os.environ['APPLICATION_ID'] = conf.application
twistedae.appserver.applyConfigToWSGIResource(conf, root)
twistedae.appserver.setupDatastore(conf.application,
                                   'dev_appserver.datastore',
                                   'dev_appserver.datastore.history',
                                   False, False)

# The main site
site = twisted.web.server.Site(root)

# Serve our application
service = twisted.application.internet.TCPServer(PORT, site)
service.setName('twistedae')
service.setServiceParent(application)
