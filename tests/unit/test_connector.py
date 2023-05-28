import unittest
from unittest.mock import Mock

from netboxkea.connector import _get_nested_attr, _set_dhcp_attr, Connector
from netboxkea.kea.exceptions import SubnetNotFound
from ..fixtures.pynetbox import ip_addresses as fixtip
from ..fixtures.pynetbox import ip_ranges as fixtr
from ..fixtures.pynetbox import prefixes as fixtp


class TestConnectorFunctions(unittest.TestCase):

    def test_get_nested_attr(self):
        obj = Mock()
        obj.assigned.device.name = 'pc.lan'
        hostname = _get_nested_attr(obj, 'assigned.device.name')
        self.assertEqual(hostname, 'pc.lan')

    def test_set_dhcp_attr(self):
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
        resa_ip_map = {
            'hw-address': ['custom_fields.dhcp_resa_hw_address',
                           'assigned_object.mac_address'],
            'hostname': ['dns_name', 'assigned_object.device.name',
                         'assigned_object.virtual_machine.name']}
        self.conn = Connector(self.nb, self.kea, {}, {}, resa_ip_map)
        self.nb.prefix.return_value = fixtp.prefix_100
        self.nb.prefixes.return_value = iter([fixtp.prefix_100])
        self.nb.all_prefixes.return_value = iter([fixtp.prefix_100])
        self.nb.ip_range.return_value = fixtr.ip_range_250
        self.nb.ip_ranges.return_value = iter([fixtr.ip_range_250])
        self.nb.ip_address.return_value = fixtip.ip_address_200
        self.nb.ip_addresses.return_value = iter([fixtip.ip_address_200])

    def test_sync_ip_address(self):
        self.conn.sync_ipaddress(200)
        self.nb.ip_address.assert_called_once_with(200)
        self.nb.prefixes.assert_called_once_with(contains='192.168.0.1/24')
        self.kea.set_reservation.assert_called_once_with(100, 200, {
                'ip-address': '192.168.0.1', 'hw-address': '11:22:33:44:55:66',
                'hostname': 'pc.lan'})

    def test_sync_ip_address_del(self):
        self.nb.ip_address.return_value = None
        self.conn.sync_ipaddress(249)
        self.nb.ip_address.assert_called_once_with(249)
        self.kea.del_resa.assert_called_once_with(249)

    def test_sync_prefix_options(self):
        self.conn.sync_prefix(100)
        self.kea.update_subnet.assert_called_once_with(100, {
            'subnet': '192.168.0.0/24'})

    def test_sync_prefix_fullsync(self):
        self.kea.update_subnet.side_effect = SubnetNotFound()
        self.conn.sync_prefix(100)
        self.nb.ip_addresses.assert_called_once_with(parent='192.168.0.0/24')
        self.nb.ip_ranges.assert_called_once_with(parent='192.168.0.0/24')
        self.kea.set_subnet.assert_called_once_with(100, {
            'subnet': '192.168.0.0/24'})
        self.kea.set_reservation.assert_called_once_with(100, 200, {
                'ip-address': '192.168.0.1', 'hw-address': '11:22:33:44:55:66',
                'hostname': 'pc.lan'})
        self.kea.set_pool.assert_called_once_with(100, 250, {
                'pool': '192.168.0.100-192.168.0.199'})

    def test_sync_prefix_del(self):
        self.nb.prefix.return_value = None
        self.conn.sync_prefix(199)
        self.kea.del_subnet.assert_called_once_with(199)

    def test_sync_ip_range(self):
        self.conn.sync_iprange(250)
        self.kea.set_pool.assert_called_once_with(100, 250, {
                'pool': '192.168.0.100-192.168.0.199'})

    def test_sync_ip_range_del(self):
        self.nb.ip_range.return_value = None
        self.conn.sync_iprange(299)
        self.kea.del_pool.assert_called_once_with(299)

    def test_sync_interface(self):
        self.conn.sync_interface(300)
        self.kea.set_reservation.assert_called_once_with(100, 200, {
                'ip-address': '192.168.0.1', 'hw-address': '11:22:33:44:55:66',
                'hostname': 'pc.lan'})

    def test_sync_device(self):
        self.conn.sync_device(400)
        self.kea.set_reservation.assert_called_once_with(100, 200, {
                'ip-address': '192.168.0.1', 'hw-address': '11:22:33:44:55:66',
                'hostname': 'pc.lan'})

    def test_sync_vminterface(self):
        self.nb.ip_address.return_value = fixtip.ip_address_250
        self.conn.sync_vminterface(350)
        self.kea.set_reservation.assert_called_once_with(100, 250, {
                'ip-address': '192.168.0.51',
                'hw-address': '11:22:33:44:55:22',
                'hostname': 'vm.lan'})

    def test_sync_virtualmachine(self):
        self.nb.ip_address.return_value = fixtip.ip_address_250
        self.conn.sync_virtualmachine(400)
        self.kea.set_reservation.assert_called_once_with(100, 250, {
                'ip-address': '192.168.0.51',
                'hw-address': '11:22:33:44:55:22',
                'hostname': 'vm.lan'})

    def test_sync_all(self):
        self.conn.sync_all()
        self.kea.set_subnet.assert_called_once_with(100, {
            'subnet': '192.168.0.0/24'})
        self.kea.set_reservation.assert_called_once_with(100, 200, {
                'ip-address': '192.168.0.1', 'hw-address': '11:22:33:44:55:66',
                'hostname': 'pc.lan'})
        self.kea.set_pool.assert_called_once_with(100, 250, {
                'pool': '192.168.0.100-192.168.0.199'})
        self.kea.commit.assert_called()
        self.kea.push.assert_called()
