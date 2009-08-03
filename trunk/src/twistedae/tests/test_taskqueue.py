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
"""Unit tests for task queue."""

import google.appengine.api.apiproxy_stub_map
import google.appengine.api.labs.taskqueue
import os
import twistedae.taskqueue
import twistedae.taskqueue_stub
import twisted.trial.unittest
import zope.interface


class TaskQueueServiceMock(object):
    """Simulates a task queue service for testing."""

    zope.interface.implements(twistedae.taskqueue.ITaskQueueService)

    @staticmethod
    def schedule(request):
        pass


class TaskQueueTestCase(twisted.trial.unittest.TestCase):
    """Testing the twistedae task queue."""

    def setUp(self):
        """Register twistedae's task queue API proxy stub."""

        google.appengine.api.apiproxy_stub_map.apiproxy = \
                    google.appengine.api.apiproxy_stub_map.APIProxyStubMap()

        taskqueue = twistedae.taskqueue_stub.TaskQueueServiceStub(
            root_path=os.path.dirname(__file__))
        google.appengine.api.apiproxy_stub_map.apiproxy.RegisterStub(
            'taskqueue', taskqueue)

        taskqueue.taskqueue_service = TaskQueueServiceMock()

        #taskqueue = (google.appengine.api.labs.taskqueue.taskqueue_stub.
        #             TaskQueueServiceStub(root_path=os.path.dirname(__file__)))
        #google.appengine.api.apiproxy_stub_map.apiproxy.RegisterStub(
        #    'taskqueue', taskqueue)

        self.stub = google.appengine.api.apiproxy_stub_map.apiproxy.GetStub(
            'taskqueue')

    def testAddingTasks(self):
        """Tests for adding tasks."""

        google.appengine.api.labs.taskqueue.add(url='/run')
        assert self.stub.GetTasks('default')[0].get('url') == '/run'
        google.appengine.api.labs.taskqueue.Queue('test').add(
            google.appengine.api.labs.taskqueue.Task(url='/foo'))
        assert self.stub.GetTasks('test')[0].get('url') == '/foo'
        assert self.stub.GetQueues()[0]['name'] == 'default'
        assert self.stub.GetQueues()[0]['tasks_in_queue'] == 1
