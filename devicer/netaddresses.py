

def netaddress(address):
    return IPv4(address)


class IPv4(object):

    def __init__(self, address):
        self._ip = None
        if isinstance(address, int):
            self._ip = address
        elif isinstance(address, str):
            self._ip = self._ip_from_str(address)
        elif isinstance(address, (list, tuple)):
            self._ip = self._ip_from_bytes(address)
        else:
            raise Exception()

    @property
    def str_address(self):
        return '.'.join(map(str, self._ip.to_bytes(4, 'big')))

    def _ip_from_str(self, address):
        if '/' in address:
            address, mask = address.split('/')
        return self._ip_from_bytes(address.split('.'))

    def _ip_from_bytes(self, address):
        octets = map(int, address)
        return int.from_bytes(octets, byteorder='big')

    def __str__(self):
        return self.str_address
