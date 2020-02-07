import argparse
import zmq

from .parser import METHOD_TABLE


class Server(object):
    """ A socket-based server that receives IPC calls from another process.
    """
    def __init__(self, port):
        """ Initialize the socket and bind it to the given port.
        """
        context = zmq.Context.instance()
        self.socket = context.socket(zmq.REP)
        self.socket.bind('tcp://0.0.0.0:%s' % port)

    def process(self):
        """ Receive a message from the socket, process it, and send a reply.
        """
        try:
            msg = self.socket.recv_json()
        except ValueError:
            self.send_error('Invalid message format')
            return

        if 'method' not in msg:
            self.send_error('Invalid message format')
        elif msg['method'] not in METHOD_TABLE:
            self.send_error('No such method')
        else:
            try:
                ret = METHOD_TABLE[msg['method']](*msg.get('args', []))
            except Exception as e:
                self.send_error('Error processing message: %s' % e)
            else:
                self.socket.send_json({
                    'error': False,
                    'ret': ret
                })

    def send_error(self, error):
        """ Send an error message to the socket.
        """
        self.socket.send_json({
            'error': error
        })

    def shutdown(self):
        """ Shutdown the server and close the underlying socket.
        """
        self.socket.close()

    def __del__(self):
        """ On deletion, shutdown the server.
        """
        self.shutdown()


def main():
    parser = argparse.ArgumentParser(description='rparse')
    parser.add_argument('port', type=int)
    args = parser.parse_args()

    server = Server(args.port)
    while True:
        server.process()
