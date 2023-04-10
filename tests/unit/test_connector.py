import unittest
from unittest.mock import Mock

from netboxkea.connector import Connector
from netboxkea.kea.exceptions import SubnetNotFound
from ..fixtures.pynetbox import ip_addresses as fixtip
from ..fixtures.pynetbox import ip_ranges as fixtr
from ..fixtures.pynetbox import prefixes as fixtp


class TestConnector(unittest.TestCase):

    def setUp(self):
        self.nb = Mock()
        self.kea = Mock()
        self.conn = Connector(self.nb, self.kea)
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
        self.kea.set_reservation.assert_called_once_with(
            prefix_id=100, ipaddr_id=200, ipaddr='192.168.0.1',
            hw_addr='11:22:33:44:55:66', hostname='pc.lan')

    def test_sync_ip_address_del(self):
        self.nb.ip_address.return_value = None
        self.conn.sync_ipaddress(249)
        self.nb.ip_address.assert_called_once_with(249)
        self.kea.del_resa.assert_called_once_with(249)

    def test_sync_prefix_options(self):
        self.conn.sync_prefix(100)
        self.kea.set_subnet_options.assert_called_once_with(
            prefix_id=100, subnet='192.168.0.0/24', options={})

    def test_sync_prefix_fullsync(self):
        self.kea.set_subnet_options.side_effect = SubnetNotFound()
        self.conn.sync_prefix(100)
        self.nb.ip_addresses.assert_called_once_with(parent='192.168.0.0/24')
        self.nb.ip_ranges.assert_called_once_with(parent='192.168.0.0/24')
        self.kea.set_subnet.assert_called_once_with(
            prefix_id=100, subnet='192.168.0.0/24', options={})
        self.kea.set_reservation.assert_called_once_with(
            prefix_id=100, ipaddr_id=200, ipaddr='192.168.0.1',
            hw_addr='11:22:33:44:55:66', hostname='pc.lan')
        self.kea.set_pool.assert_called_once_with(
            prefix_id=100, iprange_id=250, start='192.168.0.100',
            end='192.168.0.199')

    def test_sync_prefix_del(self):
        self.nb.prefix.return_value = None
        self.conn.sync_prefix(199)
        self.kea.del_subnet.assert_called_once_with(199)

    def test_sync_ip_range(self):
        self.conn.sync_iprange(250)
        self.kea.set_pool.assert_called_once_with(
            prefix_id=100, iprange_id=250, start='192.168.0.100',
            end='192.168.0.199')

    def test_sync_ip_range_del(self):
        self.nb.ip_range.return_value = None
        self.conn.sync_iprange(299)
        self.kea.del_pool.assert_called_once_with(299)

    def test_sync_interface(self):
        self.conn.sync_interface(300)
        self.kea.set_reservation.assert_called_once_with(
            prefix_id=100, ipaddr_id=200, ipaddr='192.168.0.1',
            hw_addr='11:22:33:44:55:66', hostname='pc.lan')

    def test_sync_device(self):
        self.conn.sync_device(400)
        self.kea.set_reservation.assert_called_once_with(
            prefix_id=100, ipaddr_id=200, ipaddr='192.168.0.1',
            hw_addr='11:22:33:44:55:66', hostname='pc.lan')

    def test_sync_vminterface(self):
        self.nb.ip_address.return_value = fixtip.ip_address_250
        self.conn.sync_vminterface(350)
        self.kea.set_reservation.assert_called_once_with(
            prefix_id=100, ipaddr_id=250, ipaddr='192.168.0.51',
            hw_addr='11:22:33:44:55:22', hostname='vm.lan')

    def test_sync_virtualmachine(self):
        self.nb.ip_address.return_value = fixtip.ip_address_250
        self.conn.sync_virtualmachine(400)
        self.kea.set_reservation.assert_called_once_with(
            prefix_id=100, ipaddr_id=250, ipaddr='192.168.0.51',
            hw_addr='11:22:33:44:55:22', hostname='vm.lan')

    def test_sync_all(self):
        self.conn.sync_all()
        self.kea.set_subnet.assert_called_once_with(
            prefix_id=100, subnet='192.168.0.0/24', options={})
        self.kea.set_reservation.assert_called_once_with(
            prefix_id=100, ipaddr_id=200, ipaddr='192.168.0.1',
            hw_addr='11:22:33:44:55:66', hostname='pc.lan')
        self.kea.set_pool.assert_called_once_with(
            prefix_id=100, iprange_id=250, start='192.168.0.100',
            end='192.168.0.199')
        self.kea.commit.assert_called()
        self.kea.push.assert_called()
