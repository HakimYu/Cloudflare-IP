#!/usr/bin/env python
# coding=utf-8
import json
import math
import socket
import threading
import requests
import queue
from ping3 import ping
from aliyunsdkalidns.request.v20150109.DescribeDomainRecordsRequest import \
    DescribeDomainRecordsRequest
from aliyunsdkalidns.request.v20150109.UpdateDomainRecordRequest import \
    UpdateDomainRecordRequest
from aliyunsdkcore.acs_exception.exceptions import (ClientException,
                                                    ServerException)
from aliyunsdkcore.auth.credentials import (AccessKeyCredential,
                                            StsTokenCredential)
from aliyunsdkcore.client import AcsClient
# 阿里云API设置
ID = ""
KEY = ""
# 阿里云根域名(数组)，用于获取域名相关信息
DOMAIN = ["baidu.com"]
DOMAIN_RR_AND_RECORDID = {
    "www": "000000000000000000",
}
# 扫描出的IP文件的名称(数组)
RES_NAME = [
    "Alibaba Cloud - 中国 香港.txt",
]
#需要的IP
NEED_PORT = [
    80,
    443
]
# Ping线程数
THREAD_NUM = 8

# 线程类


class MYThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        testIPs()

# 请求域名信息


def askForRecordID(id, key, domain):
    credentials = AccessKeyCredential(id, key)
    client = AcsClient(region_id='cn-hangzhou', credential=credentials)
    request = DescribeDomainRecordsRequest()
    request.set_accept_format('json')
    request.set_DomainName(domain)
    response = client.do_action_with_exception(request)
    record = json.loads(response)['DomainRecords']['Record']
    for i in range(0, len(record)):
        re = record[i]
        print('{}) {} {} 线路:{}  RECORDID: {}'.format(
            i, re['RR'], re['DomainName'], re['Line'], record[i]['RecordId']))

# 修改域名解析


def UpdateDomainRecord(id, key, IP, domain_record):
    credentials = AccessKeyCredential(id, key)
    client = AcsClient(region_id='cn-hangzhou', credential=credentials)
    request = UpdateDomainRecordRequest()
    request.set_accept_format('json')
    request.set_RecordId(domain_record[1])
    request.set_RR(domain_record[0])
    request.set_Type("A")
    request.set_Value(IP)
    response = client.do_action_with_exception(request)
    print(str(response, encoding='utf-8'))


# ping端口
def portPing(host, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    result = sock.connect_ex((str(host), int(port)))
    sock.close()
    if result == 0:
        return 1
    else:
        return 0


IPList = []
IPDict = {}
RES_ADDRESS = "https://raw.gh.fakev.cn/ip-scanner/cloudflare/daily/"
workQueue = queue.Queue()

for i in DOMAIN:
    askForRecordID(ID, KEY, i)

for i in RES_NAME:
    getIP = requests.get(RES_ADDRESS + i)
    if getIP.status_code == 200:
        IPList.extend(getIP.content.decode("utf8").splitlines())
for i in IPList:
    workQueue.put(i)


def testIPs():
    while workQueue.empty() == False:
        i = workQueue.get()
        result = ping(i, timeout=1)
        if result != None:
            IPDict[i] = math.ceil(result*100)


threads = []

print("正在ping测试{}个IP...".format(len(IPList)))
for i in range(THREAD_NUM-1):
    exec("thread{}=MYThread()".format(i))
    exec("thread{}.start()".format(i))
    exec("threads.append(thread{})".format(i))

for i in threads:
    i.join()


IPDict = sorted(IPDict.items(), key=lambda x: x[1])
IPList = []
for i in IPDict:
    IPList.append(i[0])

numOfIP = 0


for i in NEED_PORT:
    while True:
        status_code = 200
        try:
            status_code = requests.get(
                ("http://{}:{}").format(IPList[numOfIP], i)).status_code
        except:
            status_code = 200
            print("err")
        if portPing(IPList[numOfIP], i) != 1 and status_code == 200:
            numOfIP = numOfIP + 1
        else:
            break

#可用最快IP
print(IPList[numOfIP])

for i in DOMAIN_RR_AND_RECORDID:
    dic = [i, DOMAIN_RR_AND_RECORDID[i]]
    UpdateDomainRecord(ID, KEY, IPList[numOfIP], dic)
