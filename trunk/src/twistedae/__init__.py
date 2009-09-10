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

import StringIO
import capability_stub
import errno
import google.appengine.api.apiproxy_stub_map
import google.appengine.api.appinfo
import google.appengine.api.mail_stub
import google.appengine.api.urlfetch_stub
import google.appengine.api.user_service_stub
import google.appengine.api.xmpp.xmpp_service_stub
import google.appengine.ext.webapp
import imp
import memcache_stub
import mongodb.datastore_mongo_stub
import os
import pickle
import re
import runpy
import sys
import taskqueue.taskqueue_stub


def getAppConfig(directory='.'):
    """Returns a configuration object."""

    path = os.path.join(directory, 'app.yaml')
    conf_file = open(path, 'r')

    try:
        conf = google.appengine.api.appinfo.LoadSingleAppInfo(conf_file)
    except IOError:
        raise RuntimeError
    finally:
        conf_file.close()

    return conf


def initURLMapping(conf):
    """Returns a list with mappings URL to module name and script."""

    login = google.appengine.api.appinfo.URLMap()
    login.url = '/login'
    login.script = '$PYTHON_LIB/twistedae/handlers/login.py'
    login.login = 'required'

    url_mapping = []

    for handler in [login] + conf.handlers:
        script = handler.script
        regexp = handler.url
        if script != None:
            if script.startswith('$PYTHON_LIB'):
                module = script.replace('/', '.')[12:][0:len(script)-15]
            else:
                module_path, unused_ext = os.path.splitext(script)
                module = module_path.replace(os.sep, '.')

            if not regexp.startswith('^'):
                regexp = '^' + regexp
            if not regexp.endswith('$'):
                regexp += '$'
            compiled = re.compile(regexp)
            path = os.path.join(os.getcwd(), script)
            url_mapping.append((compiled, module, path))
 
    return url_mapping


class NotImplementedClass(object):
    """Provided by classes not implemented in the restricted environment."""

    @staticmethod
    def _raise(*args, **kw):
        raise NotImplementedError('This class/method is not available.')

    __init__ = _raise


def RestrictedOpen(filename, flags, mode=0777):
  """Restricted implementation of os.open."""

  raise OSError(errno.EPERM, "Operation not permitted", filename)


class RestrictedFile(file):
    """Restricted file class which provides read-only access."""

    _ALLOWED_MODES = frozenset(['r', 'rb', 'U', 'rU'])

    def __init__(self, filename, mode='r', bufsize=-1, **kw):
        if mode not in RestrictedFile._ALLOWED_MODES:
            raise IOError('invalid mode: %s' % mode)

        super(RestrictedFile, self).__init__(filename, mode, bufsize, **kw)


# See http://code.google.com/appengine/docs/python/runtime.html#Pure_Python for
# more information on restrictions in the GAE Python runtime environment.

RESTRICTED_NAMES = {
    'open': RestrictedOpen,
}

RESTRICTED_MODULES = {
    '__builtin__': {'buffer': NotImplementedClass,
                    'file': RestrictedFile,
                    'open': RestrictedOpen
                    },
    'cPickle': pickle.__dict__,
    'ftplib': None,
    'imp': None,
    'select': None,
    'socket': None,
    'tempfile': {'TemporaryFile': StringIO.StringIO},
    'marshal': None,
    'os': {'environ': os.environ,
           'path': os.path
           },
    }


class RestrictedImportHook(object):
    """Import hook to replace registered modules with restricted variants."""
    
    _restricted = set()

    @classmethod
    def add(cls, fullname):
        cls._restricted.add(fullname)

    def find_module(self, fullname, path=None):
        if path: return
        if fullname in self._restricted:
            return self

    def load_module(self, fullname):
        new_module = imp.new_module(fullname)
        new_module.__dict__.update(RESTRICTED_MODULES[fullname] or dict())
        return new_module


class DisallowExtensionsImportHook(object):
    """Simple import hook to disallow import of C extensions."""

    def find_module(self, fullname, path=None):
        if path:
            parts = fullname.split('.')
            submodule = parts.pop()
            try:
                result = imp.find_module(submodule, path)
            except ImportError:
                pass
            else:
                source_file, pathname, description = result
                suffix, mode, file_type = description
                if file_type == imp.C_EXTENSION:
                    raise ImportError
        return


def setupCapability():
    """Sets up cabability service."""

    google.appengine.api.apiproxy_stub_map.apiproxy.RegisterStub(
        'capability_service', capability_stub.CapabilityServiceStub())


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
        taskqueue.taskqueue_stub.TaskQueueServiceStub(root_path=root_path))


def setupURLFetchService():
    """Sets up urlfetch."""

    google.appengine.api.apiproxy_stub_map.apiproxy.RegisterStub('urlfetch',
        google.appengine.api.urlfetch_stub.URLFetchServiceStub())


def setupUserService():
    """Sets up user service."""

    google.appengine.api.apiproxy_stub_map.apiproxy.RegisterStub('user',
        google.appengine.api.user_service_stub.UserServiceStub(
            login_url='/login?=%s', logout_url='/logout?=%s'))


def setupXMPP():
    """Sets up XMPP."""

    google.appengine.api.apiproxy_stub_map.apiproxy.RegisterStub('xmpp',
        google.appengine.api.xmpp.xmpp_service_stub.XmppServiceStub())


def setupStubs(conf):
    """Sets up api proxy stubs."""

    google.appengine.api.apiproxy_stub_map.apiproxy = \
        google.appengine.api.apiproxy_stub_map.APIProxyStubMap()

    setupCapability()

    setupDatastore(conf.application,
                   'dev_appserver.datastore',
                   'dev_appserver.datastore.history',
                   False, False)

    setupMail('localhost', 25, '', '')

    setupMemcache()

    setupTaskQueue()

    setupURLFetchService()

    setupUserService()

    setupXMPP()
