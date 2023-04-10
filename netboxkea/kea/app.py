import logging
from copy import deepcopy
from ipaddress import ip_interface, ip_network

from .api import DHCP4API, FileAPI
from .exceptions import DuplicateValue, KeaCmdError, SubnetNotFound

logger = logging.getLogger('KeaApp')

# Kea configuration keys
SUBNETS = 'subnet4'
USR_CTX = 'user-context'
POOLS = 'pools'
RESAS = 'reservations'
PREFIX = 'netbox_prefix_id'
IP_RANGE = 'netbox_ip_range_id'
IP_ADDR = 'netbox_ip_address_id'


def autocommit(func):
    """ Decoraton to autocommit changes after method execution """

    def wrapper(self, *args, **kwargs):
        res = func(self, *args, **kwargs)
        commit_arg = kwargs.get('commit')
        if commit_arg is True or (commit_arg is None and self.auto_commit):
            self.commit()
        return res
    return wrapper


def boundaries(ip_range):
    """ Return a tuple of first and last ip_interface of the pool """

    # pool may be expressed by a "-" seperated range or by a network
    try:
        start, end = ip_range.split('-')
    except ValueError:
        net = ip_network(ip_range)
        return ip_interface(net.network_address), ip_interface(
            net.broadcast_address)
    else:
        return ip_interface(start), ip_interface(end)


class DHCP4App:

    def __init__(self, url=None):
        if url.startswith('http://') or url.startswith('https://'):
            self.api = DHCP4API(url)
        elif url.startswith('file://'):
            self.api = FileAPI(url.lstrip('file://'))
        else:
            raise ValueError(
                'Kea URL must starts either with "http(s)://" or "file://"')
        self.conf = None
        self.commit_conf = None
        self._has_commit = False
        self.auto_commit = True
        # self.pull()

    def pull(self):
        """ Fetch configuration from DHCP server  """

        self.conf = self.api.get_conf()
        # Set minimal expected keys and remove unwanted ones
        self.conf.setdefault(SUBNETS, [])
        for s in self.conf[SUBNETS]:
            try:
                # id key generates conflicts when conf is pushed back to server
                del s['id']
            except KeyError:
                pass
            s.setdefault(USR_CTX, {}).setdefault(PREFIX, None)
            for r in s.setdefault(RESAS, []):
                r.setdefault(USR_CTX, {}).setdefault(IP_ADDR, None)
            for p in s.setdefault(POOLS, []):
                p.setdefault(USR_CTX, {}).setdefault(IP_RANGE, None)

        self.commit_conf = deepcopy(self.conf)
        self.ip_uniqueness = self.conf.get('ip-reservations-unique', True)

    def commit(self):
        """ Record changes to the configuration. Return True if success """

        try:
            logger.debug('check configuration')
            self.api.raise_conf_error(self.conf)
        except KeaCmdError:
            # Drop current working config
            logger.error('config check failed, drop uncommited changes')
            self.conf = deepcopy(self.commit_conf)
            raise
        else:
            logger.debug('commit configuration')
            self.commit_conf = deepcopy(self.conf)
            self._has_commit = True
            return True

    def push(self):
        """ Update DHCP server configuration """

        if self._has_commit:
            logger.info('push configuration to runtime DHCP server')
            try:
                self.api.set_conf(self.commit_conf)
                logger.info('write configuration to permanent file')
                self.api.write_conf()
            except KeaCmdError as e:
                logger.error(f'config push or write rejected: {e}')

            self._has_commit = None
            # DHCP server is the true source, get config from it
            self.pull()
        else:
            logger.debug('no commit to push')

    def _check_commit(self, commit=None):
        """ Commit conf if required by argument or instance attribute """

        if commit is True or (commit is None and self.auto_commit):
            self.commit()

    @autocommit
    def set_subnet(self, prefix_id, subnet, options={}):
        """ Replace subnet {prefix_id} or append a new one """

        new = options.copy()
        new.update({'subnet': subnet, USR_CTX: {PREFIX: prefix_id},
                    RESAS: [], POOLS: []})
        found = None
        for s in self.conf[SUBNETS]:
            if s[USR_CTX][PREFIX] == prefix_id:
                found = s
            # Continue in order to check duplicates
            elif s['subnet'] == subnet:
                raise DuplicateValue(f'duplicate subnet {subnet}')
        if found:
            logger.info(f'subnets > ID {prefix_id}: replace with {subnet}')
            found.clear()
            found.update(new)
        else:
            logger.info(f'subnets: add {subnet}, ID {prefix_id}')
            self.conf[SUBNETS].append(new)

    @autocommit
    def del_subnet(self, prefix_id, commit=None):
        logger.info(f'subnets: remove subnet {prefix_id} if it exists')
        self.conf[SUBNETS] = [
            s for s in self.conf[SUBNETS] if s[USR_CTX][PREFIX] != prefix_id]

    @autocommit
    def del_all_subnets(self):
        logger.info('delete all current subnets')
        self.conf[SUBNETS].clear()

    @autocommit
    def set_subnet_options(self, prefix_id, subnet, options):
        """
        Replace options of subnet identified by the pair {prefix_id}/{subnet}.
        Raise SubnetNotFound if no subnet matches.
        """

        if 'subnet' in options:
            raise ValueError('"subnet" key must not be in options')

        for s in self.conf[SUBNETS]:
            if (s[USR_CTX][PREFIX] == prefix_id and s['subnet'] == subnet):
                logger.info(f'subnet {subnet}: update with {options}')
                s.update(options)
                break
        else:
            raise SubnetNotFound(f'key pair id={prefix_id}/subnet="{subnet}"')

    @autocommit
    def set_pool(self, prefix_id, iprange_id, start, end):
        """ Replace pool or append a new one """

        pool = f'{start}-{end}'
        new = {'pool': pool, USR_CTX: {IP_RANGE: iprange_id}}
        ip_start, ip_end = ip_interface(start), ip_interface(end)

        def raise_conflict(p):
            pool = p.get('pool')
            if pool:
                s, e = boundaries(pool)
                if s <= ip_start <= e or s <= ip_end <= e:
                    raise DuplicateValue(f'overlaps existing pool {pool}')

        self._set_subnet_item(
            prefix_id, POOLS, IP_RANGE, iprange_id, new, raise_conflict, pool)

    @autocommit
    def del_pool(self, iprange_id):
        self._del_prefix_item(POOLS, IP_RANGE, iprange_id)

    @autocommit
    def set_reservation(self, prefix_id, ipaddr_id, ipaddr, hw_addr, hostname):
        """ Replace host reservation or append a new one """

        new = {'ip-address': ipaddr, 'hw-address': hw_addr,
               'hostname': hostname, USR_CTX: {IP_ADDR: ipaddr_id}}

        def raise_conflict(resa):
            if resa.get('hw-address') == hw_addr:
                raise DuplicateValue(f'duplicate hw-address={hw_addr}')
            elif self.ip_uniqueness and resa.get('ip-address') == ipaddr:
                raise DuplicateValue(f'duplicate address={ipaddr}')

        self._set_subnet_item(
            prefix_id, RESAS, IP_ADDR, ipaddr_id, new, raise_conflict, hw_addr)

    @autocommit
    def del_resa(self, ipaddr_id):
        self._del_prefix_item(RESAS, IP_ADDR, ipaddr_id)

    def _set_subnet_item(self, prefix_id, item_list, item_key, item_id, new,
                         raise_conflict, display):
        """ Replace either a pool or a host reservation """

        for s in self.conf[SUBNETS]:
            found = None
            if s[USR_CTX][PREFIX] == prefix_id:
                # Prefix found
                for i in s[item_list]:
                    if i[USR_CTX][item_key] == item_id:
                        found = i
                    # Continue in order to check duplicates
                    else:
                        raise_conflict(i)

                if found:
                    logger.info(
                        f'subnet {prefix_id} > {item_list} > ID {item_id}: '
                        f'replace with {display}')
                    found.clear()
                    found.update(new)
                else:
                    logger.info(
                        f'subnet {prefix_id} > {item_list}: add {display}, '
                        f'ID {item_id}')
                    s[item_list].append(new)
                break
        else:
            raise SubnetNotFound(f'subnet {prefix_id}')

    def _del_prefix_item(self, item_list, item_key, item_id):
        """ Delete item from all subnets. Silently ignore non-existent item """

        logger.info(f'{item_list}: delete resa {item_id} if it exists')
        for s in self.conf[SUBNETS]:
            s[item_list] = [
                i for i in s[item_list] if i[USR_CTX][item_key] != item_id]
