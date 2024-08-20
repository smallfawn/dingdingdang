const host = 'http://127.0.0.1:12345'
//初始化账号密码
let username = ''
let password = ''
let ql_host = bucketGet('smallfawn', "ql_host")//获取bucket桶的key值
let ql_app_id = bucketGet('smallfawn', "ql_app_id")
let ql_app_secret = bucketGet('smallfawn', "ql_app_secret")
//存储桶相关API
async function login() {

}
async function check() {

}
async function sms() {

}
async function update() {

}
function httpRequest(...args) {
    let body = request({
        url: "xxx",//地址
        headers: '',
        method: "post",//网络请求方法get,post,put,delete,head,patch
        dataType: "json",//数据类型json(json数据类型)、location(跳转页)
        body: {//请求体
            code: xxx,
        },
        formData: {//请求参数
            key1: xxx,
            key1: xxx,
            key1: xxx,
            key1: xxx,
        },

        timeOut: 3000//单位为毫秒ms，也可以都小写timeout
    })
}
