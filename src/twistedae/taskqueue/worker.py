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
"""Task worker implementation."""

from amqplib import client_0_8 as amqp
import logging
import simplejson
import urllib2


def recv_callback(msg):
    """Decodes received message and processes task."""

    task = simplejson.loads(msg.body)
    req = urllib2.Request(
        url='http://127.0.0.1:8080%s' % task['url'],
        data=task['payload'],
        headers={'Content-Type': 'text/plain'}
        )
    try:
        res = urllib2.urlopen(req)
    except urllib2.URLError, err_obj:
        logging.error("failed task %s (reason: %s)" % (task, err_obj))
        return
    if res.code != 200:
        logging.error("failed task %s (response code: %i" % (task, res.code))


def main():
    """The main function."""

    logging.basicConfig(
        format='%(levelname)-8s %(asctime)s %(filename)s:%(lineno)s] '
               '%(message)s',
        level=logging.DEBUG)

    conn = amqp.Connection(
        host="localhost:5672",
        userid="guest",
        password="guest",
        virtual_host="/",
        insist=False)

    chan = conn.channel()

    chan.queue_declare(
        queue="tasks", durable=True, exclusive=False, auto_delete=False)
    chan.exchange_declare(
        exchange="taskqueue", type="direct", durable=True, auto_delete=False)
    chan.queue_bind(queue="tasks", exchange="taskqueue", routing_key="worker")

    chan.basic_consume(
        queue='tasks', no_ack=True, callback=recv_callback, consumer_tag="test")

    try:
        while True:
            chan.wait()
    finally:
        chan.basic_cancel("test")

        chan.close()
        conn.close()


if __name__ == "__main__":
    main()
