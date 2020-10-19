# -*- coding: utf-8 -*-
"""
Created on Mon Aug 31 09:32:24 2020

@author:占小雨
"""

import lctools
from OP_Method import DingDingRobotService
import tab_pic
import update_model_score
import pandas as pd
from datetime import datetime,timedelta
import bs_meathod
import os
import numpy as np
import json

class GetScoreData():
    def __init__(self, user, passward, db_host=None):
        self.user = user
        self.passward = passward
        if db_host is None:
            self.db_host = "rr-uf6i4aq7jg3z292vv.mysql.rds.aliyuncs.com"
        else:
            self.db_host = db_host
        self.mysql_server = bs_meathod.MysqlService(self.db_host,
                                                    self.user, self.passward)
    
    def get_score_data(self, start_time, end_time, product_name_list, service_id_list):
        get_data_sql = """
            SELECT lo.id, lo.create_time as '调用日期',lo.product_name, lo.service_id, lo.user_id, lo.raw_data_service, lo.data,
                    au.description, aps.description
            FROM log_inout_common lo
            left join api_user au on lo.user_id = au.id
            left join api_service aps on lo.service_id = aps.id
            WHERE lo.create_time >='{}' and lo.create_time <= '{}'
            AND lo.product_name in {} and lo.service_id in {} and lo.user_id not in (5, 35, 43,44,90)
            """.format(start_time, end_time, product_name_list, service_id_list)
        data = self.mysql_server.get_sql_data('risk-data-gateway', get_data_sql)
        return data

def main(path, mysql_server,start_time,end_time):
    score_server = mysql_server
    save_path = path
    id_list = [342, 343, 374, 380, 381, 382, 383, 384, 385, 377, 367, 347, 350, 387, 388
               ] + [i for i in range(409, 418, 1)]
    name_list1 = ['finance_fraud_score_t1'] + ['finance_fraud_score_t1_v' + str(i + 1) for i in range(9)]
    name_list2 = ['finance_fraud_score_t2'] + ['finance_fraud_score_t2_v' + str(i + 1) for i in range(3)]
    name_list3 = ['finance_credit_score_b1']
    
    biaozhun_risk_data = score_server.get_score_data(start_time, end_time, tuple(name_list1 + name_list2 + name_list3),
                                                     tuple(id_list))
    if biaozhun_risk_data.shape[0] > 0:
        # biaozhun_risk_data.to_csv(os.path.join(save_path, '{}_分数调用记录.csv'.format(now_strf)), index=False)
       return biaozhun_risk_data
    else:
       return pd.DataFrame()
        
        
        
def api_rename_func(x):
    if '联邦学习' in x:
        for fh in [' ', '（', '(', '）', ')', '__']:
            x = x.replace(fh, '_')
        if '_测试' in x:
            x = x.replace('_测试', '')
        if '测试_' in x:
            x = x.replace('测试_', '')
        if '测试' in x:
            x = x.replace('测试', '')
        if '反欺诈t2_' in x:
            x = x.replace('反欺诈t2_', '')
        if x[-1] == '_':
            x = x[:-1]
        return x
    elif '信用分b1' in x:
        for fh in [' ', '（', '(', '）', ')', ',', '，', '__']:
            x = x.replace(fh, '_')
            x2 = x.split('_')
        x_leave = []
        for i in x2:
            if '给' not in i and 'DY' not in i and i != '':
                x_leave.append(i)
        return '_'.join(x_leave)
    elif '标准反欺诈分' in x:
        for fh in [' ', '（', '(', '）', ')', ',', '，', '__']:
            x = x.replace(fh, '_')
        if '_V2' in x:
            x = x.replace('_V2', '')
        if 'V2' in x:
            x = x.replace('V2', '')
        if x[-1] == '_':
            x = x[:-1]
        return x.replace('tx标准', '')
    else:
        return x


def jiexi(x):
    try:
        out = json.loads(str(x))
    except Exception as e:
        print(e)
        print(x)


def data_clean(df):
    data = df.copy()
    data['api_user_name'] = data['description'].map(lambda x: x.split('生产账号')[0] if '生产账号' in x else (
        x.split('内部账号')[0] if '内部账号' in x else x))  # 客户名称
    data['api_service_name'] = data['aps.description'].map(api_rename_func)  # 产品名称
    data = data[data['data'].notna()]
    data['data2'] = data['data'].map(
        lambda x: json.loads(str(x)) if '=' not in str(x) else (x.split('=')[1].split(',')[0] if '=' in str(x) else x))
    data['score'] = data['data2'].map(
        lambda x: x['evil_level'] if isinstance(x, dict) and 'evil_level' in x.keys() else (
            x if isinstance(x, int) or isinstance(x, float) or isinstance(x, str) else np.nan
        ))
    data['score'] = data['score'].astype(float)  # 分数解析
    data.drop(['description', 'aps.description', 'data2', 'data'], axis=1, inplace=True)
    return data

if __name__ == '__main__':
    #提取数据
    mysql_server = GetScoreData('prod_readonly', 'On1moBvlecAJspzp')
    save_path = r'C:/Test/监控预警/模型分数监控/分数调用记录'
    
    end_time=datetime.now()
    start_time=end_time-timedelta(minutes=5)
    biaozhun_risk_data=main(save_path,mysql_server,start_time,end_time)
    _data= biaozhun_risk_data
    
    if _data.empty==False:
        try:
            _data = data_clean(_data)
        except json.decoder.JSONDecodeError as e:
            raise ValueError('数据解析出错')
  
   #_data.to_excel('C:/Test/监控预警/模型分数监控/a.xlsx')
    
        _data['score_min']=0.015
        _data['score_max']=_data['api_service_name'].map(lambda x:  1 if '联邦学习' in x else 100)
        _data['warning']=(_data['score']>_data['score_max']) | (_data['score']<_data['score_min']) 
   # _data.to_excel('C:/Test/监控预警/模型分数监控/a.xlsx')
        
        call=_data[_data['warning']==True]
        now=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        text_lst=[]
     
        if call.empty==False:
            lst=call.to_dict(orient='records')
            for i,j in enumerate(lst):
                print(j)
                texti = '告警：评分超出范围！！！{}_{},\n---------------\n分数值为:{}\n分数最小值为:{}\n分数最大值为:{}\n时间：{}'\
                .format(j['api_user_name'],j['api_service_name'],j['score'],j['score_min'],j['score_max'],now)
                text_lst.append(texti)
    else:
        text_lst=[]
        
     
    url='https://oapi.dingtalk.com/robot/send?access_token=e8dc4ae17543199c25f4d6a1c92862b2aa288bcf83941da98d760378c1e5cf38'
    dd_server =DingDingRobotService(url,1)
    title='调用告警'
    file_url=None
    text_lst=['告警:测试bat运行']
    for i in text_lst:
        text = i
        dd_server.dingding(title,text,file_url)    
        
    
 
