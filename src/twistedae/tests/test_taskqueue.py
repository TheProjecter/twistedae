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
import twistedae.taskqueue_stub
import twisted.trial.unittest


class TestCase(twisted.trial.unittest.TestCase):
    """Testing the twistedae task queue."""

    def setUp(self):
        """Register twistedae's task queue API proxy stub."""

        google.appengine.api.apiproxy_stub_map.apiproxy = \
                    google.appengine.api.apiproxy_stub_map.APIProxyStubMap()
        taskqueue = twistedae.taskqueue_stub.TaskQueueServiceStub(
            root_path='.')
        google.appengine.api.apiproxy_stub_map.apiproxy.RegisterStub(
            'taskqueue', taskqueue)

    def testAddingTask(self):
        """Test for adding a task."""

        google.appengine.api.labs.taskqueue.add(url='/run')
