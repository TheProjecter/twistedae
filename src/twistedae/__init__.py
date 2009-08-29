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
import errno
import google.appengine.api.apiproxy_stub_map
import google.appengine.api.appinfo
import google.appengine.api.mail_stub
import google.appengine.api.urlfetch_stub
import google.appengine.ext.webapp
import google.appengine.tools.dev_appserver
import imp
import memcache_stub
import mimetypes
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


_MODULE_CACHE = {}

# See http://code.google.com/appengine/docs/python/runtime.html#Pure_Python for
# more information on restrictions in the GAE Python runtime environment.

_RESTRICTED_NAMES = {
    'open': RestrictedOpen,
}

_RESTRICTED_MODULES = {
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
        new_module.__dict__.update(_RESTRICTED_MODULES[fullname] or dict())
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


class WSGIApplication(google.appengine.ext.webapp.WSGIApplication):
    """The WSGI application."""

    def __init__(self, debug=True):
        super(WSGIApplication, self).__init__([], debug)

    def __call__(self, environ, response):
        """Returns the output of all handlers.

        We have to adjust os.environ in same way GAE does. Namely, it must
        provide the request parameters.
        """

        # Evaluate path translated
        for pattern, handler in self._url_mapping:
            if re.match(pattern, environ['PATH_INFO']) is not None:
                environ['PATH_TRANSLATED'] = (
                    _MODULE_CACHE.get(handler.__module__).get('__file__'))
                break

        # Copy original encironment and clear it for re-initialization
        orig_env = dict(os.environ)
        os.environ.clear()

        # Create a new applicaten environment without wsgi.* keys
        app_env = dict(environ)
        for key in ('wsgi.errors', 'wsgi.input', 'wsgi.multiprocess',
                    'wsgi.multithread', 'wsgi.run_once', 'wsgi.url_scheme',
                    'wsgi.version'):
            del app_env[key]

        # Copy the application environment to os.environment
        os.environ.update(app_env)
        try:
            result = super(WSGIApplication, self).__call__(environ, response)
        finally:
            os.environ.clear()
            os.environ.update(orig_env)

        return result or ['']


def getWSGIApplication(conf, unrestricted=False):
    """Returns a master WSGI application object."""

    apps = []

    if not unrestricted:
        [RestrictedImportHook.add(m) for m in _RESTRICTED_MODULES]
        restricted_names = _RESTRICTED_NAMES
        sys.meta_path = [RestrictedImportHook(),
                         DisallowExtensionsImportHook()]
    else:
        restricted_names = dict()

    for handler in conf.handlers:
        script = handler.script
        if script != None:
            base, ext = os.path.splitext(os.path.basename(script))

            if base in _MODULE_CACHE:
                mod = _MODULE_CACHE[base]
            else:
                modules = dict(sys.modules)
                for m in _RESTRICTED_MODULES:
                    if m in sys.modules:
                        del sys.modules[m]
                if hasattr(sys, 'path_importer_cache'):
                    sys.path_importer_cache.clear()

                try:
                    mod = runpy.run_module(
                        base,
                        init_globals=restricted_names,
                        run_name=None)
                finally:
                    del sys.modules
                    sys.modules = dict(modules)

                _MODULE_CACHE[base] = mod

            app_class = google.appengine.ext.webapp.WSGIApplication
            apps += [mod[v] for v in mod if isinstance(mod[v], app_class)]

    sys.meta_path = []

    app = WSGIApplication()

    for a in apps:
        for k in ['_handler_map', '_pattern_map', '_url_mapping']:
            o = getattr(app, k)
            if isinstance(o, dict):
                o.update(getattr(a, k))
            elif isinstance(o, list):
                o += getattr(a, k)

    return app


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
