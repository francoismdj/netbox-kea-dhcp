from unittest.mock import Mock

from pynetbox.core.response import Record
from pynetbox.models.dcim import Interfaces

from . import devices

api = Mock(base_url='http://netbox')

_common = {
    '_occupied': False,
    'bridge': None,
    'cable': None,
    'cable_end': '',
    'created': '2023-01-01T12:00:00.000000Z',
    'connected_endpoints': None,
    'connected_endpoints_reachable': None,
    'connected_endpoints_type': None,
    'count_fhrp_groups': 0,
    'custom_fields': {},
    'description': '',
    'duplex': None,
    'enabled': True,
    'has_details': False,
    'l2vpn_termination': None,
    'label': '',
    'lag': None,
    'last_updated': '2023-01-01T12:00:00.000000Z',
    'link_peers': [],
    'link_peers_type': None,
    'mark_connected': False,
    'mgmt_only': False,
    'mode': None,
    'module': None,
    'mtu': None,
    'parent': None,
    'poe_mode': None,
    'poe_type': None,
    'rf_channel': None,
    'rf_channel_frequency': None,
    'rf_channel_width': None,
    'rf_role': None,
    'speed': None,
    'tagged_vlans': [],
    'tags': [],
    'tx_power': None,
    'type': Record(
        {'label': '1000BASE-T (1GE)', 'value': '1000base-t'}, api, None),
    'untagged_vlan': None,
    'vdcs': [],
    'vrf': None,
    'wireless_lans': [],
    'wireless_link': None,
    'wwn': None}

# pynetbox record __dict__ attribute
_if_300 = _common.copy()
_if_300.update({
    'count_ipaddresses': 1,
    #'device': tests.fixtures.pynetbox.devices.device_400,
    'device': devices.device_400,
    'display': 'pc-if0',
    'id': 300,
    'mac_address': '11:22:33:44:55:66',
    'name': 'pc-if0',
    'url': 'http://netbox/api/dcim/interfaces/300/',
    })

interface_300 = Interfaces(_if_300, api, None)
