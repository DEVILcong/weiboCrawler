#coding:utf8

from selenium import webdriver
from prettytable import PrettyTable
from io import BytesIO
import gzip
import urllib.request
import urllib.parse
import re
import time
import sys
import json
import os

class WeiboCrawler:
    def __init__(self):
        '''
        init
        '''
        pass

    def login(self):
        '''
        登陆，记录cookie，并保存cookie到本地文件‘cookie’中
        '''
        print('please login to weibo in the browser')
        driver = webdriver.Chrome()
        time.sleep(2)
        driver.get(self._login_url)

        timeout = 0
        while 1:
            time.sleep(1)
            if timeout > 300:
                print('timeout quit...')
                sys.exit()
            if None != re.match(self._login_success_url, driver.current_url):
                break
            timeout += 1
        
        for i in driver.get_cookies():
            self._cookies[i['name']] = i['value']
        driver.quit()

        self._cookies['wvr'] = '6'
        self._cookies['UOR'] = ',,login.sina.com.cn'
        self._cookies['_s_tentry'] = 'login.sina.com.cn'

        
        self.update_cookies()

        cookie_json = json.dumps(self._cookies)
        with open('cookie', 'w') as file1:
            file1.write(cookie_json)

        print('login success')

        return
    
    def update_cookies(self):
        cookie_tmp = ''
        for item in self._cookies.items():
            short = '='.join(item)
            if cookie_tmp == '':
                cookie_tmp = short
            else:
                cookie_tmp = ';'.join((cookie_tmp, short))

        self._cookie = cookie_tmp
        self._headers['Cookie'] = cookie_tmp
        self._headers_ajax['Cookie'] = cookie_tmp

    def get_local_cookie(self):
        '''
        读取本地文件中的cookie，传递给_cookies，并根据_cookies生成_headers里面的Cookie
        '''
        cookie_tmp = ''
        with open('cookie') as file1:
            cookie_tmp = file1.read()
        
        self._cookies = json.loads(cookie_tmp)
        self.update_cookies()
        print('get cookie success')
        return

    def make_url(self, url, dataD):
        '''
        将url和要post的数据连接起来，因为用urllib提供的方法时遇到了问题
        '''
        tmp_str = ''
        for item in dataD.items():
            if tmp_str == '':
                tmp_str = '='.join((str(item[0]), str(item[1])))
            else:
                tmp_str = '&'.join((tmp_str, '='.join((str(item[0]), str(item[1])))))

        return '?'.join((url, tmp_str))

    def gzip2str(self, data):
        buff = BytesIO(data)
        f = gzip.GzipFile(fileobj = buff)
        return f.read().decode('utf-8')

    def search_user(self, user):
        '''
        根据关键字搜索用户，返回20个相关用户ID以及对应的uid
        '''
        searchD = urllib.parse.urlencode({'q':user}).encode()
        response = urllib.request.urlopen(self._search_user_url, data = searchD, timeout = 4)

        response = response.read().decode('utf-8')
        users = re.findall(self._search_data['pat_user_name'], response)
        uids = re.findall(self._search_data['pat_uid'], response)
        if len(users) != len(uids):
            print('get user name and uid error, exit...')
            sys.exit()
        
        for i in range(len(users)):
            users[i] = users[i].replace(self._search_data['useless_sen1'], '')
            users[i] = users[i].replace(self._search_data['useless_sen2'], '')

        table = PrettyTable(['No', 'User Name', 'User ID'])
        table.border = 1
        for i in range(len(users)):
            table.add_row([i+1, users[i], uids[i]])
        print(table)

        return

    def get_init(self, uid):
        self._get_ajax_post['id'] = ''.join((self._get_ajax_post['domain'], uid))
        self._get_ajax_post['script_uri'] = uid
        self._ajax_url_get = self.make_url(self._ajax_url, self._get_ajax_post)

    def get_page_count(self):
        if not os.path.exists(self.get_file_path(1, 3, 1)):
            print('failed to get page count, quit...')
            sys.exit()

        with open(file_loc) as file1:
            content = file1.read()

        pat = '第&nbsp;(.*?)&nbsp;页'
        return re.search(pat, content).group(1)

    def get_file_path(self, page, part, tag):
        str_tmp = ''
        str_tmp = ''.join((str_tmp, self._main_folder_name))
        str_tmp = ''.join((str_tmp, self._sub_folder_prefix))
        str_tmp = ''.join((str_tmp, str(page)))
        
        if tag == 0:
            return str_tmp

        str_tmp = ''.join((str_tmp, '/'))
        str_tmp = ''.join((str_tmp, self._file_prefix))
        str_tmp = ''.join((str_tmp, str(part)))
        str_tmp = ''.join((str_tmp, self._file_suffix))

        return str_tmp


    def get_ajax(self, page, pre_page, pagebar, no):
        url = re.sub('page=.*?&', ''.join((''.join(('page=', str(page))), '&')), self._ajax_url_get)
        url = re.sub('pre_page=.*?&', ''.join((''.join(('pre_page=', str(pre_page))), '&')), url)
        url = re.sub('pagebar=.*?&', ''.join((''.join(('pagebar=', str(pagebar))), '&')), url)
     
        header = urllib.request.Request(url = url, headers = self._headers_ajax)

        try:
            response = urllib.request.urlopen(header, timeout = 4) 
        except urllib.error.HTTPError as error:
            return error.getcode()
        except urllib.error.URLError:
            return -1
        else:
            with open(self.get_file_path(page, no, 1), 'w') as file1:
                file1.write(json.loads(self.gzip2str(response.read()))['data'])
        return 1

    def get_content(self, uid):
        self.get_init(uid)
        
        if not os.path.exists(self._main_folder_name):
            os.mkdir(self._main_folder_name[:-1])
        if not os.path.exists(self.get_file_path(1, 0, 0)):
            os.mkdir(self.get_file_path(1, 0, 0))

        self.get_ajax(1, 2, 0, 0)
        time.sleep(2)
        self.get_ajax(1, 1, 0, 1)
        time.sleep(2)
        self.get_ajax(1, 1, 1, 2)

        page_count = self.get_page_count()

        i = 2
        success = 0
        failed = 0
        while i <= page_count:
            if not os.path.exists(self.get_file_path(i, 0, 0)):
                os.mkdir(self.get_file_path(i, 0, 0))


        

    _main_url = 'https://www.weibo.com/'
    _login_url = 'https://www.weibo.com/login.php'
    _login_success_url = 'https://www.weibo.com/u'
    _search_user_url = 'https://s.weibo.com/user'
    _ajax_url = 'https://www.weibo.com/p/aj/v6/mblog/mbloglist'
    _ajax_url_get = ''

    _main_folder_name = 'result/'
    _sub_folder_prefix = 'page'
    _file_prefix = 'part'
    _file_suffix = '.html'

    _cookie = '' 

    _search_data = {
            'pat_user_name' : 'user_name\">(.*?)</a>',
            'pat_uid' : 'uid=(.*?) action',
            'useless_sen1' :'<em class=\"s-color-red\">',
            'useless_sen2' : '</em>'
            }
    _get_content_post = {
            'page':9,
            'profile_ftype':'1',
            'is_all':'1'
            }
    _get_ajax_post = {
            'ajwvr':'6',
            'domain':'100505',
            'profile_ftype':'1',
            'is_all':'1',
            'pagebar':'',
            'pl_name':'Pl_Official_MyProfileFeed__22',
            'id':'',
            'script_uri':'',
            'feed_type':'0',
            'page':'9',
            'pre_page':'9',
            'domain_op':'100505',
            #'__rnd':''
            }

    _cookies = {}

    _headers = {
            'Accept':r'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Accept-Encoding':r'gzip, deflate, br',
            'Accept-Language':r'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7,pt;q=0.6,ca;q=0.5',
            'Cache-Control':r'max-age=0',
            'Connection':'keep-alive',
            'Host':r'weibo.com',
            'Cookie':'',
            'User-Agent': r'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.116 Safari/537.36'
            }
    _headers_ajax = {
            'Accept':'*/*',
            'Accept-Encoding':'gzip, deflate, br',
            'Accept-Language':r'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7,pt;q=0.6,ca;q=0.5',
            'Connection':'keep-alive',
            'Cookie':'',
            'Host':'weibo.com',
            'Sec-Fetch-Dest':'document',
            'Sec-Fetch-Mode':'navigate',
            'Sec-Fetch-Site':'none',
            'Sec-Fetch-User':'?1',
            'User-Agent':r'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.116 Safari/537.36',
            }
