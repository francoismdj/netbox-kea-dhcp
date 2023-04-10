from unittest.mock import Mock

from pynetbox.core.response import Record

from . import virtual_machines

api = Mock(base_url='http://netbox')

# Note: record method "full_detail()" was called
_common = {
    'bridge': None,
    'count_fhrp_groups': 0,
    'created': '2023-01-01T12:00:00.000000Z',
    'custom_fields': {},
    'description': '',
    'enabled': True,
    'has_details': True,
    'l2vpn_termination': None,
    'last_updated': '2023-03-28T08:15:56.256950Z',
    'mac_address': '11:22:33:44:55:22',
    'mode': None,
    'mtu': None,
    'parent': None,
    'tagged_vlans': [],
    'tags': [],
    'untagged_vlan': None,
    'vrf': None}

_vif_350 = _common.copy()
_vif_350.update({
    'count_ipaddresses': 1,
    'display': 'vm001-if0',
    'id': 350,
    'name': 'vm001-if0',
    'virtual_machine': virtual_machines.virtual_machine_450,
    'url': 'http://netbox:8000/api/virtualization/interfaces/350/'})

vminterface_350 = Record(_vif_350, api, None)
