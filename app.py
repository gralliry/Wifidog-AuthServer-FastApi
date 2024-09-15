#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Description:
import sqlite3
import uuid

from fastapi import FastAPI, Request, Form, Query
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI()
# 添加 SessionMiddleware，设置 secret_key
app.add_middleware(SessionMiddleware, secret_key="your-secret-key")
templates = Jinja2Templates(directory="pages")

# 连接到SQLite数据库，如果数据库文件不存在，将会创建它
conn = sqlite3.connect('database.db')

"""
Hostname                  (Mandatory; Default: NONE)
SSLAvailable              (Optional; Default: no; Possible values: yes, no)
SSLPort                   (Optional; Default: 443)
HTTPPort                  (Optional; Default: 80)

Path                      (Optional; Default: /wifidog/       
Note:  The path must be both prefixed and suffixed by /.  Use a single / for server root.)

LoginScriptPathFragment   (Optional; Default: login/?         
Note:  This is the script the user will be sent to for login.)

PortalScriptPathFragment  (Optional; Default: portal/?       
Note:  This is the script the user will be sent to after a successfull login.)

MsgScriptPathFragment     (Optional; Default: gw_message.php? 
Note:  This is the script the user will be sent to upon error to read a readable message.)

PingScriptPathFragment    (Optional; Default: ping/?          
Note:  This is the script the user will be sent to upon error to read a readable message.)

AuthScriptPathFragment    (Optional; Default: auth/?          
Note:  This is the script the user will be sent to upon error to read a readable message.)
"""

Path = "/wifidog/"
LoginScriptPathFragment = "login/?"
PortalScriptPathFragment = "portal/?"
MsgScriptPathFragment = "gw_message.php?"
PingScriptPathFragment = "ping/?"
AuthScriptPathFragment = "auth/?"

GWAddress = "10.0.0.1"
GWPort = "2060"
GWId = "64644ADFE3CE"


def verify_server(gw_address: str = None, gw_port: str = None, gw_id: str = None):
    if gw_address is not None and gw_address != GWAddress:
        return False
    if gw_port is not None and gw_port != GWPort:
        return False
    if gw_id is not None and gw_id != GWId:
        return False
    return True


# 面向user
@app.get(f"{Path}{LoginScriptPathFragment}"[:-1])
async def login_get(
        request: Request,
        gw_address: str = Query(alias="gw_address"),
        gw_port: str = Query(alias="gw_port"),
        gw_id: str = Query(alias="gw_id"),
        # ip: str = Query(alias="ip"),
        # mac: str = Query(alias="mac"),
        # url: str = Query(alias="url"),
):
    if not verify_server(gw_address=gw_address, gw_port=gw_port, gw_id=gw_id):
        return f"当前页面({gw_address, gw_port, gw_id})不属于你处在的认证网络{GWAddress, GWPort, GWId}"
    return templates.TemplateResponse("login.html", context={"request": request})


# 面向user
@app.post(f"{Path}{LoginScriptPathFragment}"[:-1])
async def login_post(
        request: Request,
        username: str = Form(alias="username"),
        password: str = Form(alias="password"),
        gw_address: str = Query(alias="gw_address"),
        gw_port: str = Query(alias="gw_port"),
        gw_id: str = Query(alias="gw_id"),
        ip: str = Query(alias="ip"),
        mac: str = Query(alias="mac"),
        url: str = Query(alias="url"),
):
    if not verify_server(gw_address=gw_address, gw_port=gw_port, gw_id=gw_id):
        return f"当前页面(login_post:{gw_address, gw_port, gw_id})不属于你处在的认证网络{GWAddress, GWPort, GWId}"
    # 创建一个Cursor对象
    cursor = conn.cursor()
    cursor.execute(
        'SELECT id FROM user_info where username = ? and password = ?',
        (username, password)
    )
    # 提交事务
    conn.commit()
    result = cursor.fetchone()
    if result is None:
        cursor.close()
        return templates.TemplateResponse("message.html",
                                          context={'message': "账号不存在或密码错误", "request": request})
    # 更新用户信息
    user_id = result[0]
    token = str(uuid.uuid4())
    cursor.execute(
        'INSERT INTO connection (token, ip, mac, user_id) VALUES (?, ?, ?, ?)',
        (token, ip, mac, user_id)
    )
    cursor.close()
    # 成功重定向
    return RedirectResponse(url=f"http://{GWAddress}:{GWPort}/wifidog/auth?token={token}", status_code=302)


# 面向user
@app.get(f"{Path}{PortalScriptPathFragment}"[:-1])
async def portal(
        request: Request,
        gw_id: str = Query(alias="gw_id"),
):
    if not verify_server(gw_id=gw_id):
        return f"当前页面(portal:{gw_id})不属于你处在的认证网络{GWAddress, GWPort, GWId}"
    return templates.TemplateResponse("portal.html", context={"request": request})


# 面向user
@app.get(f"{Path}{MsgScriptPathFragment}"[:-1])
async def message(
        request: Request,
        msg: str = Query(alias="message"),
):
    return templates.TemplateResponse("message.html", context={'message': msg, "request": request})


# 面向Wifidog
@app.get(f"{Path}{PingScriptPathFragment}"[:-1])
async def ping(
        gw_id: str = Query(alias="gw_id"),
        sys_uptime: str = Query(alias="sys_uptime"),
        sys_memfree: str = Query(alias="sys_memfree"),
        sys_load: str = Query(alias="sys_load"),
        wifidog_uptime: str = Query(alias="wifidog_uptime"),
):
    # GET /wifidog/ping/?gw_id=64644ADFE3CE&sys_uptime=164&sys_memfree=26132&sys_load=0.30&wifidog_uptime=172
    # print({
    #     "gw_id": gw_id,
    #     "sys_uptime": sys_uptime,
    #     "sys_memfree": sys_memfree,
    #     "sys_load": sys_load,
    #     "wifidog_uptime": wifidog_uptime,
    # })
    if not verify_server(gw_id=gw_id):
        # 不回应非当前网络的请求
        return None
    return "Pong"


# 面向Wifidog
@app.get(f"{Path}{AuthScriptPathFragment}"[:-1])
async def auth(
        stage: str = Query(alias="stage"),
        ip: str = Query(alias="ip"),
        mac: str = Query(alias="mac"),
        token: str = Query(alias="token"),
        incoming: int = Query(alias="incoming"),
        outgoing: int = Query(alias="outgoing"),
        gw_id: str = Query(alias="gw_id"),
):
    if not verify_server(gw_id=gw_id):
        return "Auth: 0"
    cursor = conn.cursor()
    cursor.execute(
        'SELECT 1 FROM connection where token = ?',
        (token,)
    )
    conn.commit()
    result = cursor.fetchone()
    if result is None:
        cursor.close()
        return "Auth: 0"
    cursor.execute(
        'UPDATE connection SET ip = ?, mac = ?, incoming = ?, outgoing = ? WHERE token = ?',
        (ip, mac, incoming, outgoing, token)
    )
    conn.commit()
    cursor.close()
    return "Auth: 1"
