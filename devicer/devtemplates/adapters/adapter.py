# -*- encode utf-8 -*-

import os
import re
import string
import subprocess
from datetime import datetime

PRINTABLE = set(string.printable)


class Adapter(object):

    def __init__(self, address, port, **options):
        self.address = address
        self.port = port
        self.timeout = 10
        self._resp = None
        self._ping = None
        self._log = []
        for option, value in options.items():
            setattr(self, option, value)

    def log(self, data, prefix='recv'):
        self._log.append((datetime.now().__str__(), prefix, data))

    def get_log(self):
        def lines(_log):
            for l in _log:
                data = l[2]
                try: data = data.decode('utf-8', 'replace')
                except AttributeError: pass
                if l[1] == 'send':
                    yield '%s %s: %r' % (l[0], l[1].upper(), data)
                else:
                    yield '%s %s:\n%s' % (l[0], l[1].upper(), self._output(data))
        return list(lines(self._log))

    def ping(self, address=None, count=3, timeout=2):
        if address is None:
            address = self.address
        ping = "ping -c %d -W %d %s" % (count, timeout, address)
        self.log(ping, 'send')
        proc = subprocess.Popen(ping, shell=True, stdout=subprocess.PIPE)
        proc.output = proc.communicate()
        self.log(proc.output[0])
        return proc

    def disconnect(self):
        raise NotImplementedError

    def connect(self):
        raise NotImplementedError

    def start_prompt(self):
        raise NotImplementedError

    def send(self):
        raise NotImplementedError

    def expect(self):
        raise NotImplementedError

    def _output(self, output):
        output = ''.join(filter(lambda x: x in PRINTABLE, tuple(output)))
        output = output.replace('\r', '')
        return output.strip()

    def _format_output(self, output):
        return output

    def format_output(self, output):
        output = self._output(output)
        # experiment
        output = re.sub(r'^.*?\n','',output)
        output = re.sub(r'\n+.*?$','',output)
        #
        output = self._format_output(output)
        return output.strip()
