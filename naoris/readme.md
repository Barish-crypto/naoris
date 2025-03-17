# Naoris Bot Auto Ping/ Ref

Tool được phát triển bởi nhóm tele Airdrop Hunter Siêu Tốc (https://t.me/airdrophuntersieutoc)

## Features

- Automatically ping
- Auto reff
- Multi Accounts
- Multi nodes support.
- Uses proxies to avoid IP bans.
- Logs Accounts
- Can see point each accounts

## Requirements

- Node.js v18.20.5 LTS or latest.

## Notes

- Make sure to use valid proxies to avoid IP bans.
- If you just running new account you need rerun bot again (maybe next update i will update it to handle this condition)
- If you didn't get point just wait.

## Installation

1. Clone the repository:

   ```sh
   git clone https://github.com/Hunga9k50doker/naoris.git
   cd naoris
   ```

2. Install the dependencies:

   ```sh
   npm install
   ```

3. Create proxy (optional) `nano proxy.txt` file in the root directory and add your proxies (one per line).
   Format Proxy

   ```
   http://user:pw@host:port
   http://user:pw@host:port
   http://user:pw@host:port
   ```

4. Follow the prompts to enter your referral code

## Output

- The created accounts will be saved in `accounts.txt` and `accounts.json`.

5. Create accounts.json `nano accounts.json` in the root directory and add your account format. (if you using my bot reff just copy paste accounts.json to this root directory)

   ```json
   [
     {
       "walletAddress": "your wallet1",
       "deviceHash": [13131131, 13213132, 13131313] // make in array to using multi devices
     },
     {
       "walletAddress": "your wallet1",
       "deviceHash": [13131131, 13213132, 13131313] // make in array to using multi devices
     },
     {
       "walletAddress": "your wallet1",
       "deviceHash": [13131131, 13213132, 13131313] // make in array to using multi devices
     }
   ]
   ```

## Usage

1. Run the bot:

   ```sh
   node .
   ```

2. and you done.

## Stay Connected

- Channel Telegram : [Telegram](https://t.me/airdrophuntersieutoc)
