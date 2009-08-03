# -*- coding: utf-8 -*-
#
# Copyright 2007 Google Inc., 2009 Tobias Rodäbel
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


import base64
import google.appengine.api.apiproxy_stub
import google.appengine.api.urlfetch
from google.appengine.api.labs.taskqueue import taskqueue_service_pb
from google.appengine.api.labs.taskqueue import taskqueue_stub
import google.appengine.runtime.apiproxy_errors
import logging
import taskqueue
import twisted.internet.reactor

DEFAULT_RATE        = '5.00/s'
DEFAULT_BUCKET_SIZE = 5

_CompareEta         = taskqueue_stub._CompareEta
_FormatEta          = taskqueue_stub._FormatEta
_EtaDelta           = taskqueue_stub._EtaDelta


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

        tasks = self.taskqueues.setdefault(request.queue_name(), [])
        tasks.append(request)
        tasks.sort(_CompareEta)

        self.taskqueue_service.schedule(request)

        return

    def GetQueues(self):
        """Gets all the applications's queues.

        Returns:
          A list of dictionaries, where each dictionary contains one queue's
          attributes.
        """

        queues = []
        queue_info = self.queue_yaml_parser(self.root_path)
        has_default = False
        if queue_info and queue_info.queue:
            for entry in queue_info.queue:
                if entry.name == 'default':
                    has_default = True
                queue = {}
                queues.append(queue)
                queue['name'] = entry.name
                queue['max_rate'] = entry.rate
                if entry.bucket_size:
                    queue['bucket_size'] = entry.bucket_size
                else:
                    queue['bucket_size'] = DEFAULT_BUCKET_SIZE

                tasks = self.taskqueues.setdefault(entry.name, [])
                if tasks:
                    queue['oldest_task'] = _FormatEta(tasks[0].eta_usec())
                    queue['eta_delta'] = _EtaDelta(tasks[0].eta_usec())
                else:
                    queue['oldest_task'] = ''
                queue['tasks_in_queue'] = len(tasks)

        if not has_default:
            queue = {}
            queues.append(queue)
            queue['name'] = 'default'
            queue['max_rate'] = DEFAULT_RATE
            queue['bucket_size'] = DEFAULT_BUCKET_SIZE

            tasks = self.taskqueues.get('default', [])
            if tasks:
                queue['oldest_task'] = _FormatEta(tasks[0].eta_usec())
                queue['eta_delta'] = _EtaDelta(tasks[0].eta_usec())
            else:
                queue['oldest_task'] = ''
            queue['tasks_in_queue'] = len(tasks)
        return queues

    def GetTasks(self, queue_name):
        """Gets a queue's tasks.

        Args:
          queue_name: Queue's name to return tasks for.

        Returns:
          A list of dictionaries, where each dictionary contains one task's
          attributes.
        """

        tasks = self.taskqueues.get(queue_name, [])
        result_tasks = []
        for task_request in tasks:
            task = {}
            result_tasks.append(task)
            task['name'] = task_request.task_name()
            task['url'] = task_request.url()
            method = task_request.method()
            if (method == taskqueue_service_pb.TaskQueueAddRequest.GET):
                task['method'] = 'GET'
            elif (method == taskqueue_service_pb.TaskQueueAddRequest.POST):
                task['method'] = 'POST'
            elif (method == taskqueue_service_pb.TaskQueueAddRequest.HEAD):
                task['method'] = 'HEAD'
            elif (method == taskqueue_service_pb.TaskQueueAddRequest.PUT):
                task['method'] = 'PUT'
            elif (method == taskqueue_service_pb.TaskQueueAddRequest.DELETE):
                task['method'] = 'DELETE'

            task['eta'] = _FormatEta(task_request.eta_usec())
            task['eta_delta'] = _EtaDelta(task_request.eta_usec())
            task['body'] = base64.b64encode(task_request.body())
            headers = google.appengine.api.urlfetch._CaselessDict()
            task['headers'] = headers
            for req_header in task_request.header_list():
                headers[req_header.key()] = req_header.value()

            headers['X-AppEngine-QueueName'] = queue_name
            headers['X-AppEngine-TaskName'] = task['name']
            headers['X-AppEngine-TaskRetryCount'] = '0'
            headers['X-AppEngine-Development-Payload'] = '1'
            headers['Content-Length'] = len(task['body'])
            headers['Content-Type'] = headers.get(
                'Content-Type', 'application/octet-stream')

        return result_tasks

    def DeleteTask(self, queue_name, task_name):
        """Deletes a task from a queue.

        Args:
          queue_name: the name of the queue to delete the task from.
          task_name: the name of the task to delete.
        """

        raise NotImplementedError

    def FlushQueue(self, queue_name):
        """Removes all tasks from a queue.

        Args:
          queue_name: the name of the queue to remove tasks from.
        """

        raise NotImplementedError
