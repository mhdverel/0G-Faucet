import requests
from twocaptcha import TwoCaptcha
from colorama import init, Fore, Style
from datetime import datetime
import pytz
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import tzlocal

init(autoreset=True)

# CONFIG THREADS AND 2CAPTCHA API KEY
THREADS = 30
TWO_CAPTCHA_API_KEY = "your-2captcha-api-key"

HCAPTCHA_SITEKEY = "914e63b4-ac20-4c24-bc92-cdb6950ccfde"
HCAPTCHA_PAGE_URL = "https://faucet.0g.ai"
WALLETS_FILE = "wallets.txt"
PROXIES_FILE = "proxies.txt"
FAUCET_API_URL = "https://faucet.0g.ai/api/faucet"
headers = {"Content-Type": "application/json"}

def now_local():
    tz = tzlocal.get_localzone()  # Get local timezone
    return datetime.now(tz).strftime("%H:%M:%S %d/%m/%Y")

def log_info(msg, idx=None):
    if idx is not None:
        print(f"{Fore.CYAN}[{now_local()}] [{idx}] {msg}{Style.RESET_ALL}")
    else:
        print(f"{Fore.CYAN}[{now_local()}] {msg}{Style.RESET_ALL}")

def log_success(msg, idx=None):
    if idx is not None:
        print(f"{Fore.GREEN}[{now_local()}] [{idx}] {msg}{Style.RESET_ALL}")
    else:
        print(f"{Fore.GREEN}[{now_local()}] {msg}{Style.RESET_ALL}")

def log_fail(msg, idx=None):
    if idx is not None:
        print(f"{Fore.RED}[{now_local()}] [{idx}] {msg}{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}[{now_local()}] {msg}{Style.RESET_ALL}")

with open(PROXIES_FILE, "r") as f:
    proxies_list = [line.strip() for line in f if line.strip()]

proxy_index = 0
PROXY_LOCK = threading.Lock()

def get_next_proxy():
    global proxy_index
    with PROXY_LOCK:
        if not proxies_list:
            return None
        p = proxies_list[proxy_index % len(proxies_list)]
        proxy_index += 1
        return p

def get_current_ip(proxy, idx=None):
    try:
        r = requests.get("https://api.myip.com", proxies={"http": proxy, "https": proxy}, timeout=30)
        if r.status_code == 200:
            return r.json().get("ip", "Unknown IP")
        return "Unknown IP"
    except Exception as e:
        log_fail(f"Error getting IP: {e}", idx=idx)
        return "Error"

def solve_hcaptcha(idx=None):
    try:
        r = TwoCaptcha(TWO_CAPTCHA_API_KEY).hcaptcha(sitekey=HCAPTCHA_SITEKEY, url=HCAPTCHA_PAGE_URL)
        if isinstance(r, dict) and "code" in r:
            log_success("hCaptcha Solved", idx=idx)
            return r["code"]
        log_info(f"Invalid 2Captcha response: {r}", idx=idx)
        return None
    except Exception as e:
        log_fail(f"hCaptcha solve error: {e}", idx=idx)
        return None

def faucet_claim(wallet, token, proxy, idx=None):
    try:
        resp = requests.post(
            FAUCET_API_URL,
            json={"address": wallet, "hcaptchaToken": token},
            headers=headers,
            proxies={"http": proxy, "https": proxy},
            timeout=300
        )
        return resp.json()
    except Exception as e:
        log_fail(f"Faucet API error for {wallet}: {e}", idx=idx)
        return None

def process_wallet(wallet, index, stop_event):
    log_info(f"Claiming address: {wallet}", idx=index)
    success_flag = False
    attempts = 0
    while not success_flag and attempts < len(proxies_list):
        if stop_event.is_set():
            log_info("Stop event detected. Exiting thread.", idx=index)
            return
        proxy = get_next_proxy()
        ip = get_current_ip(proxy, idx=index)
        log_info(f"Using proxy: {ip}", idx=index)

        log_info(f"Solving hCaptcha...")
        token = solve_hcaptcha(idx=index)
        if not token:
            log_fail("Captcha solve failed, switching to next proxy.", idx=index)
            attempts += 1
            continue

        resp = faucet_claim(wallet, token, proxy, idx=index)
        if resp:
            msg = resp.get("message", "")
            log_success(f"Faucet response: {resp}", idx=index)
            if msg == "Please wait 24 hours before requesting again":
                success_flag = True
            elif msg in ["Timeout. Please retry.", "Unable to Send Transaction", "Invalid Captcha"]:
                attempts += 1
            elif ("connection aborted" in msg.lower() or 
                  "closed connection" in msg.lower() or 
                  "httpsconnectionpool" in msg.lower()):
                attempts += 1
            else:
                success_flag = True
        else:
            log_fail("No valid faucet response, switching to next proxy.", idx=index)
            attempts += 1

    if not success_flag:
        log_fail(f"Claim for {wallet} failed after {attempts} proxy attempts.", idx=index)

def main(stop_event):
    log_info("Start reading wallets file and proceed to faucet...")
    log_info(f"Number of threads: {THREADS}")

    with open(WALLETS_FILE, "r") as f:
        wallets = [line.strip() for line in f if line.strip()]
    
    with ThreadPoolExecutor(max_workers=THREADS) as executor:
        futures = {executor.submit(process_wallet, wallet, i, stop_event): wallet 
                   for i, wallet in enumerate(wallets, start=1)}
        try:
            for future in as_completed(futures):
                future.result()
        except KeyboardInterrupt:
            log_info("KeyboardInterrupt detected in main loop. Setting stop event...")
            stop_event.set()
            for future in futures:
                future.cancel()
            raise

if __name__ == "__main__":
    stop_event = threading.Event()
    try:
        main(stop_event)
    except KeyboardInterrupt:
        log_info("User has stopped the program. Exiting...")
