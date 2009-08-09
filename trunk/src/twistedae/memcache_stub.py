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
"""Memcache integration."""

import google.appengine.api.apiproxy_stub
import google.appengine.api.memcache.memcache_service_pb
import pylibmc

MemcacheSetResponse      = (google.appengine.api.memcache.memcache_service_pb.
                            MemcacheSetResponse)
MemcacheSetRequest       = (google.appengine.api.memcache.memcache_service_pb.
                            MemcacheSetRequest)
MemcacheIncrementRequest = (google.appengine.api.memcache.memcache_service_pb.
                            MemcacheIncrementRequest)
MemcacheDeleteResponse   = (google.appengine.api.memcache.memcache_service_pb.
                            MemcacheDeleteResponse)


class MemcacheServiceStub(google.appengine.api.apiproxy_stub.APIProxyStub):
    """Memcache service stub.

    This stub uses memcached to store data.
    """

    def __init__(self, service_name='memcache'):
        """Initializes memcache service stub.

        Args:
            service_name: Service name expected for all calls.
        """
        super(MemcacheServiceStub, self).__init__(service_name)
        self._cache = pylibmc.Client(["127.0.0.1:11211"])

    def _Dynamic_Get(self, request, response):
        """Implementation of MemcacheService::Get().

        Args:
            request: A MemcacheGetRequest.
            response: A MemcacheGetResponse.
        """
        for key in set(request.key_list()):
            item = response.add_item()
            item.set_key(key)
            value = self._cache.get(key)
            item.set_value(value)

    def _Dynamic_Set(self, request, response):
        """Implementation of MemcacheService::Set().

        Args:
            request: A MemcacheSetRequest.
            response: A MemcacheSetResponse.
        """
        for item in request.item_list():
            key = item.key()
            set_policy = item.set_policy()
            old_entry = self._cache.get(key)
            set_status = MemcacheSetResponse.NOT_STORED
            if ((set_policy == MemcacheSetRequest.SET) or
                (set_policy == MemcacheSetRequest.ADD and old_entry is None) or
                (set_policy == MemcacheSetRequest.REPLACE and
                 old_entry is not None)):

                if (old_entry is None or set_policy == MemcacheSetRequest.SET):
                    self._cache.set(key, item.value())
                    set_status = MemcacheSetResponse.STORED

            response.add_set_status(set_status)

    def _Dynamic_Delete(self, request, response):
        """Implementation of MemcacheService::Delete().

        Args:
            request: A MemcacheDeleteRequest.
            response: A MemcacheDeleteResponse.
        """

        raise NotImplementedError

    def _Dynamic_Increment(self, request, response):
        """Implementation of MemcacheService::Increment().

        Args:
            request: A MemcacheIncrementRequest.
            response: A MemcacheIncrementResponse.
        """

        raise NotImplementedError
