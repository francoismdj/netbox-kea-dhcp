from unittest.mock import Mock

from pynetbox.core.response import Record
from pynetbox.models.virtualization import VirtualMachines

api = Mock(base_url='http://netbox')

_common = {
    'cluster': Record({'display': 'My cluster'}, api, None),
    'comments': '',
    'config_context': {},
    'created': '2023-01-01T12:00:00.000000Z',
    'custom_fields': {},
    'device': None,
    'disk': None,
    'has_details': False,
    'last_updated': '2023-01-01T12:00:00.000000Z',
    'local_context_data': None,
    'memory': None,
    'platform': None,
    'primary_ip6': None,
    'role': None,
    'site': None,
    'status': Record({'label': 'Active', 'value': 'active'}, api, None),
    'tags': [],
    'tenant': None,
    'vcpus': None}

_vm_450 = _common.copy()
_vm_450.update({
    'display': 'vm',
    'id': 450,
    'name': 'vm',
    # Primary IP addresse associations are postponed into ip_addresses module
    # to avoid circular import failures.
    # 'primary_ip': ip_addresse.ip_address_300,
    # 'primary_ip4': ip_addresses.ip_address_300,
    'url': 'http://netbox/api/virtualization/virtual-machines/450/'})

virtual_machine_450 = VirtualMachines(_vm_450, api, None)
