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

import Queue
import datetime
import google.appengine.api.apiproxy_stub
import google.appengine.api.labs.taskqueue.taskqueue_service_pb
import google.appengine.api.labs.taskqueue.taskqueue_stub
import google.appengine.api.urlfetch
import google.appengine.runtime.apiproxy_errors
import threading
import time

NUMBER_OF_WORKERS_PER_QUEUE = 1
PORT = 8080


class Worker(object):
    """Runs within one or more daemonized threads."""

    def __init__(self, queue):
        self.queue = queue
        self.block = True

    def handle_next(self):
        request = self.queue.get(self.block)
        eta = datetime.datetime.fromtimestamp(request.eta_usec()/1000000)
        now = datetime.datetime.utcnow()
        if now > eta:
            response = google.appengine.api.urlfetch.fetch(
                url='http://127.0.0.1:' + str(PORT) + request.url(),
                payload=request.body(),
                method=request.method(),
                headers={'Content-Type': 'text/plain'}
                )
            if response.status_code == 200:
                self.queue.task_done()
        else:
            if not self.queue.empty():
                self.handle_next()
            else:
                time.sleep(0.5)
            self.queue.put(request)

    def __call__(self):
        while True:
            self.handle_next()


class TaskQueueServiceStub(google.appengine.api.apiproxy_stub.APIProxyStub):
    """Task queue service stub."""

    yaml = google.appengine.api.labs.taskqueue.taskqueue_stub._ParseQueueYaml

    def __init__(self, service_name='taskqueue', root_path=None):
        super(TaskQueueServiceStub, self).__init__(service_name)
        self.taskqueues = {}
        self.next_task_id = 1
        self.root_path = root_path

    def _ValidQueue(self, queue_name):
        if queue_name == 'default':
            return True
        queue_info = self.yaml(self.root_path)
        if queue_info and queue_info.queue:
            for entry in queue_info.queue:
                if entry.name == queue_name:
                    return True
        return False

    def _Dynamic_Add(self, request, unused_response):
        if not self._ValidQueue(request.queue_name()):
            raise google.appengine.runtime.apiproxy_errors.ApplicationError(
                google.appengine.api.labs.taskqueue.taskqueue_service_pb.
                TaskQueueServiceError.UNKNOWN_QUEUE)
            return

        if request.queue_name() not in self.taskqueues:
            q = Queue.Queue()
            self.taskqueues[request.queue_name()] = q
            for i in range(NUMBER_OF_WORKERS_PER_QUEUE):
                worker = Worker(q)
                t = threading.Thread(target=worker)
                t.setDaemon(True)
                t.start()
        else:
            q = self.taskqueues[request.queue_name()]

        if not request.task_name():
            request.set_task_name('task%d' % self.next_task_id)
            self.next_task_id += 1

        q.put(request)

        return

    def GetQueues(self):
        """Gets all the applications's queues.

        Returns:
            A list of dictionaries, where each dictionary contains one queue's
            attributes.
        """
        queues = []

        for k in self.taskqueues.keys():
            queues.append(
                dict(
                    name=k,
                    tasks_in_queue=self.taskqueues[k].unfinished_tasks
                    )
                )

        return queues