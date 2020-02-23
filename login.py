# coding:utf8

import urllib.request
import urllib.parse
import re
import time

class weiboCrawler:
    def __init__(self):
        '''
        初始化函数
        '''
        pass

    def login(self):
        #get three cookies on the main login page
        headers = urllib.request.Request(url = self._login_url, headers = self._headers)
        response = urllib.request.urlopen(headers, timeout = 4)
        cookie = response.getheader('Set-Cookie')
        pat = '(login_sid_t=.*?),'
        self._cookies['login_sid_t'] = re.findall(pat, cookie)[0]
        pat = '(cross_origin_proto=.*?),'
        self._cookies['cross_origin_proto'] = re.findall(pat, cookie)[0]
        pat = '(Ugrow-G0=.*?/)'
        self._cookies['Ugrow-G0'] = re.findall(pat, cookie)[0]

        #get login cookie used to get login qrcode 
        serverTime = time.time()
        serverTime = str(serverTime)
        data = {
            'entry':'weibo',
            'callback':'sinaSSOController.preloginCallBack',
            'su':'',
            'rsakt':'',
            'client':'ssologin.js(v1.4.19)',
            '_':serverTime[0:10]+serverTime[11:14]
                }
        data = urllib.parse.urlencode(data).encode()
        self._headers['Accept'] = '*/*'
        self._headers['Cookie'] = self._cookies['SINAGLOBAL']
        self._headers['Host'] = 'login.sina.com.cn'
        self._headers['Referer'] = self._login_url   #new item
        self._headers['Sec-Fetch-Dest'] = 'script'
        self._headers['Sec-Fetch-Mode'] = 'no-cors'
        self._headers['Sec-Fetch-Site'] = 'cross-site'
        headers = urllib.request.Request(self._prelogin_url, headers = self._headers)
        response = urllib.request.urlopen(headers, data = data, timeout = 4)
        self._cookies['login'] = response.getheader('Set-Cookie')[:-8]
        self._datas['prelogin'] = response.read().decode('utf-8')

        #get qrcode url
        data = {
            'entry':'weibo',
            'size':'180',
            'callback':'STK_15814782070471'
                }
        self._headers.pop('Sec-Fetch-User')
        data = urllib.parse.urlencode(data).encode()
        self._headers['Cookie'] = self._cookies['SINAGLOBAL']+';'+self._cookies['login']+';'+self._cookies['Apache']
        headers = urllib.request.Request(self._get_qrcode_url, headers = self._headers)
        response = urllib.request.urlopen(headers, data = data, timeout = 4)
        print(self._headers)
        print(response.getheaders())
        print(response.read().decode('utf-8'))


    def output(self):
        print(self._cookies)

    _headers = {
            'Accept':r'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Accept-Encoding':r'gzip, deflate, br',
            'Accept-Language':r'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7,pt;q=0.6,ca;q=0.5',
            'Connection':'keep-alive',
            'Host':r'weibo.com',
            'Sec-Fetch-Dest':'document',
            'Sec-Fetch-Mode':'navigate',
            'Sec-Fetch-Site':r'none',
            'Sec-Fetch-User':r'?1',
            'Upgrade-Insecure-Request':'1',
            'User-Agent':r'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.87 Safari/537.36'
            }
    _cookies = {
            'login_sid_t':r'',
            'cross_origin_proto':r'',
            'Ugrow-G0':r'',
            'SINAGLOBAL':r'SINAGLOBAL=112.38.111.76_1581430924.91170',
            'login':r'',
            'Apache':'Apache=112.38.111.76_1581478705.747454'
            }
    _datas = {
            'prelogin':''
            }

    _login_url = 'https://www.weibo.com/login.php'
    _prelogin_url = 'https://login.sina.com.cn/sso/prelogin.php'
    _get_qrcode_url = 'https://login.sina.com.cn/sso/qrcode/image'
