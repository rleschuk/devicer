
import os
import nmap

from .. import exceptions
from . import adapters


for module in os.listdir(os.path.dirname(__file__)):
    if not module.startswith('__') and module.endswith('.py'):
        __import__('%s.%s' % (__package__, module[:-3]), locals(), globals())
del module


def find_template(attrs):
    for name, module in globals().items():
        cls = getattr(module, name.capitalize(), None)
        if hasattr(cls, 'check_template') and cls.check_template(attrs):
            return cls


def devtemplate(attrs):
    cls = find_template(attrs)
    if cls is None:
        adapter = None
        open_ports = scan_ports(str(attrs.address))
        if 23 in open_ports:
            adapter = adapters.TelnetAdapter(str(attrs.address))
            attrs.start_prompt = adapter.start_prompt()
            cls = find_template(attrs)
            if cls:
                return cls(attrs)
        if cls is None:
            cls = default.DevTemplate
            return cls(attrs)
    return cls(attrs)


def scan_ports(address, ports='22,23'):
    nm = nmap.PortScanner()
    result = nm.scan(address, ports, '-T5 --open')
    return result.get('scan', {}).get(address, {}).get('tcp', {})
