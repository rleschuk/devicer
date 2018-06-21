# -*- encode utf-8 -*-

import re
import time
import socket
import pexpect

from .. import exceptions
from .adapter import Adapter


class SSHAdapter(Adapter):

    def __init__(self, address, username="root", port=22, **kwargs):
        super().__init__(address, port, **kwargs)
        self._child = None
        self.command = 'ssh %s@%s -o "StrictHostKeyChecking no"' % (username, address)
        self._start_prompt = None

    def connect(self):
        self.disconnect()
        try:
            if self._ping is None:
                self._ping = self.ping(self.address)
            if self._ping.returncode != 0:
                raise exceptions.ICMPError()
            #self.open(self.address, self.port, self.timeout)
            self._child = pexpect.spawn(self.command, encoding='utf8')
        except socket.timeout:
            raise exceptions.SocketTimeout()
        except ConnectionRefusedError:
            raise exceptions.ConnectError('connection refused')

    def disconnect(self):
        try: self._child.close()
        except: pass

    def send(self, line, end=None, logmask=None):
        self.log(line if logmask is None else str(logmask) * len(line), 'send')
        self._child.write(line + ('\r' if end is None else end))

    def expect(self, regex, timeout=None):
        timeout = timeout or self.timeout
        if not isinstance(regex, list):
            regex = [regex]
        indices = range(len(regex))
        for i in indices:
            if not hasattr(regex[i], "search"):
                regex[i] = re.compile(regex[i])
        index = -1
        reg = None
        before = ''
        response = index
        try:
            response = self._child.expect(regex, timeout=timeout)
        except pexpect.TIMEOUT:
            pass
        except pexpect.EOF:
            raise Exception('expect eof')
        index = response
        try: reg = self._child.match.group()
        except: pass
        before = self._child.before
        self.log(before + reg)
        return (index, reg, before)
