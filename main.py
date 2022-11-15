# -*- coding:UTF-8 -*-

import os
import uuid

from flask import Flask, request, g, jsonify
import json
# from contextlib import closing
import sqlite3
from flask_cors import *

DATABASE = "./apitest.db"
DEBUG = True

UPLOAD_FOLDER = './upload'
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc'])  # 允许上传的文件类型

server = Flask(__name__)
server.config['JSON_AS_ASCII'] = False
server.config['JSONIFY_MIMETYPE'] = "application/json;charset=utf-8"
server.config.from_object(__name__)

CORS(server)


def connect_db():
    return sqlite3.connect(server.config['DATABASE'])


@server.before_request
def before_request():
    g.db = connect_db()


@server.after_request
def after_request(response):
    g.db.close()
    return response


@server.route("/login", methods=["get", 'post'])
def login():
    # 登录
    if request.method == "POST":
        values = json.loads(request.data)
        name = values['name']
        pwd = values['pwd']
    else:
        name = request.values['name']
        pwd = request.values['pwd'] if 'pwd' in request.values else None
    if name is None:
        return error('用户名不可为空！')
    if pwd is None:
        return error("密码不可为空！")
    cur = query_db("select token from users where name = ? and pwd = ?", [name, pwd], one=True)
    if cur is None:
        return error('用户名或密码错误！')
    return success(cur, '登陆成功')


@server.get("/users")
def user_list():
    cur = query_db("select name from users")
    return success(cur)


@server.post("/register")
def register():
    # 注册用户信息
    data = request.data
    values = json.loads(data)
    name = values.get('name')
    if name is None:
        return error('用户名不可为空！')
    pwd = values.get('pwd')
    if pwd is None:
        return error("密码不可为空！")
    email = values.get("email") if 'email' in values else None
    remark = values.get("remark") if 'remark' in values else None
    sex = values.get('sex') if 'sex' in values else None
    label = values.get("label") if 'label' in values else None
    cur = query_db('select id from users where name = ?', [name], one=True)
    if cur is not None:
        return error(f"{name}已经存在，不可以再注册！")
    token = str(uuid.uuid4().hex)
    cur = g.db.execute('insert into users (name, pwd,email,sex,label,remark,token) values (?, ?,?,?,?,?,?)',
                       [name, pwd, email, sex, label, remark, token])
    g.db.commit()
    if cur is None:
        return error('注册失败，请重试！')
    cur = query_db('select id,name,email,label,sex,remark from users where name =?', [name], True)
    return success(cur, '注册成功！')


@server.put("/update/<string:token>")
def update(token):
    # 修改用户信息
    if token is None:
        return error("用户token不可为空！")
    cur = query_db("select id ,email,label,remark,sex,pwd from users where token = ?", [token], one=True)
    if cur is None:
        return error("不存在该用户！")
    data = request.data
    values = json.loads(data)
    pwd = values.get('pwd') if 'pwd' in values else cur['pwd']
    email = values.get("email") if 'email' in values else cur['email']
    remark = values.get("remark") if 'remark' in values else cur['remark']
    sex = values['sex'] if ('sex' in values) else cur['sex']
    label = values.get("label") if 'label' in values else cur['label']
    cur = g.db.execute("update users set email=?,label=?,sex=?,pwd=?,remark=? where token = ?",
                       [email, label, sex, pwd, remark, token])
    g.db.commit()
    if cur is None:
        return error("修改失败，请重试！")
    return success(msg='修改成功！')


@server.get("/user/info/<string:token>")
def user_info(token):
    if token is None:
        return error("用户token不可为空！")
    cur = query_db("select id from users where token = ?", [token], one=True)
    if cur is None:
        return error("不存在该用户！")
    cur = query_db('select id,name,email,label,sex,remark from users where token =?', [token], True)
    return success(cur, '获取用户信息成功！')


@server.delete("/user/delete/<string:token>")
def delete(token):
    if token is None:
        return error("用户token不可为空！")
    cur = query_db("select id from users where token = ?", [token], one=True)
    if cur is None:
        return error("不存在该用户！")
    cur = g.db.execute("delete from users where token = ?", [token])
    g.db.commit()
    if cur is None:
        return error("删除失败！")
    return success(msg='删除成功！')


def allowed_file(filename):
    # 验证上传的文件名是否符合要求，文件名必须带点并且符合允许上传的文件类型要求，两者都满足则返回 true
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@server.post('/upload_file')
def upload_file():
    file = request.files['file']  # 获取上传的文件
    if file and allowed_file(file.filename):  # 如果文件存在并且符合要求则为 true
        filename = file.filename
        file.save(os.path.join(server.config['UPLOAD_FOLDER'], filename))  # 保存文件
        return success(filename, msg='上传成功！')  # 返回保存成功的信息
    return error('文件类型不符合！')


def success(data=None, msg=''):
    return jsonify({'data': data, 'code': 200, 'msg': msg})


def error(msg: str, code=0):
    return jsonify({'data': None, 'code': code, 'msg': msg})


def query_db(query, args=(), one=False):
    cur = g.db.execute(query, args)
    rv = [dict((cur.description[idx][0], value)
               for idx, value in enumerate(row)) for row in cur.fetchall()]
    return (rv[0] if rv else None) if one else rv


if __name__ == "__main__":
    server.run(host='0.0.0.0', port=6000)
