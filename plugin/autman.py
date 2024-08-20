# [disable:false]
# [title:京东密码登陆]
# [open_source: true]
# [class: 工具类]

# [platform: qq,wx,tg,tb]
# [price: 999999]
# [service: 大帅逼]
# [rule: ^京东(.*)$]
# [admin: false]
# [version: 1.0.1]
# [description: 【测试版：无短信登陆正常，请测试有短信(异地验证)的情况下有无报错】</br>京东账号密码自动更新ck，检测ck过期调用账号密码更新(京东运行指令)，对接路飞的docke项目</br>用户指令：京东登陆</br>管理员指令：京东运行(用于自动更新ck，配合奥特曼的定时推送功能)</br>密码可能有泄露风险，前先开启支付验证以及虚拟财产支付密码，项目开源]
# [param: {"required":true,"key":"JDConfig.host","bool":false,"placeholder":"","name":"项目接口","desc":"http://项目接口ip:端口"}]
# [param: {"required":true,"key":"JDConfig.notify","bool":false,"placeholder":"","name":"通知渠道","desc":"例如：wx,qq,tg,tb，也就是机器人对接的渠道"}]


import time
import middleware,requests,re



class JD:
    def __init__(self, user, sender):
        self.user = user
        self.sender = sender
        self.tongname = "JD_login"#桶名
        self.tongconfig = "JDConfig"#桶配置
        self.host = middleware.bucketGet(self.tongconfig,"host")
        if self.host == "":
            self.sender.reply("没有填写过滑块接口")
            exit(0)
        ts = middleware.bucketGet(self.tongconfig,"notify")
        if ts == "":
            middleware.bucketSet(self.tongconfig,"notify","wx")
            ts = middleware.bucketGet(self.tongconfig, "notify")


        self.ts = ts.split(",")
        self.success = 0
        self.error = 0

    def get_ck(self):

        tong = middleware.bucketGet(self.tongname, self.user)
        if tong == "" or tong == "[]":
            if tong == "[]":
                middleware.bucketDel(self.tongname, self.user)
            self.sender.reply("【JD账号密码登陆】请输入京东绑定的手机号\n------\ntips:密码可能有泄露风险，在京东设置开启支付验证以免出现安全问题\nq退出")
            phone = self.sender.listen(180000)
            if phone == "" or phone == "q":
                self.sender.reply("退出")
                exit()
            elif re.compile(r'^1[3-9]\d{9}$').match(phone):
                self.sender.reply("输入密码")
                password = self.sender.listen(180000)
                qd = self.sender.getImtype()
                if password == "" or password == "q":
                    self.sender.reply("退出")
                    exit()
                else:
                    self.l(phone,password,qd)
            else:
                self.sender.reply("手机号错误")
        else:
            self.sender.reply("【JD账号密码登陆】已有账号，选择操作\n1、提交账号密码\n2、运行更新ck\n------\ntips:密码可能有泄露风险，在京东设置开启支付验证以免出现安全问题\nq退出")
            xh = self.sender.listen(180000)
            if xh == "q" or xh == "":
                self.sender.reply("退出")
                exit(0)
            elif xh == "1":
                self.sender.reply("输入手机号")
                phone = self.sender.listen(180000)
                if phone == "" or phone == "q":
                    self.sender.reply("退出")
                    exit()
                elif re.compile(r'^1[3-9]\d{9}$').match(phone):
                    self.sender.reply("输入密码")
                    qd = self.sender.getImtype()
                    password = self.sender.listen(180000)
                    if password == "" or password == "q":
                        self.sender.reply("退出")
                        exit()
                    else:
                        self.l(phone, password,qd)
                else:
                    self.sender.reply("手机号错误")
            elif xh == "2":
                msg = ""
                tong = eval(tong)
                n = 0
                for i in tong:
                    n += 1
                    phone = f'{i.split("#")[0][:3]}***{i.split("#")[0][7:]}'
                    msg += f"[{n}]:{phone}\n"
                self.sender.reply(f"选择账号序号更新cookie\n{msg}")
                xh = self.sender.listen(180000)
                if xh == "" or xh == "q":
                    self.sender.reply("退出")
                    exit()
                elif int(xh)-1 <= len(tong):
                    phone = tong[int(xh)-1].split("#")[0]
                    password = tong[int(xh)-1].split("#")[1]
                    qd = tong[int(xh)-1].split("#")[2]
                    self.l(phone,password,qd)
                else:
                    self.sender.reply("错误退出")
                    exit()

    def l(self,phone,password,qd,usid=None,auto=None):

        # 开始登录login
        loginData = self.login(phone, password)
        if loginData:
            if loginData["status"] != "pass":
                self.sender.reply(f"错误退出：{loginData}")
                exit()
            else:
                self.sender.reply(f"{phone[:3]}***{phone[7:]}正在登录中...")
                uid = loginData["uid"]
                # check,获取cookie
                for t in range(30):
                    time.sleep(1)
                    checkData = self.check(uid)
                    if checkData:
                        if checkData["status"] == "pass":

                            # 无验证
                            cookie = checkData["cookie"]
                            pin = re.search(r"pt_pin=([^;]+)",cookie).group(1)
                            # 调用青龙
                            # qlData = QL(cookie, user, sender).put_ql()
                            # self.sender.reply(qlData)

                            # 存储账号密码到奥特曼桶
                            if auto != "auto":
                                tong = middleware.bucketGet(self.tongname, self.user)
                                if tong == "":
                                    old = [f"{phone}#{password}#{qd}#{cookie}"]
                                    middleware.bucketSet(self.tongname, self.user, f"{old}")
                                    self.sender.reply(f"{pin}提交成功")
                           
                                    return
                                else:
                                    tong = eval(tong)
                                    a = 0
                                    for z in tong:
                                        if phone == z.split("#")[0]:
                                            qd = self.sender.getImtype()
                                            tong[a] = f"{phone}#{password}#{qd}#{cookie}"
                                            middleware.bucketSet(self.tongname, self.user, f"{tong}")
                                            self.sender.reply(f"{pin}更新成功")
                                         
                                            return
                                        a += 1
                                    tong.append(f"{phone}#{password}#{qd}#{cookie}")
                                    middleware.bucketSet(self.tongname, self.user, f"{tong}")
                                    self.sender.reply(f"{pin}提交成功")
                                  
                                    return
                            else:
                                tong = middleware.bucketGet(self.tongname, usid)
                                tong = eval(tong)
                                a = 0
                                for z in tong:
                                    if phone == z.split("#")[0]:
                                        qd = z.split("#")[2]
                                        tong[a] = f"{phone}#{password}#{qd}#{cookie}"
                                        middleware.bucketSet(self.tongname, usid, f"{tong}")
                                        self.sender.reply(f"{pin}更新成功")
                                        self.success
                                        return
                        elif checkData["status"] == "SMS":
                            self.error += 1
                            # 进行验证
                            if usid is not None:
                                middleware.push(qd,"",usid,f"京东账号密码自动登陆通知","[JD密码自动登陆通知]\n您的账号需要手机号验证，本次无法自动更新ck，请发送[京东登陆]手动更新ck")
                            self.sender.reply(f"{checkData['msg']},已发送短信")
                            code = self.sender.listen(180000)  # 等待3分钟
                            if code == "q" or code is None:
                                self.sender.reply("验证失败")
                                return
                            else:
                                # 验证码
                                smsData = self.sms(uid, code)
                                if smsData:
                                    if smsData["status"] == "pass":
                                        # 成功
                                        # for i in range(30):
                                        self.sender.reply(f"{uid}{code}")
                                        self.sender.reply(f"{smsData}")
                                        for i in range(30):
                                            checkData = self.check(uid)
                                            if checkData:
                                                if checkData["status"] == "pass":
                                                   
                                                    # 无验证
                                                    cookie = checkData["cookie"]
                                                    pin = re.search(r"pt_pin=([^;]+)", cookie).group(1)
                                                    # 调用青龙
                                                    # qlData = QL(cookie, user, sender).put_ql()
                                                    # self.sender.reply(qlData)
                                                    # 存储账号密码到奥特曼桶
                                                    if auto != "auto":
                                                        tong = middleware.bucketGet(self.tongname, self.user)
                                                        if tong == "" and auto != "auto":
                                                            old = [f"{phone}#{password}#{qd}#{cookie}"]
                                                            middleware.bucketSet(self.tongname, self.user, f"{old}")
                                                            self.sender.reply(f"{pin}提交成功")
                                                            
                                                            return
                                                        elif tong != "" and auto != "auto":
                                                            tong = eval(tong)
                                                            a = 0
                                                            for z in tong:
                                                                if phone == z.split("#")[0]:
                                                                    qd = z.split("#")[2]
                                                                    if self.sender.getImtype():
                                                                        qd = self.sender.getImtype()
                                                                    tong[a] = f"{phone}#{password}#{qd}#{cookie}"
                                                                    middleware.bucketSet(self.tongname, self.user,
                                                                                         f"{tong}")
                                                                    self.sender.reply(f"{pin}更新成功")
                                                                    
                                                                    return
                                                                a += 1

                                                            tong.append(f"{phone}#{password}#{qd}#{cookie}")
                                                            middleware.bucketSet(self.tongname, self.user,
                                                                                 f"{tong}")
                                                            self.sender.reply(f"{pin}提交成功")
                                                           
                                                            return
                                                    elif auto == "auto":
                                                        tong = middleware.bucketGet(self.tongname, usid)
                                                        tong = eval(tong)
                                                        a = 0
                                                        for z in tong:
                                                            if phone == z.split("#")[0]:
                                                                qd = z.split("#")[2]
                                                                tong[a] = f"{phone}#{password}#{qd}#{cookie}"
                                                                middleware.bucketSet(self.tongname, usid,
                                                                                     f"{tong}")
                                                                self.sender.reply(f"{pin}更新成功")
                                                                self.success
                                                                return
                                                            a += 1



                                                elif checkData["status"] == "pending":

                                                    time.sleep(3)
                                                    continue
                                                elif checkData["status"] == "SMS":
                                                    time.sleep(3)
                                                    continue
                                                else:
                                                    self.sender.reply(f"3{checkData['msg']}")
                                                    return

                                        else:
                                            self.sender.reply(f"检测失败")
                                            return
                                        # self.sender.reply("验证超时")
                                        # exit(0)



                                    else:
                                        # 验证码错误
                                        self.sender.reply(f"{smsData['msg']}")
                                        return
                                else:
                                    self.sender.reply("服务错误")
                                    return
                        elif checkData["status"] == "pending":
                            time.sleep(3)
                            continue
                        else:
                            self.sender.reply(f"{checkData['msg']}")
                            return



                    else:
                        self.sender.reply("服务错误")
                    time.sleep(1)
                # self.sender.reply("验证超时")
                # exit(0)
        else:
            self.sender.reply("服务错误")

    def run(self):
        if self.sender.isAdmin():
            users = middleware.bucketAllKeys(self.tongname)
            user = 0
            for i in users:
                tong = eval(middleware.bucketGet(self.tongname, i))
                for t in tong:
                    user += 1
            middleware.notifyMasters(f"[JD账号密码系统]开始检测更新ck，共发现{user}个号", self.ts)
            having = 0
            for usid in users:
                tong = eval(middleware.bucketGet(self.tongname,usid))
                #try:
                for t in tong:
                    phone = t.split("#")[0]
                    password = t.split("#")[1]
                    qd = t.split("#")[2]
                    ck = t.split("#")[3]
                    if self.check_login(ck):
                        having += 1
                        pass
                    else:
                        self.l(phone,password,qd,usid,"auto")
                        time.sleep(2)
                # except Exception as e:
                #     print(f"======{e}=======")
                #     continue
            middleware.notifyMasters(f"[JD账号密码系统]开始检测完毕\n总账号：{user}\n未失效：{having}\n成功数：{self.success}\n需要短信验证：{self.error}", self.ts)
            exit(0)

    def check_login(self,ck):
        url = "https://me-api.jd.com/user_new/info/GetJDUserInfoUnion"

        headers = {
            "Host": "me-api.jd.com",
            'Accept': "*/*",
            'Connection': "keep-alive",
            'Cookie': ck,
            "User-Agent": '"Android WebView";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
            "Accept-Language": "zh-cn",
            "Referer": "https://home.m.jd.com/myJd/newhome.action?sceneval=2&ufc=&",
            "Accept-Encoding": "gzip, deflate, br"
        }
        res = requests.get(url, headers=headers).text
        if "not login" not in res:
            return True
        else:
            return False


    def login(self,phone,pd):
        res = requests.post(f"{self.host}/login",json={"id":phone,"pw":pd,"remarks":phone})
        if res.status_code == 200:
            return res.json()
        else:
            return False

    def check(self,uid):
        res = requests.post(f"{self.host}/check", json={"uid": uid})
        if res.status_code == 200:
            return res.json()
        else:
            return False
    def sms(self,uid,code):
        res = requests.post(f"{self.host}/sms", json={"uid": uid,"code":code})
        if res.status_code == 200:
            return res.json()
        else:
            return False




if __name__ == "__main__":
    senderID = middleware.getSenderID()
    sender = middleware.Sender(senderID)
    user = sender.getUserID()
    JD = JD(user, sender)
    message = sender.getMessage()

    if "登陆" in message or "登录" in message:
        JD.get_ck()
    elif "运行" in message:
        JD.run()

