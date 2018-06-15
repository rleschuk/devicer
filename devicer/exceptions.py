

class _Exception(Exception):
    def __init__(self, *args):
        self.args = args if args else ('',)
    #def __str__(self):
    #    if self.args:
    #        return '%s: %s' % (self.__class__.__name__, *self.args[:1])
    #    else:
    #        return self.__class__.__name__
    #def get(self, item, default=None):
    #    return getattr(self, item, default)


class ICMPError(_Exception): pass
class SocketTimeout(_Exception): pass
class PromptTimeout(_Exception): pass
class LoginError(_Exception): pass
class MaxAttempt(_Exception): pass
class NotFound(_Exception): pass
class ConnectError(_Exception): pass
class AttrError(_Exception): pass
