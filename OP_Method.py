#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2019/10/24 14:46
# @Author  : Daiyong

import configparser
import pymysql.cursors
import pandas as pd
from ftplib import FTP
import os
import oss2
import json
import urllib.request
import time
import datetime
import smtplib
from email.header import Header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.utils import parseaddr, formataddr

# import uuid
# from qiniu import Auth, put_file, etag
# import qiniu.config

class MysqlService:
    def __init__(self):
        # 获取数据库参数
        cf = configparser.ConfigParser()
        cf.read(r'C:\Users\运营\Documents\python auto_run\Basic_Method\config\hz_operator.conf')
        self.__db_host = cf.get("mysql_db", "db_host")
        self.__db_port = cf.getint("mysql_db", "db_port")
        self.__db_user = cf.get("mysql_db", "db_user")
        self.__db_pwd = cf.get("mysql_db", "db_pwd")

    def get_sql_data(self, db_name, sql):
        con = pymysql.connect(
            host=self.__db_host,
            user=self.__db_user,
            passwd=self.__db_pwd,
            db=db_name,
            port=self.__db_port,
            cursorclass=pymysql.cursors.DictCursor,
            charset='utf8')
        try:
            with con.cursor() as cur:
                cur.execute(sql)
                # col = cur.description
                data = cur.fetchall()
                data = pd.DataFrame(data)
                return data
        except Exception as e:
            print(e)
        finally:
            con.close()


class OpFtp:
    """
    file_path示例: '/data/100.yong'
    """

    def __init__(self):
        self.ftp = FTP()
        self.ftp.set_debuglevel(3)
        self.host = '10.1.120.101'
        self.username = 'hzph-02'
        self.password = 'xyG50tPtN'
        self.ftp.connect(self.host, 21)      
        self.ftp.login(self.username, self.password)
#        self.ftp.encoding = "GB18030"

    def downloan_file(self, remote_path, remote_file_name, local_path, local_file_name):
        self.ftp.cwd(remote_path)
        self.ftp.set_pasv(True)
        with open(os.path.join(local_path, local_file_name), 'wb') as fp:
            self.ftp.retrbinary('RETR ' + remote_file_name, fp.write, 1024)

    def upload_file(self, remote_path, remote_file_name, local_path, local_file_name):
        self.ftp.cwd(remote_path)
        self.ftp.set_pasv(False)
        with open(os.path.join(local_path, local_file_name), 'rb') as fp:
            self.ftp.retrbinary('STOR' + remote_file_name, fp.write, 1024)

    def ftp_close(self):
        self.ftp.close()


class FileUrl:
    def __init__(self, local_path, file_name):
        self.path = local_path
        self.file_name = file_name

    @property
    def file_url(self):
        auth = oss2.Auth('', '')
        bucket = oss2.Bucket(
            auth,
            '',
            '')
        # bucket.create_bucket(oss2.BUCKET_ACL_PRIVATE)
        bucket.put_object_from_file(
            self.file_name, os.path.join(
                self.path, self.file_name))
        url = bucket.sign_url('GET', self.file_name, 86400)
        return url

    # def file_url(self):
    #     q = Auth('', '')
    #     bucket_name = 'neal2020'
    #     key = uuid.uuid4().hex
    #     token = q.upload_token(bucket_name, key, 864000)
    #     ret, info = put_file(token, key, os.path.join(self.path, self.file_name))
    #     domain = 'http://qabsdytzy.bkt.clouddn.com/'
    #     url = domain + key
    #     return url


class DingDingRobotService:
    def __init__(self, url, message_type):
        self.url = url
        self.message_type = message_type

    @property
    def set_dingding_model(self):
        """返回钉钉模型数据，1:文本；2:markdown所有人；3:markdown带图片，@接收人；4:link类型"""
        if self.message_type == 1:
            my_data = {"msgtype": "text", "text": {"content": " "},
                       "at": {"atMobiles": ['18221084854'], "isAtAll": True}}
        elif self.message_type == 2:
            my_data = {
                "msgtype": "link", "link": {
                    "text": "",
                    "title": "",
                    "picUrl": "",
                    "messageUrl": ""}}
        elif self.message_type == 3:
            my_data = {
                "actionCard": {
                    "title": "",
                    "text": "",
                    "hideAvatar": "0",
                    "btnOrientation": "0",
                    "singleTitle": "点击下载数据",
                    "singleURL": ""},
                "msgtype": "actionCard"
            }
        elif self.message_type == 4:
            my_data = {
                "msgtype": "markdown",
                "markdown": {
                    "title": "",
                    "text": ""},
                "at": {
                    "atMobiles": ["15301707357"],
                    "isAtAll": False}}
        else:
            my_data = {}
            print('无匹配钉钉消息类型')
        return my_data

    def send_request(self, datas):
        """传入url和内容发送请求,构建一下请求头部"""
        header = {"Content-Type": "application/json", "Charset": "UTF-8"}
        send_data = json.dumps(datas)  # 将字典类型数据转化为json格式
        send_data = send_data.encode("utf-8")  # python3的Request要求data为byte类型
        request = urllib.request.Request(url=self.url, data=send_data, headers=header)  # 发送请求
        opener = urllib.request.urlopen(request)  # 将请求发回的数据构建成为文件格式
        print(opener.read())

    def dingding(self, title, text, file_url, pic_url=''):
        my_data = self.set_dingding_model
        if self.message_type == 1:
            my_data["text"]["content"] = text
            self.send_request(my_data)
        elif self.message_type == 2:
            my_data["link"]["messageUrl"] = file_url
            my_data["link"]["picUrl"] = pic_url
            my_data["link"]["text"] = text
            my_data["link"]["title"] = title
            self.send_request(my_data)
        elif self.message_type == 3:
            my_data["actionCard"]["title"] = title
            my_data["actionCard"]["text"] = text
            my_data["actionCard"]["singleURL"] = file_url
            self.send_request(my_data)
        elif self.message_type == 4:
            my_data["markdown"]["title"] = title
            my_data["markdown"]["text"] = text
            my_data["at"]["atMobiles"] = '15301707357'
            self.send_request(my_data)


def _format_addr(s):
    name, addr = parseaddr(s)
    return formataddr((Header(name, 'utf-8').encode(), addr))


class EmailService:

    def __init__(self, user, password):
        # 使用的邮箱的smtp服务器地址
        self.__mail_host = "smtp.mxhichina.com"
        # 用户名
        self.mail_user = user
        # 密码
        self.__mail_pass = password
        self.messgae = MIMEMultipart()
        self.server = smtplib.SMTP(self.__mail_host)  # 163邮箱服务器地址，端口默认为25
        self.server.login(self.mail_user, self.__mail_pass)

    def send_email(self, title, toaddrs, content, path, filename):
        toaddrs = ','.join(toaddrs)
        message = self.messgae
        message['From'] = _format_addr('{0}<{1}>'.format(title, self.mail_user))
        message['Subject'] = Header("数据更新时间" + time.strftime("%Y-%m-%d %H", time.localtime()), 'utf-8').encode()
        message['To'] = toaddrs
        part = MIMEApplication(open(os.path.join(path, filename), 'rb').read())
        part.add_header('Content-Disposition', 'attachment', filename=filename)
        message.attach(part)
        message.attach(MIMEText(content, 'plain', 'utf-8'))
        try:
            self.server.sendmail(self.mail_user, toaddrs.split(","), message.as_string())
            print(toaddrs)
            print('success')

        except smtplib.SMTPException as e:
            print('error', e)  # 打印错误

    def mail_quit(self):
        self.server.quit()
if __name__=='__main__':
    now_time = int(datetime.datetime.now().strftime('%H'))
    this_day_now = datetime.datetime.now()
    delta1 = datetime.timedelta(days=1)
    if now_time<14:
        this_day = this_day_now-delta1
    else:
        this_day = this_day_now
    today = this_day.strftime('%Y-%m-%d')
    remote_name = today+'_'+str(now_time)
    ftp = OpFtp()
    
    ftp.downloan_file('/data/901.creditcard/Report/click_report_pic','2020-10-19_16.png','D:\97.Dong','click_report.png')
    ftp.ftp_close()
    url = ''
    title = 'click_report'
    dd_server = DingDingRobotService(url,4)
    file_server = FileUrl('D:\97.Dong','click_report.png')
    file_url = file_server.file_url
    text = '#####    **click_report**  \n![screenshot]({})  \n'.format(file_url)
    dd_server.dingding(title,text,file_url)
    
    
    
