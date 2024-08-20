const axios = require('axios')
const fs = require('fs')
//使用前在同目录创建CK_WxPusherUid.json文件  里面内容默认为[]
const GoDongGoCarHost = 'https://127.0.0.1:12345'
const key = 'XXXXX'
//请使用前拉 调用该库进行通知
//旧版本青龙
//ql repo https://github.com/ccwav/QLScript2.git "jd_" "NoUsed" "ql|sendNotify|utils"
//新版本青龙
//ql repo https://github.com/ccwav/QLScript2.git "jd_" "NoUsed" "ql|sendNotify|utils|USER_AGENTS|jdCookie|JS_USER_AGENTS"

async function main() {
    //读取CK_WxPusherUid.json
    let CK_WxPusherUidArr = []
    try {
        CK_WxPusherUidArr = fs.readFileSync('./CK_WxPusherUid.json', 'utf8')
    } catch (e) {
        console.log(`未找到CK_WxPusherUid.json文件`);
        return
    }
    try {
        CK_WxPusherUidArr = JSON.parse(CK_WxPusherUidArr)
    } catch (e) {
        console.log(`CK_WxPusherUid.json不是有效的JSON格式`);
        return
    }
    const { data: users } = await axios.get(`${GoDongGoCarHost}/get?k=${key}`);
    for (const user of users) {
        if (user?.wxpusherUid) {
            //如果存在
            if (CK_WxPusherUidArr.find(item => item.pt_pin == user.ptpin)) {

            } else {
                CK_WxPusherUidArr.push({ pt_pin: user.ptpin, Uid: user.wxpusherUid })


            }
        }
    }
    console.log(CK_WxPusherUidArr)
    console.log(`更新完成`)
    //写入CK_WxPusherUid.json
    try {
        fs.writeFileSync('CK_WxPusherUid.json', JSON.stringify(CK_WxPusherUidArr, null, 4))

    } catch (e) {
        console.log(`写入CK_WxPusherUid.json失败`);
        return
    }

}
main()