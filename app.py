# -*- coding: utf-8 -*-

"""
@IDE--Env : PyCharm--
@Time    : 2022/5/6 1:10
@Author  : runyuan zhan
@connect : remubuweiliang@qq.com
@Project : GaitRecognizer
@File    : app.py
@Version : 1.0.0 
@Desc    :
@LastTime: 
"""

import re  # 正则表达式，进行文字匹配
import json
import os
import datetime
import time
from bs4 import BeautifulSoup  # 网页解析，获取数据
import urllib.request  # 制定URL，获取网页数据
from selenium import webdriver
from selenium.webdriver.common.keys import Keys  # 键盘导入类
from time import sleep
import flask
from flask import Flask, render_template, \
    request, redirect, session, url_for, \
    jsonify, flash, get_flashed_messages, send_from_directory
from flask_cors import CORS  # 导入包
from geventwebsocket.handler import WebSocketHandler
from gevent.pywsgi import WSGIServer
from geventwebsocket.websocket import WebSocket
import requests

app = Flask(__name__, template_folder='templates', static_folder='static', static_url_path='/static')
app.debug = True  # 开启调试模式
app.secret_key = "20202005185ZhanRunYuan"  # 设置密钥
CORS(app, supports_credentials=True)  # 设置参数,支持跨域

user_socket_dict = {}  # 创建一个空字典用来存储用户
chat_record = []  # 用于存储聊天数据
log_data = []  # 服务器历史操作记录
user_data = [{'user': '123', 'password': '123123', 'phone': '18128456615', 'gender': 'female',
              'desc': '一只可爱的小海绵~',
              'dynamic_list': []}]  # 用于存储用户的账号信息
admin_data = {'user': '233', 'password': '233233', 'phone': '15816543014', 'gender': 'male',
              'desc': '严肃沙雕的管理员！',
              'dynamic_list': [
                  {'time': '22-05-09 13:00:00', 'name': 'box.stl', 'url': '15816543014/box.stl'}]}  # 用于存储管理员的账号信息
log_comment = [{'comment': '这个网站很不错，功能齐全观感美观~', 'star': 5, 'user': '123', 'time': '22-05-08 09:15:16'}]

findLink = re.compile(r'<a href="(.*?)" target="_blank">')
findTitle = re.compile(r'<h2>\n<a href="(.*?)" target="_blank">(.*?)\n</h2>')
findSubTitle = re.compile(r'<p>(.*)</p>')
findTime = re.compile(r'<p>\n(.*?)<span>(.*?)</span>\n</p>')
findDetailTitle = re.compile(r'<h1 class="news_title">(.*)</h1>')
findContent = re.compile(
    r'<div class="news_txt" data-size="standard">([\s\S]*)</div>\n<div class="top_word_relation">')


# 无session重定向
@app.before_request
def before(*arg, **kwarg):
    """
    在每次request请求时先进行session判定，无特定session则弹回
    :param arg: 参数
    :param kwarg: 参数列表
    :return: 成功与否
    """
    if request.path == '/login':
        return None
    else:
        name = session.get('user')
        if not name:
            log_data.append(get_time() + " 非法访问被弹回！")
            print('非法访问！！！')
            return redirect('/login')  # 未登录弹回
        else:
            return None


@app.before_first_request
def first():
    """
    项目启动时执行
    :return: None
    """
    log_data.append(get_time() + " 项目启动成功！")
    print("项目启动成功")


# 登录页面
@app.route('/login', methods=['GET', 'POST'], endpoint='login')
def login():
    """
    Get:        获取页面
    Post:       提交登录数据
    :return:    返回带有状态的json字符
    """
    if request.method == "GET":
        return render_template('login.html')
    else:
        res = request.get_json(silent=True)
        user = res['data']['user']
        pwd = res['data']['password']
        ans = {}
        # 管理员身份判定
        if user == admin_data['user'] and pwd == admin_data['password']:
            session['user'] = user  # 设置session为用户名
            session['level'] = 1  # 设置用户的权限等级，特殊用户为1级权限
            log_data.append(get_time() + ' 管理员 ' + " 登录成功！")
            print("管理员登录成功！")
            ans = {'state': 1, 'js': 'console.log("管理员成功！");'}
            return jsonify(ans)

        right = False
        # 账号密码判定
        for item in user_data:
            if user == item['user'] and pwd == item['password']:
                right = True

        if right:
            session['user'] = user  # 设置session为用户名
            session['level'] = 0  # 设置用户的权限等级，普通用户为0级权限
            log_data.append(get_time() + ' ' + user + ' ' + " 登录成功！")
            print(user + "登录成功！")
            ans = {'state': 1, 'js': 'console.log("登录成功！");'}
        else:
            log_data.append(get_time() + ' ' + user + ' ' + " 登录失败！")
            print(user + "登录失败！")
            ans = {'state': 0, 'js': 'console.log("登录失败！");'}
        return jsonify(ans)


# 注册页面
@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    Get:        获取页面
    Post:       提交注册数据
    :return:    返回带有状态的json字符
    """
    if request.method == "GET":
        return render_template('register.html')
    else:
        res = request.get_json(silent=True)
        user = res['data']['user']
        phone = res['data']['phone']
        for item in user_data:
            if user == item['user']:
                log_data.append(get_time() + ' ' + user + ' ' + " 注册失败！")
                print(user + "注册失败！")
                ans = {'state': 0, 'js': 'console.log("注册失败！");'}
                return jsonify(ans)
            elif phone == item['phone']:
                log_data.append(get_time() + ' ' + user + ' ' + " 注册失败！")
                print(user + "注册失败！")
                ans = {'state': 0, 'js': 'console.log("注册失败！");'}
                return jsonify(ans)
        ans = res['data']
        ans['dynamic_list'] = []
        user_data.append(ans)  # 存进用户数组

        # 创建用户私人目录
        os.mkdir('./static/data/' + phone)
        log_data.append(get_time() + ' 用户 ' + user + " 私人文件夹创建成功")
        print(user + "私人文件夹创建成功！")
        print(user_data)

        log_data.append(get_time() + ' ' + user + ' ' + " 注册成功！")
        print(user + "注册成功！")
        ans = {'state': 1, 'js': 'console.log("注册成功！");'}
        return jsonify(ans)


# 获取该用户详细数据信息
@app.route('/get_userdata')
def get_userdata():
    """
    通过前端session获取用户详细信息
    :return: 返回用带有户信息的json字符
    """
    name = session.get('user')
    x = {}
    if name == admin_data['user']:
        x = {'user': admin_data['user'], 'gender': admin_data['gender'], 'phone': admin_data['phone'],
             'desc': admin_data['desc'], 'dynamic_list': admin_data['dynamic_list']}
        x = jsonify(x)
        return x
    for item in user_data:
        if name == item['user']:
            x = {'user': item['user'], 'gender': item['gender'], 'phone': item['phone'], 'desc': item['desc'],
                 'dynamic_list': item['dynamic_list']}
            x = jsonify(x)
            return x
    return None


# 主页
@app.route('/')
@app.route('/index', endpoint='index')
def index():
    """
    返回主页页面
    :return: 主页页面
    """
    return render_template('index.html')


# 基础页面
@app.route('/home')
def home():
    """
    返回基础页面
    :return: 基础页面
    """
    return render_template('home.html')


@app.route('/upload')
def upload():
    """
    返回上传
    :return: 上传页面
    """
    return render_template('upload.html')


@app.route('/file')
def file_management():
    """
    返回文件管理页面
    :return: 文件管理页面
    """
    return render_template('file.html')


@app.route('/gait')
def gait():
    """
    返回步态页面
    :return: 步态页面
    """
    return render_template('gait.html')


@app.route('/add_data', methods=['GET', 'POST'])  # 用户上传文件，更新玩家数据
def add_data():
    """
    用户上传文件
    :return: 返回带有状态的json字符
    """
    name = session.get('user')
    # secure_filename(file.filename))
    # file获取到的前端的文件
    for item in user_data:
        if name == item['user']:
            if request.data == b'':
                file = request.files['file']
                item['temp'] = file.filename
                # print(file.filename)
                file.save('./static/data/' + item['phone'] + '/' + file.filename)
                # print("预备上传:", file)
            else:
                item['dynamic_list'].append({
                    'time': get_time(),
                    'name': item['temp'],
                    'url': item['phone'] + '/' + item['temp'],
                })
                ans = {'state': 1, 'js': 'console.log("上传成功！");'}
                print(name + " 成功上传文件：" + item['temp'])
                log_data.append(get_time() + ' 用户 ' + name + " 成功上传文件:" + item['temp'])
                return jsonify(ans)
    ans = {'state': 0, 'js': 'console.log("上传失败！");'}
    return jsonify(ans)


@app.route('/search_file/<path:filepath>')  # 用户获取文件视图
def search_file(filepath):
    """
    用户获取个人文件视图
    :param filepath: 用户个人路径
    :return: json格式的文件数据
    """
    return jsonify(scan_dir('./static/data/' + filepath))


def scan_dir(path='static/data/15816543014'):  # 读取用户私人文件夹下的信息
    data = []
    for file in os.scandir(path):
        x = {
            'name': file.name,
            'size': str(file.stat().st_size) + " B" if file.stat().st_size < 1024 else
            str(round(file.stat().st_size / 1024, 2)) + " KB" if file.stat().st_size / 1024 < 1024 else
            str(round(file.stat().st_size / 1024 / 1024, 2)) + " MB",
            'visit_time': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(file.stat().st_atime))),
            'modify_time': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(file.stat().st_mtime))),
            'establish_time': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(file.stat().st_ctime))),
            'is_dir': file.is_dir()
        }
        data.append(x)
    # print(data)
    return data


@app.route('/download/<path:filename>', methods=['GET', 'POST'])  # 下载文件
def download(filename):
    """
    下载文件
    :param filename: 需要下载的文件路径
    :return: 返回该文件
    """
    name = session.get('user')
    print(name + " 下载文件：" + filename)
    log_data.append(get_time() + ' 用户 ' + name + " 下载文件:" + filename)
    return send_from_directory("./static/data/", filename, as_attachment=True)


@app.route('/search', methods=['GET', 'POST'])
def search():
    """
    返回实事资讯页面
    :return: 实事咨询页面
    """
    return render_template('search.html')


# 实事资讯数据地址
@app.route('/real_time_info', methods=['GET', 'POST'])
def real_time_info():
    """
    获取实事咨询数据
    :return: json格式咨询数据
    """
    res = request.get_json(silent=True)
    return jsonify(get_real_time_info(res['txt']))


def get_real_time_info(find):
    """
    获取实事咨询数据
    :param find: 查询词汇
    :return: 查询到的表层列表
    """
    options = webdriver.ChromeOptions()
    # 静默模式
    options.add_argument("headless")
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-dev-shm-usage')
    browser = webdriver.Chrome(chrome_options=options)  # 指定和打开浏览器
    try:
        # get打开指定的url，传入要打开的url
        browser.get('https://www.thepaper.cn/searchResult.jsp')
        # 通过find_element_by_name获取到网页标签，send_keys()输入内容,在搜索栏输入python
        browser.find_element_by_class_name('sc_inp').send_keys(find)  # 在输入框输入内容
        # sleep(1)
        browser.find_element_by_class_name('sc_inp').send_keys(Keys.ENTER)  # 回车键
        soup = BeautifulSoup(browser.page_source, "html.parser")
        # html = json.loads(browser.page_source)
        dataset = []
        for item in soup.find_all('div', class_="search_res"):  # 查找符合要求的字符串\
            data = {}
            item = str(item)
            data['link'] = '/real_time_info/' + re.findall(findLink, item)[0]  # 通过正则表达式查找
            data['titles'] = re.findall(findTitle, item)[0][1]
            data['subTitles'] = re.findall(findSubTitle, item)[0]
            dataset.append(data)
        browser.close()
        # print(dataset)
        return dataset
    except Exception as e:
        print("模拟登录失败：{}".format(e))
        browser.close()
        pass


# @app.route('/detail')
# def detail():
#     return render_template('detail.html')


@app.route('/real_time_info/<string:url>', methods=['GET', 'POST'])
def real_time_info_get_detail(url):
    """
    获取实事咨询的具体数据
    :param url: 具体咨询的后缀url
    :return: 返回json格式字符串
    """
    return jsonify(get_detail(url))


def get_detail(url):
    """
    获取详细的文章信息
    :param url: 具体咨询文章的后缀url
    :return: 返回json格式的数据
    """
    url = "https://www.thepaper.cn/" + url  # 要爬取的网页链接
    html = ask_url(url)  # 保存获取到的网页源码
    soup = BeautifulSoup(html, "html.parser")
    # html = json.loads(browser.page_source)
    data = {}
    try:
        for item in soup.find_all('div', class_="newscontent"):  # 查找符合要求的字符串
            item = str(item)
            data['titles'] = re.findall(findDetailTitle, item)[0]
            data['time'] = []
            data['time'].append(re.findall(findTime, item)[0][0].replace("&", ""))
            data['time'].append(re.findall(findTime, item)[0][1])
            data['content'] = re.findall(findContent, item)[0]
        return data
    except:
        log_data.append(get_time() + ' 咨询查询出错！')
        print("资讯查询出错")
        pass


def ask_url(url):
    """
    获取网页源码
    :param url: 网页url
    :return: 返回网页源码字符串
    """
    head = {  # 模拟浏览器头部信息，向服务器发送消息
        "User-Agent": "Mozilla / 5.0(Windows NT 10.0; Win64; x64) "
                      "AppleWebKit / 537.36(KHTML, like Gecko) Chrome "
                      "/ 80.0.3987.122  Safari / 537.36"
    }
    # 用户代理（本质上是告诉浏览器，我们可以接收什么水平的文件内容）
    req = urllib.request.Request(url, headers=head)
    html = ""
    try:
        response = urllib.request.urlopen(req)
        html = response.read().decode("utf-8")
    except urllib.error.URLError as e:
        if hasattr(e, "code"):
            print(e.code)
        if hasattr(e, "reason"):
            print(e.reason)
    return html


@app.route('/chatroom')
def chatroom():
    """
    返回聊天室页面
    :return: 聊天室页面
    """
    return render_template('chatroom.html')


@app.route('/websockets/<user_nick>', methods=['GET', 'POST'])  # 设置Flask路由,前端通过访问这个地址拆解信息,<user_nick>即前端登录聊天室时的用户名
def ws_app(user_nick):
    """
    用户的聊天室进程
    :param user_nick: 登录聊天室时候的用户名
    :return: 该用户应当获取的消息串
    """
    log_data.append(get_time() + ' ' + user_nick + ' ' + " 进入聊天室！")
    print(user_nick + '进入聊天室！')
    user_socket = request.environ.get("wsgi.websocket")  # type:WebSocket
    if user_socket is None:
        print('您使用的是Http协议')
        return '您使用的是Http协议'
    try:
        log_data.append(get_time() + ' ' + user_nick + ' ' + " 聊天室登录成功！")
        print(user_nick + '聊天室登录成功！')
        # 取出environ中的wsgi.websocket对应的值
        if user_nick not in user_socket_dict:
            user_socket_dict[user_nick] = user_socket  # 以<user_nick>为key在字典中插入用户信息
        for item in chat_record:  # 新用户传入历史消息
            user_socket.send(item)
        print(user_socket_dict)
        while True:
            msg = user_socket.receive()  # 取出发送内容
            msg = json.loads(msg)
            chat_record.append(msg)
            for user in list(user_socket_dict.values()):
                user.send(json.dumps(msg))
        user_socket.close()
    except exception as e:
        del user_socket_dict[user_nick]
        log_data.append(get_time() + ' ' + user_nick + ' ' + " 退出聊天室！")
        print("One connection closed")
        print(user_socket_dict)


@app.route('/service')
def service():
    """
    返回智能客服页面
    :return: 智能客服页面
    """
    return render_template('ai_chat.html')


@app.route('/chat_info', methods=['GET', 'POST'])
def chat_info(*arg, **kwarg):
    """
    获取智能聊天词库
    :param arg: 参数
    :param kwarg: 参数列表
    :return: 返回json字符串
    """
    res = request.get_json(silent=True)
    return get_answer(res['txt'])


def get_data(text):
    """
    思知账号
    :param text:
    :return:
    """
    data = {
        "appid": "c70bd1d89ff502540d7ae2b951e80719",
        "userid": "4Ee1yHiK",
        "spoken": text,
    }
    return data


def get_answer(text):
    data = get_data(text)
    url = 'https://api.ownthink.com/bot'
    response = requests.post(url=url, data=data)
    response.encoding = 'utf-8'
    result = response.json()
    res = result['data']['info']['text']
    return res


@app.route('/comment')
def comment():
    """
    根据用户权限，返回不同的评价页面
    :return: 评价页面
    """
    level = session.get('level')
    if level == 0:  # 普通用户权限
        return render_template('comment.html')
    elif level == 1:  # 管理员权限
        return render_template('comment_data.html')
    else:
        flask.abort(404)


# 提交用户评价，获取用户评价
@app.route('/comment_data', methods=['GET', 'POST'])
def comment_data():
    """
    Get:        获取用户评价的数据
    Post:       提交用户评价的数据
    :return:    用户评价的数据/提交的状态json字符串
    """
    if request.method == "GET":
        user = session.get('user')
        # 管理员身份判定
        if user == admin_data['user']:
            return jsonify(log_comment)
        else:
            return None
    else:
        res = request.get_json(silent=True)
        x = {'comment': res['data']['comment'], 'star': res['data']['star'], 'user': res['data']['user'],
             'time': get_time()}
        log_comment.append(x)
        ans = {'state': 1, 'js': 'console.log("提交成功");'}
        log_data.append(get_time() + ' ' + res['data']['user'] + ' ' + " 评价成功！")
        print(log_comment)
        return jsonify(ans)


@app.route('/setting')
def setting():
    """
    返回设置页面
    :return: 设置页面
    """
    level = session.get('level')
    if level == 0:  # 普通用户权限
        return render_template('setting.html')
    elif level == 1:  # 管理员权限
        return render_template('log.html')
    else:
        flask.abort(404)


@app.route('/get_log')
def get_log():
    """
    管理员获取调试信息的接口
    :return: json格式调试信息
    """
    user = session.get('user')
    # 管理员身份判定
    if user == admin_data['user']:
        return jsonify(log_data)
    else:
        return None


@app.errorhandler(404)
def error_404(error):
    flask.abort(404)
    user = session.get('user')
    log_data.append(get_time() + ' ' + user + ' ' + " 进入404页面！")
    print("404错误")
    return error


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static/ico'),  # 对于当前文件所在路径,比如这里是static下的favicon.ico
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


def get_time(flag=True):
    """
    获取时间函数
    :param flag: 是否获取转化后的字符串
    :return: 返回字符串/时间戳
    """
    if flag:
        return datetime.datetime.now().strftime('%y-%m-%d %H:%M:%S')
    else:
        return datetime.datetime.now()


if __name__ == '__main__':
    # 表示如果是http请求就直接app处理，如果是websocket就交给handler再给app
    http_serv = WSGIServer(('127.0.0.1', 5000), app, handler_class=WebSocketHandler)
    http_serv.serve_forever()