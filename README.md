# 新浪微博爬虫

## 0.注意
    建议用Typora查看本文件，github不能正常显示流程图

## 1.基本功能
    本爬虫针对传统网页版微博，即<https://www.weibo.com>，爬取某个用户发表的所有微博，提取文本内容保存至result.csv文件中，所有图片链接保存至pics.csv文件中，并下载所有图片链接对应的图片，保存至pictures文件中；
    获取到的所有网页文件会保存在result文件夹中，在解析完毕后不会删除

## 2.使用到的一些东西

selenium、re、lxml&xpath、urllib、multiprocessing、json、csv

## 3.运行环境

Linux  4.19

python 3.8.1

需要安装的python包：

​    `pip install selenium lxml prettytable`

需要安装chromedriver、chrome浏览器（下面命令适用于manjaro）：

​    `sudo pacman -S google-chrome chromedriver`

## 4.实现基本功能主要函数执行流程

```flow
init=>start: 初始化
judge_con=>condition: 是否是第一次使用
login=>operation: login() 登录获取cookie
get_cookie=>operation: get_local_cookie() 获取事先保存的cookie
get_uid=>operation: search_user('uaer_name') 通过搜索用户名获取用户ID
get_content=>operation: get_content('user_id') 传入用户ID获得基本网页内容
resolve=>operation: resolve_content() 解析基本网页内容得到文本，并下载微博图片
done=>end: 操作完成

init->judge_con
judge_con(yes)->login
judge_con(no)->get_cookie
login->get_uid
get_cookie->get_uid
get_uid->get_content
get_content->resolve
resolve->done
```

## 5.使用效果演示

<https://www.bilibili.com/video/av94014345>

## 6.思路

    利用ajax向微博服务器请求获取信息，得到的网页文件保存在result文件夹中，而后解析函数依次读取result文件夹中的网页文件，并从中获取微博文本信息及图片链接，而后将两种信息写入文件，并根据图片链接下载文件

## 7.主要函数功能描述

### login()
    使用selenium启动chrome浏览器，并打开微博登陆页面<https://www.weibo.com/login.php>等待用户登录，用户登录成功后会跳转到用户主页，函数在检测到当前网址变为用户主页后自动退出chrome浏览器，将得到的cookie信息传入类的相关变量中，并写入本地文件‘cookie’，供用户以后使用
    chrome浏览器在等待300s后仍未检测到用户主页时，自动退出程序

### get_local_cookie()
    从本地文件‘cookie’中读取以前登录时保存的cookie，注意，使用以前保存的cookie存在cookie过期失效的问题，目前尚不清楚cookie失效的具体时间，如遇到cookie失效，下面获取网页会全部是404错误，并且程序可能会提示，这部分尚不完善

### search_user('user_name')
    传入用户名获取用户的uid号，uid号类似于身份证号，用来唯一的表示一个微博用户，此项功能只会返回搜索结果的前二十个用户的用户名及uid号，此项功能通过微博的用户名搜索页面<https://s.weibo.com/user>实现

### get_content('uid')
    传入uid获取uid对应用户所有的微博文本内容网页，并将网页文件保存至result文件夹中
    该函数先获取用户的第一页，获取第一页成功后调用类中的get_page_count()函数获取微博用户的总页数，然后进行多线程获取用户的微博网页，获取过程中遇到URLError、HTTPError、TimeOut等错误时程序不会退出，在获取所有页面后程序会重试获取出问题的页面，只重试一次

### resolve_content()
    该函数可以指定网页文件的存放位置，默认是result文件夹
    读取网页文件，解析相关信息，将得到的微博文本信息及图片链接写入result.csv和pics.csv，并调用类中的get_pics()函数，传递图片链接dict，使其下载图片    
