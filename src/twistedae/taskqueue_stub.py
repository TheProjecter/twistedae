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
"""Task queue implementation."""

import google.appengine.api.apiproxy_stub
from google.appengine.api.labs.taskqueue import taskqueue_service_pb
from google.appengine.api.labs.taskqueue import taskqueue_stub
import google.appengine.runtime.apiproxy_errors
import taskqueue


class TaskQueueServiceStub(google.appengine.api.apiproxy_stub.APIProxyStub):
    """Twisted based task queue service stub."""

    queue_yaml_parser = taskqueue_stub._ParseQueueYaml
    taskqueue_service = taskqueue.Service()

    def __init__(self, service_name='taskqueue', root_path=None):
        super(TaskQueueServiceStub, self).__init__(service_name)
        self.taskqueues = {}
        self.next_task_id = 1
        self.root_path = root_path

    def _ValidQueue(self, queue_name):
        if queue_name == 'default':
            return True
        queue_info = self.queue_yaml_parser(self.root_path)
        if queue_info and queue_info.queue:
            for entry in queue_info.queue:
                if entry.name == queue_name:
                    return True
        return False

    def _Dynamic_Add(self, request, unused_response):
        if not self._ValidQueue(request.queue_name()):
            raise google.appengine.runtime.apiproxy_errors.ApplicationError(
                taskqueue_service_pb.TaskQueueServiceError.UNKNOWN_QUEUE)
            return

        if not request.task_name():
            request.set_task_name('task%d' % self.next_task_id)
            self.next_task_id += 1

        self.taskqueue_service.schedule(request)
        return
