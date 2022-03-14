import time
from flask import Flask, request, session, g, redirect, url_for, \
    abort, render_template, flash
import json
from contextlib import closing
import sqlite3

DATABASE = "./apitest.db"
DEBUG = True

server = Flask(__name__)
server.config.from_object(__name__)


def connect_db():
    return sqlite3.connect(server.config['DATABASE'])


def init_db():
    with closing(connect_db()) as db:
        with server.open_resource('db.sql') as f:
            db.cursor().executescript(f.read())
        db.commit()


@server.before_request
def before_request():
    g.db = connect_db()


@server.after_request
def after_request(response):
    g.db.close()
    return response


@server.route("/login", methods=["get", 'post'])
def login():
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
    cur = query_db("select id,name from users where name = ? and pwd = ?", [name, pwd], one=True)
    if cur is None:
        return error('用户名或密码错误！')
    return success(cur, '登陆成功')


@server.post("/register")
def register():
    data = request.data
    values = json.loads(data)
    name = values.get('name')
    if name is None:
        return error('用户名不可为空！')
    pwd = values.get('pwd')
    if pwd is None:
        return error("密码不可为空！")
    cur = query_db('select id from users where name = ?', [name], one=True)
    if cur is not None:
        return error(f"{name}已经存在，不可以再注册！")
    cur = g.db.execute('insert into users (name, pwd) values (?, ?)', [name, pwd])
    g.db.commit()
    if cur is None:
        return error('注册失败，请重试！')
    cur = query_db('select id,name from users where name =?', [name], True)
    return success(cur, '注册成功！')


def success(data, msg=''):
    return json.dumps({'data': data, 'code': 200, 'msg': msg})


def error(msg: str, code=0):
    return json.dumps({'data': None, 'code': code, 'msg': msg})


def query_db(query, args=(), one=False):
    cur = g.db.execute(query, args)
    rv = [dict((cur.description[idx][0], value)
               for idx, value in enumerate(row)) for row in cur.fetchall()]
    return (rv[0] if rv else None) if one else rv


server.run(port=6000, debug=True)
