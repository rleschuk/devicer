# -*- encode utf-8 -*-

import re
import time
import socket
import selectors
from telnetlib import Telnet, _TelnetSelector
from time import monotonic as _time

from .. import exceptions
from .adapter import Adapter


class TelnetAdapter(Adapter, Telnet):

    def __init__(self, address, port=23, **kwargs):
        Telnet.__init__(self)
        super().__init__(address, port, **kwargs)
        self._start_prompt = None

    def connect(self):
        self.disconnect()
        try:
            if self._ping is None:
                self._ping = self.ping(self.address)
            if self._ping.returncode != 0:
                raise exceptions.ICMPError()
            self.open(self.address, self.port, self.timeout)
        except socket.timeout:
            raise exceptions.SocketTimeout()
        except ConnectionRefusedError:
            raise exceptions.ConnectError('connection refused')

    def disconnect(self):
        self.close()

    def start_prompt(self, sleep=10):
        if self._start_prompt is None:
            self.connect()
            for _ in range(sleep):
                time.sleep(1)
                self._start_prompt = self.read_very_eager().decode('utf-8', 'replace')
                if len(self._start_prompt) > 0:
                    break
        return self._start_prompt

    def send(self, line, end=None, logmask=None):
        self.log(line if logmask is None else str(logmask) * len(line), 'send')
        self.write((line + ('\r' if end is None else end)).encode('utf-8'))

    def expect(self, regex, timeout=None):
        timeout = timeout or self.timeout
        if not isinstance(regex, list):
            regex = [regex]
        indices = range(len(regex))
        for i in indices:
            if not hasattr(regex[i], "search"):
                regex[i] = re.compile(regex[i])
        if timeout is not None:
            deadline = _time() + timeout
        with _TelnetSelector() as selector:
            selector.register(self, selectors.EVENT_READ)
            while not self.eof:
                self.process_rawq()
                for i in indices:
                    m = regex[i].search(self.cookedq.decode('utf-8', 'replace'))
                    if m:
                        e = m.end()
                        text = self.cookedq[:e]
                        self.cookedq = self.cookedq[e:]
                        self.log(text)
                        return (i, m, text)
                if timeout is not None:
                    ready = selector.select(timeout)
                    timeout = deadline - _time()
                    if not ready:
                        if timeout < 0:
                            break
                        else:
                            continue
                self.fill_rawq()
        text = self.read_very_lazy()
        if not text and self.eof:
            raise EOFError
        self.log(text)
        return (-1, None, text)
