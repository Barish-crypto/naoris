from curl_cffi import requests
from fake_useragent import FakeUserAgent
from datetime import datetime
import asyncio
import json
import os
import pytz
from typing import Optional, List, Dict, Any
from pyfiglet import Figlet
import shutil
from dataclasses import dataclass
import logging
from logging.handlers import RotatingFileHandler

# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        RotatingFileHandler('naoris_bot.log', maxBytes=5_000_000, backupCount=5),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

wib = pytz.timezone('Asia/Jakarta')

@dataclass
class Config:
    BASE_API: str = "https://naorisprotocol.network"
    PING_API: str = "https://beat.naorisprotocol.network"
    TIMEOUT: int = 60
    RETRIES: int = 5
    REFRESH_INTERVAL: int = 30 * 60  # 30 minutes
    WALLET_CHECK_INTERVAL: int = 15 * 60  # 15 minutes
    PING_INTERVAL: int = 10  # 10 seconds
    MSG_PROD_INTERVAL: int = 10 * 60  # 10 minutes

class NaorisProtocol:
    def __init__(self) -> None:
        self.config = Config()
        self.headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
            "Origin": "chrome-extension://cpikalnagknmlfhnilhfelifgbollmmp",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-Storage-Access": "active",
            "User-Agent": FakeUserAgent().random
        }
        self.proxies: List[str] = []
        self.proxy_index: int = 0
        self.account_proxies: Dict[str, str] = {}
        self.access_tokens: Dict[str, str] = {}
        self.refresh_tokens: Dict[str, str] = {}

    def clear_terminal(self) -> None:
        """Clear the terminal screen based on the operating system."""
        os.system('cls' if os.name == 'nt' else 'clear')

    def welcome(self) -> None:
        """Display a welcome banner."""
        figlet = Figlet(font='slant')
        banner = figlet.renderText("Naoris Bot")
        terminal_width = shutil.get_terminal_size().columns
        centered_banner = "\n".join(line.center(terminal_width) for line in banner.splitlines())
        print(centered_banner)
        print("Auto Ping Naoris by Bg WIN".center(terminal_width))

    def format_seconds(self, seconds: int) -> str:
        """Format seconds into HH:MM:SS format."""
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"

    def load_accounts(self) -> List[Dict[str, Any]]:
        """Load accounts from accounts.json file."""
        filename = "accounts.json"
        try:
            if not os.path.exists(filename):
                logger.error(f"File {filename} not found.")
                return []
            with open(filename, 'r') as file:
                data = json.load(file)
                return data if isinstance(data, list) else []
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse {filename}: {e}")
            return []

    async def load_proxies(self, use_proxy_choice: int) -> None:
        """Load proxies based on user choice (Monosans or private)."""
        filename = "proxy.txt"
        try:
            if use_proxy_choice == 1:
                response = await asyncio.to_thread(
                    requests.get,
                    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/all.txt",
                    timeout=self.config.TIMEOUT
                )
                response.raise_for_status()
                self.proxies = response.text.splitlines()
                with open(filename, 'w') as f:
                    f.write(response.text)
            else:
                if not os.path.exists(filename):
                    logger.error(f"File {filename} not found.")
                    return
                with open(filename, 'r') as f:
                    self.proxies = f.read().splitlines()

            if not self.proxies:
                logger.error("No proxies found.")
                return

            logger.info(f"Loaded {len(self.proxies)} proxies.")
        except Exception as e:
            logger.error(f"Failed to load proxies: {e}")
            self.proxies = []

    def normalize_proxy(self, proxy: str) -> str:
        """Ensure proxy has a valid scheme."""
        schemes = ["http://", "https://", "socks4://", "socks5://"]
        return proxy if any(proxy.startswith(scheme) for scheme in schemes) else f"http://{proxy}"

    def get_proxy(self, account: str) -> Optional[str]:
        """Get the next proxy for an account."""
        if not self.proxies:
            return None
        if account not in self.account_proxies:
            proxy = self.normalize_proxy(self.proxies[self.proxy_index])
            self.account_proxies[account] = proxy
            self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return self.account_proxies[account]

    def rotate_proxy(self, account: str) -> Optional[str]:
        """Rotate to the next proxy for an account."""
        if not self.proxies:
            return None
        proxy = self.normalize_proxy(self.proxies[self.proxy_index])
        self.account_proxies[account] = proxy
        self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return proxy

    def mask_account(self, account: str) -> str:
        """Mask account address for display."""
        return account[:6] + '*' * 6 + account[-6:]

    def print_question(self) -> int:
        """Prompt user to select proxy option."""
        while True:
            try:
                print("1. Run With Monosans Proxy")
                print("2. Run With Private Proxy")
                print("3. Run Without Proxy")
                choice = int(input("Choose [1/2/3] -> ").strip())
                if choice in [1, 2, 3]:
                    logger.info(f"Selected proxy option: {choice}")
                    return choice
                logger.warning("Invalid choice. Please enter 1, 2, or 3.")
            except ValueError:
                logger.warning("Invalid input. Enter a number (1, 2, or 3).")

    async def api_request(self, method: str, url: str, headers: Dict[str, str], data: Optional[Any] = None,
                         proxy: Optional[str] = None, retries: int = 5) -> Optional[Dict[str, Any]]:
        """Generic method for making API requests."""
        for attempt in range(retries):
            try:
                kwargs = {
                    'url': url,
                    'headers': headers,
                    'timeout': self.config.TIMEOUT,
                    'impersonate': 'chrome120'  # Updated to a more recent Chrome version
                }
                if data:
                    kwargs['json'] = data if isinstance(data, dict) else json.loads(data)
                if proxy:
                    kwargs['proxy'] = proxy

                response = await asyncio.to_thread(getattr(requests, method.lower()), **kwargs)
                response.raise_for_status()
                return response.json() if response.content else {'message': response.text}
            except Exception as e:
                if attempt < retries - 1:
                    logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}. Retrying...")
                    await asyncio.sleep(5)
                    continue
                logger.error(f"Request to {url} failed after {retries} attempts: {e}")
                return None

    async def generate_token(self, address: str, proxy: Optional[str] = None) -> Optional[Dict[str, str]]:
        """Generate authentication token for an account."""
        url = f"{self.config.BASE_API}/sec-api/auth/gt-event"
        data = {"wallet_address": address}
        headers = {
            **self.headers,
            "Content-Type": "application/json"
        }
        response = await self.api_request('post', url, headers, data, proxy)
        if response:
            if isinstance(response, dict) and "token" in response:
                logger.info(f"Generated token for {self.mask_account(address)}")
                return response
            logger.error(f"Token generation failed for {self.mask_account(address)}: Invalid response")
        return None

    async def refresh_token(self, address: str, proxy: Optional[str] = None) -> Optional[Dict[str, str]]:
        """Refresh authentication token."""
        url = f"{self.config.BASE_API}/sec-api/auth/refresh"
        data = {"refreshToken": self.refresh_tokens.get(address, '')}
        headers = {
            **self.headers,
            "Content-Type": "application/json"
        }
        response = await self.api_request('post', url, headers, data, proxy)
        if response:
            if isinstance(response, dict) and "token" in response:
                logger.info(f"Refreshed token for {self.mask_account(address)}")
                return response
            logger.error(f"Token refresh failed for {self.mask_account(address)}: Invalid response")
        return None

    async def wallet_details(self, address: str, proxy: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Fetch wallet details."""
        url = f"{self.config.BASE_API}/sec-api/api/wallet-details"
        headers = {
            **self.headers,
            "Authorization": f"Bearer {self.access_tokens.get(address, '')}"
        }
        response = await self.api_request('get', url, headers, proxy=proxy)
        if response:
            logger.info(f"Fetched wallet details for {self.mask_account(address)}")
        return response

    async def add_whitelist(self, address: str, proxy: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Add URL to whitelist."""
        url = f"{self.config.BASE_API}/sec-api/api/addWhitelist"
        data = {"walletAddress": address, "url": "naorisprotocol.network"}
        headers = {
            **self.headers,
            "Authorization": f"Bearer {self.access_tokens.get(address, '')}",
            "Content-Type": "application/json"
        }
        response = await self.api_request('post', url, headers, data, proxy)
        if response and response.get("message") == "url saved successfully":
            logger.info(f"Added to whitelist for {self.mask_account(address)}")
        return response

    async def toggle_activation(self, address: str, device_hash: int, state: str, proxy: Optional[str] = None) -> Optional[str]:
        """Toggle device activation state."""
        url = f"{self.config.BASE_API}/sec-api/api/switch"
        data = {"walletAddress": address, "state": state, "deviceHash": device_hash}
        headers = {
            **self.headers,
            "Authorization": f"Bearer {self.access_tokens.get(address, '')}",
            "Content-Type": "application/json"
        }
        response = await self.api_request('post', url, headers, data, proxy)
        if response and isinstance(response, dict) and "message" in response:
            logger.info(f"Toggled {state} for {self.mask_account(address)}: {response['message']}")
            return response['message']
        return None

    async def initiate_msg_product(self, address: str, device_hash: int, proxy: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Initiate message production."""
        url = f"{self.config.PING_API}/sec-api/api/htb-event"
        data = {"inputData": {"walletAddress": address, "deviceHash": device_hash}}
        headers = {
            **self.headers,
            "Authorization": f"Bearer {self.access_tokens.get(address, '')}",
            "Content-Type": "application/json"
        }
        response = await self.api_request('post', url, headers, data, proxy)
        if response and response.get("message") == "Message production initiated":
            logger.info(f"Initiated message production for {self.mask_account(address)}")
        return response

    async def perform_ping(self, address: str, proxy: Optional[str] = None) -> Optional[str]:
        """Perform a ping operation."""
        url = f"{self.config.PING_API}/api/ping"
        headers = {
            **self.headers,
            "Authorization": f"Bearer {self.access_tokens.get(address, '')}",
            "Content-Type": "application/json"
        }
        response = await self.api_request('post', url, headers, data={}, proxy=proxy)
        if response and isinstance(response, dict) and response.get("message") == "Ping Success!!":
            logger.info(f"Ping successful for {self.mask_account(address)}")
            return response['message']
        return None

    async def process_generate_token(self, address: str, use_proxy: bool) -> bool:
        """Process token generation with retries."""
        proxy = self.get_proxy(address) if use_proxy else None
        while True:
            token_data = await self.generate_token(address, proxy)
            if token_data and "token" in token_data and "refreshToken" in token_data:
                self.access_tokens[address] = token_data["token"]
                self.refresh_tokens[address] = token_data["refreshToken"]
                logger.info(f"Token generation successful for {self.mask_account(address)}")
                return True
            logger.warning(f"Retrying token generation for {self.mask_account(address)}")
            proxy = self.rotate_proxy(address) if use_proxy else None
            await asyncio.sleep(5)

    async def process_refresh_token(self, address: str, use_proxy: bool) -> None:
        """Periodically refresh token."""
        while True:
            await asyncio.sleep(self.config.REFRESH_INTERVAL)
            proxy = self.get_proxy(address) if use_proxy else None
            token_data = await self.refresh_token(address, proxy)
            if token_data and "token" in token_data and "refreshToken" in token_data:
                self.access_tokens[address] = token_data["token"]
                self.refresh_tokens[address] = token_data["refreshToken"]
            else:
                logger.error(f"Failed to refresh token for {self.mask_account(address)}")
                proxy = self.rotate_proxy(address) if use_proxy else None
                await asyncio.sleep(5)

    async def process_get_wallet_details(self, address: str, use_proxy: bool) -> None:
        """Periodically fetch wallet details."""
        await self.add_whitelist(address, self.get_proxy(address) if use_proxy else None)
        while True:
            proxy = self.get_proxy(address) if use_proxy else None
            wallet = await self.wallet_details(address, proxy)
            total_earning = wallet.get("message", {}).get("totalEarnings", "N/A") if wallet else "N/A"
            logger.info(f"Earning total for {self.mask_account(address)}: {total_earning} PTS")
            await asyncio.sleep(self.config.WALLET_CHECK_INTERVAL)

    async def process_send_ping(self, address: str, use_proxy: bool) -> None:
        """Periodically send ping."""
        while True:
            proxy = self.get_proxy(address) if use_proxy else None
            if await self.perform_ping(address, proxy):
                logger.info(f"Ping sent for {self.mask_account(address)}")
            await asyncio.sleep(self.config.PING_INTERVAL)

    async def process_initiate_msg_product(self, address: str, device_hash: int, use_proxy: bool) -> None:
        """Periodically initiate message production."""
        while True:
            proxy = self.get_proxy(address) if use_proxy else None
            if await self.initiate_msg_product(address, device_hash, proxy):
                logger.info(f"Message production initiated for {self.mask_account(address)}")
            await asyncio.sleep(self.config.MSG_PROD_INTERVAL)

    async def process_activate_toggle(self, address: str, device_hash: int, use_proxy: bool) -> None:
        """Manage device activation and related tasks."""
        while True:
            proxy = self.get_proxy(address) if use_proxy else None
            deactivate = await self.toggle_activation(address, device_hash, "OFF", proxy)
            if deactivate in ["Session ended and daily usage updated", "No action needed"]:
                activate = await self.toggle_activation(address, device_hash, "ON", proxy)
                if activate == "Session started":
                    tasks = [
                        asyncio.create_task(self.process_initiate_msg_product(address, device_hash, use_proxy)),
                        asyncio.create_task(self.process_send_ping(address, use_proxy))
                    ]
                    await asyncio.gather(*tasks)
            await asyncio.sleep(60)  # Avoid tight loops

    async def process_accounts(self, address: str, device_hash: int, use_proxy: bool) -> None:
        """Process tasks for a single account."""
        if await self.process_generate_token(address, use_proxy):
            tasks = [
                asyncio.create_task(self.process_refresh_token(address, use_proxy)),
                asyncio.create_task(self.process_get_wallet_details(address, use_proxy)),
                asyncio.create_task(self.process_activate_toggle(address, device_hash, use_proxy))
            ]
            await asyncio.gather(*tasks)

    async def main(self) -> None:
        """Main entry point for the bot."""
        try:
            accounts = self.load_accounts()
            if not accounts:
                logger.error("No accounts loaded. Exiting.")
                return

            use_proxy_choice = self.print_question()
            use_proxy = use_proxy_choice in [1, 2]

            self.clear_terminal()
            self.welcome()
            logger.info(f"Total accounts: {len(accounts)}")

            if use_proxy:
                await self.load_proxies(use_proxy_choice)

            tasks = []
            for account in accounts:
                address = account.get("Address", "").lower()
                device_hash = int(account.get("deviceHash", 0))
                if address and device_hash:
                    tasks.append(asyncio.create_task(self.process_accounts(address, device_hash, use_proxy)))

            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Main process error: {e}")
            raise

if __name__ == "__main__":
    try:
        bot = NaorisProtocol()
        asyncio.run(bot.main())
    except KeyboardInterrupt:
        logger.info("Naoris Protocol Node - BOT terminated by user.")