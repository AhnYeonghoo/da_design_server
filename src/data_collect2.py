import os
from bs4 import BeautifulSoup
import requests
import datetime
from pymongo import MongoClient
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

def save_to_db(logger, stock_pairs):
    """Put the given {company: stock} pairs into DB

    :param logger: logger instance
    :type logger: logging.Logger
    :param stock_pairs: {company: stock} pairs
    :type stock_pairs: dict
    """
    today = datetime.date.today()
    today = datetime.datetime(today.year, today.month, today.day)

    for company in stock_pairs.keys():
        # Insert the company data if not exists.
        doc_company = col_company.find_one({'name': company})
        if not doc_company:
            col_company.insert_one({
                'name': company,
                'company_stock': []
            })
            doc_company = col_company.find_one({'name': company})
        company_id = doc_company['_id']

        # Insert stock value of today if not exists.
        doc_company_stock = col_company.find_one({
            '_id': company_id, 'company_stock.date': today})
        if not doc_company_stock:
            col_company.update_one(
                {"_id": company_id},
                {"$push": {
                    'company_stock': {
                        'date': today,
                        'value': float(stock_pairs[company])
                    }
                }
                }
            )
            logger.info('{} {}: new item in DB = {}'.format(
                today, company, stock_pairs[company]))
        else:
            logger.info('{} {}: already exist, so skipped.'.format(
                today, company))

    

def show_db(logger, limit=10):
    """Show company-related data in DB.

    :param logger: logger instance
    :type logger: logging.Logger
    :param limit: maximum # of items to show
    :type limit: int
    """
    for i, d in enumerate(col_company.find({})):
        if i == limit:
            break
        logger.info('DB(Company): {} {}'.format(
            d['name'], d['company_stock']))

if __name__ == '__main__':
    project_root_path = os.getenv("DA_DESIGN_SERVER")
    cfg = myconfig.get_config('{}/share/project.config'.format(project_root_path))
    log_path = cfg['logger'].get('log_directory')
    logger = mylogger.get_logger(log_path)

    ret = crawl_stock(logger)

    print('{} data collected.'.format(len(ret)))
    if not ret:
        exit()
    print('Top data instances:')
    for i, x in enumerate(ret.items()):
        logger.info('{}'.format(x))
        if i >= 10:
            break

    db_ip = cfg['db']['ip']
    db_port = int(cfg['db']['port'])
    db_name = cfg['db']['name']

    db_client = MongoClient(db_ip, db_port)
    db = db_client[db_name]

    col_company = db[cfg['db']['col_company']]

    # DB에 입력하기 전
    logger.info('DB status (before)')
    show_db(logger)

    # DB 입력
    logger.info('Saving to DB ----------------------')
    save_to_db(logger, ret)
    logger.info('----------------------  Saved to DB')
1
    # DB에 입력한 후
    logger.info('DB status (after)')
    show_db(logger)
