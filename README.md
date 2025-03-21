
# 🚰 0G Faucet Script

Welcome to the **0G Faucet Script** – a Python-based tool that automates A0GI token claims on the [0g.ai](https://faucet.0g.ai) testnet faucet.

> 🔧 Supports multi-threaded requests with captcha solving and proxy usage.

---

## 📦 Features

- ✅ Claim A0GI, BTC, ETH, USDT tokens for multiple wallets  
- 🔁 Automatic hCaptcha solving using [2Captcha](https://2captcha.com)  
- 🧵 Multi-threaded execution with adjustable thread count  
- 🛡️ Proxy rotation support  
- 📊 Check A0GI balance for wallets via RPC  
- 📁 Outputs wallets with/without balance to files  
- 💬 Community support via Telegram  

---

## 🛠️ Installation Guide

### ✅ Prerequisites

Ensure you have **Python 3.8+** and **pip** installed.

---

### 🐧 For Linux/macOS

- Clone the repo
```bash
git clone https://github.com/rpchubs/0G-Faucet.git
cd 0G-Faucet
```

- Install required libraries
```bash
pip install -r requirements.txt
```

---

### 🪟 For Windows

- Clone the repo
```powershell
git clone https://github.com/rpchubs/0G-Faucet.git
cd 0G-Faucet
```

- Install required libraries
```powershell
pip install -r requirements.txt
```

---

## ⚙️ Configuration

Open the `faucet.py` script and scroll to **line 13–14**:

```python
THREADS = 30
TWO_CAPTCHA_API_KEY = "your-2captcha-api-key"
```

🔁 Replace:
- `THREADS` with the number of parallel threads you want to run (e.g., 20–50 recommended).
- `TWO_CAPTCHA_API_KEY` with your valid API key from [2Captcha](https://2captcha.com).

---

## 🧾 Required Files

Ensure the following files exist in the script directory:

- `wallets.txt` – 📜 List of wallet addresses (one per line)
- `proxies.txt` – 🌍 List of HTTP proxies (one per line) format ```http://user:password@ip:port```

---

## 🚀 Running the Faucet Script

After setup:

```bash
python faucet.py
```

✅ The script will:
- Solve captchas using 2Captcha  
- Use proxies in rotation  
- Claim A0GI for each wallet  
- Log progress in terminal  

---
## 💸 Faucet Multiple Tokens ($BTC, $ETH, $USDT)

> 🔑 Want to claim more than just A0GI? You can now faucet $BTC, $ETH, and $USDT with a single script!

### ⚙️ Setup Instructions

1. 📥 **Import Private Keys**
   - Add each private key (one per line) into the `priv.txt` file.
   - Example:
     ```
     0xabc123...
     0xdef456...
     ```

2. 🌍 **Ensure You Have A0GI as Gas**
   - Each wallet used for faucet must already have **A0GI tokens** to pay for gas fees on the 0G Testnet.

3. 🚀 **Run the Script**
   ```bash
   python faucet-3-tokens.py
   ```

✅ The script will automatically:
- Connect via proxy (defined in `proxies.txt`)
- Mint $USDT → $ETH → $BTC (with retries)
- Log success/failure per token per wallet

📁 Output will be displayed in the terminal with timestamps and colorized logs.

---

🔄 **Threaded Execution**

- Supports concurrent minting using Python’s `concurrent.futures.ThreadPoolExecutor`
- Adjust number of threads directly in `faucet-3-tokens.py` (default is 50):
  ```python
  THREADS = 50
  ```

---

🎯 **Pro Tip**

- 🔁 Use fresh proxies to avoid rate limits
- 🧪 Test on a few wallets before scaling up
- ⛽ Top up A0GI if transactions are failing due to insufficient gas

---

## 💰 Check A0GI Balances

Use `check-balance.py` to verify wallet balances:

```bash
python check-balance.py
```

📤 Outputs:
- `has_balance.txt` – Wallets that received A0GI
- `no_balance.txt` – Wallets with 0 balance

---

## 🙋 Support & Community

Having issues or want to discuss?

Join our Telegram channels:

- 🛠️ [RPC Hubs Channel](https://t.me/RPC_Hubs)  
- 💬 [RPC Community Chat](https://t.me/chat_RPC_Community)  

---

## 📌 Notes

- ✅ Recommended: Use fresh proxies and rotate often  
- 🕒 Faucet has a 24h cooldown per wallet  
- 📶 Make sure your 2Captcha balance is sufficient  

---

Made with ❤️ by the RPC Hubs Team
