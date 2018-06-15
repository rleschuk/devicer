
import os
import re

from .default import DevTemplate
from .adapters import TelnetAdapter
from . import exceptions


class Cisco(DevTemplate):

    @staticmethod
    def check_template(attrs):
        return (attrs.vendor and 'cisco' in attrs.vendor) or\
               (attrs.model and 'cisco' in attrs.model) or\
               (attrs.start_prompt and\
                re.search('\nUser Access Verification\r\n\r\nUsername:', attrs.start_prompt))

    def __init__(self, attrs, **options):
        super().__init__(attrs)
        self.username = attrs.username or os.getenv('TAC_USERNAME', 'cisco')
        self.password = attrs.password or os.getenv('TAC_PASSWORD', 'cisco')
        self.prompt_username = re.compile(r'name:.*?$')
        self.prompt_password = re.compile(r'word:.*?$')
        self.prompt_cli = re.compile(r'#$')
        self.prompt_more = re.compile(r' --more--\s+', re.I)
        self._adapter = TelnetAdapter(str(attrs.address), **options)
        self._adapter._format_output = self._format_output

    def _format_output(self, output):
        return self.prompt_more.sub('', output)

    def login(self, attempt=1, **kwargs):
        self.adapter.connect()
        try:
            self.adapter._resp = self.adapter.expect(self.prompt_username)
            self.adapter._start_prompt = self.adapter._resp[2]
        except (EOFError, BrokenPipeError) as err:
            if attempt > self.max_attempt: raise err
            return self.login(attempt=attempt+1, **kwargs)
        if self.adapter._resp[0] == 0:
            return self.send_username(attempt=attempt, **kwargs)
        else:
            raise exceptions.PromptTimeout('prompt timeout: %r' %\
                self.prompt_username.pattern if hasattr(self.prompt_username, 'pattern')\
                                             else self.prompt_username)

    def send_username(self, **kwargs):
        #print('send_username', kwargs)
        self.adapter.send(kwargs.get('username', self.username))
        self.adapter._resp = self.adapter.expect(self.prompt_password)
        if self.adapter._resp[0] == 0:
            return self.send_password(**kwargs)
        else:
            raise exceptions.PromptTimeout('prompt timeout: %r' %\
                self.prompt_password.pattern if hasattr(self.prompt_password, 'pattern')\
                                             else self.prompt_password)

    def send_password(self, attempt=1, **kwargs):
        #print('send_password', kwargs)
        self.adapter.send(kwargs.get('password', self.password), logmask='*')
        self.adapter._resp = self.adapter.expect([self.prompt_cli, self.prompt_username])
        if self.adapter._resp[0] == 0:
            self.logged = True
            return self.adapter._resp
        elif self.adapter._resp[0] == 1:
            if attempt > 1 or kwargs.get('username', self.username) == os.getenv('TAC_USERNAME'):
                raise exceptions.LoginError('incorrect username or password')
            else:
                return self.login(attempt=attempt + 1,
                    username=os.getenv('TAC_USERNAME', 'cisco'),
                    password=os.getenv('TAC_PASSWORD', 'cisco'))
        else:
            raise exceptions.PromptTimeout('prompt timeout: %r' %\
                self.prompt_cli.pattern if hasattr(self.prompt_cli, 'pattern')\
                                        else self.prompt_cli)

    def cmd(self, cmd, timeout=None, attempt=1):
        if attempt > self.max_attempt:
            raise exceptions.MaxAttempt('maximum attempts')
        if not self.logged:
            self.login()
        self.adapter.send(cmd)
        try:
            self.adapter._resp = self.adapter.expect([self.prompt_cli, self.prompt_more], timeout=timeout)
            #print(resp)
        except (EOFError, BrokenPipeError):
            self.logged = False
            return self.cmd(cmd, timeout=timeout, attempt=attempt+1)
        if self.adapter._resp[0] < 0:
            raise exceptions.PromptTimeout('prompt timeout')
        elif self.adapter._resp[0] == 0:
            return self.adapter.format_output(self.adapter._resp[2].decode('utf-8'))
        elif self.adapter._resp[0] == 1:
            output = self.adapter._resp[2]
            while True:
                self.adapter.send(' ', end='')
                self.adapter._resp = self.adapter.expect([self.prompt_cli, self.prompt_more], timeout=timeout)
                #print(resp)
                if self.adapter._resp[0] == 0:
                    output += self.adapter._resp[2]
                    break
                elif self.adapter._resp[0] == 1:
                    output += self.adapter._resp[2]
                else:
                    raise exceptions.PromptTimeout('prompt timeout')
            return self.adapter.format_output(output.decode('utf-8'))
