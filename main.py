import asyncio
import json
import os
from datetime import datetime
from colorama import Fore, Style
import pytz
from fake_useragent import FakeUserAgent
import requests

wib = pytz.timezone('Asia/Jakarta')
whiteList = []

class NaorisProtocol:
    def __init__(self) -> None:
        self.headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
            "Origin": "chrome-extension://cpikalnagknmlfhnilhfelifgbollmmp",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "none",
            "User-Agent": FakeUserAgent().random
        }
        self.proxies = []
        self.proxy_index = 0
        self.account_proxies = {}

    def log(self, message):
        print(f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().astimezone(wib).strftime('%x %X %Z')} ]{Style.RESET_ALL} {Fore.WHITE + Style.BRIGHT}| {Style.RESET_ALL}{message}", flush=True)

    def welcome(self):
        print(f"{Fore.YELLOW + Style.BRIGHT}Tool phát triển bởi nhóm tele Airdrop Hunter Siêu Tốc (https://t.me/airdrophuntersieutoc)")

    def format_seconds(self, seconds):
        return str(datetime.timedelta(seconds=seconds))

    async def load_proxies(self, use_proxy_choice: int):
        try:
            filename = "proxy.txt"
            if use_proxy_choice == 1:
                response = await asyncio.to_thread(requests.get, "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/all.txt")
                response.raise_for_status()
                with open(filename, 'w') as f:
                    f.write(response.text)
                self.proxies = response.text.splitlines()
            elif os.path.exists(filename):
                with open(filename, 'r') as f:
                    self.proxies = f.read().splitlines()
            else:
                self.log(f"{Fore.RED + Style.BRIGHT}File proxy.txt không tồn tại.{Style.RESET_ALL}")
                return

            self.log(f"{Fore.GREEN + Style.BRIGHT}Tổng số proxy: {Style.RESET_ALL}{len(self.proxies)}")
        except Exception as e:
            self.log(f"{Fore.RED + Style.BRIGHT}Lỗi tải proxy: {e}{Style.RESET_ALL}")
            self.proxies = []

    def check_proxy_schemes(self, proxies):
        schemes = ["http://", "https://", "socks4://", "socks5://"]
        return proxies if any(proxies.startswith(scheme) for scheme in schemes) else f"http://{proxies}"

    def get_next_proxy_for_account(self, account):
        if account not in self.account_proxies and self.proxies:
            proxy = self.check_proxy_schemes(self.proxies[self.proxy_index])
            self.account_proxies[account] = proxy
            self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return self.account_proxies.get(account)

    def rotate_proxy_for_account(self, account):
        if self.proxies:
            proxy = self.check_proxy_schemes(self.proxies[self.proxy_index])
            self.account_proxies[account] = proxy
            self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
            return proxy

    def load_accounts(self):
        try:
            with open('accounts.json', 'r') as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def mask_account(self, account):
        return f"{account[:6]}{'*' * 6}{account[-6:]}"

    def print_message(self, address, proxy, color, message):
        self.log(
            f"{Fore.CYAN + Style.BRIGHT}[ Tài khoản:{Style.RESET_ALL}{Fore.WHITE + Style.BRIGHT}{self.mask_account(address)}{Style.RESET_ALL} "
            f"{Fore.MAGENTA + Style.BRIGHT}-{Style.RESET_ALL} Proxy: {Fore.WHITE + Style.BRIGHT}{proxy}{Style.RESET_ALL} "
            f"{Fore.MAGENTA + Style.BRIGHT}-{Style.RESET_ALL} {Fore.CYAN + Style.BRIGHT}Trạng thái:{Style.RESET_ALL}{color + Style.BRIGHT} {message} {Style.RESET_ALL}{Fore.CYAN + Style.BRIGHT}] {Style.RESET_ALL}"
        )

    async def process_user_login(self, address: str, proxy=None, retries=5):
        url = "https://naorisprotocol.network/sec-api/auth/generateToken"
        data = json.dumps({"wallet_address": address})
        headers = {**self.headers, "Content-Length": str(len(data)), "Content-Type": "application/json"}

        for attempt in range(retries):
            try:
                response = await asyncio.to_thread(requests.post, url, headers=headers, data=data, proxy=proxy, timeout=60, impersonate="safari15_5")
                if response.status_code == 401:
                    return self.print_message(address, proxy, Fore.RED, "Lỗi xác thực: Blocked by Cloudflare")
                response.raise_for_status()
                return response.json().get('token')
            except Exception as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                return self.print_message(address, proxy, Fore.RED, f"Lỗi lấy token: {e}")

    async def process_wallet_details(self, address: str, token: str, use_proxy: bool, proxy=None, retries=5):
        url = "https://naorisprotocol.network/testnet-api/api/testnet/walletDetails"
        data = json.dumps({"walletAddress": address})
        headers = {**self.headers, "Authorization": f"Bearer {token}", "Token": token, "Content-Length": str(len(data)), "Content-Type": "application/json"}

        for attempt in range(retries):
            try:
                response = await asyncio.to_thread(requests.post, url, headers=headers, data=data, proxy=proxy, timeout=60, impersonate="safari15_5")
                if response.status_code == 401:
                    token = await self.process_user_login(address, proxy)
                    headers["Authorization"] = f"Bearer {token}"
                    continue
                response.raise_for_status()
                return response.json().get('details')
            except Exception as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                return self.print_message(address, proxy, Fore.RED, f"Lỗi lấy thông tin ví: {e}")

    async def process_send_heartbeats(self, address: str, device_hash: int, token: str, use_proxy: bool, proxy=None, retries=5):
        url = "https://naorisprotocol.network/sec-api/api/produce-to-kafka"
        data = json.dumps({"topic": "device-heartbeat", "inputData": {"walletAddress": address, "deviceHash": device_hash}})
        headers = {**self.headers, "Authorization": f"Bearer {token}", "Content-Length": str(len(data)), "Content-Type": "application/json"}

        for attempt in range(retries):
            try:
                response = await asyncio.to_thread(requests.post, url, headers=headers, data=data, proxy=proxy, timeout=60, impersonate="safari15_5")
                if response.status_code == 401:
                    token = await self.process_user_login(address, proxy)
                    headers["Authorization"] = f"Bearer {token}"
                    continue
                response.raise_for_status()
                if response.json().get("message") == "Message production initiated":
                    self.print_message(address, proxy, Fore.GREEN, "PING thành công")
                return
            except Exception as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.print_message(address, proxy, Fore.RED, f"Lỗi PING: {e}")

    async def process_accounts(self, address: str, device_hash: int, use_proxy: bool):
        token = await self.process_user_login(address, self.get_next_proxy_for_account(address) if use_proxy else None)
        if token:
            tasks = [
                asyncio.create_task(self.process_wallet_details(address, token, use_proxy, self.get_next_proxy_for_account(address) if use_proxy else None)),
                asyncio.create_task(self.process_send_heartbeats(address, device_hash, token, use_proxy, self.get_next_proxy_for_account(address) if use_proxy else None))
            ]
            await asyncio.gather(*tasks)

    async def main(self):
        try:
            accounts = self.load_accounts()
            if not accounts:
                self.log(f"{Fore.RED}Không có tài khoản nào được tải.{Style.RESET_ALL}")
                return

            use_proxy_choice = self.print_question()

            use_proxy = use_proxy_choice in [1, 2]

            self.clear_terminal()
            self.welcome()
            self.log(f"{Fore.GREEN + Style.BRIGHT}Số lượng tài khoản: {Style.RESET_ALL}{len(accounts)}")

            if use_proxy:
                await self.load_proxies(use_proxy_choice)

            while True:
                tasks = [asyncio.create_task(self.process_accounts(account['walletAddress'], device_hash, use_proxy)) 
                         for account in accounts for device_hash in account['deviceHash']]
                await asyncio.gather(*tasks)
                await asyncio.sleep(10)

        except Exception as e:
            self.log(f"{Fore.RED + Style.BRIGHT}Lỗi: {e}{Style.RESET_ALL}")


if __name__ == "__main__":
    try:
        bot = NaorisProtocol()
        asyncio.run(bot.main())
    except KeyboardInterrupt:
        print(f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().astimezone(wib).strftime('%x %X %Z')} ]{Style.RESET_ALL} {Fore.WHITE + Style.BRIGHT}| {Style.RESET_ALL}{Fore.RED + Style.BRIGHT}[ EXIT ]{Style.RESET_ALL} Naoris Protocol Node - BOT")
