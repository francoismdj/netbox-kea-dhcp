from unittest.mock import Mock

from pynetbox.core.response import Record
from pynetbox.models.ipam import IpRanges

api = Mock(base_url='http://netbox')

_common = {
    'comments': '',
    'created': '2023-01-01T12:00:00.000000Z',
    'custom_fields': {},
    'description': '',
    'family': Record({'label': 'IPv4', 'value': 4}, api, None),
    'has_details': False,
    'last_updated': '2023-01-01T12:00:00.000000Z',
    'role': None,
    'size': 100,
    'tags': [],
    'tenant': None,
    'vrf': None}

_r_250 = _common.copy()
_r_250.update({
    'display': '192.168.0.100-200/24',
    'end_address': '192.168.0.199/24',
    'id': 250,
    'start_address': '192.168.0.100/24',
    'status': Record({'label': 'DHCP', 'value': 'dhcp'}, api, None),
    'url': 'http://netbox/api/ipam/ip-ranges/250/'})

ip_range_250 = IpRanges(_r_250, api, None)
