
import os
import re

from .cisco import Cisco
from .adapters import TelnetAdapter
from . import exceptions


class Mikrotik(Cisco):

    @staticmethod
    def check_template(attrs):
        return (attrs.vendor and 'mikrotik' in attrs.vendor) or\
               (attrs.model and 'mikrotik' in attrs.model) or\
               (attrs.start_prompt and\
                re.search('MikroTik', attrs.start_prompt))

    def __init__(self, attrs, **options):
        super().__init__(attrs, **options)
        self.username = attrs.username or 'admin'
        self.password = attrs.password or ''
        self.prompt_username = re.compile(r'login:.*?$', re.I)
        self.prompt_password = re.compile(r'word:.*?$')
        self.prompt_cli = re.compile(r'>\s+\r')
        self.prompt_more = re.compile(r'\[Q quit\|', re.I)
        self._adapter = TelnetAdapter(str(attrs.address), timeout=15, **options)
        self._adapter._format_output = self._format_output

    def send_username(self, **kwargs):
        self.adapter.send(kwargs.get('username', self.username) + '+c')
        self.adapter._resp = self.adapter.expect(self.prompt_password)
        if self.adapter._resp[0] == 0:
            return self.send_password(**kwargs)
        else:
            raise exceptions.PromptTimeout('prompt timeout: %r' %\
                self.prompt_password.pattern if hasattr(self.prompt_password, 'pattern')\
                                             else self.prompt_password)

    def send_password(self, **kwargs):
        self.adapter.send(kwargs.get('password', self.password))
        self.adapter._resp = self.adapter.expect([self.prompt_cli, self.prompt_username],
            timeout=self.adapter.timeout + 5)
        if self.adapter._resp[0] == 0:
            self.logged = True
            return self.adapter._resp
        elif self.adapter._resp[0] == 1:
            raise exceptions.LoginError('incorrect username or password')
        else:
            raise exceptions.PromptTimeout('prompt timeout: %r' %\
                self.prompt_cli.pattern if hasattr(self.prompt_cli, 'pattern')\
                                        else self.prompt_cli)
