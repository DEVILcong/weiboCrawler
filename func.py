#coding:utf8

from selenium import webdriver
from multiprocessing import Pool, Manager
from queue import Queue
from prettytable import PrettyTable
from io import BytesIO
from lxml import etree as et
import gzip
import urllib.request
import urllib.parse
import re
import time
import sys
import json
import os
import socket
import csv

class WeiboCrawler:
    def __init__(self):
        '''
        init
        '''
        socket.setdefaulttimeout(self._timeout)

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
        a = self._cookies.pop('SSOLoginState', None)
        
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
        response = urllib.request.urlopen(self._search_user_url, data = searchD, timeout = self._timeout)

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
        file_loc = self.get_file_path(1, 2, 1)
        if not os.path.exists(file_loc):
            print('failed to get page count, quit...')
            sys.exit()

        with open(file_loc) as file1:
            content = file1.read()

        pat = '第&nbsp;(.*?)&nbsp;页'
        return re.search(pat, content).group(1)

    def get_file_path(self, page, part, tag):
        str_tmp = ''
        str_tmp = ''.join((str_tmp, self._main_folder_name))
        str_tmp = '/'.join((str_tmp, self._sub_folder_prefix))
        str_tmp = ''.join((str_tmp, str(page)))
        
        if tag == 0:
            return str_tmp

        str_tmp = ''.join((str_tmp, '/'))
        str_tmp = ''.join((str_tmp, self._file_prefix))
        str_tmp = ''.join((str_tmp, str(part)))
        str_tmp = ''.join((str_tmp, self._file_suffix))

        return str_tmp

    def str_clean(self, str_a):
        str_a = str_a.replace(' ', '')
        str_a = str_a.replace('\n', '')
        str_a = str_a.replace('\u200b', '')
        str_a = str_a.replace('\t', '')

        return str_a

    def get_ajax(self, vPage, vFailCount, qFailPage, pageCount, lockP, lockFC, lockFP, lockPrint):
        
        while True:  #attention !!!!!!!!
            lockP.acquire()
            page = vPage.value
            vPage.value += 1
            lockP.release()

            if page > pageCount:
                break
            

            if not os.path.exists(self.get_file_path(page, 0, 0)):
                os.mkdir(self.get_file_path(page, 0, 0))

            if page == 1:
                pre_page = page + 1
            else:
                pre_page = page - 1

            url1 = re.sub('page=.*?&', ''.join((''.join(('page=', str(page))), '&')), self._ajax_url_get)
            url1 = re.sub('pre_page=.*?&', ''.join((''.join(('pre_page=', str(pre_page))), '&')), url1)
            url1 = re.sub('pagebar=.*?&', ''.join((''.join(('pagebar=', '0')), '&')), url1)
     
            url2 = re.sub('pre_page=.*?&', ''.join((''.join(('pre_page=', str(page))), '&')), url1)
            url3 = re.sub('pagebar=.*?&', ''.join((''.join(('pagebar=', '1')), '&')), url2)
            urls = [url1, url2, url3]
        
            header1 = urllib.request.Request(url = url1, headers = self._headers_ajax)
            header2 = urllib.request.Request(url = url2, headers = self._headers_ajax)
            header3 = urllib.request.Request(url = url3, headers = self._headers_ajax)
            headers = [header1, header2, header3]

            fail_count = 0
            fails = []
            fail_reason = []

            for i in range(len(headers)):
                #print(urls[i])
                try:
                    response = urllib.request.urlopen(headers[i], timeout = self._timeout) 
                except urllib.error.HTTPError as error:
                    fail_count += 1
                    fails.append(urls[i])
                    fail_reason.append(str(error.getcode()))
                    time.sleep(1)
                except urllib.error.URLError:
                    fail_count += 1
                    fails.append(urls[i])
                    fail_reason.append('URLError')
                    time.sleep(1)
                except socket.timeout:
                    fail_count += 1
                    fails.append(urls[i])
                    fail_reason.append('Timeout')
                    time.sleep(1)
                else:
                    with open(self.get_file_path(page, i, 1), 'w') as file1:
                        file1.write(json.loads(self.gzip2str(response.read()))['data'])
                    time.sleep(2)

            lockFC.acquire()
            lockFP.acquire()
            lockPrint.acquire()
            if fail_count == 0:
                print('successfully get page ', page)
            else:
                print('-------error when get page ', page, '; ', fail_reason)
                fails = vFailCount.value
                if fails + 1 >= self._max_fail:
                    print('too many failures, exit')
                    sys.exit()
                else:
                    vFailCount.value += 1
                    qFailPage.put(page)
            lockFC.release()
            lockFP.release()
            lockPrint.release()
            
        return 

    def get_content(self, uid):
        self.get_init(uid)
        
        vPage = Manager().Value('i', 1)
        vFailCount = Manager().Value('i', 0)
        qFailPage = Manager().Queue()

        lockP = Manager().Lock()
        lockFC = Manager().Lock()
        lockFP = Manager().Lock()
        lockPrint = Manager().Lock()

        if not os.path.exists(self._main_folder_name):
            os.mkdir(self._main_folder_name)

        self.get_ajax(vPage, vFailCount, qFailPage, 1, lockP, lockFC, lockFP, lockPrint)

        page_count = self.get_page_count()
        print('-------page count:' + page_count + '----------')
        time.sleep(2)
        self._max_fail = float(page_count) / 3

        pool = Pool(self._process_count)
        data = ((vPage, vFailCount, qFailPage, int(page_count), lockP, lockFC, lockFP, lockPrint) for i in range(self._process_count))
        pool.starmap(self.get_ajax, data)

        pool.close()
        pool.join()
        
        print(''.join(('Your file is saved in ', self._main_folder_name)))
        print('Have a good day')

    def resolve_content(self, loc = None):
        if loc is None:
            loc = self._main_folder_name

        if not os.path.exists(loc):
            print('main folder doesn\'t exist, quiting...')
            return
        contents = []
        img_locs = {}
        parser = et.HTMLParser(encoding = 'utf-8')
        
        pages = os.listdir(loc)
        pages.sort(key = lambda page:int(page[4:]))

        page_count = 0
        part_count = 0

        for page in pages:
            parts = os.listdir('/'.join((loc, page)))
            parts.sort()
            print(page)
            print(parts)
            page_count += 1
            part_count = 0

            for part in parts:
                part_count += 1
                with open(os.path.join(loc, page, part)) as file1:
                    content = file1.read()
                    items = et.HTML(content, parser = parser)
                    items = items.xpath('//div[@action-type="feed_list_item"]')
                    if len(items) == 0:
                        continue
                   
                    for item in items:
                        part_content = ['' for i in range(10)]

                        subtitle = item.xpath('.//span[@class="subtitle"]')
                        if len(subtitle) != 0:
                            part_content[4] = 'like'
                            act_content = subtitle[0].xpath('.//a/text()')
                            act_content = ''.join(act_content)
                            part_content[5] = self.str_clean(act_content)

                        data_device = item.xpath('.//div[@class="WB_from S_txt2"]')
                        a_str = data_device[0].xpath('.//a/text()')
                        part_content[0] = self.str_clean(a_str[0])[:-5]
                        part_content[1] = self.str_clean(a_str[0])[-5:]
                        
                        if len(a_str) == 2: 
                            part_content[3] = self.str_clean(a_str[1])
                        else:
                            part_content[3] = 'unknown'

                        author = item.xpath('//a[@class="W_f14 W_fb S_txt1"]/text()')
                        part_content[2] = self.str_clean(author[0])
                        
                        content_list = item.xpath('.//div[@class="WB_text W_f14"]/text()')
                        content_list = ''.join(content_list)
                        content_list = self.str_clean(content_list)

                        if part_content[4] == 'like':
                            part_content[6] = content_list
                        else:
                            part_content[5] = content_list
                        
                        repost_content = item.xpath('.//a[@bpfilter="page_frame" and @class="W_fb S_txt1"]')
                        if len(repost_content) != 0:
                            part_content[4] = 'repost'
                                
                            repost_author = self.str_clean(''.join(repost_content[0].xpath('./text()')))
                            repost_text = item.xpath('.//div[@class="WB_text" and @node-type="feed_list_reason"]/text()')
                            repost_text = ''.join(repost_text)
                            repost_text = self.str_clean(repost_text)
                            part_content[6] = ':'.join((repost_author, repost_text))
                        elif part_content[4] == '':
                            part_content[4] = 'origin'

                        media = item.xpath('.//div[@class="media_box"]')
                        if len(media) != 0:
                            srcs = media[0].xpath('.//img/@src')
                            if len(srcs) != 0:
                                for src_c in range(len(srcs)):
                                    if srcs[src_c][0] == '/':
                                        img_locs['_'.join((part_content[0], str(src_c+1)))] = srcs[src_c][2:]
                                    elif srcs[src_c][0] == 'h':
                                        img_locs['_'.join((part_content[0], str(src_c+1)))] = srcs[src_c][8:]
                                    else:
                                        continue

                        feed = item.xpath('.//div[@class="WB_feed_handle"]')[0]
                        forward = feed.xpath('.//span[@node-type="forward_btn_text"]')[0]
                        em = forward.xpath('.//em')[1]
                        part_content[7] = self.str_clean(em.xpath('./text()')[0])

                        forward = feed.xpath('.//span[@node-type="comment_btn_text"]')[0]
                        em = forward.xpath('.//em')[1]
                        part_content[8] = self.str_clean(em.xpath('./text()')[0])

                        forward = feed.xpath('.//span[@node-type="like_status"]')[0]
                        em = forward.xpath('.//em')[1]
                        part_content[9] = self.str_clean(em.xpath('./text()')[0])

                        contents.append(part_content)
                    print('successfully get page:', str(page_count), ',part:', str(part_count))
        
        print('all resolve done, start writing files')
        
        #write text content to file
        with open('result.csv', 'w') as file1:
            csv_w = csv.writer(file1)
            csv_w.writerow(['日期', '时间', '作者', '设备', '操作类型', '操作内容', '操作附加内容', '转发数', '评论数', '点赞数'])
            csv_w.writerows(contents)

        with open('pics.csv', 'w') as file1:
            csv_w = csv.writer(file1)
            csv_w.writerow(['name', 'location'])

            for item in img_locs.items():
                csv_w.writerow(item)
        
        print('write file done, start get pics')
        #get pics according to img_locs
        if not os.path.exists(self._pics_folder):
            os.mkdir(self._pics_folder)

        fail_pics = {}
        fail_count = 0
        success_count = 0
        for img in img_locs.items():
            url = ''.join(('https://', img[1]))
            url = re.sub(self._small_pic, self._big_pic, url)
            try:
                urllib.request.urlretrieve(url, os.path.join(self._pics_folder,''.join((img[0], img[1][-4:]))))
            except Exception as e:
                print('failed to get ', img[0], ', try agine later')
                print(e)
                fail_pics[img[0]] = img[1]
                fail_count += 1
            else:
                print('successfully get ', img[0])
                success_count += 1
            time.sleep(1)

        if fail_count > 0:
            print('try to get failed pics')
            keys = list(fail_pics.keys())
            for key in keys:
                url = ''.join(('https://', fail_pics[key]))
                url = re.sub(self._small_pic, self._big_pic, url)
                try:
                    urllib.request.urlretrieve(url, os.path.join(self._pics_folder,''.join((key, img_locs[key][-4:]))))
                except Exception:
                    print('get ', key, ' error')
                else:
                    print('successfully get ', key)
                    fail_count -= 1
                    success_count += 1
                time.sleep(1)

        print('success:', success_count)
        print('fail:', fail_count)
        print('pics are saved in ', self._pics_folder)


        return (contents, img_locs)



    _main_url = 'https://www.weibo.com/'
    _login_url = 'https://www.weibo.com/login.php'
    _login_success_url = 'https://www.weibo.com/u'
    _search_user_url = 'https://s.weibo.com/user'
    _ajax_url = 'https://www.weibo.com/p/aj/v6/mblog/mbloglist'
    _ajax_url_get = ''

    _main_folder_name = 'result'
    _sub_folder_prefix = 'page'
    _file_prefix = 'part'
    _file_suffix = '.html'

    _pics_folder = 'pictures'
    _small_pic = 'orj360'
    _big_pic = 'mw690'
    
    _max_fail = 1
    _process_count = 4
    _timeout = 5

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
