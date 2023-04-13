import logging
from ipaddress import ip_interface

from .kea.exceptions import KeaError, KeaClientError, SubnetNotFound

logger = logging.getLogger('Connector')


def _map_dhcp_attrs(dhcp_map, netbox_fields):
    """ Convert netbox fields to DHCP configuration dictionary """

    dhcp_conf = {}
    # For each custom field, get corresponding DHCP server attribute
    for k, v in netbox_fields.items():
        # Kea don’t like None value (TODO even if JSON converts to "null"?)
        if v is None:
            continue
        try:
            # DHCP server attribute represents dot-separated nested attrs
            parts = dhcp_map[k].split('.')
        except KeyError:
            # self.logger.debug(f'no mapping for netbox DHCP attr {k}')
            continue
        # option-data are in a list of data/name dict
        if parts[0] == 'option-data':
            dhcp_conf.setdefault('option-data', []).append(
                {'name': parts[1], 'data': v})
        else:
            # Convert attribute parts to dict, except for the last part
            # which actually hold the value.
            opt = dhcp_conf
            last_index = len(parts) - 1
            for i, part in enumerate(parts):
                if i < last_index:
                    if part not in opt:
                        opt[part] = {}
                    opt = opt[part]
            opt[part] = v
    return dhcp_conf


class Connector:
    def __init__(self, nb, kea, check=False, prefix_dhcp_map={}):
        self.nb = nb
        self.kea = kea
        self.check = check
        self.prefix_dhcp_map = prefix_dhcp_map

        # Pull DHCP configuration
        logger.info('pull config from DHCP server')
        self.kea.pull()

    def sync_all(self):
        """ Replace current DHCP configuration by a new generated one """

        self.kea.del_all_subnets()

        # Create DHCP configuration for each prefix
        all_failed = None
        for p in self.nb.all_prefixes():
            if all_failed is None:
                all_failed = True
            pl = f'prefix {p}: '
            logger.debug(f'{pl}generate DHCP config')
            # Speed up things by disabling auto-commit
            self.kea.auto_commit = False
            try:
                self._prefix_to_subnet(p, fullsync=True)
            except KeaError as e:
                logger.error(f'{pl}config failed. Error: {e}')
                continue

            # Make intermediate commits only when not in check mode to avoid
            # false errors of missing, not yet created, subnets.
            if not self.check:
                try:
                    self.kea.commit()
                except KeaError as e:
                    logger.error(f'{pl}commit failed. Error: {e}')
                    # Retry with auto-commit enabled to catch the faulty item
                    logger.warning(f'{pl}retry with auto commit on')
                    self.kea.auto_commit = True
                    try:
                        self._prefix_to_subnet(p, fullsync=True)
                    except KeaError as e:
                        logger.error(f'{pl}config failed. Error: {e}')
                        continue

            all_failed = False

        if all_failed is not True:
            self.push_to_dhcp()

    def push_to_dhcp(self):
        if self.check:
            logger.info('check mode on: config will NOT be pushed to server')
        else:
            self.kea.push()

    def sync_prefix(self, id_):
        p = self.nb.prefix(id_)
        self._prefix_to_subnet(p) if p else self.kea.del_subnet(id_)

    def sync_iprange(self, id_):
        r = self.nb.ip_range(id_)
        self._iprange_to_pool(r) if r else self.kea.del_pool(id_)

    def sync_ipaddress(self, id_):
        i = self.nb.ip_address(id_)
        self._ipaddr_to_resa(i) if i else self.kea.del_resa(id_)

    def sync_interface(self, id_):
        for i in self.nb.ip_addresses(interface_id=id_):
            self.sync_ipaddress(i.id)

    def sync_device(self, id_):
        for i in self.nb.ip_addresses(device_id=id_):
            self.sync_ipaddress(i.id)

    def sync_vminterface(self, id_):
        for i in self.nb.ip_addresses(vminterface_id=id_):
            self.sync_ipaddress(i.id)

    def sync_virtualmachine(self, id_):
        for i in self.nb.ip_addresses(virtual_machine_id=id_):
            self.sync_ipaddress(i.id)

    def _prefix_to_subnet(self, pref, fullsync=False):
        options = _map_dhcp_attrs(self.prefix_dhcp_map, pref.custom_fields)
        if not fullsync:
            try:
                self.kea.set_subnet_options(
                    prefix_id=pref.id, subnet=pref.prefix, options=options)
            except SubnetNotFound:
                # No subnet matching prefix_id/subnet_value. Create a new one
                self.kea.del_subnet(pref.id, commit=False)
                fullsync = True

        if fullsync:
            self.kea.set_subnet(
                prefix_id=pref.id, subnet=pref.prefix, options=options)
            # Add host reservations
            for i in self.nb.ip_addresses(parent=pref.prefix):
                try:
                    self._ipaddr_to_resa(i, prefix=pref)
                except KeaClientError as e:
                    logger.error(f'prefix {pref} > IP {i}: {e}')
            # Add pools
            for r in self.nb.ip_ranges(parent=pref.prefix):
                try:
                    self._iprange_to_pool(r, prefix=pref)
                except KeaClientError as e:
                    logger.error(f'prefix {pref} > range {r}: {e}')

    def _iprange_to_pool(self, iprange, prefix=None):
        prefixes = [prefix] if prefix else self.nb.prefixes(
            contains=iprange.start_address)
        for pref in prefixes:
            try:
                start = str(ip_interface(iprange.start_address).ip)
                end = str(ip_interface(iprange.end_address).ip)
                self.kea.set_pool(
                    prefix_id=pref.id, iprange_id=iprange.id, start=start,
                    end=end)
            except SubnetNotFound:
                logger.warning(
                    f'subnet {pref.prefix} is missing, let’s sync it again')
                self._prefix_to_subnet(pref, fullsync=True)

    def _ipaddr_to_resa(self, ip, prefix=None):
        prefixes = [prefix] if prefix else self.nb.prefixes(
            contains=ip.address)
        # Get hostname from DNS name, fallback to device name
        if ip.dns_name:
            hostname = ip.dns_name
        else:
            try:
                hostname = ip.assigned_object.device.name
            except AttributeError:
                hostname = ip.assigned_object.virtual_machine.name
        for pref in prefixes:
            try:
                addr = str(ip_interface(ip.address).ip)
                self.kea.set_reservation(
                    prefix_id=pref.id, ipaddr_id=ip.id, ipaddr=addr,
                    hw_addr=ip.assigned_object.mac_address, hostname=hostname)
            except SubnetNotFound:
                self._prefix_to_subnet(pref)
