# -*- encode utf-8 -*-

import re
import time
import socket
import pexpect

from .. import exceptions
from .adapter import Adapter


class SSHAdapter(Adapter, pexpect.spawn):

    def __init__(self, address, port=23, **kwargs):
        pexpect.spawn.__init__(self, command=None, timeout=self.timeout)
        super().__init__(address, port, **kwargs)
        self._start_prompt = None
        self.__command = ' '.join(['ssh',
            '-o UserKnownHostsFile=/dev/null',
            '-o StrictHostKeyChecking=no',
            '%s@%s' % (username, host)
        ])

    def connect(self):
        self.disconnect()
        #try:
        if not self.ping(self.address):
            raise exceptions.ICMPError()
        self._spawn(self.command)

    def disconnect(self):
        self.close()
