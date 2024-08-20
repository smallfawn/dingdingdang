#!/bin/bash
# -*- coding: utf-8 -*-
# api.py
run_host = "0.0.0.0"
run_port = 12345
# 计划实现 WxPusher绑定

from quart import Quart, request, jsonify, send_from_directory, send_file
import hashlib, asyncio
import login as backend
import ddddocr
import json
import os
import requests
import re
import time
import urllib.parse


ocr = ddddocr.DdddOcr(show_ad=False, beta=True)
ocrDet = ddddocr.DdddOcr(show_ad=False, beta=True, det=True)



class account:
    status = ""
    uid = ""
    account = ""
    password = ""
    isAuto = False
    type = ""
    cookie = ""
    SMS_CODE = ""
    msg = ""

    def __init__(self, data):
        try:
            self.status = "pending"
            self.account = data.get("id", None)
            self.type = data.get("type", None)
            self.remarks = data.get("remarks", None)
            self.password = data.get("pw", None)
            self.isAuto = data.get("isAuto", False)
            if not self.account:
                raise ValueError("账号不能为空")
            if type == "password" and not self.password:
                raise ValueError("密码不能为空")

            c = str(self.account) + str(self.password)
            self.uid = hashlib.sha256(c.encode("utf-8")).hexdigest()
        except:
            raise ValueError("账号密码错误：" + str(data))


# 正在处理的账号列表
workList = {}
"""
(global) workList ={
    uid: {
        status: pending,
        account: 138xxxxxxxx, 
        password: admin123,
        isAuto: False
        cookie: ""
        SMS_CODE: None,
        msg: "Error Info"
    },
    ...
}
"""
app = Quart(__name__)


def mr(status, **kwargs):
    r_data = {}
    r_data["status"] = status
    for key, value in kwargs.items():
        r_data[str(key)] = value
    r_data = jsonify(r_data)
    r_data.headers["Content-Type"] = "application/json; charset=utf-8"
    return r_data


# -----router-----
@app.route("/", methods=["GET"])
async def index():
    # 请求外部验证接口

    response = await send_file("index.html")

    # 添加缓存控制的头部信息
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response
    """
    response = requests.get('https://888.88:9/vilate')

    if response.status_code == 200:
        result = response.json()
        if result.get('status', False):  # 检查 'status' 键的值
            return send_file('index.html')
    
    return "加载失败", 403
    """


# 传入账号密码，启动登录线程
@app.route("/login", methods=["POST"])
async def login():
    # print("login")
    data = await request.get_json()
    if "type" not in data:
        data["type"] = "password"
    return loginPublic(data)


# 启动登录线程
@app.route("/loginNew", methods=["POST"])
async def loginNew():
    print("loginPassword")
    data = await request.get_json()
    return loginPublic(data)


# 调用后端进行登录
async def THREAD_DO_LOGIN(workList, uid, ocr, ocrDet):
    try:
        await backend.main(workList, uid, ocr, ocrDet)
    except Exception as e:
        #print(e)
        workList[uid].msg = str(e)

    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        loop.run_until_complete(backend.start(workList, uid))
    except Exception as e:
        print(e)
        workList[uid].msg = str(e)
    """


# 检查后端进度记录
@app.route("/check", methods=["POST"])
async def check():
    data = await request.get_json()
    uid = data.get("uid", None)
    r = None
    # 账号列表有记录
    if workList.get(uid, ""):
        status = workList[uid].status
        if status == "pass":
            cookie = workList[uid].cookie
            r = mr(status, cookie=cookie, msg="成功")
            # 登录成功后保存账户和密码到文件
            # 正则取出cookie 里面pt_pin=的值
            ql_api = QLAPI()
            ql_api.load_config()
            ql_api.get_token()  # 获取并设置TOKEN
            if ql_api.get_ck():  # 获取现有的CK环境变量
                ql_api.check_ck(
                    cookie, workList[uid].remarks
                )  # 调用 check_ck 方法进行处理
            ptpin = extract_pt_pin(workList[uid].cookie)
            account_data = {
                "account": workList[uid].account,
                "password": workList[uid].password,
                "ptpin": ptpin,
                "remarks": workList[uid].remarks,
                "wxpusherUid":""
            }
            #
            filename = "data.json"
            existing_data = load_from_file(filename)
            print(existing_data)
            # Only save the data if it does not already exist
            if not any(
                item["account"] == account_data["account"]
                and item["password"] == account_data["password"]
                for item in existing_data
            ):
                existing_data.append(account_data)
                save_to_file(filename, existing_data)
                if(ql_api.isWxPusher):
                    loginNotify(ql_api.wxpusherAppToken,ql_api.wxpusherAdminUid,"账号" + ptpin + "登录成功:"+workList[uid].remarks)

        elif status == "pending":
            r = mr(status, msg="正在处理中，请等待")
        elif status == "error":
            r = mr(status, msg="登录失败，请在十秒后重试：" + workList[uid].msg)
        elif status == "SMS":
            r = mr(status, msg="需要短信验证")
        elif status == "wrongSMS":
            r = mr(status, msg="短信验证错误，请重新输入")
        else:
            r = mr("error", msg="笨蛋开发者，忘记适配新状态啦：" + status)
    # 账号列表无记录
    else:
        r = mr("error", msg="未找到该账号记录，请重新登录")
    return r


# 传入短信验证码，更新账号列表使后端可以调用
@app.route("/sms", methods=["POST"])
async def sms():
    data = await request.get_json()
    uid = data.get("uid", None)
    code = data.get("code", None)
    # 检查传入验证码合规
    if len(code) != 6 and not code.isdigit():
        r = mr("wrongSMS", msg="验证码错误")
        return r
    try:
        THREAD_SMS(uid, code)
        r = mr("pass", msg="成功提交验证码")
        return r
    except Exception as e:
        r = mr("error", msg=str(e))
        return r
#登录通知
def loginNotify(token,uid,content):
    encoded_content = urllib.parse.quote(content)
    url = "https://wxpusher.zjiecode.com/api/send/message/?appToken="+token+"&content="+encoded_content+"&uid="+uid+"&url=http%3a%2f%2fbaidu.com"
    response = requests.get(url)
    return ""
def loginPublic(data):
    try:
        u = account(data)
    except Exception as e:
        r = mr("error", msg=str(e))
        return r
    # 检测重复提交
    if workList.get(u.uid):
        workList[u.uid].SMS_CODE = None
        r = mr("pass", uid=u.uid, msg=f"{u.account}已经在处理了，请稍后再试")
        return r

    # 新增记录
    workList[u.uid] = u
    # 非阻塞启动登录线程
    asyncio.create_task(THREAD_DO_LOGIN(workList, u.uid, ocr, ocrDet))
    # 更新信息，响应api请求
    workList[u.uid].status = "pending"
    r = mr("pass", uid=u.uid, msg=f"{u.account}处理中, 到/check查询处理进度")
    return r


def THREAD_SMS(uid, code):
    print("phase THREAD_SMS: " + str(code))
    u = workList.get(uid, "")
    if not u:
        raise ValueError("账号不在记录中")
    if u.status == "SMS" or u.status == "wrongSMS":
        u.SMS_CODE = code
    else:
        raise ValueError("账号不在SMS过程中")


# -----regular functions-----
# 删除成功或失败的账号记录
async def deleteSession(uid):
    await asyncio.sleep(5)
    del workList[uid]


def load_from_file(filename):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # 组合脚本目录与文件名形成相对路径
    file_path = os.path.join(script_dir, filename)

    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_to_file(filename, data):
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"保存到文件时出错: {e}")


# 新增的 GET 路由
@app.route("/get", methods=["GET"])
async def get_data():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # 组合脚本目录与文件名形成相对路径
    file_path = os.path.join(script_dir, "config.json")

    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            config = json.load(f)
            param_k = request.args.get("k")
            # 接受GET传参k
            if param_k == config["key"]:
                filename = "data.json"
                data = load_from_file(filename)
                return jsonify(data)
            else:
                return jsonify([])


@app.route("/status", methods=["GET"])
async def checkql():
    ql_api = QLAPI()
    try:
        ql_api.load_config()
        ql_api.get_token()
        if ql_api.qltoken is None:
            r = mr(
                "wrongQL",
                msg="存储容器检测失败, 请检查参数是否正确",
                data={"name": ql_api.name, "notice": ql_api.notice,"isPush":ql_api.isWxPusher},
            )
        else:
            r = mr(
                "pass",
                msg="存储容器检测成功",
                data={"name": ql_api.name, "notice": ql_api.notice,"isPush":ql_api.isWxPusher},
            )
        return r
    except:
        r = mr(
            "wrongFile",
            msg="存储容器检测失败, 请检查config.json",
            data={},
        )
        return r


"""
@app.route("/delck", methods=["POST"])
def delck():
    data = request.get_json()
    uid = data.get("uid", None)
    if not exist(uid):
        r = mr(False, msg="not exist")
        return r

    THREAD_DELCK(uid)
"""


def extract_pt_pin(cookie_string):
    # 正则表达式匹配 pt_pin= 后的内容
    match = re.search(r"pt_pin=([^;]+)", cookie_string)
    if match:
        return match.group(1)
    else:
        return ""
@app.route("/qrcode", methods=["POST"])
async def createQrCode():
    data = await request.get_json()  # Retrieve JSON data from the POST request
    ptpin = data.get('params', '')
    result = createQrCodeApi(ptpin)
    if not result:
        return mr("error",msg='error',data='')
    return mr("pass",msg='ok', data=result)

def createQrCodeApi(params):
    ql_api = QLAPI()
    ql_api.load_config()
    url = "https://wxpusher.zjiecode.com/api/fun/create/qrcode"
    payload = {
        "appToken": ql_api.wxpusherAppToken,
        "extra": params,
        "validTime": 300
    }
    headers = {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br",
        "User-Agent": "PostmanRuntime-ApipostRuntime/1.1.0",
        "Connection": "keep-alive",
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        result = response.json()
        
        if result.get("code") == 1000:
            return result.get("data", {}).get("url")
        else:
            print(f"API Error: {result.get('msg', 'Unknown error')}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return False

#这里主要是实现了 如果用户扫码成功 wxpusher就会调用这个方法  具体传参看https://wxpusher.zjiecode.com/docs/#/?id=subscribe-callback
#然后我们根据传参接收参数 保存至json
@app.route("/wxpushercallback", methods=["POST"])
async def wxpushercallback():
    params = await request.get_json()
    uid = params.get('data', {}).get('uid', '')
    extra = params.get('data', {}).get('extra', '')
    #这里保存到JSON文件
    #找到DATA.JSON文件 DATA.JSON是一个数组
    #找到和extra等于ptpin的一项
    print("接收WXPUSHER CALLBACK UID"+uid)
    print("接收WXPUSHER CALLBACK EXTRA" + extra)
    data = load_from_file("data.json")

    # Find the item where extra equals ptpin
    for item in data:
        #print(item["ptpin"])
        #print(extra)
        if item["ptpin"] == extra:
            item["wxpusherUid"] = uid
            save_to_file("data.json", data)
            return mr("pass", msg='ok', data=item)

    return mr("error", msg='Item not found', data='')


class QLAPI:
    def __init__(self):
        self.config_file = "config.json"
        self.ql_isNewVersion = True
        self.qltoken = None
        self.qlhd = None
        self.qlhost = None
        self.qlid = None
        self.qlsecret = None
        self.qlenvs = []
        self.name = "GoDongGoCar"
        self.notice = "欢迎光临"
        self.wxpusherAppToken = None
        self.wxpusherAdminUid = None
        self.isWxPusher = False

    def load_config(self):
        # print(os.getcwd())
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # 组合脚本目录与文件名形成相对路径
        file_path = os.path.join(script_dir, self.config_file)

        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        self.qlhost = config["ql_host"]
        self.qlid = config["ql_app_id"]
        self.qlsecret = config["ql_app_secret"]
        self.ql_isNewVersion = config["ql_isNewVersion"]
        self.name = config["name"]
        self.notice = config["notice"]
        self.wxpusherAppToken = config["wxpusherAppToken"]
        self.wxpusherAdminUid = config["wxpusherAdminUid"]
        self.isWxPusher = config["isWxPusher"]

    def get_token(self):
        # print(self.qlhost)
        url = f"{self.qlhost}/open/auth/token?client_id={self.qlid}&client_secret={self.qlsecret}"
        print(url)
        response = requests.get(url)
        res = response.json()
        if res.get("code") == 200:
            self.qltoken = res["data"]["token"]
            self.qlhd = {
                "Authorization": f"Bearer {self.qltoken}",
                "accept": "application/json",
                "Content-Type": "application/json",
            }

    def get_ck(self):
        url = f"{self.qlhost}/open/envs?searchValue=JD_COOKIE&t={int(time.time())}"
        response = requests.get(url, headers=self.qlhd)
        res = response.json()
        if res.get("code") == 200:
            self.qlenvs = res["data"]
            return True
        else:
            return False

    def update_env(self, name, value, id, remarks):
        if self.ql_isNewVersion:
            params = {"name": name, "value": value, "id": id, "remarks": remarks}
        else:
            params = {"name": name, "value": value, "_id": id, "remarks": remarks}
        url = f"{self.qlhost}/open/envs"
        response = requests.put(url, headers=self.qlhd, data=json.dumps(params))
        res = response.json()
        if res.get("code") == 200:
            return True
        else:
            return False

    def create_env(self, name, value, remarks):
        params = [{"value": value, "name": name, "remarks": remarks}]
        url = f"{self.qlhost}/open/envs"
        response = requests.post(url, headers=self.qlhd, data=json.dumps(params))
        res = response.json()
        if res.get("code") == 200:
            return True
        else:
            return False

    def check_ck(self, ck, remarks):
        # 这里获取到CK的状态 1 失效
        # 正则取出pt_pin=后面的值
        # print(self.qlenvs)
        # FOR循环 找到extract_pt_pin(value) 和 extract_pt_pin(cookie) 相同的 如果不同则继续循环 如果循环结束 还是没有 则调用creat_env
        for i in self.qlenvs:
            if extract_pt_pin(i["value"]) == extract_pt_pin(ck):
                if self.ql_isNewVersion:
                    self.update_env(i["name"], ck, i["id"], remarks)
                else:
                    self.update_env(i["name"], ck, i["_id"], remarks)
                if i["status"] == 1:
                    if self.ql_isNewVersion:
                        self.enable_ck(i["id"])
                    else:
                        self.enable_ck(i["_id"])
                return
        self.create_env("JD_COOKIE", ck, remarks)

    def enable_ck(self, id):
        params = [id]
        url = f"{self.qlhost}/open/envs/enable"
        response = requests.put(url, headers=self.qlhd, data=json.dumps(params))
        res = response.json()
        if res.get("code") == 200:
            return True
        else:
            return False


# 创建本线程的事件循环，运行flask作为第一个任务
# asyncio.new_event_loop().run_until_complete(app.run(host=run_host, port=run_port))
# 确保 app.run 是一个协程函数
""".
async def start_app():
    await app.run(host=run_host, port=run_port)

# 然后将协程传递给 run_until_complete
loop = asyncio.get_event_loop()
if loop.is_running():
        # If a loop is already running, use it to run the app
    asyncio.ensure_future(start_app())
else:
    loop.run_until_complete(start_app())
"""

# asyncio.new_event_loop().run_until_complete(start_app())