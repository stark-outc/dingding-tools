# -*- coding: utf-8 -*-
# @Time    : 2020/6/15 10:36
# @Author  : Daiyong

import os
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
import sys

sys.path.append(r'C:\Users\徐钦华\Desktop\数据分析项目\模型分数监控')
from hz_tools import bs_meathod_n


class GetScoreData():
    def __init__(self, user, passward, db_host=None):
        self.user = user
        self.passward = passward
        if db_host is None:
            self.db_host = ""
        else:
            self.db_host = db_host
        self.mysql_server = bs_meathod_n.MysqlService(self.db_host,
                                                    self.user, self.passward)
    
    def get_score_data(self, start_time, end_time, product_name_list, service_id_list):
        get_data_sql = """
            SELECT lo.id, lo.create_time as '调用日期',lo.product_name, lo.service_id, lo.user_id, lo.raw_data_service, lo.data,
                    au.description, aps.description
            FROM log_inout_common lo
            left join api_user au on lo.user_id = au.id
            left join api_service aps on lo.service_id = aps.id
            WHERE lo.create_time >= '{}' and lo.create_time < '{}'
            AND lo.product_name in {} and lo.service_id in {} and lo.user_id not in (5, 35, 43,44,90)
            """.format(start_time, end_time, product_name_list, service_id_list)
        data = self.mysql_server.get_sql_data('risk-data-gateway', get_data_sql)
        return data


def main(path, mysql_server, n=0):
    score_server = mysql_server
    save_path = path
    today = datetime.today().date() - timedelta(days=n)
    yestoday = today - timedelta(days=1)
    yestoday_strf = datetime.strftime(yestoday, '%Y%m%d')
    
    id_list = [342, 343, 374, 380, 381, 382, 383, 384, 385, 377, 367, 347, 350, 387, 388
               ] + [i for i in range(409, 418, 1)]
    name_list1 = ['finance_fraud_score_t1'] + ['finance_fraud_score_t1_v' + str(i + 1) for i in range(9)]
    name_list2 = ['finance_fraud_score_t2'] + ['finance_fraud_score_t2_v' + str(i + 1) for i in range(3)]
    name_list3 = ['finance_credit_score_b1']
    
    biaozhun_risk_data = score_server.get_score_data(yestoday, today, tuple(name_list1 + name_list2 + name_list3),
                                                     tuple(id_list))
    if biaozhun_risk_data.shape[0] > 0:
        biaozhun_risk_data.to_csv(os.path.join(save_path, '{}_分数调用记录.csv'.format(yestoday_strf)), index=False)


if __name__ == '__main__':
    mysql_server = GetScoreData('user', 'password')
    save_path = r'C:\Users\徐钦华\Desktop\数据分析项目\模型分数监控\模型分数监控\分数调用记录'
    main(save_path, mysql_server, n=0)

