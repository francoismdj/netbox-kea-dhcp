from unittest.mock import Mock

from pynetbox.core.response import Record
from pynetbox.models.ipam import IpAddresses

from . import devices, interfaces, virtual_machines, vminterfaces

api = Mock(base_url='http://netbox')

_common = {
    'comments': '',
    'created': '2023-01-01T12:00:00.000000Z',
    'custom_fields': {},
    'description': '',
    'has_details': False,
    'family': Record({'label': 'IPv4', 'value': 4}, api, None),
    'last_updated': '2023-01-01T12:00:00.000000Z',
    'nat_inside': None,
    'nat_outside': [],
    'role': None,
    'tags': [],
    'tenant': None,
    'vrf': None}

_ip_200 = _common.copy()
_ip_200.update({
    'address': '192.168.0.1/24',
    'assigned_object': interfaces.interface_300,
    'assigned_object_id': 300,
    'assigned_object_type': 'dcim.interface',
    'display': '192.168.0.1/24',
    'dns_name': 'pc.lan',
    'id': 200,
    'status': Record({'label': 'DHCP', 'value': 'dhcp'}, api, None),
    'url': 'https://netbox/api/ipam/ip-addresses/200/'})

ip_address_200 = IpAddresses(_ip_200, api, None)
# Associate here IP address with device to avoid circular import failure
devices.device_400.primary_ip = ip_address_200
devices.device_400.primary_ip4 = ip_address_200

_ip_250 = _common.copy()
_ip_250.update({
    'address': '192.168.0.51/24',
    'assigned_object': vminterfaces.vminterface_350,
    'assigned_object_id': 350,
    'assigned_object_type': 'virtualization.vminterface',
    'display': '192.168.0.51/24',
    'dns_name': 'vm.lan',
    'id': 250,
    'status': Record({'label': 'DHCP', 'value': 'dhcp'}, api, None),
    'url': 'https://netbox/api/ipam/ip-addresses/250/'})

ip_address_250 = IpAddresses(_ip_250, api, None)
# Associate here IP address with device to avoid circular import failure
virtual_machines.virtual_machine_450.primary_ip = ip_address_250
virtual_machines.virtual_machine_450.primary_ip4 = ip_address_250
