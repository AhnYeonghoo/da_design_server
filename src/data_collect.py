import os
from bs4 import BeautifulSoup
import requests
import datetime
from da_design_server.src import mylogger, myconfig
import pdb

def crawl_stock(logger, market='kospi', limit=60):
    """Collect data from www.sedaily.com, and return data pairs.
    :param logger: logger instance
    :type logger: logging.Logger
    :param market: "kospi" or "kosdaq" (default "kospi")
    :type marget: str
    :param limit: maximum # of items (default 60)
    :type limit: int
    :return: pairs of {company: stock}
    :rtype: dict
    """
    market = 1 if market == "kospi" else 2
    root_url = \
        ('https://www.sedaily.com/Stock/Content/StockInfoAjax?market=%d' % market) + \
         '&Sorting=0&Page=%d&Period=1&SubOrder=Desc&SubSorting=0'

    stocks = {}

    n_got = 0 # # of current items
    page = 1 # webpage index
    while n_got < limit:
        url = root_url % page
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        tr_list = [tr for tr in soup.select('tbody.no_line tr') if 'id' in tr.attrs]
        if not tr_list: 
            break
        for tr in tr_list:
            name = tr.select('td span a span')[1].text
            value = int(tr.select('td span.td_position')[1].text.replace(',', ''))
            stocks[name] = value
            n_got += 1
            if n_got == limit:
                break

            page += 1

        logger.info('{} items collected.'.format(n_got))
        return stocks


if __name__ == '__main__':

    project_root_path = os.getenv("DA_DESIGN_SERVER")
    cfg = myconfig.get_config('{}/share/project.config'.format(project_root_path))
    log_path = cfg['logger'].get('log_directory')
    logger = mylogger.get_logger(log_path)
    ret = crawl_stock(logger)
    pdb.set_trace()
