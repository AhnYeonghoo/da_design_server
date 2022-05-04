from configparser import SafeConfigParser
import os

def get_config(filepath):
    """Get config parser.

    :param filepath: a config filepath to read.
    :type filepath: str
    :return: a parser (Use it like a "dictionary")
    :rtype: configparser.SafeConfigParser
    """
    parser = SafeConfigParser(os.environ)
    ret = parser.read(filepath)
    if not ret:
        print('get_config(): Failed to parser.read()')
        return False
    return parser

