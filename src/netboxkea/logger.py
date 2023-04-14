import logging
import syslog

_SD_DAEMON_MAP = {
    logging.DEBUG: syslog.LOG_DEBUG,
    logging.INFO: syslog.LOG_INFO,
    logging.WARNING: syslog.LOG_WARNING,
    logging.ERROR: syslog.LOG_ERR,
    logging.CRITICAL: syslog.LOG_CRIT
    }


def init_logger(log_level_name, ext_log_level_name, syslog_level_prefix):
    """ Configure loggers """

    log_level = _level_name_to_int(log_level_name)
    if syslog_level_prefix:
        logger = logging.getLogger()
        logger.setLevel(log_level)
        ch = logging.StreamHandler()
        ch.setFormatter(_SdDaemonFormatter())
        logger.addHandler(ch)
    else:
        logging.basicConfig(
            level=log_level, format='%(asctime)s [%(levelname)s] %(message)s')
        logger = logging.getLogger()

    # Log level for external modules
    ext_log_level = _level_name_to_int(ext_log_level_name)
    logging.getLogger('urllib3.connectionpool').setLevel(ext_log_level)


def _level_name_to_int(name):
    num = getattr(logging, name.upper(), None)
    if not isinstance(num, int):
        raise ValueError(f'Invalid log level name: {name}')
    return num


class _SdDaemonFormatter(logging.Formatter):
    def format(self, record):
        sd_levelno = _SD_DAEMON_MAP.get(record.levelno, syslog.LOG_INFO)
        return f'<{sd_levelno}>' + super().format(record)
