import logging

from ipaddress import ip_interface

from .kea.exceptions import (KeaError, KeaClientError, SubnetNotEqual,
                             SubnetNotFound)


def _get_nested(obj, attrs, sep='.'):
    """ Get value from a nested list of attributes or keys separated by sep """

    value = obj
    for a in attrs.split(sep):
        # getattr must be tried before dict.get because it is able to trigger
        # additionnal queries to netbox API.
        try:
            value = getattr(value, a)
        except AttributeError:
            value = value[a]

    return value


def _set_dhcp_attr(dhcp_item, key, value):
    """
    Set value to DHCP item dictionary. Key may be nested keys separated
    by dots, in which case each key represents a nested dictionary (or list, if
    the parent attribut is known to use a list).
    """

    k1, _, k2 = key.partition('.')
    if not k2:
        dhcp_item[key] = value
    elif k1 in ['option-data']:
        # Some keys hold a list of name/data dicts
        dhcp_item.setdefault(k1, []).append(
            {'name': k2, 'data': value})
    else:
        dhcp_item.setdefault(k1, {})[k2] = value


def _mk_dhcp_item(nb_obj, mapping):
    """ Convert a netbox object to a DHCP dictionary item """

    dhcp_item = {}
    for dhcp_attr, nb_attr in mapping.items():
        # Get value from netbox object
        attrs = [nb_attr] if isinstance(nb_attr, str) else nb_attr
        # Map value is expected to be list of attributes. The first
        # existing and non-null attribute will be used as the DHCP value
        value = None
        for a in attrs:
            try:
                value = _get_nested(nb_obj, a)
            except (TypeError, KeyError):
                continue
            if value:
                break

        # Set value to DHCP setting
        # Kea don’t like None value (TODO even if JSON converts it to "null"?)
        if value is not None:
            _set_dhcp_attr(dhcp_item, dhcp_attr, value)

    return dhcp_item


class Connector:
    """ Main class that connects Netbox objects to Kea DHCP config items """

    def __init__(self, nb, kea, prefix_subnet_map, pool_iprange_map,
                 reservation_ipaddr_map, check=False):
        self.nb = nb
        self.kea = kea
        self.subnet_prefix_map = prefix_subnet_map
        self.pool_iprange_map = pool_iprange_map
        self.reservation_ipaddr_map = reservation_ipaddr_map
        self.check = check

    def sync_all(self):
        """ Replace current DHCP configuration by a new generated one """

        self.kea.pull()
        self.kea.del_all_subnets()

        # Create DHCP configuration for each prefix
        all_failed = None
        for p in self.nb.all_prefixes():
            if all_failed is None:
                all_failed = True
            pl = f'prefix {p}: '
            logging.debug(f'{pl}generate DHCP config')
            # Speed up things by disabling auto-commit
            self.kea.auto_commit = False
            try:
                self._prefix_to_subnet(p, fullsync=True)
            except KeaError as e:
                logging.error(f'{pl}config failed. Error: {e}')
                continue

            # Make intermediate commits only when not in check mode to avoid
            # false errors of missing, not yet created, subnets.
            if not self.check:
                try:
                    self.kea.commit()
                except KeaError as e:
                    logging.error(f'{pl}commit failed. Error: {e}')
                    # Retry with auto-commit enabled to catch the faulty item
                    logging.warning(f'{pl}retry with auto commit on')
                    self.kea.auto_commit = True
                    try:
                        self._prefix_to_subnet(p, fullsync=True)
                    except KeaError as e:
                        logging.error(f'{pl}config failed. Error: {e}')
                        continue

            all_failed = False

        self.kea.auto_commit = True
        if all_failed is not True:
            self.push_to_dhcp()

    def push_to_dhcp(self):
        if self.check:
            logging.info('check mode on: config will NOT be pushed to server')
        else:
            self.kea.push()

    def reload_dhcp_config(self):
        self.kea.pull()

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
        subnet = _mk_dhcp_item(pref, self.subnet_prefix_map)
        subnet['subnet'] = pref.prefix
        if not fullsync:
            try:
                self.kea.update_subnet(pref.id, subnet)
            except (SubnetNotEqual, SubnetNotFound):
                # Subnet address has changed or subnet is missing, recreate it
                fullsync = True

        if fullsync:
            self.kea.set_subnet(pref.id, subnet)
            # Add host reservations
            for i in self.nb.ip_addresses(parent=pref.prefix):
                try:
                    self._ipaddr_to_resa(i, prefix=pref)
                except KeaClientError as e:
                    logging.error(f'prefix {pref} > IP {i}: {e}')
            # Add pools
            for r in self.nb.ip_ranges(parent=pref.prefix):
                try:
                    self._iprange_to_pool(r, prefix=pref)
                except KeaClientError as e:
                    logging.error(f'prefix {pref} > range {r}: {e}')

    def _iprange_to_pool(self, iprange, prefix=None):
        prefixes = [prefix] if prefix else self.nb.prefixes(
            contains=iprange.start_address)
        pool = _mk_dhcp_item(iprange, self.pool_iprange_map)
        start = str(ip_interface(iprange.start_address).ip)
        end = str(ip_interface(iprange.end_address).ip)
        pool['pool'] = f'{start}-{end}'
        for pref in prefixes:
            try:
                self.kea.set_pool(pref.id, iprange.id, pool)
            except SubnetNotFound:
                if not prefix:
                    logging.warning(
                        f'subnet {pref.prefix} is missing, sync it again')
                    self._prefix_to_subnet(pref, fullsync=True)
                else:
                    logging.error(f'requested subnet {pref.prefix} not found')

    def _ipaddr_to_resa(self, ip, prefix=None):
        prefixes = [prefix] if prefix else self.nb.prefixes(
            contains=ip.address)
        resa = _mk_dhcp_item(ip, self.reservation_ipaddr_map)
        if not resa.get('hw-address'):
            self.kea.del_resa(ip.id)
            return

        resa['ip-address'] = str(ip_interface(ip.address).ip)
        for pref in prefixes:
            try:
                self.kea.set_reservation(pref.id, ip.id, resa)
            except SubnetNotFound:
                if not prefix:
                    logging.warning(
                        f'subnet {pref.prefix} is missing, sync it again')
                    self._prefix_to_subnet(pref)
                else:
                    logging.error(f'requested subnet {pref.prefix} not found')
