/**
 * @title JDCK自动更新脚本
 * @author smallfawn
 * @version v1.0.0
 */
//定时0 0 6 * * * 测试版 搭配检测CK脚本
let bucket = Bucket("smallfawn");
let qlappid = bucket["ql_app_id"];
let qlappsecret = bucket["ql_app_secret"];
let ptpins = bucket["ptpins"];
let qlhost = bucket["ql_host"];
let jdckhost = 'http://127.0.0.1:12345'
let failEnv = [];//初始化失败的环境变量
let token = "";
let env = []
/**
 * 获取临时Token
 */
function getToken() {
    let { body: tokenRes } = request({
        url: `${qlhost}/open/auth/token?client_id=${qlappid}&client_secret=${qlappsecret}`,
        method: "get",
        json: true,
    })
    if (tokenRes.code != 200) {
        console.log(`青龙密钥错误`);
        return;
    } else {
        token = tokenRes.data.token;
    }
}
/**
 * 获取青龙环境
 */
function getEnv() {
    let { body: envRes } = request({
        url: `${qlhost}/open/envs?t=${new Date().getTime()}&&searchValue=JD_COOKIE`,
        method: "get",
        headers: {
            Authorization: `Bearer ${token}`,
        },
        json: true,
    })
    if (envRes.code != 200) {
        console.log(`青龙环境获取失败`);
        return;
    } else {
        env = envRes.data;
        console.log(`青龙环境获取成功`);
    }
}
/**
 * 检索失效的京东COOKIE
 */
function checkEnv() {
    for (let i = 0; i < env.length; i++) {
        if (env[i].name == "JD_COOKIE") {
            if (
                env[i].value.match(/pt_pin=([^; ]+)(?=;?)/)
            ) {
                if (env[i].status == 1) {


                    //无效
                    failEnv.push({ id: env[i].id, ptpin: env[i].value.match(/pt_pin=([^; ]+)(?=;?)/)[1] });
                }
            }
        }
    }
}
//请求获得失效的京东COOKIE
//匹配pt_pin //根据存储桶拿到pt_pin 相关的手机号和密码


//再次请求登录
//理论上第一次需要经过短信验证 这里在用户第一次提交账号密码时就已经通过了
function login(account, password) {
    account = account + "";
    password = password + "";
    const response = request({
        url: `${jdckhost}/login`,
        method: "post",
        json: true,
        body: { id: account, pw: password },
    });
    if (response.body.status == 'pass') {
        for (let i = 0; i < 15; i++) {
            time.sleep(1000)
            let checkRes = request({
                url: `${jdckhost}/check`,
                method: "post",
                json: true,
                body: { uid: response.body.uid },
            });
            if (checkRes.body.status == 'pass') {
                return checkRes.body.cookie
            }
        }

    } else {
        const response = request({
            url: `${jdckhost}/login`,
            method: "post",
            json: true,
            body: { id: account, pw: password },
        });
        if (response.body.status == 'pass') {
            for (let i = 0; i < 15; i++) {
                time.sleep(1000)
                let checkRes = request({
                    url: `${jdckhost}/check`,
                    method: "post",
                    json: true,
                    body: { uid: response.body.uid },
                });
                if (checkRes.body.status == 'pass') {
                    return checkRes.body.cookie
                }
            }
        } else {
            return ''
        }
    }
}
function updateEnv(id, cookie) {
    let { body: res } = request({
        url: `${qlhost}/open/envs?t=${new Date().getTime()}`,
        method: "put",
        headers: {
            Authorization: `Bearer ${token}`,
        },
        json: true,
        body: { "name": "JD_COOKIE", "value": cookie, "remarks": null, "id": id }
    })
    if (res.code == 200) {
        console.log(`更新青龙成功`);
    } else {
        console.log(`更新青龙失败`);
    }
}
function enableEnv(id) {
    let { body: res } = request({
        url: `${qlhost}/open/envs/enable?t=${new Date().getTime()}`,
        method: "put",
        headers: {
            Authorization: `Bearer ${token}`,
        },
        json: true,
        body: [id]
    })
    if (res.code == 200) {
        console.log(`启用青龙成功`);
    } else {
        console.log(`启用青龙失败`);
    }
}
//更新青龙
function main() {
    try {
        ptpins = JSON.parse(ptpins);
    } catch (error) {
        console.log(`存储桶解析失败`);
        return;
    }
    getToken();
    if (token !== '') {
        getEnv();
        checkEnv();
        for (let i = 0; i < ptpins.length; i++) {
            for (let j = 0; j < failEnv.length; j++) {
                if (ptpins[i].ptpin == failEnv[j].ptpin) {
                    let account = ptpins[i].account;
                    let password = ptpins[i].password;
                    let cookie = login(account, password);
                    if (cookie != '') {
                        //更新青龙
                        //应该更新完毕之后 再去启动变量
                        //未完待续
                        updateEnv(failEnv[j].id, cookie);
                        enableEnv(failEnv[j].id)
                        return
                    }
                }

            }
        }
        return console.log(`未找到匹配的失效账号`)
    }

    //...
}
main()