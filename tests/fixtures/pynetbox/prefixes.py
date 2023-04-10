from unittest.mock import Mock

from pynetbox.core.response import Record
from pynetbox.models.ipam import Prefixes

api = Mock(base_url='http://netbox')

_common = {
    'children': 0,
    'comments': '',
    'created': '2023-01-01T12:00:00.000000Z',
    'custom_fields': {'dhcp_enable': True,
                      'dhcp_option_data_domain_search': 'local, lan',
                      'dhcp_option_data_routers': '192.168.0.254'},
    'description': '',
    'family': Record({'label': 'IPv4', 'value': 4}, api, None),
    'has_details': False,
    'is_pool': False,
    'last_updated': '2023-01-01T12:00:00.000000Z',
    'mark_utilized': False,
    'role': None,
    'site': None,
    'status': Record({'label': 'Active', 'value': 'active'}, api, None),
    'tags': [],
    'tenant': None,
    'url': 'http://netbox/api/ipam/prefixes/100/',
    'vlan': None,
    'vrf': None}

_pref_100 = _common.copy()
_pref_100.update({
    'display': '192.168.0.0/24',
    'id': 100,
    'prefix': '192.168.0.0/24'})

prefix_100 = Prefixes(_pref_100, api, None)
