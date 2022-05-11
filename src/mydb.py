from pymongo import MongoClient
from da_design_server.src import mylogger, myconfig
import datetime
import os
import pdb

class mydb:
    def __init__(self, cfg):
        """Get DB.

        :param cfg: config parser
        :type cfg: configparser.SafeConfigParser
        """
        self._db_ip = cfg['db']['ip']
        self._db_port = int(cfg['db']['port'])
        self._db_name = cfg['db']['name']

        self._db_client = MongoClient(self._db_ip, self._db_port)
        # pymongo.database.Database
        self._db = self._db_client[self._db_name]
        self._cfg = cfg

    def get_col_company(self):
        """Get compnay collection.

        :return: company collection.
        :rtype: pymongo.collection.Collection
        """
        return self._db[self._cfg['db']['col_company']]

    def get_company_value_of_date(self, the_date, topk=10):
        """Get company-value(of the day) pairs.

        :param the_date: the date we want to get pairs.
        :type the_date: datetime.datetime
        :param topk: top-k items
        :type topk: int
        :return: company-value pairs.
        :rtype: dict
        """
        col_company = self.get_col_company()
        docs_company = col_company.find()
        ret = dict()
        for c in docs_company:
            for cstock in c['company_stock']:
                d, v = cstock['date'], cstock['value']
                if the_date.date() == d.date():
                    ret[c['name']] = v
                    if len(ret) >= topk:
                        return ret
        return ret
if __name__ == '__main__':
    project_root_path = os.getenv("DA_DESIGN_SERVER")
    cfg = myconfig.get_config('{}/share/project.config'.format(project_root_path))
    log_path = cfg['logger'].get('log_directory')
    logger = mylogger.get_logger(log_path)

    db = mydb(cfg)
    col_company = db.get_col_company()

    logger.info('What\'s in DB company collection..')
    for i, d in enumerate(col_company.find({})):
        if i == 10:
            break
        logger.info('DB(Company): {} {}'.format(
            d['name'], d['company_stock']))

    d = datetime.datetime.today()
    result = db.get_company_value_of_date(d)
    print(result)

