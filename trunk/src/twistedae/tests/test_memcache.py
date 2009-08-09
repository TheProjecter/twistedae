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
import google.appengine.api.memcache
import twistedae.memcache_stub
import twisted.trial.unittest


class MemcacheTestCase(twisted.trial.unittest.TestCase):
    """Testing the twistedae memcache."""

    def setUp(self):
        """Register twistedae's memcache API proxy stub."""

        google.appengine.api.apiproxy_stub_map.apiproxy = \
                    google.appengine.api.apiproxy_stub_map.APIProxyStubMap()

        #google.appengine.api.apiproxy_stub_map.apiproxy.RegisterStub(
        #    'memcache', twistedae.memcache_stub.MemcacheServiceStub())

        google.appengine.api.apiproxy_stub_map.apiproxy.RegisterStub('memcache',
            google.appengine.api.memcache.memcache_stub.MemcacheServiceStub())

        self.stub = google.appengine.api.apiproxy_stub_map.apiproxy.GetStub(
            'memcache')

    def testCachingItem(self):
        """Simple in-memory caching."""

        foo = [0, 1, 2, 3]
        google.appengine.api.memcache.add('foo', foo, 10)
        assert google.appengine.api.memcache.get('foo') == foo
