from unittest.mock import Mock

from pynetbox.core.response import Record
from pynetbox.models.dcim import Devices

api = Mock(base_url='http://netbox')

_common = {
    'airflow': None,
    'asset_tag': None,
    'cluster': None,
    'comments': '',
    'config_context': {},
    'created': '2023-01-01T12:00:00.000000Z',
    'custom_fields': {},
    'device_role': Record({'display': 'Unknown'}, api, None),
    'device_type': Record({'display': 'Unknown'}, api, None),
    'face': None,
    'has_details': False,
    'last_updated': '2023-01-01T12:00:00.000000Z',
    'local_context_data': None,
    'location': None,
    'parent_device': None,
    'platform': None,
    'position': None,
    'primary_ip6': None,
    'rack': None,
    'serial': '',
    'site': None,
    'status': Record({'label': 'Active', 'value': 'active'}, api, None),
    'tags': [],
    'tenant': None,
    'vc_position': None,
    'vc_priority': None,
    'virtual_chassis': None}

_dev_400 = _common.copy()
_dev_400.update({
    'display': 'pc',
    'id': 400,
    'name': 'pc',
    # Primary IP addresse associations are postponed into ip_addresses module
    # to avoid circular import failures.
    # 'primary_ip':  ip_addresses.ip_address_200,
    # 'primary_ip4': ip_addresses.ip_address_200,
    'url': 'http://netbox/api/dcim/devices/400/'})

device_400 = Devices(_dev_400, api, None)
