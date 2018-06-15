

class DevTemplate(object):
    methods = {}

    def __init__(self, attrs):
        self.attrs = attrs
        self.max_attempt = 3
        self.logged = False
        self._adapter = None

    def __getattr__(self, item):
        if item in self.methods:
            return self.methods[item]
        raise AttributeError("'%s' object has no attribute '%s'" % \
            (self.__class__.__name__, item))

    def __del__(self):
        if self.adapter is not None:
            self.adapter.disconnect()

    @property
    def adapter(self):
        return self._adapter

    @adapter.setter
    def adapter(self, adapter):
        self._adapter = adapter

    @classmethod
    def method(cls, name, *args, **kwargs):
        def decorator(func):
            def decorated(*args, **kwargs):
                return func(*args, **kwargs)
            if hasattr(cls, name):
                setattr(cls, name, func)
            else:
                self.methods[name] = func
            return decorated
        return decorator

    def login(self):
        raise NotImplementedError
