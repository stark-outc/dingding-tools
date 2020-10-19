import numpy as np
import pandas as pd
from datetime import datetime
import re
import math


def judge_age(id_number):
    if len(str(id_number)) == 18:
        ydm = str(id_number)[6:14]
        year = ydm[:4]
        month = ydm[4:6]
        day = ydm[6:8]

        # dt = datetime(*(int(i) for i in [year, month, day]))
        # age = (datetime.now()-dt).days/365
        # age = (datetime(2020,2,21) - dt).days / 365
        # age = math.ceil(age)
        age = 2020 - int(year)

    elif len(str(id_number)) == 15:
        ydm = '19'+str(id_number)[6:12]
        year = ydm[:4]
        month = ydm[4:6]
        day = ydm[6:8]

        # dt = datetime(*(int(i) for i in [year, month, day]))
        # # age = (datetime.now()-dt).days/365
        # age = (datetime(2020, 1, 21) - dt).days / 365
        # age = math.ceil(age)
        age = 2020 - int(year)

    else:
        ydm = np.nan
        year = np.nan
        month = np.nan
        day = np.nan

        dt = np.nan
        age = np.nan

    return age


def judge_sex(id_number):
    if len(str(id_number)) == 18:
        if int(str(id_number)[16]) in (1, 3, 5, 7, 9):
            return '男'
        elif int(str(id_number)[16]) in (2, 4, 6, 8, 0):
            return '女'
    elif len(str(id_number)) == 15:
        if int(str(id_number)[14]) in (1, 3, 5, 7, 9):
            return '男'
        elif int(str(id_number)[14]) in (2, 4, 6, 8, 0):
            return '女'
    return np.nan


def cut_age(x):
    if x >= 45:
        return 'A4'
    elif x >= 30:
        return 'A3'
    elif x >= 22:
        return 'A2'
    else:
        return 'A1'


def cut_sex(x):
    if x == '男':
        return 'M'

    elif x == '女':
        return 'F'

    else:
        return 'U'


def cut_pro(x):
    if x in ['上海', '天津',  '浙江',  '江苏', '北京', '重庆']:
        return 'P1'
    elif x in ['广东', '安徽', '四川', '河南']:
        return 'P2'
    # elif x in ['江西',  '山东', '山西',  '甘肃', '云南', '湖南', '河北', '湖北']:
    #     return 'P3'
    # elif x in ['青海', '新疆', '西藏', '宁夏', '内蒙古', '辽宁'] + ['贵州', '广西', '陕西', '福建', '黑龙江', '吉林', '海南']:
    #     return 'P5'
    else:
        return 'P5'


def set_rules_x_portrait(x):
    if x in ['A2-F-P1', 'A2-M-P1', 'A3-M-P1', 'A3-F-P2', 'A3-F-P1', 'A4-F-P1', 'A4-M-P1', 'A4-F-P2']:
        return 0
    #'A0-F-P1',
    elif x in ['A3-F-P3', 'A4-M-P2', 'A3-M-P3', 'A4-M-P3', 'A3-M-P2', 'A1-F-P1', 'A2-M-P2', 'A2-M-P3', 'A4-F-P3', 'A2-F-P2']:
        return 1
    else:
        return 2


def two_sides(x, side_type='left'):
    if pd.isnull(x):
        x1 = 0
        x2 = 0
    else:
        if '<' in x:
            x1 = -float('inf')
            x2 = float(x[1:])
        elif '>=' in x:
            x1 = float(x[2:])
            x2 = float('inf')
        elif (r'[' in x) and (r')' in x):
            x1 = float(re.findall('\[.*?,', x)[0][1:-1])
            x2 = float(re.findall(',.*?\)', x)[0][1:-1])
        else:
            pass

    if side_type == 'left':
        return x1
    elif side_type == 'right':
        return x2
    else:
        raise TypeError
