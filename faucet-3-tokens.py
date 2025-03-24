import requests
from colorama import init, Fore, Style
from datetime import datetime
import pytz
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- Web3 và các hàm hỗ trợ ---
from web3 import Web3, HTTPProvider
from eth_account import Account
from eth_utils import to_checksum_address

init(autoreset=True)

# ==================== CONFIG =====================
THREADS = 50

PRIV_FILE = "privatekey.txt"
PROXIES_FILE = "proxies.txt"

NODE_URL = "https://evmrpc-testnet.0g.ai"  # RPC của bạn
CHAIN_ID = 16600                           # chainId testnet

# ----- Tạo hàm khởi tạo Web3 kèm proxy -----
def create_web3_with_proxy(node_url: str, proxy: str) -> Web3:
    session = requests.Session()
    session.proxies = {
        "http": proxy,
        "https": proxy
    }
    provider = HTTPProvider(node_url, session=session)
    return Web3(provider)

# ----- USDT: contract & methodID -----
USDT_CONTRACT = to_checksum_address("0x9A87C2412d500343c073E5Ae5394E3bE3874F76b")
USDT_METHOD_DATA = "0x1249c58b"
USDT_MAX_RETRIES = 5

# ----- ETH faucet: contract & methodID -----
ETH_CONTRACT = to_checksum_address("0xce830D0905e0f7A9b300401729761579c5FB6bd6")
ETH_METHOD_DATA = "0x1249c58b"
ETH_MAX_RETRIES = 5

# ----- BTC faucet: contract & methodID -----
BTC_CONTRACT = to_checksum_address("0x1E0D871472973c562650E991ED8006549F8CBEfc")
BTC_METHOD_DATA = "0x1249c58b"
BTC_MAX_RETRIES = 5

# ==================== LOG FUNCTIONS ====================
def now_vn():
    tz = pytz.timezone("Asia/Ho_Chi_Minh")
    return datetime.now(tz).strftime("%H:%M:%S %d/%m/%Y")

def log_info(msg, idx=None):
    if idx is not None:
        print(f"{Fore.CYAN}[{now_vn()}] [{idx}] {msg}{Style.RESET_ALL}")
    else:
        print(f"{Fore.CYAN}[{now_vn()}] {msg}{Style.RESET_ALL}")

def log_success(msg, idx=None):
    if idx is not None:
        print(f"{Fore.GREEN}[{now_vn()}] [{idx}] {msg}{Style.RESET_ALL}")
    else:
        print(f"{Fore.GREEN}[{now_vn()}] {msg}{Style.RESET_ALL}")

def log_fail(msg, idx=None):
    if idx is not None:
        print(f"{Fore.RED}[{now_vn()}] [{idx}] {msg}{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}[{now_vn()}] {msg}{Style.RESET_ALL}")

# ==================== PROXIES LOGIC ====================
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
    """Dùng proxy call API myip.com để lấy IP hiển thị (nếu cần)."""
    try:
        r = requests.get("https://api.myip.com", proxies={"http": proxy, "https": proxy}, timeout=30)
        if r.status_code == 200:
            return r.json().get("ip", "Unknown IP")
        return "Unknown IP"
    except Exception as e:
        log_fail(f"Error getting IP: {e}", idx=idx)
        return "Error"

# ==================== HÀM CHUNG MINT TOKEN ON-CHAIN ====================
def mint_token(w3_local, private_key, contract_addr, method_data, token_name="UNKNOWN", idx=None):
    """
    Dùng chung để mint token on-chain qua w3_local (đã gắn proxy).
    Trả về True nếu success, False nếu fail.
    """
    try:
        sender_account = w3_local.eth.account.from_key(private_key)
        sender_address = w3_local.to_checksum_address(sender_account.address)

        tx_for_estimate = {
            "from": sender_address,
            "to": contract_addr,
            "data": method_data,
            "value": 0
        }

        gas_estimate = w3_local.eth.estimate_gas(tx_for_estimate)
        gas_limit = int(gas_estimate * 1.5)
        estimated_gas_price = w3_local.eth.gas_price
        adjusted_gas_price = int(estimated_gas_price * 1.5)

        nonce = w3_local.eth.get_transaction_count(sender_address)
        tx = {
            "chainId": CHAIN_ID,
            "nonce": nonce,
            "to": contract_addr,
            "data": method_data,
            "gas": gas_limit,
            "gasPrice": adjusted_gas_price,
            "value": 0
        }

        signed_tx = sender_account.sign_transaction(tx)
        tx_hash = w3_local.eth.send_raw_transaction(signed_tx.rawTransaction)
        receipt = w3_local.eth.wait_for_transaction_receipt(tx_hash)

        if receipt.status == 1:
            log_success(f"{token_name} Mint OK (contract {contract_addr}), txHash: {tx_hash.hex()}", idx=idx)
            return True
        else:
            log_fail(f"{token_name} Mint FAILED (contract {contract_addr}), txHash: {tx_hash.hex()}", idx=idx)
            return False

    except Exception as e:
        log_fail(f"{token_name} Mint error (contract {contract_addr}): {e}", idx=idx)
        return False

def faucet_usdt(w3_local, private_key, idx=None):
    return mint_token(w3_local, private_key, USDT_CONTRACT, USDT_METHOD_DATA, token_name="USDT", idx=idx)

def faucet_eth(w3_local, private_key, idx=None):
    return mint_token(w3_local, private_key, ETH_CONTRACT, ETH_METHOD_DATA, token_name="ETH", idx=idx)

def faucet_btc(w3_local, private_key, idx=None):
    return mint_token(w3_local, private_key, BTC_CONTRACT, BTC_METHOD_DATA, token_name="BTC", idx=idx)

# ==================== HÀM LẤY ĐỊA CHỈ TỪ PRIVATE KEY ====================
def get_address_from_privatekey(pk: str) -> str:
    """
    Lấy địa chỉ ví offline, không cần gọi RPC.
    """
    return Account.from_key(pk).address

# ==================== XỬ LÝ MỖI PRIVATE KEY (THREAD) ====================
def process_account(private_key, index, stop_event):
    """
    Thứ tự: USDT -> ETH -> BTC (mỗi cái có retry riêng).
    Nếu USDT fail vẫn sang ETH, ETH fail vẫn sang BTC, v.v.
    Cuối cùng log kết quả.
    """
    address = get_address_from_privatekey(private_key)
    log_info(f"Faucet for address: {address}", idx=index)

    # ----- 1) USDT Faucet -----
    usdt_success = False
    usdt_attempts = 0
    while not usdt_success and usdt_attempts < USDT_MAX_RETRIES:
        if stop_event.is_set():
            log_info("Stop event detected. Exiting thread (USDT).", idx=index)
            return
        proxy = get_next_proxy()
        ip = get_current_ip(proxy, idx=index)
        log_info(f"[USDT] Attempt {usdt_attempts+1}, Using proxy: {ip}", idx=index)

        # Khởi tạo Web3 kèm proxy
        w3_local = create_web3_with_proxy(NODE_URL, proxy)

        if faucet_usdt(w3_local, private_key, idx=index):
            usdt_success = True
        else:
            usdt_attempts += 1

    # ----- 2) ETH Faucet -----
    eth_success = False
    eth_attempts = 0
    while not eth_success and eth_attempts < ETH_MAX_RETRIES:
        if stop_event.is_set():
            log_info("Stop event detected. Exiting thread (ETH).", idx=index)
            return
        proxy = get_next_proxy()
        ip = get_current_ip(proxy, idx=index)
        log_info(f"[ETH] Attempt {eth_attempts+1}, Using proxy: {ip}", idx=index)

        # Khởi tạo Web3 kèm proxy
        w3_local = create_web3_with_proxy(NODE_URL, proxy)

        if faucet_eth(w3_local, private_key, idx=index):
            eth_success = True
        else:
            eth_attempts += 1

    # ----- 3) BTC Faucet -----
    btc_success = False
    btc_attempts = 0
    while not btc_success and btc_attempts < BTC_MAX_RETRIES:
        if stop_event.is_set():
            log_info("Stop event detected. Exiting thread (BTC).", idx=index)
            return
        proxy = get_next_proxy()
        ip = get_current_ip(proxy, idx=index)
        log_info(f"[BTC] Attempt {btc_attempts+1}, Using proxy: {ip}", idx=index)

        # Khởi tạo Web3 kèm proxy
        w3_local = create_web3_with_proxy(NODE_URL, proxy)

        if faucet_btc(w3_local, private_key, idx=index):
            btc_success = True
        else:
            btc_attempts += 1

    # TỔNG KẾT TỪNG PHẦN
    if usdt_success:
        log_success(f"USDT: success after {usdt_attempts+1} tries", idx=index)
    else:
        log_fail(f"USDT: fail after {usdt_attempts} retries", idx=index)

    if eth_success:
        log_success(f"ETH: success after {eth_attempts+1} tries", idx=index)
    else:
        log_fail(f"ETH: fail after {eth_attempts} retries", idx=index)

    if btc_success:
        log_success(f"BTC: success after {btc_attempts+1} tries", idx=index)
    else:
        log_fail(f"BTC: fail after {btc_attempts} retries", idx=index)

    log_info(f"[DONE] Address: {address} => USDT={usdt_success}, ETH={eth_success}, BTC={btc_success}", idx=index)

# ==================== MAIN FUNCTION ====================
def main(stop_event):
    log_info("Start reading privatekey.txt and proceed to on-chain faucets: USDT, ETH, BTC...", idx=0)
    log_info(f"Number of threads: {THREADS}", idx=0)

    # Đọc private keys từ file
    with open(PRIV_FILE, "r") as f:
        private_keys = [line.strip() for line in f if line.strip()]

    with ThreadPoolExecutor(max_workers=THREADS) as executor:
        futures = {
            executor.submit(process_account, pk, i, stop_event): pk
            for i, pk in enumerate(private_keys, start=1)
        }
        try:
            for future in as_completed(futures):
                future.result()
        except KeyboardInterrupt:
            log_info("KeyboardInterrupt detected in main loop. Setting stop event...", idx=0)
            stop_event.set()
            for future in futures:
                future.cancel()
            raise

# ==================== ENTRY POINT ====================
if __name__ == "__main__":
    stop_event = threading.Event()
    try:
        main(stop_event)
    except KeyboardInterrupt:
        log_info("User has stopped the program. Exiting...", idx=0)
