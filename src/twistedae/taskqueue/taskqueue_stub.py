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
"""Task queue API proxy stub."""

from amqplib import client_0_8 as amqp
import google.appengine.api.apiproxy_stub
import google.appengine.api.labs.taskqueue.taskqueue_service_pb
import google.appengine.api.labs.taskqueue.taskqueue_stub
import google.appengine.api.urlfetch
import google.appengine.runtime.apiproxy_errors
import logging
import simplejson
import socket


MAX_RETRIES = 1


class TaskQueueServiceStub(google.appengine.api.apiproxy_stub.APIProxyStub):
    """Task queue service stub."""

    pyaml = google.appengine.api.labs.taskqueue.taskqueue_stub._ParseQueueYaml

    def __init__(self, service_name='taskqueue', root_path=None):
        super(TaskQueueServiceStub, self).__init__(service_name)
        self.next_task_id = 1
        self.root_path = root_path
        self.conn = None
        self.channel = None

    def __del__(self):
        if self.channel is not None:
            self.channel.close()
        if self.conn is not None:
            self.conn.close()

    def connect(self):
        self.conn = amqp.Connection(
            host="localhost:5672",
            userid="guest",
            password="guest",
            virtual_host="/",
            insist=False)
        self.channel = self.conn.channel()

    def _ValidQueue(self, queue_name):
        if queue_name == 'default':
            return True
        queue_info = self.pyaml(self.root_path)
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

        task = dict(
            name=request.task_name(),
            url=request.url(),
            method=request.method(),
            eta=request.eta_usec()/1000000,
            payload=request.body(),
            queue=request.queue_name()
        )

        msg = amqp.Message(simplejson.dumps(task))
        msg.properties["delivery_mode"] = 2
        retries = 0
        while retries <= MAX_RETRIES:
            try:
                self.channel.basic_publish(
                    msg, exchange="taskqueue", routing_key="worker")
                break
            except Exception, err_obj:
                retries += 1
                if retries > MAX_RETRIES:
                    raise Exception, err_obj
                if isinstance(err_obj, socket.error):
                    logging.error("queue server not reachable. retrying...")
                self.connect()

        return

    def GetQueues(self):
        """Gets all the applications's queues.

        Returns:
            A list of dictionaries, where each dictionary contains one queue's
            attributes.
        """
        queues = []

        return queues