import logging
import sys
from argparse import ArgumentParser
from dataclasses import dataclass, field
try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

from .__about__ import __version__


@dataclass(frozen=True)
class Config:
    config_file: str = None
    check_only: bool = False
    full_sync_at_startup: bool = False
    listen: bool = False
    bind: str = '127.0.0.1'
    port: int = 8001
    secret: str = None
    secret_header: str = 'X-netbox2kea-secret'
    log_level: str = 'warning'
    ext_log_level: str = 'warning'
    syslog_level_prefix: bool = False
    kea_url: str = None
    netbox_url: str = None
    netbox_token: str = None
    prefix_filter: dict = field(default_factory=lambda: {
        'cf_dhcp_enabled': True})
    ipaddress_filter: dict = field(default_factory=lambda: {'status': 'dhcp'})
    iprange_filter: dict = field(default_factory=lambda: {'status': 'dhcp'})
    subnet_prefix_map: dict = field(default_factory=lambda: {
        'option-data.routers': 'custom_fields.dhcp_option_data_routers',
        'option-data.domain-search':
            'custom_fields.dhcp_option_data_domain_search',
        'option-data.domain-name-servers':
            'custom_fields.dhcp_option_data_domain_name_servers',
        'next-server': 'custom_fields.dhcp_next_server',
        'boot-file-name': 'custom_fields.dhcp_boot_file_name',
        'valid-lifetime': 'custom_fields.dhcp_valid_lifetime'})
    pool_iprange_map: dict = field(default_factory=lambda: {})
    reservation_ipaddr_map: dict = field(default_factory=lambda: {
        # Get MAC address from custom field, fallback to assigned interface
        'hw-address': ['custom_fields.dhcp_reservation_hw_address',
                       'assigned_object.mac_address'],
        # Get hostname from DNS name, fallback to device/vm name
        'hostname': ['dns_name', 'assigned_object.device.name',
                     'assigned_object.virtual_machine.name']
        })


def get_config():
    settings = {}

    parser = ArgumentParser()
    parser.add_argument(
        '--version', action='version', version=f'Version {__version__}')
    parser.add_argument('-c', '--config-file', help='configuration file')
    parser.add_argument('-n', '--netbox-url', help='')
    parser.add_argument('-t', '--netbox-token', help='')
    parser.add_argument('-k', '--kea-url', help='')
    parser.add_argument(
        '-l', '--listen', action='store_true', default=None, help='')
    parser.add_argument('-b', '--bind', help='')
    parser.add_argument('-p', '--port', type=int, help='')
    parser.add_argument(
        '--secret', help=f'Default header: {Config.secret_header}')
    parser.add_argument(
        '-s', '--sync-now', action='store_true', dest='full_sync_at_startup',
        default=None, help='')
    parser.add_argument(
        '--check', action='store_true', dest='check_only', default=None,
        help='')
    parser.add_argument(
        '-v', '--verbose', action='count', default=0,
        help='Increase verbosity. May be specified up to 3 times')
    # TODO: parser.add_argument('-f', '--foreground', help='')
    args = parser.parse_args()

    # Load TOML config file
    if args.config_file is not None:
        with open(args.config_file, 'rb') as f:
            tomlconf = tomllib.load(f)
        settings.update(tomlconf)

    # Load non-None command line arguments
    if args.verbose == 1:
        args.log_level = 'info'
    elif args.verbose == 2:
        args.log_level = 'debug'
        settings['ext_log_level'] = 'info'
    elif args.verbose >= 3:
        args.log_level = 'debug'
        settings['ext_log_level'] = 'debug'
    del args.verbose
    settings.update({k: v for k, v in args.__dict__.items() if v is not None})

    # Check existence of required settings
    for attr in ('kea_url', 'netbox_url'):
        if attr not in settings:
            logging.fatal(
                f'Setting "{attr}" not found, neither on command line '
                'arguments nor in configuration file (if any)')
            sys.exit(1)

    conf = Config(**settings)

    if not set(['hw-address', 'hostname']).issubset(
            conf.reservation_ipaddr_map):
        logging.fatal(
            'Setting "reservation_ipaddr_map" must have a mapping for '
            '"hw-address" and "hostname" DHCP parameters')
        sys.exit(1)

    return conf
