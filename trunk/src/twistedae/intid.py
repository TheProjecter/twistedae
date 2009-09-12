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
"""Simple intid server implementation."""

import logging
import pymongo.connection
import signal
import socket
import threading

logging.basicConfig(
    format='%(levelname)-8s %(asctime)s %(filename)s:%(lineno)s] %(message)s',
    level=logging.INFO)

lock = threading.Lock()
db = pymongo.connection.Connection()['intid']


def increment(delta=1):
    """Returns incremented intid."""

    intid = db.intid
    result = intid.find_one()
    if result is None:
        obj_id = intid.save({u'i': 0})
        result = intid.find_one({u'_id': obj_id})
    value = result.get(u'i') + delta
    intid.update(result, {"$set": {u'i': value}})
    return value


class Worker(threading.Thread):
    """The worker thread."""

    def __init__(self, sock):
        super(Worker, self).__init__()
        self.socket = sock

    def run(self):
        while 1:
            data = self.socket.recv(3)
            if data == 'int':
                lock.acquire()
                self.socket.send(str(increment()))
                lock.release()
            elif data == 'con':
                self.socket.send('ack')
            else:
                self.socket.close()
                break


def main():
    """The main function."""

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("127.0.0.1", 9009))
    server_socket.listen(10)

    logging.info("server starting")

    client_num = 0

    try:
        while 1:
            socketfd, address = server_socket.accept()
            client_num += 1
            logging.info("client %i %s connected" % (client_num, address))
            t = Worker(socketfd)
            t.run()
    finally:
        server_socket.close() 
