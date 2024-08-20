/**
 * @title JDCK
 * @author smallfawn
 * @version v1.0.0
 * @rule 叮叮当
 */
/**
 * 你必须设置存储桶smallfawn
 * 且 存储桶内有 ql_host 、ql_app_id 、ql_app_secret
 */
const s = sender;
const chat = s.getChatId();
const qq = s.getUserId();
const inputTimeout = 30 * 1000;
const host = "http://127.0.0.1:12345";
const bucket = Bucket("smallfawn");
let ql_host = bucket["ql_host"];
let ql_app_id = bucket["ql_app_id"];
let ql_app_secret = bucket["ql_app_secret"];
let input = "";

function main() {
    try {
        if (bucket["ptpins"] == null) {
            bucket["ptpins"] = '[]'
        }
        let ptpins = bucket["ptpins"];
        try {
            ptpins = JSON.parse(ptpins);
        } catch (error) {
            s.reply(`存储桶解析失败`);
            return;
        }

        let account = "";
        let password = "";
        let code = "";
        promptInput("手机号", (input) => { !isNaN(input) && isValidPhoneNumber(input) });
        if (!input) return s.reply("超时/已退出");
        account = input;
        promptInput("密码", (input) => input !== "");
        if (!input) return s.reply("超时/已退出");
        password = input;
        const loginResponse = loginApi(account + "", password);
        if (!loginResponse || loginResponse.status !== "pass") return;

        s.reply(`${qq}#${s.getUserName()} 正在执行登录，请稍等`);
        for (let t = 0; t < 20; t++) {
            time.sleep(1000);
            const checkResponse = checkApi(loginResponse.uid);
            if (checkResponse.status === "pass") {
                s.reply(`${qq}#${s.getUserName()} 登录成功`);
                let ptpinValue = checkResponse.cookie.match(/pt_pin=([^; ]+)(?=;?)/)[1];
                //如果存在则不push
                if (ptpins.find((item) => item.ptpin === ptpinValue)) {
                    //s.reply(`${qq}#${s.getUserName()} 账号已存在`);
                } else {
                    ptpins.push({ id: s.getUserId(), ptpin: ptpinValue, account, password });
                    bucket["ptpins"] = JSON.stringify(ptpins);
                }
                update(checkResponse.cookie)
                return;
            } else if (checkResponse.status === "SMS") {
                s.reply(`${qq}#${s.getUserName()} 正在发送短信，请稍等`);
                promptInput("短信验证码", (input) => !isNaN(input));
                if (!input) return s.reply("超时/已退出");
                code = input;
                let smsResponse = smsApi(loginResponse.uid, code + "");
                if (smsResponse.status === "wrongSMS") {
                    s.reply(`${qq}#${s.getUserName()} 短信验证码错误`);
                    promptInput("短信验证码", (input) => !isNaN(input));
                    if (!input) return s.reply("超时/已退出");
                    code = input;
                    smsResponse = smsApi(loginResponse.uid, code + "");
                    if (smsResponse.status === "pass") {
                        s.reply(`${qq}#${s.getUserName()} 短信验证码正确`);
                        const checkResponse = checkApi(loginResponse.uid);
                        if (checkResponse.status === "pass") {
                            s.reply(`${qq}#${s.getUserName()} 登录成功`);
                            let ptpinValue = checkResponse.cookie.match(
                                /pt_pin=([^; ]+)(?=;?)/
                            )[1];
                            if (ptpins.find((item) => item.ptpin === ptpinValue)) {
                                //s.reply(`${qq}#${s.getUserName()} 账号已存在`);
                            } else {
                                ptpins.push({ id: s.getUserId(), ptpin: ptpinValue, account, password });
                                bucket["ptpins"] = JSON.stringify(ptpins);
                            }
                            update(checkResponse.cookie)
                            return;
                        }
                    }
                }
                if (smsResponse.status === "pass") {
                    s.reply(`${qq}#${s.getUserName()} 短信验证码正确`);
                    const checkResponse = checkApi(loginResponse.uid);
                    if (checkResponse.status === "pass") {
                        s.reply(`${qq}#${s.getUserName()} 登录成功`);
                        return;
                    }
                }
            } else if (checkResponse.status === "error") {
                s.reply(`${qq}#${s.getUserName()}` + checkResponse.msg);
                return;
            }
        }
    } catch (error) {
        s.reply(`操作失败：${error.message}`);
    }
}

function promptInput(promptText, validationFunction) {
    s.reply(
        `@${qq}#${s.getUserName()} 请在 ${inputTimeout / 1000
        }s 内输入正确的 ${promptText}`
    );
    s.listen({
        handle: (s) => {
            input = s.getContent();
            if (validationFunction(input) && isSameUserAndChat()) {
                //s.reply(`@${qq}#${s.getUserName()} 输入正确 ` + input);
                return;
            } else if (input === "q" && isSameUserAndChat()) {
                input = "";
                return;
            } else {
                input = "";
                return;
            }
        },
        timeout: inputTimeout,
    });
}

function isSameUserAndChat() {
    return s.getUserId() === qq && s.getChatId() === chat;
}

function loginApi(account, password) {
    const response = request({
        url: `${host}/login`,
        method: "post",
        json: true,
        body: { id: account, pw: password },
    });
    return response.body;
}

function checkApi(uid) {
    const response = request({
        url: `${host}/check`,
        method: "post",
        json: true,
        body: { uid: uid },
    });
    return response.body;
}

function smsApi(uid, code) {
    const response = request({
        url: `${host}/sms`,
        method: "post",
        json: true,
        body: { uid: uid, code: code },
    });
    return response.body;
}
//根据存储桶拿到青龙密钥
function isValidUrl(url) {
    const pattern = /^(https?:\/\/)[^\s/$.?#].[^\s]*\.[^\s]*$/i;
    return pattern.test(url);
}
function isValidPhoneNumber(phoneNumber) {
    const pattern = /^1[3-9]\d{9}$/;
    return pattern.test(phoneNumber);
}
//进行更新上传操作
function update(cookies) {
    if (!ql_app_id || !ql_app_secret || !ql_host) {
        s.reply(`请先配置青龙密钥和APPID和青龙地址`);
        return;
    }
    if (!isValidUrl(ql_host)) {
        s.reply(`青龙地址格式错误`);
        return;
    }
    let token = ''
    let { body: tokenRes } = request({
        url: `${ql_host}/open/auth/token?client_id=${ql_app_id}&client_secret=${ql_app_secret}`,
        method: "get",
        json: true,
    })
    if (tokenRes.code != 200) {
        s.reply(`青龙密钥错误`);
        return;
    }
    token = tokenRes.data.token
    let { body: env } = request({
        url: `${ql_host}/open/envs?t=${Date.now()}&searchValue=JD_COOKIE`,
        method: "get",
        headers: {
            Authorization: `Bearer ${token}`,
        },
        json: true,
    })
    let found = false; // 标记是否找到匹配的 pt_pin
    if (env.data.length == 0) {
        createEnv(cookies);
    } else {
        for (let i = 0; i < env.data.length; i++) {
            if (env.data[i].name == "JD_COOKIE") {
                if (
                    env.data[i].value.match(/pt_pin=([^; ]+)(?=;?)/) &&
                    env.data[i].value.match(/pt_pin=([^; ]+)(?=;?)/)[1] == cookies.match(/pt_pin=([^; ]+)(?=;?)/)[1]
                ) {
                    found = true;
                    let id = env.data[i].id;
                    let { body: updateRes } = request({
                        url: `${ql_host}/open/envs?t=${Date.now()}`,
                        method: "put",
                        headers: {
                            Authorization: `Bearer ${token}`,
                        },
                        json: true,
                        body: { "name": "JD_COOKIE", "value": cookies, "remarks": null, "id": id }
                    })
                    if (updateRes.code == 200) {
                        s.reply(`更新成功`);
                    }
                }
            }
        }

    }
    if (!found) {
        createEnv(cookies);
    }
    // 创建新变量的函数
    function createEnv(cookie) {
        let { body: createRes } = request({
            url: `${ql_host}/open/envs?t=${Date.now()}`,
            method: "post",
            headers: {
                Authorization: `Bearer ${token}`,
            },
            json: true,
            body: [{ "value": cookie, "name": "JD_COOKIE" }]
        })
        //s.reply(createRes)
        if (createRes.code == 200) {
            s.reply(`创建成功`);
        }
    }
}
main();
