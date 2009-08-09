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
"""Unit tests for memcache."""

import google.appengine.api.apiproxy_stub_map
import google.appengine.api.memcache.memcache_stub
import time
import twistedae.memcache_stub
import twisted.trial.unittest


class MemcacheTestCase(twisted.trial.unittest.TestCase):
    """Testing the twistedae memcache."""

    def setUp(self):
        """Register twistedae's memcache API proxy stub."""

        google.appengine.api.apiproxy_stub_map.apiproxy = \
            google.appengine.api.apiproxy_stub_map.APIProxyStubMap()

        # Uncomment to run tests against twistedae's memcache service stub.
        # Requires running memcached.
        #
        #google.appengine.api.apiproxy_stub_map.apiproxy.RegisterStub(
        #    'memcache', twistedae.memcache_stub.MemcacheServiceStub())

        google.appengine.api.apiproxy_stub_map.apiproxy.RegisterStub(
            'memcache',
            google.appengine.api.memcache.memcache_stub.MemcacheServiceStub())

        self.stub = google.appengine.api.apiproxy_stub_map.apiproxy.GetStub(
            'memcache')

    def testAddingItem(self):
        """Simple in-memory caching."""

        foo = "bar"
        google.appengine.api.memcache.add('foo', foo)
        assert google.appengine.api.memcache.get('foo') == foo

    def testDeletingItem(self):
        """Tries to set and delete a key and its value."""

        data = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
        google.appengine.api.memcache.set('data', data)
        assert google.appengine.api.memcache.get('data') == data
        google.appengine.api.memcache.delete('data')
        assert google.appengine.api.memcache.get('data') == None

    def testExpirationTime(self):
        """Adds an expireing item."""

        bye = "Good bye!"
        google.appengine.api.memcache.add('bye', bye, 1)
        assert google.appengine.api.memcache.get('bye') == bye
        time.sleep(1)
        assert google.appengine.api.memcache.get('bye') == None

    def testReplaceItem(self):
        """Adds and replaces a cached item."""

        first = "Little pig, little pig, let me come in!"
        second = "Not by the hair on my chinny-chin-chin!"
        google.appengine.api.memcache.add('first', first)
        assert google.appengine.api.memcache.get('first') == first
        google.appengine.api.memcache.replace('first', second)
        assert google.appengine.api.memcache.get('first') == second

    def testFlushAll(self):
        """Flushes the whole cache."""

        spam = "Hello, World!"
        google.appengine.api.memcache.set('spam', spam)
        assert google.appengine.api.memcache.get('spam') == spam
        google.appengine.api.memcache.flush_all()
        assert google.appengine.api.memcache.get('spam') == None
