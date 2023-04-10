import pynetbox
from ipaddress import ip_interface, ip_network


class NetboxApp:

    def __init__(self, url, token, prefix_filter={}, iprange_filter={},
                 ipaddress_filter={'status': 'dhcp'}):
        self.nb = pynetbox.api(url, token=token)
        self.prefix_filter = prefix_filter
        self.iprange_filter = iprange_filter
        self.ipaddress_filter = ipaddress_filter

    def prefix(self, id_):
        return self.nb.ipam.prefixes.get(id=id_, **self.prefix_filter)

    def prefixes(self, contains):
        return self.nb.ipam.prefixes.filter(
            **self.prefix_filter, contains=contains)

    def all_prefixes(self):
        return self.nb.ipam.prefixes.filter(**self.prefix_filter)

    def ip_range(self, id_):
        return self.nb.ipam.ip_ranges.get(id=id_, **self.iprange_filter)

    def ip_ranges(self, parent):
        # Emulate "parent" filter as NetBox API doesn’t support it on
        # ip-ranges objects (v3.4).
        parent_net = ip_network(parent)
        for r in self.nb.ipam.ip_ranges.filter(
                parent=parent, **self.iprange_filter):
            if (ip_interface(r.start_address) in parent_net
                    and ip_interface(r.end_address) in parent_net):
                yield r

    def ip_address(self, id_):
        i = self.nb.ipam.ip_addresses.get(
            id=id_, assigned_to_interface=True, **self.ipaddress_filter)
        if i and i.assigned_object.mac_address:
            return i

    def ip_addresses(self, **filters):
        if not filters:
            raise ValueError(
                'Netboxapp.ip_addresses() requires at least one keyword arg')
        for i in self.nb.ipam.ip_addresses.filter(
                assigned_to_interface=True, **self.ipaddress_filter,
                **filters):
            if i.assigned_object.mac_address:
                yield i
