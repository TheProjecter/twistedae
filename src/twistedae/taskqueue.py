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
"""Simple task queue implementation."""

import datetime
import google.appengine.api.labs.taskqueue.taskqueue_stub
import google.appengine.api.urlfetch
import logging
import threading
import twisted.internet.reactor
import zope.interface

_EtaDelta = google.appengine.api.labs.taskqueue.taskqueue_stub._EtaDelta


class ITaskQueueService(zope.interface.Interface):
    """The task queue service interface."""

    def schedule(request):
        """Schedules a task for the given request."""


class TaskRunner(threading.Thread):

    def __init__(self, url, data, method):
        threading.Thread.__init__(self)
        self.url = url
        self.data = data
        self.method = method

    def run(self):
        response = google.appengine.api.urlfetch.fetch(
            url=self.url,
            payload=self.data,
            method=self.method,
            headers={'Content-Type': 'text/plain'})
        if response.status_code == 404:
            raise Exception
        return


class Service(object):
    """The task queue service."""

    zope.interface.implements(ITaskQueueService)

    addr = '127.0.0.1'
    port = 8080

    @classmethod
    def _urlopen(cls, request):
        url = 'http://%s:%i%s' % (cls.addr, cls.port, request.url())
        opener = TaskRunner(url, request.body(), request.method())
        opener.start()
        return

    @classmethod
    def schedule(cls, request):
        eta = datetime.datetime.fromtimestamp(request.eta_usec()/1000000)
        now = datetime.datetime.utcnow()
        delta = 0.0
        if eta > now:
            raise NotImplemented
        twisted.internet.reactor.callLater(delta, cls._urlopen, request)
