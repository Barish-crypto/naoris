const fetch = require('node-fetch');
const fs = require('fs');
const readlineSync = require('readline-sync');
const { exec } = require('child_process');
const moment = require('moment-timezone');

const wib = moment.tz("Asia/Jakarta");
const whiteList = [];

class NaorisProtocol {
    constructor() {
        this.headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
            "Origin": "chrome-extension://cpikalnagknmlfhnilhfelifgbollmmp",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "none",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        };
        this.proxies = [];
        this.proxy_index = 0;
        this.account_proxies = {};
        this.clearTerminal(); // Clear terminal on initialization
    }

    // Method for printing a question
    printQuestion() {
        while (true) {
            const choice = readlineSync.questionInt('Choose [1/2/3] -> \n1. Run With Monosans Proxy\n2. Run With Private Proxy\n3. Run Without Proxy\n');
            if ([1, 2, 3].includes(choice)) {
                const proxyType = choice === 1 ? "Run With Monosans Proxy" :
                                  choice === 2 ? "Run With Private Proxy" :
                                  "Run Without Proxy";
                console.log(`${proxyType} Selected.`);
                return choice;
            } else {
                console.log('Please enter either 1, 2, or 3.');
            }
        }
    }

    // Log method
    log(message) {
        console.log(`[ ${wib.format('MM/DD/YYYY HH:mm:ss z')} ] | ${message}`);
    }

    // Welcome message
    welcome() {
        this.log('Tool developed by group tele Airdrop Hunter Siêu Tốc');
    }

    async loadProxies(useProxyChoice) {
        const filename = 'proxy.txt';
        try {
            if (useProxyChoice === 1) {
                const response = await fetch("https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/all.txt");
                const data = await response.text();
                fs.writeFileSync(filename, data);
                this.proxies = data.split('\n');
            } else if (fs.existsSync(filename)) {
                const data = fs.readFileSync(filename, 'utf-8');
                this.proxies = data.split('\n');
            } else {
                this.log('File proxy.txt does not exist.');
                return;
            }
            this.log(`Total proxies: ${this.proxies.length}`);
        } catch (error) {
            this.log(`Error loading proxies: ${error}`);
            this.proxies = [];
        }
    }

    checkProxySchemes(proxy) {
        const schemes = ["http://", "https://", "socks4://", "socks5://"];
        return schemes.some(scheme => proxy.startsWith(scheme)) ? proxy : `http://${proxy}`;
    }

    getNextProxyForAccount(account) {
        if (!this.account_proxies[account] && this.proxies.length) {
            const proxy = this.checkProxySchemes(this.proxies[this.proxy_index]);
            this.account_proxies[account] = proxy;
            this.proxy_index = (this.proxy_index + 1) % this.proxies.length;
        }
        return this.account_proxies[account];
    }

    async processUserLogin(address, proxy = null, retries = 5) {
        const url = "https://naorisprotocol.network/sec-api/auth/generateToken";
        const data = JSON.stringify({ "wallet_address": address });
        const headers = { ...this.headers, "Content-Length": String(data.length), "Content-Type": "application/json" };
        
        for (let attempt = 0; attempt < retries; attempt++) {
            try {
                const response = await fetch(url, { method: 'POST', headers, body: data, proxy });
                if (response.status === 401) {
                    this.log(`Authentication error: Blocked by Cloudflare for ${address}`);
                    return;
                }
                const result = await response.json();
                return result.token;
            } catch (error) {
                if (attempt < retries - 1) {
                    await new Promise(resolve => setTimeout(resolve, 5000));
                    continue;
                }
                this.log(`Error fetching token: ${error}`);
            }
        }
    }

    async processWalletDetails(address, token, useProxy, proxy = null, retries = 5) {
        const url = "https://naorisprotocol.network/testnet-api/api/testnet/walletDetails";
        const data = JSON.stringify({ "walletAddress": address });
        const headers = { ...this.headers, "Authorization": `Bearer ${token}`, "Token": token, "Content-Length": String(data.length), "Content-Type": "application/json" };

        for (let attempt = 0; attempt < retries; attempt++) {
            try {
                const response = await fetch(url, { method: 'POST', headers, body: data, proxy });
                if (response.status === 401) {
                    token = await this.processUserLogin(address, proxy);
                    headers["Authorization"] = `Bearer ${token}`;
                    continue;
                }
                const result = await response.json();
                return result.details;
            } catch (error) {
                if (attempt < retries - 1) {
                    await new Promise(resolve => setTimeout(resolve, 5000));
                    continue;
                }
                this.log(`Error fetching wallet details: ${error}`);
            }
        }
    }

    async processSendHeartbeats(address, deviceHash, token, useProxy, proxy = null, retries = 5) {
        const url = "https://naorisprotocol.network/sec-api/api/produce-to-kafka";
        const data = JSON.stringify({ "topic": "device-heartbeat", "inputData": { "walletAddress": address, "deviceHash": deviceHash } });
        const headers = { ...this.headers, "Authorization": `Bearer ${token}`, "Content-Length": String(data.length), "Content-Type": "application/json" };

        for (let attempt = 0; attempt < retries; attempt++) {
            try {
                const response = await fetch(url, { method: 'POST', headers, body: data, proxy });
                if (response.status === 401) {
                    token = await this.processUserLogin(address, proxy);
                    headers["Authorization"] = `Bearer ${token}`;
                    continue;
                }
                const result = await response.json();
                if (result.message === "Message production initiated") {
                    this.log(`${address}: PING successful`);
                }
                return;
            } catch (error) {
                if (attempt < retries - 1) {
                    await new Promise(resolve => setTimeout(resolve, 5000));
                    continue;
                }
                this.log(`Error sending PING: ${error}`);
            }
        }
    }

    async processAccounts(address, deviceHash, useProxy) {
        const token = await this.processUserLogin(address, this.getNextProxyForAccount(address) || null);
        if (token) {
            const tasks = [
                this.processWalletDetails(address, token, useProxy, this.getNextProxyForAccount(address) || null),
                this.processSendHeartbeats(address, deviceHash, token, useProxy, this.getNextProxyForAccount(address) || null)
            ];
            await Promise.all(tasks);
        }
    }

    async main() {
        try {
            const accounts = JSON.parse(fs.readFileSync('accounts.json', 'utf-8'));
            if (!accounts.length) {
                this.log('No accounts loaded.');
                return;
            }

            const useProxyChoice = this.printQuestion();
            const useProxy = useProxyChoice === 1 || useProxyChoice === 2;

            this.clearTerminal();
            this.welcome();
            this.log(`Total Accounts: ${accounts.length}`);

            if (useProxy) {
                await this.loadProxies(useProxyChoice);
            }

            while (true) {
                const tasks = [];
                for (const account of accounts) {
                    const { walletAddress: address, deviceHashs } = account;
                    if (address && deviceHashs) {
                        for (const deviceHash of deviceHashs) {
                            tasks.push(this.processAccounts(address, deviceHash, useProxy));
                        }
                    }
                }
                await Promise.all(tasks);
                await new Promise(resolve => setTimeout(resolve, 10000));
            }

        } catch (error) {
            this.log(`Error: ${error}`);
        }
    }

    clearTerminal() {
        exec(process.platform === 'win32' ? 'cls' : 'clear', (err, stdout, stderr) => {
            if (err) {
                console.error('Error clearing terminal:', err);
            }
        });
    }
}

// Main entry point
(async () => {
    const bot = new NaorisProtocol();
    try {
        const useProxyChoice = bot.printQuestion();
        await bot.main();
    } catch (error) {
        console.log('Error:', error);
    }
})();
