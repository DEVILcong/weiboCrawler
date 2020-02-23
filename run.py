#! /usr/bin/env python3
#coding:utf8

import func

weibo = func.WeiboCrawler()

weibo.get_local_cookie()
weibo.get_content('1890196401')
