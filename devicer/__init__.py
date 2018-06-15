
import json
import datetime
from collections import OrderedDict

from . import exceptions
from .devtemplates import devtemplate
from .attrs import Attrs


def json_serial(obj):
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    return str(obj)


class Device(object):

    def __init__(self, **attrs):
        self.attrs = Attrs(attrs)
        self.template = None
        self.results = OrderedDict()
        self.tasks = OrderedDict()
        self.columns = OrderedDict()

    def init(self):
        if self.attrs.address is None:
            raise exceptions.AttrError('bad address')
        self.template = devtemplate(self.attrs)
        return self

    def __getattr__(self, item):
        if hasattr(self.template, item):
            return getattr(self.template, item)
        if item in self.tasks:
            return self.tasks[item]
        if self.attrs.hasattr(item):
            return getattr(self.attrs, item)
        raise AttributeError("'%s' object has no attribute '%s'" % \
            (self.__class__.__name__, item))

    def __repr__(self):
        return json.dumps(self.to_dict(), default=json_serial)

    def to_dict(self):
        return {
            **self.attrs.to_dict(),
            **{'results': dict(self.results),
               'log': self.adapter.get_log() if self.adapter else None}
        }

    def _execute_task(self, task, func=None, args=(), kwargs={}):
        self.results[task] = None
        try:
            if func is None:
                func = self.tasks[task]
            self.results[task] = func(self, *args, **kwargs)
        except TypeError:
            self.results[task] = func(*args, **kwargs)
        except KeyError:
            raise exceptions.NotFound('task not found')
        return self.results[task]

    def run_tasks(self, tasks=[], *args, **kwargs):
        if self.template is None: self.init()
        if isinstance(tasks, (list, tuple)):
            if len(tasks) == 0:
                tasks = self.tasks.keys()
            for task in tasks:
                self._execute_task(task, args=args, kwargs=kwargs)
        else:
            self._execute_task(tasks, args=args, kwargs=kwargs)
        return self.results

    def run_columns(self, *args, **kwargs):
        for name, func in self.columns.items():
            self.attrs.rowattrs[name] = func(*args, **kwargs)
        return self.attrs.rowattrs

    def task(self, name, condition=None):
        def decorator(func):
            def decorated(*args, **kwargs):
                return self._execute_task(name, func, args, kwargs)
            if (condition and condition(self.attrs)) or condition is None:
                self.tasks[name] = decorated
            return decorated
        return decorator

    def column(self, name):
        def decorator(func):
            def decorated(*args, **kwargs):
                return func(*args, **kwargs)
            self.columns[name] = decorated
            return decorated
        return decorator
