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

import base64
import cPickle
import google.appengine.api.apiproxy_stub
import google.appengine.api.memcache.memcache_service_pb
import os
import pylibmc
import simplejson

DEFAULT_ADDR = '127.0.0.1'
DEFAULT_PORT = 11211

MemcacheSetResponse      = (google.appengine.api.memcache.memcache_service_pb.
                            MemcacheSetResponse)
MemcacheSetRequest       = (google.appengine.api.memcache.memcache_service_pb.
                            MemcacheSetRequest)
MemcacheIncrementRequest = (google.appengine.api.memcache.memcache_service_pb.
                            MemcacheIncrementRequest)
MemcacheDeleteResponse   = (google.appengine.api.memcache.memcache_service_pb.
                            MemcacheDeleteResponse)


def getKey(key, namespace=None):
    """Returns a key."""

    app_id = os.environ.get('APPLICATION_ID', '')
    if app_id: app_id += '.'

    if namespace:
        key = '%(namespace)s.%(key)s' % locals()
    key = '%(app_id)s%(key)s' % locals()
    return base64.b64encode(key)


class MemcacheServiceStub(google.appengine.api.apiproxy_stub.APIProxyStub):
    """Memcache service stub.

    This stub uses memcached to store data.
    """

    def __init__(self, config=None, service_name='memcache'):
        """Initializes memcache service stub.

        Args:
            config: Dictionary containing configuration parameters.
            service_name: Service name expected for all calls.
        """
        super(MemcacheServiceStub, self).__init__(service_name)
        if config is None:
            config = dict(
                addr=DEFAULT_ADDR,
                port=DEFAULT_PORT,
            )
        self._cache = pylibmc.Client(['%(addr)s:%(port)i' % config])

    def _Dynamic_Get(self, request, response):
        """Implementation of MemcacheService::Get().

        Args:
            request: A MemcacheGetRequest.
            response: A MemcacheGetResponse.
        """
        for key in set(request.key_list()):
            value = self._cache.get(getKey(key, request.name_space()))
            if value is None:
                continue
            else:
                flags = 0
                stored_flags, stored_value = simplejson.loads(value)
                flags |= stored_flags
                if flags == google.appengine.api.memcache.TYPE_UNICODE:
                    set_value = str(stored_value.encode('utf-8'))
                else:
                    set_value = str(stored_value)
                item = response.add_item()
                item.set_key(getKey(key, request.name_space()))
                item.set_value(set_value)
                item.set_flags(flags)

    def _Dynamic_Set(self, request, response):
        """Implementation of MemcacheService::Set().

        Args:
            request: A MemcacheSetRequest.
            response: A MemcacheSetResponse.
        """
        for item in request.item_list():
            key = getKey(item.key(), request.name_space())
            set_policy = item.set_policy()
            old_entry = self._cache.get(key)
            set_status = MemcacheSetResponse.NOT_STORED
            flags = item.flags()
            if flags == google.appengine.api.memcache.TYPE_PICKLED:
                value = unicode(cPickle.dumps(cPickle.loads(item.value())))
            else:
                value = item.value()
            set_value = simplejson.dumps([flags, value])

            if ((set_policy == MemcacheSetRequest.SET) or
                (set_policy == MemcacheSetRequest.ADD and old_entry is None) or
                (set_policy == MemcacheSetRequest.REPLACE and
                 old_entry is not None)):

                if (old_entry is None or set_policy == MemcacheSetRequest.SET):
                    self._cache.set(key, set_value, item.expiration_time())
                    set_status = MemcacheSetResponse.STORED
                elif (set_policy == MemcacheSetRequest.REPLACE):
                    self._cache.replace(key, set_value)

            response.add_set_status(set_status)

    def _Dynamic_Delete(self, request, response):
        """Implementation of MemcacheService::Delete().

        Args:
            request: A MemcacheDeleteRequest.
            response: A MemcacheDeleteResponse.
        """
        for item in request.item_list():
            key = getKey(item.key(), request.name_space())
            entry = self._cache.get(key)
            delete_status = MemcacheDeleteResponse.DELETED

            if entry is None:
                delete_status = MemcacheDeleteResponse.NOT_FOUND
            else:
                self._cache.delete(key)

            response.add_delete_status(delete_status)

    def _Dynamic_Increment(self, request, response):
        """Implementation of MemcacheService::Increment().

        Args:
            request: A MemcacheIncrementRequest.
            response: A MemcacheIncrementResponse.
        """
        key = getKey(request.key(), request.name_space())
        value = self._cache.get(key)
        if value is None:
            flags, stored_value = (google.appengine.api.memcache.TYPE_INT, '0')
        else:
            flags, stored_value = simplejson.loads(value)

        if flags == google.appengine.api.memcache.TYPE_INT:
            new_value = int(stored_value)
        elif flags == google.appengine.api.memcache.TYPE_LONG:
            new_value = long(stored_value)
        if request.direction() == MemcacheIncrementRequest.INCREMENT:
            new_value += request.delta()
        elif request.direction() == MemcacheIncrementRequest.DECREMENT:
            new_value -= request.delta()

        new_stored_value = simplejson.dumps([flags, str(new_value)])
        self._cache.set(key, new_stored_value)

        response.set_new_value(new_value)

    def _Dynamic_FlushAll(self, request, response):
        """Implementation of MemcacheService::FlushAll().

        Args:
            request: A MemcacheFlushRequest.
            response: A MemcacheFlushResponse.
        """

        self._cache.flush_all()

    def _Dynamic_Stats(self, request, response):
        """Implementation of MemcacheService::Stats().

        Args:
            request: A MemcacheStatsRequest.
            response: A MemcacheStatsResponse.
        """

        raise NotImplementedError
