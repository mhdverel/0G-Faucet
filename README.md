# 🚀 0G Faucet Script

## 🌟 Overview

0G Faucet Script is a Python-based tool designed to automate the claiming of A0GI tokens from the 0g.ai testnet faucet. This script supports multi-wallet claims, automatic captcha solving, multi-threading execution, proxy rotation, and balance checking via RPC.

## 🔥 Features

✅ Claim A0GI, BTC, ETH, USDT for multiple wallets 🎭  
✅ Automatic hCaptcha solving using 2Captcha 🔐  
✅ Multi-thread execution with adjustable thread count ⚡  
✅ Proxy rotation support 🛡️  
✅ Balance checking via RPC 📊  
✅ Export wallets with/without balance to a file 📁  
✅ Community support via Telegram 💬  

---

## 🛠️ Installation

### 1️⃣ Prerequisites
Ensure you have **Python 3.8+** and `pip` installed.

### 2️⃣ Clone Repository
```bash
git clone https://github.com/mhdverel/0G-Faucet.git
cd 0G-Faucet
```

### 3️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```

---

## ⚙️ Configuration

### 🔑 Wallets
Add your private keys to `priv.txt` (one key per line).

### 🛡️ Proxy (Optional)
Add proxies to `proxies.txt` in the format: `user:pass@ip:port` (one per line).

### 🔍 2Captcha API
Add your 2Captcha API key in `faucet.py` line 14.
TWO_CAPTCHA_API_KEY = "your-2captcha-api-key"

---

## 🚀 Usage

### 💰 Claim Tokens
To claim **A0GI tokens**, run:
```bash
python faucet.py
```
To claim **A0GI, BTC, ETH, USDT**, run:
```bash
python faucet-3-tokens.py
```

### 📊 Check Wallet Balance
To check the **A0GI balance** of your wallets, run:
```bash
python check-balance.py
```

### 📤 Send Tokens
To send tokens, add sender private keys to `priv_send.txt` and run:
```bash
python send.py
```

---

## ⚠️ Important Notes

⚠️ **Do not share your private keys.**  
⚠️ **Use proxies to avoid IP bans when claiming in bulk.**  
⚠️ **For support, join our Telegram community.** 📢  

Enjoy automated claiming with **0G Faucet Script!** 🎉

