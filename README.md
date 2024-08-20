# 正式版V1已发布 接下来测试 都会在test分支进行 main主要是正式版
# V2版本目前需要20元 演示gc.onecc.cc
# 请合作者完善plugin 里面的两个机器人框架的插件 和script机器人定时执行脚本
# 目前计划适配 无界 傻妞 奥特曼
# 截至8-18 未参与issues 提议(反馈BUG和功能建议) 和 pr代码(提供和优化代码)的都会被撤去内测资格


自用 学习 爱用不用 我自己写的我想咋写咋写
```shell
mkdir godonggocar
```
```shell
在godonggocar目录下创建config.json文件
写入
{
"name": "test",
"notice": "test",
"ql_host": "http://127.0.0.1:5700",
"ql_app_id": "xxxxx",
"ql_app_secret": "xxxxx",
"ql_isNewVersion":true,
"key": "xxxxx",
"wxpusherAppToken":"AT_XXXXX",
"wxpusherAdminUid":"SSS",
"isWxPusher":true
}
创建data.json文件 里面填写[]
isWxPusher 推送开关 如果false 则不会展示二维码
wxpusherAdminUid WXPUSHER管理员UID
wxpusherAppToken WXPUSHER应用ID
ql_isNewVersion 如果大于等于2.11 则默认true 小于则false
key 指的是获取 账号密码的密钥 建议最少16位 为了保护你的账号密码信息 请务必自定义密钥且8-16位字母加数字组合
不支持标点符号等
```
```shell
ARM架构
docker run -dit \
  -v $PWD/godonggocar/config.json:/app/config.json \
  -v $PWD/godonggocar/data.json:/app/data.json \
  -p 12345:12345 \
registry.cn-hangzhou.aliyuncs.com/smallfawn/linux_arm64_ddd
```
```shell
AMD架构
docker run -dit \
  -v $PWD/godonggocar/config.json:/app/config.json \
  -v $PWD/godonggocar/data.json:/app/data.json \
  -p 12345:12345 \
registry.cn-hangzhou.aliyuncs.com/smallfawn/linux_amd64_ddd
```
```
获取账密 备注 ptpin信息 /get?k=密钥
```
第一个12345是外部接口
## `/login` 接口

### 描述
处理登录请求。接收到请求后，服务器会启动一个登录线程来处理用户登录操作。

### 请求方法
`POST`

### 请求路径
`/login`

### 请求参数

| 参数名 | 类型   | 是否必需 | 描述               |
|--------|--------|----------|--------------------|
| id     | string | 是       | 用户名或账号       |
| pw     | string | 否       | 密码               |
| type   | string | 否       | 登录类型，默认为 `password` |
| isAuto | bool   | 否       | 是否自动登录，默认为 `False` |

### 响应示例
```json
{
	"msg": "13155555555处理中, 到/check查询处理进度",
	"status": "pass",
	"uid": "7654321xxx"
}
```
```json
{
  "status": "pass",
  "uid": "7654321xxx",
  "msg": "用户名已经在处理了，请稍后再试"
}
```

### /sms 接口

### 描述
处理短信验证码的提交。用于在登录过程中输入并提交短信验证码。

### 请求方法
`POST`

### 请求路径
`/sms`

### 请求参数
| 参数名 | 类型   | 是否必需 | 描述               |
|--------|--------|----------|--------------------|
| uid    | string | 是       | 登录的用户标识符       |
| code     | string | 是     | 短信验证码（必须为6位数字）|
### 响应示例
```json
{
  "status": "pass",
  "msg": "成功提交验证码"
}
```
### 提交成功后 5s后会清除状态 所以在提交成功后 在5s内尽快check 查询cookie
```json
{
  "status": "wrongSMS",
  "msg": "验证码错误"
}
```
### /check 接口

### 描述
检查指定用户的登录状态。用于查询账号的处理进度或结果。

### 请求方法
`POST`

### 请求路径
`/check`

### 请求参数
| 参数名 | 类型   | 是否必需 | 描述               |
|--------|--------|----------|--------------------|
| uid    | string | 是       | 登录的用户标识符       |
### 响应示例
```json
{
  "status": "pass",
  "cookie": "user_cookie",
  "msg": "成功"
}
```
```json
{
  "status": "pending",
  "msg": "正在处理中，请等待"
}
```
```json
{
  "status": "error",
  "msg": "登录失败，请在十秒后重试：错误信息"
}
```
```json
{
  "status": "wrongSMS",
  "msg": "短信验证错误，请重新输入"
}
```
```json
{
  "status": "SMS",
  "msg": "需要短信验证"
}
```
