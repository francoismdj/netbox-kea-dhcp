from unittest.mock import Mock

from pynetbox.core.response import Record
from pynetbox.models.ipam import IpAddresses

from . import devices, interfaces, virtual_machines, vminterfaces

ALL_IP = []


def get(id_):
    """ Emulate pynetbox.[…].Record.get()"""
    for ip in ALL_IP:
        if ip.id == id_:
            return ip


def filter_(interface_id=None, device_id=None, vminterface_id=None,
            virtual_machine_id=None, **kwargs):
    """ Emulate pynetbox.[…].Record.filter()"""

    intf_id = vminterface_id if vminterface_id else interface_id
    if intf_id:
        return iter([ip for ip in ALL_IP if ip.assigned_object and
                     ip.assigned_object.id == intf_id])
    elif device_id:
        return iter([ip for ip in ALL_IP if
                     ip.assigned_object_type == 'dcim.interface'
                     and ip.assigned_object.device.id == device_id])
    elif virtual_machine_id:
        return iter([ip for ip in ALL_IP if
                     ip.assigned_object_type == 'virtualization.vminterface'
                     and ip.assigned_object.virtual_machine.id ==
                     virtual_machine_id])
    else:
        return iter(ALL_IP)


api = Mock(base_url='http://netbox')

_common = {
    'assigned_object': None,
    'assigned_object_id': None,
    'assigned_object_type': None,
    'comments': '',
    'created': '2023-01-01T12:00:00.000000Z',
    'custom_fields': {},
    'description': '',
    'family': Record({'label': 'IPv4', 'value': 4}, api, None),
    'has_details': False,
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
ALL_IP.append(ip_address_200)
# Associate here IP address with device to avoid circular import failure
devices.device_400.primary_ip = ip_address_200
devices.device_400.primary_ip4 = ip_address_200

_ip_201 = _common.copy()
_ip_201.update({
    'address': '192.168.0.2/24',
    'custom_fields': {'dhcp_resa_hw_address': '22:22:22:22:22:22'},
    'display': '192.168.0.2/24',
    'dns_name': 'pc2.lan',
    'id': 201,
    'status': Record({'label': 'DHCP', 'value': 'dhcp'}, api, None),
    'url': 'https://netbox/api/ipam/ip-addresses/201/'})
ip_address_201 = IpAddresses(_ip_201, api, None)
ALL_IP.append(ip_address_201)

_ip_202 = _common.copy()
_ip_202.update({
    'address': '192.168.0.3/24',
    'assigned_object': interfaces.interface_300,
    'assigned_object_id': 300,
    'assigned_object_type': 'dcim.interface',
    'custom_fields': {'dhcp_resa_hw_address': '33:33:33:33:33:33'},
    'display': '192.168.0.3/24',
    'dns_name': 'pc3.lan',
    'id': 202,
    'status': Record({'label': 'DHCP', 'value': 'dhcp'}, api, None),
    'url': 'https://netbox/api/ipam/ip-addresses/202/'})
ip_address_202 = IpAddresses(_ip_202, api, None)
ALL_IP.append(ip_address_202)

_ip_250 = _common.copy()
_ip_250.update({
    'address': '10.0.0.50/8',
    'assigned_object': vminterfaces.vminterface_350,
    'assigned_object_id': 350,
    'assigned_object_type': 'virtualization.vminterface',
    'display': '10.0.0.50/8',
    'dns_name': 'vm.lan10',
    'id': 250,
    'status': Record({'label': 'DHCP', 'value': 'dhcp'}, api, None),
    'url': 'https://netbox/api/ipam/ip-addresses/250/'})

ip_address_250 = IpAddresses(_ip_250, api, None)
ALL_IP.append(ip_address_250)
# Associate here IP address with device to avoid circular import failure
virtual_machines.virtual_machine_450.primary_ip = ip_address_250
virtual_machines.virtual_machine_450.primary_ip4 = ip_address_250
