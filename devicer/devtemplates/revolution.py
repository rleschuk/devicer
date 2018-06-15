
import os
import re

from .cisco import Cisco
from .adapters import TelnetAdapter
from . import exceptions


class Revolution(Cisco):

    @staticmethod
    def check_template(attrs):
        return (attrs.vendor and 'revolution' in attrs.vendor) or\
               (attrs.vendor and 'infinet' in attrs.vendor) or\
               (attrs.model and 'revolution' in attrs.model) or\
               (attrs.model and 'infinet' in attrs.model) or\
               (attrs.start_prompt and\
                re.search('WANFleX', attrs.start_prompt))

    def __init__(self, attrs, **options):
        super().__init__(attrs, **options)
        self.username = attrs.username or 'admin'
        self.password = attrs.password or ''
        self.prompt_username = re.compile(r'login:.*?$', re.I)
        self.prompt_password = re.compile(r'word:.*?$')
        self.prompt_cli = re.compile(r'>\s+\r')
        self.prompt_more = re.compile(r'-- more --', re.I)
        self._adapter = TelnetAdapter(str(attrs.address), timeout=10, **options)
        self._adapter._format_output = self.format_output

    def format_output(self, output):
        output = self._format_output(output)
        #output = re.sub(r'^.*?\n','',output)
        #output = re.sub(r'\n+.*?$','',output)
        return output

    def send_password(self, attempt=1, **kwargs):
        self.adapter.send(kwargs.get('password', self.password), logmask='*')
        self.adapter._resp = self.adapter.expect([
            self.prompt_cli,
            self.prompt_username, self.prompt_password
        ])
        if self.adapter._resp[0] == 0:
            self.logged = True
            return self.adapter._resp
        elif self.adapter._resp[0] in [1, 2]:
            if attempt > 1:
                raise exceptions.LoginError('incorrect username or password')
            else:
                return self.login(attempt=attempt + 1,
                    username=os.getenv('TAC_USERNAME', 'root'),
                    password=os.getenv('TAC_PASSWORD', ''))
        else:
            raise exceptions.PromptTimeout('prompt timeout: %r' %\
                self.prompt_cli.pattern if hasattr(self.prompt_cli, 'pattern')\
                                        else self.prompt_cli)
