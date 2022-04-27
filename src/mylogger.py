import logging
from logging.handlers import TimedRotatingFileHandler as handler

def get_logger(name, log_directory='', log_to_stream=True):
    """Create a new logger and return it.

    :param name: name of logger.
    :type name: str
    :param log_directory: a path to make log files. If it is empty, then it does not write log files.
    :type log_directory: str
    :param log_to_stream: whether if we want to write log messages to streams (e.g., screen).
    :type log_to_stream: bool
    :return: a logger
    :rtype: logging.Logger
    """

    logger = logging.getLogger(name=name)
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)8s] %(message)s")
    logger.setLevel(logging.DEBUG)

    if log_directory:
        file_handler = handler(filename='{}/{}'.format(log_directory, name),
            when='midnight',
            interval=1,
            encoding='utf-8')
        file_handler.setFormatter(formatter)
        file_handler.suffix = "%Y%m%d%h%m"
        file_handler.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)

    if log_to_stream:
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        stream_handler.setLevel(logging.DEBUG)
        logger.addHandler(stream_handler)

    return logger
