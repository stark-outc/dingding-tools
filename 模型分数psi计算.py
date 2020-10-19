# -*- coding: utf-8 -*-
# @Time    : 2020/8/19 11:40
# @Author  : Daiyong

import sys

sys.path.append(r'C:\Users\运营\PycharmProjects')
import pandas as pd
from hz_tools.OP_Method import DingDingRobotService, FileUrl
import os
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import json
import numpy as np
from prettytable import PrettyTable
from hz_tools import tab_pic
import update_model_score


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
    # 更新昨日分数
    update_model_score.main(r'C:\Users\运营\PycharmProjects\模型分数监控\分数调用记录',
                            update_model_score.GetScoreData('prod_readonly', 'On1moBvlecAJspzp'),
                            n=0)
    print('分数更新成功')
    # 存储地址
    data_path = r'C:\Users\运营\PycharmProjects\模型分数监控\分数调用记录'

    # 时间段区分
    # psi:昨日/本周, 本周/本月, 本月/本季; 调用量:昨日,本周,本月,本季
    today = datetime.today().date() - timedelta(days=0)
    yestoday = today - timedelta(days=1)
    yestoday_strf = datetime.strftime(yestoday, '%Y%m%d')
    week_start_day = today - timedelta(today.weekday())
    if week_start_day >= yestoday:
        week_start_day = today - timedelta(today.weekday() + 7)
    month_start_day = datetime(today.year, today.month, 1, 0, 0, 0).date()
    if month_start_day >= week_start_day:
        month_start_day = datetime(today.year, today.month, 1, 0, 0, 0).date() - relativedelta(months=1)
    q_start_day = datetime(today.year, ((today.month - 1) // 3 + 1) * 3 - 2, 1, 0, 0, 0).date()
    if q_start_day >= month_start_day:
        q_start_day = datetime(today.year, ((today.month - 1) // 3 + 1) * 3 - 2, 1, 0, 0, 0).date() - relativedelta(
            months=3)
    if q_start_day <= datetime(today.year, 1, 1, 0, 0, 0).date():
        q_start_day = datetime(today.year, 1, 1, 0, 0, 0).date()

    # 数据加载
    file_list = os.listdir(data_path)

    # 文件筛选
    file_list = [i for i in file_list if
                 int(i.split('_')[0]) >= (q_start_day.year * 10000 + q_start_day.month * 100 + q_start_day.day)]

    data_all = []
    for i in file_list:
        with open(os.path.join(data_path, i), encoding='utf-8') as f:
            _data = pd.read_csv(f)
        try:
            _data = data_clean(_data)
            data_all.append(_data)
        except json.decoder.JSONDecodeError as e:
            print(i)
            raise ValueError('文件{}解析出错'.format(i))
    data_all = pd.concat(data_all, sort=False)
    data_all['调用日期'] = data_all['调用日期'].astype(np.datetime64)
    data_all = data_all[(data_all['api_user_name'] != 'hz_data') & (
        data_all['调用日期'].map(lambda x: True if x.date() >= q_start_day else False))]

    # 时间分段

    data_all['调用日期分类'] = data_all['调用日期'].map(lambda x: 'today' if x.date() > yestoday else (
        '昨日' if x.date() == yestoday else (
            '本周' if x.date() >= week_start_day else (
                '本月' if x.date() >= month_start_day else (
                    '本季' if x.date() >= q_start_day else 'before_本季'
                )
            )
        )
    ))

    # 调用量统计
    data_all['api_service_name2'] = data_all['api_service_name'].map(lambda x: '联邦学习' if '联邦学习' in x else (
        '反欺诈评分' if '反欺诈分' in x else ('信用分' if '信用分' in x else '其他产品')
    ))
    data_all['api_service_name'] = data_all['api_service_name'].map(lambda x: '_'.join(x.split('_')[1:]))
    dy_num = pd.pivot_table(data=data_all, index=['api_service_name2', 'api_service_name', 'api_user_name'],
                            columns=['调用日期分类'], values='id', aggfunc='count').rename(
        columns=lambda x: '调用量_' + str(x)).fillna(0).reset_index()

    # psi计算
    data_all.reset_index(drop=True, inplace=True)
    bins1 = [10 * i for i in range(11)]
    bins2 = [0.0, 0.01815554, 0.02266081, 0.02748155, 0.03255707,
             0.03807066, 0.04444657, 0.05201936, 0.06242657, 0.08290853, 1.0]
    data_all.loc[data_all.api_service_name2 == '联邦学习', 'score_bins'] = pd.cut(
        data_all.loc[data_all.api_service_name2 == '联邦学习', 'score'],
        bins=bins2)
    data_all.loc[data_all.api_service_name2 != '联邦学习', 'score_bins'] = pd.cut(
        data_all.loc[data_all.api_service_name2 != '联邦学习', 'score'],
        bins=bins1)

    psi_data = []
    for i, j in data_all.groupby(['api_service_name2', 'api_user_name', 'api_service_name']):
        _data_psi = pd.pivot_table(data=j, index=['score_bins'], columns='调用日期分类', values='id', aggfunc='count')
        _data_psi = _data_psi / _data_psi.sum()
        _data_psi.fillna(0.00001, inplace=True)
        try:
            ystd_wtd_psi = _data_psi.apply(lambda x: (x['昨日'] - x['本周']) * (np.log(x['昨日'] / x['本周'])),
                                           axis=1).sum()
        except KeyError:
            ystd_wtd_psi = np.nan
        try:
            wtd_mtd_psi = _data_psi.apply(lambda x: (x['本周'] - x['本月']) * (np.log(x['本周'] / x['本月'])), axis=1).sum()
        except KeyError:
            wtd_mtd_psi = np.nan
        try:
            mtd_qtd_psi = _data_psi.apply(lambda x: (x['本月'] - x['本季']) * (np.log(x['本月'] / x['本季'])), axis=1).sum()
        except KeyError:
            mtd_qtd_psi = np.nan
        psi_data.append([*i, ystd_wtd_psi, wtd_mtd_psi, mtd_qtd_psi])
    psi_data = pd.DataFrame(psi_data, columns=['api_service_name2', 'api_user_name', 'api_service_name',
                                               '昨日psi（vs本周）', '本周psi（vs本月）', '本月psi（vs本季度）'])
    last_data = pd.merge(psi_data, dy_num, how='outer', on=['api_service_name2', 'api_user_name', 'api_service_name'])
    last_data = last_data[
        last_data[['昨日psi（vs本周）', '本周psi（vs本月）', '本月psi（vs本季度）']].apply(lambda x: False if x.isna().all() else
        True, axis=1)]
    last_data.rename(columns={'api_service_name2': '分类', 'api_service_name': '产品名称', 'api_user_name': '客户名称'},
                     inplace=True)
    columns = ['分类',
               '客户名称',
               '产品名称',
               '昨日psi（vs本周）',
               '本周psi（vs本月）',
               '本月psi（vs本季度）',
               '调用量_昨日',
               '调用量_本周',
               '调用量_本月',
               '调用量_本季']
    last_data = last_data[columns]

    # 加汇总
    last_data.reset_index(drop=True, inplace=True)
    last_data.loc[last_data.shape[0] + 1, ['调用量_昨日', '调用量_本周', '调用量_本月', '调用量_本季']] = last_data[
        ['调用量_昨日', '调用量_本周', '调用量_本月', '调用量_本季']].fillna(0).sum()

    # 异常值
    col_list = last_data.columns.tolist()
    assert_values_red = []
    assert_values_yellow = []
    assert_values_list = []
    for v in ['昨日psi（vs本周）', '本周psi（vs本月）', '本月psi（vs本季度）']:
        print(v)
        assert_values = [i for i in last_data[v].tolist() if float(i) >= 0.1]
        if len(assert_values) > 0:
            for m in assert_values:
                print(m)
                values1 = last_data.loc[last_data[v] == m, col_list[col_list.index(v) + 3]].astype(float)
                values2 = last_data.loc[last_data[v] == m, col_list[col_list.index(v) + 4]].astype(float)
                print(values1.tolist(), values2.tolist())
                if ((values1 > 200).any()) and ((values2 > 200).any()):
                    assert_values_red.append(m)
                else:
                    assert_values_yellow.append(m)
                assert_values_list.append(m)
    #     assert_values.extend(last_data[i].tolist())
    # assert_values = [i for i in assert_values if float(i) >= 0.1]
    url = 'https://oapi.dingtalk.com/robot/send?access_token=6d5ea74c7be0b6d24c40b409398286aa963d9b13fdd407b1a8021e5d59f9fca5'  # 正式群
    # url = 'https://oapi.dingtalk.com/robot/send?access_token=ef60d6f9
    #
    # aee2901132fed4ee98cc6fe2661beaa44da98bc519b49afb87bd0b5e'  # 测试群
    if len(assert_values_red) > 0:
        text_fir = []
        for i in assert_values_red:
            user_name = last_data[(last_data == i).any(axis=1)]['客户名称'].values.max()
            product_name = last_data[(last_data == i).any(axis=1)]['产品名称'].values.max()
            text_fir.append('客户：{}，产品：{} 调用分数的psi过高'.format(user_name, product_name))
        text_fir = '\n'.join(text_fir)
        dd_server_fir = DingDingRobotService(url, 1)
        dd_server_fir.dingding('', text_fir, '', '')
    else:
        dd_server_fir = DingDingRobotService(url, 1)
        dd_server_fir.dingding('', '所有客户分数psi均在正常范围内', '', '')

    assert_values_red = ['%.3f' % i for i in assert_values_red]
    assert_values_yellow = ['%.3f' % i for i in assert_values_yellow]
    assert_values_list = ['%.3f' % i for i in assert_values_list]

    # 格式处理，调用量int, psi保留3位小数
    for i in ['调用量_昨日', '调用量_本周', '调用量_本月', '调用量_本季']:
        last_data[i] = last_data[i].map(lambda x: format(x, '0,.0f'))
    for i in ['昨日psi（vs本周）', '本周psi（vs本月）', '本月psi（vs本季度）']:
        last_data[i] = last_data[i].map(lambda x: "%.3f" % x)
    last_data.replace(np.nan, '', inplace=True)
    last_data.replace('nan', '', inplace=True)

    # 生成图片
    save_path = r'C:\Users\运营\PycharmProjects\模型分数监控\分数psi记录'
    tab = PrettyTable(border=True, header=True, header_style='title')
    tab.field_names = last_data.columns.tolist()
    for row in last_data.values:
        tab.add_row(row)
    tab.align = 'r'
    tab_info = str(tab)
    tab_pic.create_table_img(
        tab_info,
        font=r'C:\Windows\Fonts\simkai.ttf',
        describe=['注：昨日：{}, 本周：{}~{}, 本月：{}~{}, 本季：{}~{}'.format(
            yestoday_strf, week_start_day, yestoday - timedelta(days=1), month_start_day,
                                           week_start_day - timedelta(days=1), q_start_day,
                                           month_start_day - timedelta(days=1))
        ]
        ,
        table_title='评分psi',
        save_path=save_path,
        save_name='psi分布表_{}.jpg'.format(yestoday_strf),
        assert_value_red=assert_values_red,
        assert_value_yellow=assert_values_yellow,
        assert_values_list=assert_values_list
    )

    # 数据同步
    dd_server = DingDingRobotService(url, 4)
    title = '评分psi'
    file_server = FileUrl(save_path, 'psi分布表_{}.jpg'.format(yestoday_strf))
    file_url = file_server.file_url
    pic_server = FileUrl(save_path, 'psi分布表_{}.jpg'.format(yestoday_strf))

    pic_url = pic_server.file_url
    text = "##### **评分psi**  \n![screenshot]({})    \n".format(pic_url)
    dd_server.dingding(title, text, file_url, pic_url)
