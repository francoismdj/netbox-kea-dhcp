import unittest
from unittest.mock import Mock, call

from netboxkea.connector import _get_nested, _set_dhcp_attr, Connector
from netboxkea.kea.exceptions import SubnetNotFound
from ..fixtures.pynetbox import ip_addresses as fixtip
from ..fixtures.pynetbox import ip_ranges as fixtr
from ..fixtures.pynetbox import prefixes as fixtp


class TestConnectorFunctions(unittest.TestCase):

    def test_01_get_nested_attr(self):
        obj = {'assigned': {'device': {'name': 'pc.lan'}}}
        hostname = _get_nested(obj, 'assigned.device.name')
        self.assertEqual(hostname, 'pc.lan')

    def test_02_set_dhcp_attr(self):
        dhcp_item = {}
        _set_dhcp_attr(dhcp_item, 'next-server', '10.0.0.1')
        _set_dhcp_attr(dhcp_item, 'option-data.routers', '192.168.0.254')
        _set_dhcp_attr(dhcp_item, 'option-data.domain-search', 'lan')
        _set_dhcp_attr(dhcp_item, 'user-context.desc', 'Test')
        _set_dhcp_attr(dhcp_item, 'user-context.note', 'Hello')
        self.assertEqual(dhcp_item, {
            'next-server': '10.0.0.1',
            'option-data': [
                {'name': 'routers', 'data': '192.168.0.254'},
                {'name': 'domain-search', 'data': 'lan'}],
            'user-context': {'desc': 'Test', 'note': 'Hello'}})


class TestConnector(unittest.TestCase):

    def setUp(self):
        self.nb = Mock()
        self.kea = Mock()

        # Set up connector
        resa_ip_map = {
            'hw-address': ['custom_fields.dhcp_resa_hw_address',
                           'assigned_object.mac_address'],
            'hostname': ['dns_name', 'assigned_object.device.name',
                         'assigned_object.virtual_machine.name']}
        self.conn = Connector(self.nb, self.kea, {}, {}, resa_ip_map)

        # Set up netbox mock
        self.nb.prefix.return_value = fixtp.prefix_100
        self.nb.prefixes.return_value = iter([fixtp.prefix_100])
        self.nb.all_prefixes.return_value = iter([fixtp.prefix_100])
        self.nb.ip_range.return_value = fixtr.ip_range_250
        self.nb.ip_ranges.return_value = iter([fixtr.ip_range_250])
        self.nb.ip_address.side_effect = fixtip.get
        self.nb.ip_addresses.side_effect = fixtip.filter_

        # Define kea calls
        self.call_subnet100 = call(100, {'subnet': '192.168.0.0/24'})
        self.call_subnet101 = call(101, {'subnet': '10.0.0.0/8'})
        self.call_resa200 = call(100, 200, {
            'ip-address': '192.168.0.1', 'hw-address': '11:11:11:11:11:11',
            'hostname': 'pc.lan'})
        self.call_resa201 = call(100, 201, {
            'ip-address': '192.168.0.2', 'hw-address': '22:22:22:22:22:22',
            'hostname': 'pc2.lan'})
        self.call_resa202 = call(100, 202, {
            'ip-address': '192.168.0.3', 'hw-address': '33:33:33:33:33:33',
            'hostname': 'pc3.lan'})
        self.call_resa250 = call(100, 250, {
            'ip-address': '10.0.0.50', 'hw-address': '55:55:55:55:55:55',
            'hostname': 'vm.lan10'})
        self.call_pool250 = call(100, 250, {
            'pool': '192.168.0.100-192.168.0.199'})

    def test_01_sync_ip_address_with_assigned_interface(self):
        self.conn.sync_ipaddress(200)
        self.nb.ip_address.assert_called_once_with(200)
        self.nb.prefixes.assert_called_once_with(contains='192.168.0.1/24')
        self.kea.set_reservation.assert_has_calls([self.call_resa200])

    def test_02_sync_ip_address_with_custom_field(self):
        self.conn.sync_ipaddress(201)
        self.nb.ip_address.assert_called_once_with(201)
        self.nb.prefixes.assert_called_once_with(contains='192.168.0.2/24')
        self.kea.set_reservation.assert_has_calls([self.call_resa201])

    def test_03_sync_ip_address_with_assigned_and_custom_field(self):
        self.conn.sync_ipaddress(202)
        self.nb.ip_address.assert_called_once_with(202)
        self.nb.prefixes.assert_called_once_with(contains='192.168.0.3/24')
        self.kea.set_reservation.assert_has_calls([self.call_resa202])

    def test_05_sync_ip_address_vm(self):
        self.conn.sync_ipaddress(250)
        self.nb.ip_address.assert_called_once_with(250)
        self.nb.prefixes.assert_called_once_with(contains='10.0.0.50/8')
        self.kea.set_reservation.assert_has_calls([self.call_resa250])

    def test_09_sync_ip_address_del(self):
        self.conn.sync_ipaddress(249)
        self.nb.ip_address.assert_called_once_with(249)
        self.kea.del_resa.assert_called_once_with(249)

    def test_10_sync_interface(self):
        self.conn.sync_interface(300)
        self.nb.ip_addresses.assert_called_once_with(interface_id=300)
        self.kea.set_reservation.assert_has_calls([self.call_resa200])

    def test_11_sync_device(self):
        self.conn.sync_device(400)
        self.nb.ip_addresses.assert_called_once_with(device_id=400)
        self.kea.set_reservation.assert_has_calls([self.call_resa200])

    def test_15_sync_vminterface(self):
        self.conn.sync_vminterface(350)
        self.nb.ip_addresses.assert_called_once_with(vminterface_id=350)
        self.kea.set_reservation.assert_has_calls([self.call_resa250])

    def test_16_sync_virtualmachine(self):
        self.conn.sync_virtualmachine(450)
        self.nb.ip_addresses.assert_called_once_with(virtual_machine_id=450)
        self.kea.set_reservation.assert_has_calls([self.call_resa250])

    def test_20_sync_ip_range(self):
        self.conn.sync_iprange(250)
        self.kea.set_pool.assert_has_calls([self.call_pool250])

    def test_21_sync_ip_range_del(self):
        self.nb.ip_range.return_value = None
        self.conn.sync_iprange(299)
        self.kea.del_pool.assert_called_once_with(299)

    def test_30_sync_prefix_update(self):
        self.conn.sync_prefix(100)
        self.kea.update_subnet.assert_called_once_with(100, {
            'subnet': '192.168.0.0/24'})

    def test_31_sync_prefix_fullsync(self):
        self.kea.update_subnet.side_effect = SubnetNotFound()
        self.conn.sync_prefix(100)
        self.nb.ip_addresses.assert_called_once_with(parent='192.168.0.0/24')
        self.nb.ip_ranges.assert_called_once_with(parent='192.168.0.0/24')
        self.kea.set_subnet.assert_has_calls([self.call_subnet100])
        self.kea.set_reservation.assert_has_calls(
            [self.call_resa200, self.call_resa201, self.call_resa202])
        self.kea.set_pool.assert_has_calls([self.call_pool250])

    def test_39_sync_prefix_del(self):
        self.nb.prefix.return_value = None
        self.conn.sync_prefix(199)
        self.kea.del_subnet.assert_called_once_with(199)

    def test_99_sync_all(self):
        self.conn.sync_all()
        self.kea.set_subnet.assert_has_calls([self.call_subnet100])
        self.kea.set_reservation.assert_has_calls(
            [self.call_resa200, self.call_resa201, self.call_resa202,
             self.call_resa250])
        self.kea.set_pool.assert_has_calls([self.call_pool250])
        self.kea.commit.assert_called()
        self.kea.push.assert_called()
