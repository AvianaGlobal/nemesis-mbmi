import os
import subprocess
import zmq
from socket import socket


class RParser(object):
    """ An object that uses an external process to parse and validate R code.
    """
    @classmethod
    def get_free_port(cls):
        """ Get a free port to use for communication with the external process.
        """
        sock = socket()
        sock.bind(('', 0))

        port = sock.getsockname()[1]
        sock.close()
        return port

    def __init__(self):
        port = RParser.get_free_port()

        # Start external process
        startupinfo = None
        if os.name == 'nt':
            # Don't show a console in Windows.
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        self._proc = subprocess.Popen([
            'rparse', str(port)
        ], startupinfo=startupinfo)

        context = zmq.Context.instance()
        self.socket = context.socket(zmq.REQ)
        self.socket.connect('tcp://127.0.0.1:%s' % port)

    def __del__(self):
        """ End the external process when this object is deleted.
        """
        if os.name == 'nt':
            # On Windows, calling terminate() does not kill the grandchild
            # processes that the R executable spawns.
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            subprocess.call([
                'taskkill', '/pid', str(self._proc.pid), '/T', '/F'
            ], shell=False, startupinfo=startupinfo)

        else:
            self._proc.terminate()

    def call(self, method, *args):
        self.socket.send_json({
            'method': method,
            'args': args
        })

        msg = self.socket.recv_json()
        if msg['error']:
            raise Exception(
                'Error communicating with parser process: {}'.format(msg['error']))

        return msg['ret']


RParser = RParser()


def is_expression(text):
    """ Check whether a string of R code is a single, valid expression.
    """
    return RParser.call('is_expression', text)