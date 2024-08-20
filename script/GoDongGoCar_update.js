const axios = require('axios');

const ql_host = "http://127.0.0.1:5700";
const GoDongGoCarHost = "http://127.0.0.1:12345";
const ql_app_id = "aaaaa";
const ql_app_secret = "bbbbb";
const ql_isNewVersion = true; // 是否为青龙新版本（>= 2.11）
const key = 'ababab'; // 密钥

let checkRes = false;
let userCookie = null;
let failEnvs = [];
let waitUpEnvs = [];

async function main() {
    try {
        const QL = new QLAPI();

        const token = await QL.getToken();
        if (!token) return;

        await QL.checkCookie();

        if (failEnvs.length > 0) {
            await updateWaitList();
        }

        console.log('待更新:', waitUpEnvs);

        for (const user of waitUpEnvs) {
            checkRes = false;
            userCookie = null;
            const loginRes = await loginApi(user.account, user.password);
            if (loginRes) {
                await handleLoginResponse(loginRes, user, QL);
            } else {
                console.log(`账号 ${user.account} 登录失败`);
            }
        }
    } catch (error) {
        console.error('An error occurred:', error);
    }
}

async function updateWaitList() {
    try {
        const { data: users } = await axios.get(`${GoDongGoCarHost}/get?k=${key}`);
        failEnvs.forEach(env => {
            const matchedUser = users.find(user => user.ptpin === env.ptpin);
            if (matchedUser) {
                matchedUser.id = env.id;
                waitUpEnvs.push(matchedUser);
            }
        });
    } catch (error) {
        console.error('Failed to update wait list:', error);
    }
}

async function loginApi(account, password) {
    try {
        const response = await axios.post(`${GoDongGoCarHost}/login`, { id: account, pw: password }, {
            headers: {
                'Content-Type': 'application/json',
                'User-Agent': 'GoDongGoCar',
            }
        });

        return response.data.status === 'pass' ? response.data.uid : false;
    } catch (error) {
        console.error('Login API request failed:', error);
        return false;
    }
}

async function checkApi(uid) {
    try {
        const response = await axios.post(`${GoDongGoCarHost}/check`, { uid }, {
            headers: {
                'Content-Type': 'application/json',
                'User-Agent': 'GoDongGoCar',
            }
        });

        const { status, cookie, msg } = response.data;
        checkRes = true;

        switch (status) {
            case 'pass':
                userCookie = cookie;
                break;
            case 'error':
                console.error('Error occurred during check');
                break;
            case 'wrongSMS':
                console.error('Wrong SMS provided');
                break;
            case 'SMS':
                console.log('SMS required, please log in once via the web to proceed');
                break;
            case 'pending':
                checkRes = false;
                break;
            default:
                console.error(`Error: ${msg}`);
        }
    } catch (error) {
        console.error('Check API request failed:', error);
    }
}

async function handleLoginResponse(loginRes, user, QL) {
    console.log('等待 2s');
    await delay(2000);

    for (let i = 0; i < 30; i++) {
        if (!checkRes) {
            await checkApi(loginRes);
        } else if (userCookie) {
            console.log(`更新成功: ${userCookie}`);
            await QL.updateEnv(user.id, userCookie, user.remarks);
            break;
        } else {
            console.log(`账号 ${user.account} 登录失败`);
            break;
        }
        await delay(1000);
    }
}

function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function getPin(cookie) {
    const match = cookie.match(/pt_pin=([^; ]+)(?=;?)/);
    return match ? match[1] : '';
}

class QLAPI {
    constructor() {
        this.ql_host = ql_host;
        this.ql_app_id = ql_app_id;
        this.ql_app_secret = ql_app_secret;
        this.ql_isNewVersion = ql_isNewVersion;
        this.ql_token = '';
    }

    async getToken() {
        try {
            const response = await axios.get(`${this.ql_host}/open/auth/token`, {
                params: { client_id: this.ql_app_id, client_secret: this.ql_app_secret }
            });

            if (response.data.code === 200) {
                this.ql_token = response.data.data.token;
                return this.ql_token;
            }
        } catch (error) {
            console.error('Failed to get token:', error);
        }
        return false;
    }

    async updateEnv(id, cookie, remarks) {
        const body = this.ql_isNewVersion
            ? { name: "JD_COOKIE", value: cookie, id, remarks }
            : { name: "JD_COOKIE", value: cookie, _id: id, remarks };

        try {
            const response = await axios.put(`${this.ql_host}/open/envs?t=${Date.now()}`, body, {
                headers: {
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${this.ql_token}`,
                }
            });

            return response.data.code === 200;
        } catch (error) {
            console.error('Failed to update environment variable:', error);
            return false;
        }
    }

    async checkCookie() {
        const envs = await this.getEnvs();
        failEnvs = envs.filter(env => env.status === 1).map(env => ({
            id: this.ql_isNewVersion ? env.id : env._id,
            ptpin: getPin(env.value)
        }));
    }

    async getEnvs() {
        try {
            const response = await axios.get(`${this.ql_host}/open/envs`, {
                params: { searchValue: 'JD_COOKIE' },
                headers: { Authorization: `Bearer ${this.ql_token}` },
            });

            return response.data.code === 200 ? response.data.data : [];
        } catch (error) {
            console.error('Failed to get environment variables:', error);
            return [];
        }
    }
}

main().catch(console.error);
