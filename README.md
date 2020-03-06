# 新浪微博爬虫

## 1.使用到的一些东西

selenium、re、lxml&xpath、urllib、multiprocessing、json、csv

## 2.运行环境

Linux  4.19

python 3.8.1

需要安装的python包：

​    `pip install selenium lxml prettytable`

需要安装chromedriver、chrome浏览器（下面命令适用于manjaro）：

​    `sudo pacman -S google-chrome chromedriver`

## 3.实现基本功能主要函数执行流程

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

## 4.使用效果演示

<https://www.bilibili.com/video/av94014345>