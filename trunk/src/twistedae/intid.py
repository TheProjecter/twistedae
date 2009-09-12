import pymongo.connection
import socket
import threading

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(("", 9009))
server_socket.listen(5)

lock = threading.Lock()

db = pymongo.connection.Connection()['intid']

def increment(delta=1):
    """ Returns incremented intid."""
    intid = db.intid
    result = intid.find_one()
    if result is None:
        obj_id = intid.save({u'i': 0})
        result = intid.find_one({u'_id': obj_id})
    value = result.get(u'i') + delta
    intid.update(result, {"$set": {u'i': value}})
    return value

class Client(threading.Thread):
    def __init__(self, sock):
        super(Client, self).__init__()
        self.socket = sock

    def run(self):
        while 1:
            data = self.socket.recv(3)
            if data == 'int':
                with lock:
                    self.socket.send(str(increment()))
            elif data == 'con':
                self.socket.send('ack')
            else:
                self.socket.close()
                break

def main():
    while 1:
        socketfd, address = server_socket.accept()
        client = Client(socketfd)
        client.run()
