import logging

from .config import get_config
from .connector import Connector
from .kea.app import DHCP4App
from .listener import WebhookListener
from .netbox import NetboxApp


def run():
    conf = get_config()

    # Configure logger
    num_log_level = getattr(logging, conf.log_level.upper(), None)
    if not isinstance(num_log_level, int):
        raise ValueError(f'Invalid log level: {conf.log_level}')

    logging.basicConfig(
        # level=num_log_level, format='[%(levelname)s] %(name)s - %(message)s')
        level=num_log_level, format='[%(levelname)s] %(message)s')
    logger = logging.getLogger()
    # Log level for external modules
    ext_num_log_level = getattr(logging, conf.ext_log_level.upper(), None)
    logging.getLogger('urllib3.connectionpool').setLevel(ext_num_log_level)

    logger.info(f'netbox: {conf.netbox_url}, kea: {conf.kea_url}')
    nb = NetboxApp(
        conf.netbox_url, conf.netbox_token, prefix_filter=conf.prefix_filter,
        iprange_filter=conf.iprange_filter,
        ipaddress_filter=conf.ipaddress_filter)
    kea = DHCP4App(conf.kea_url)
    conn = Connector(
        nb, kea, check=conf.check_only, prefix_dhcp_map=conf.prefix_dhcp_map)

    # Start a full synchronisation
    if conf.full_sync_at_startup:
        logger.info('Start full sync')
        conn.sync_all()

    # Start listening for events
    if conf.listen:
        logger.info(f'Listen for events on {conf.bind}:{conf.port}')
        server = WebhookListener(
            connector=conn, host=conf.bind, port=conf.port, secret=conf.secret,
            secret_header=conf.secret_header)
        server.run()
