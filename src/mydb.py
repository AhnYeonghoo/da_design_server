from pymongo import MongoClient
from sklearn.linear_model import LinearRegression as lr
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

    def get_col_predicted_company_stock(self):
        """Get collection of predicted company stock.

        :return: predicted company stock collection.
        :rtype: pymongo.collection.Collection
        """
        return self._db[self._cfg['db']['col_predicted_company_stock']]

    def get_predicted_company_stock(self, company_name, logger, D=3, W=3):
        """Predict future(tomorrow) stock value based on the previous data

        :param company_name: company name
        :type company_name: str
        :param logger: logger instance
        :type logger: logging.Logger
        :param D: # of stock values to use for training model
        :type D: int
        :param W: feature dimension (window size)
        :type W: int
        :return: predicted stock value
        :rtype: float
        """
        col_company = self.get_col_company()
        doc_company = col_company.find_one({'name': company_name})
        if not doc_company:
            logger.info('{} 기업은 존재하지 않음'.format(company_name))
            return 0.0

        col_pred_company_stock = self.get_col_predicted_company_stock()
        doc_pred_company_stock = col_pred_company_stock.find_one({'Company': doc_company['_id']})
        # 해당 기업에 대한 예측한 사례가 없었으면, 일단 빈 껍데기 만듬
        if not doc_pred_company_stock:
            col_pred_company_stock.insert_one({
                'Company': doc_company['_id'],
                'company_stock': []})
            doc_pred_company_stock = col_pred_company_stock.find_one({'Company': doc_company['_id']})

        # 내일에 해당되는 예측 값이 없으면 만들어줌
        tomorrow = datetime.datetime.today() + datetime.timedelta(days=1)
        tomorrow = datetime.datetime(tomorrow.year, tomorrow.month, tomorrow.day)
        doc_new = col_pred_company_stock.find_one({
            'Company': doc_company['_id'], 'company_stock.date': tomorrow})

        predicted_value = None
        if not doc_new:
            data = [x['value'] for x in doc_company['company_stock']]
            if len(data) < W + 1:
                logger.info('{} 기업의 데이터가 {}개보다 적어서 최근 값으로 예측'.format(company_name, W))
                predicted_value = data[-1]
            else:
                if len(data) <= D:
                    target_data = data[:]
                else:
                    target_data = data[len(data)-D:]

                # 모델 학습
                m = lr()
                X = []
                y = []
                for i in range(len(target_data) - W):
                    X += [target_data[i:i+W]]
                    y += [target_data[i+W]]
                m.fit(X, y)
                logger.info('{}개의 데이터로 모델 학습 완료.'.format(len(X)))

                # 내일 값 예측
                X = [target_data[len(target_data)-W:]]
                predicted_value = m.predict(X)[0]

            col_pred_company_stock.update_one(
                    {'Company': doc_company['_id']},
                    {'$push': {
                        'company_stock': {
                            'date': tomorrow,
                            'value': float(predicted_value)
                        }
                    }})
        else:
            logger.info('기 존재하는 예측치 사용.')
            for dvs in doc_new['company_stock']:
                if dvs['date'] == tomorrow:
                    predicted_value = dvs['value']
                    break
        return predicted_value
    
    

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

    result = db.get_predicted_company_stock('삼성전자', logger)
    print(result)

