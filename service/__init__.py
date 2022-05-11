from flask import Flask, request, render_template
from flask_cors import CORS
import os
from da_design_server.src import mylogger, myconfig, mydb
import pdb
import datetime

app = Flask(__name__)
CORS(app)

# create a logger.
project_root_path = os.getenv("DA_DESIGN_SERVER")
cfg = myconfig.get_config('{}/share/project.config'.format(
    project_root_path))
log_directory = cfg['logger'].get('log_directory')
logger = mylogger.get_logger('app', log_directory)
db = mydb.mydb(cfg)



@app.route('/')
def web_main():
    return render_template("index.html")

@app.route('/help')
def web_help():
    return render_template("help.html")


@app.route('/api-list', methods=["POST"])
def api_list():
    top_k = request.json.get('top_k')
    logger.info('> API:list with {}'.format(top_k))

    ret = {"result": None, "msg": ""}
    if top_k:
        top_k = int(top_k)
        today_date = datetime.datetime.now()
        result = db.get_company_value_of_date(today_date, top_k)
        if result:
            ret["result"] = result
        else:
            ret['msg'] = '결과값 생성에 실패하였습니다.'
    else:
        ret['msg'] = 'top_k 값이 주어져있지 않습니다.'

    logger.info('< API:list with {}'.format(ret))
    return ret


