import logging

from .config import get_config
from .connector import Connector
from .kea.app import DHCP4App
from .listener import WebhookListener
from .logger import init_logger
from .netbox import NetboxApp


def run():
    conf = get_config()
    init_logger(conf.log_level, conf.ext_log_level, conf.syslog_level_prefix)

    # Instanciate source, sink and connector
    logging.info(f'netbox: {conf.netbox_url}, kea: {conf.kea_url}')
    nb = NetboxApp(
        conf.netbox_url, conf.netbox_token, prefix_filter=conf.prefix_filter,
        iprange_filter=conf.iprange_filter,
        ipaddress_filter=conf.ipaddress_filter)
    kea = DHCP4App(conf.kea_url)
    conn = Connector(
        nb, kea, conf.subnet_prefix_map, conf.pool_iprange_map,
        conf.reservation_ipaddr_map, check=conf.check_only)

    if not conf.full_sync_at_startup and not conf.listen:
        logging.warning('Neither full sync nor listen mode has been asked')

    # Start a full synchronisation
    if conf.full_sync_at_startup:
        logging.info('Start full sync')
        conn.sync_all()

    # Start listening for events
    if conf.listen:
        logging.info(f'Listen for events on {conf.bind}:{conf.port}')
        server = WebhookListener(
            connector=conn, host=conf.bind, port=conf.port, secret=conf.secret,
            secret_header=conf.secret_header)
        server.run()
