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


from google.appengine.api import apiproxy_stub
from google.appengine.api.labs.taskqueue import taskqueue_service_pb
from google.appengine.api.labs.taskqueue import taskqueue_stub


def _CompareEta(a, b):
    """Python sort comparator for task ETAs."""

    if a.eta_usec() > b.eta_usec():
      return 1
    if a.eta_usec() < b.eta_usec():
      return -1
    return 0


class TaskQueueServiceStub(apiproxy_stub.APIProxyStub):
    """Twisted based task queue service stub."""

    queue_yaml_parser = taskqueue_stub._ParseQueueYaml

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
            raise apiproxy_errors.ApplicationError(
                taskqueue_service_pb.TaskQueueServiceError.UNKNOWN_QUEUE)
            return

        if not request.task_name():
            request.set_task_name('task%d' % self.next_task_id)
            self.next_task_id += 1

        tasks = self.taskqueues.setdefault(request.queue_name(), [])
        tasks.append(request)
        tasks.sort(_CompareEta)
        return

    def GetQueues(self):
        """Gets all the applications's queues.

        Returns:
          A list of dictionaries, where each dictionary contains one queue's
          attributes.
        """

        queues = []
        return queues

    def GetTasks(self, queue_name):
        """Gets a queue's tasks.

        Args:
          queue_name: Queue's name to return tasks for.

        Returns:
          A list of dictionaries, where each dictionary contains one task's
          attributes.
        """

        tasks = []
        return tasks

    def DeleteTask(self, queue_name, task_name):
        """Deletes a task from a queue.

        Args:
          queue_name: the name of the queue to delete the task from.
          task_name: the name of the task to delete.
        """

    def FlushQueue(self, queue_name):
        """Removes all tasks from a queue.

        Args:
          queue_name: the name of the queue to remove tasks from.
        """
