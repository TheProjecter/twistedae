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
"""Helper functions for registering App Engine API proxy stubs."""

import google.appengine.api.apiproxy_stub_map
import google.appengine.api.mail_stub
import google.appengine.api.urlfetch_stub
import google.appengine.ext.webapp
import google.appengine.tools.dev_appserver
import memcache_stub
import mongodb.datastore_mongo_stub
import os
import taskqueue_stub


def getAppConfig(directory='.'):
    """Returns a configuration object."""

    conf, matcher = google.appengine.tools.dev_appserver.LoadAppConfig(
        directory, {})

    return conf


def setupDatastore(app_id, datastore, history, require_indexes, trusted):
    """Sets up datastore."""

    tmp_dir = os.environ['TMPDIR']
    if not os.path.exists(tmp_dir):
        os.mkdir(tmp_dir)

    datastore_path = os.path.join(tmp_dir, datastore)
    history_path = os.path.join(tmp_dir, history)

    datastore = mongodb.datastore_mongo_stub.DatastoreMongoStub(
        app_id, datastore_path, history_path, require_indexes=require_indexes)

    google.appengine.api.apiproxy_stub_map.apiproxy.RegisterStub(
        'datastore_v3', datastore)


def setupMail(smtp_host, smtp_port, smtp_user, smtp_password,
              enable_sendmail=False, show_mail_body=False):
    """Sets up mail."""

    google.appengine.api.apiproxy_stub_map.apiproxy.RegisterStub('mail',
        google.appengine.api.mail_stub.MailServiceStub(
            smtp_host, smtp_port, smtp_user, smtp_password,
            enable_sendmail=enable_sendmail, show_mail_body=show_mail_body))


def setupMemcache():
    """Sets up memcache."""

    google.appengine.api.apiproxy_stub_map.apiproxy.RegisterStub('memcache',
        memcache_stub.MemcacheServiceStub())


def setupTaskQueue(root_path='.'):
    """Sets up task queue."""

    google.appengine.api.apiproxy_stub_map.apiproxy.RegisterStub('taskqueue',
        taskqueue_stub.TaskQueueServiceStub(root_path=root_path))


def setupURLFetchStub():
    """Sets up urlfetch."""

    google.appengine.api.apiproxy_stub_map.apiproxy.RegisterStub('urlfetch',
        google.appengine.api.urlfetch_stub.URLFetchServiceStub())


def setupStubs(conf):
    """Sets up api proxy stubs."""

    google.appengine.api.apiproxy_stub_map.apiproxy = \
                    google.appengine.api.apiproxy_stub_map.APIProxyStubMap()

    setupDatastore(conf.application,
                   'dev_appserver.datastore',
                   'dev_appserver.datastore.history',
                   False, False)

    setupMail('localhost', 25, '', '')

    setupMemcache()

    setupTaskQueue()

    setupURLFetchStub()


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
