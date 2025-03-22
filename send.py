import asyncio
import json
import time
from web3 import Web3
from web3.middleware import geth_poa_middleware

# Konfigurasi jaringan
RPC_URL = "https://evmrpc-testnet.0g.ai"
CHAIN_ID = 16600
CURRENCY_SYMBOL = "AOGI"
EXPLORER_URL = "https://chainscan-newton.0g.ai"
SLOW_GAS_PRICE = Web3.to_wei(9.90, "gwei")  # 9.90 Gwei untuk transaksi lambat

# Maksimal transaksi berjalan
MAX_CONCURRENT_TASKS = 10
WAIT_FOR_CONFIRMATION = False

# Koneksi ke node blockchain
web3 = Web3(Web3.HTTPProvider(RPC_URL))
web3.middleware_onion.inject(geth_poa_middleware, layer=0)

def is_valid_address(address):
    """Periksa apakah alamat Ethereum valid."""
    return Web3.is_address(address)

async def send_aogi(private_key, destination_address, wallet_index):
    """Mengirim AOGI dari satu akun ke alamat tujuan."""
    try:
        account = web3.eth.account.from_key(private_key)
        from_address = account.address
        print(f"\n[Thread {wallet_index}] Memproses dompet {from_address}...")

        # Cek saldo akun
        balance = web3.eth.get_balance(from_address)
        balance_eth = Web3.from_wei(balance, "ether")
        print(f"[Thread {wallet_index}] Saldo: {balance_eth} {CURRENCY_SYMBOL}")

        if balance == 0:
            print(f"[Thread {wallet_index}] Saldo 0, melewati...")
            return {"success": False, "error": "Saldo nol", "from": from_address, "index": wallet_index}

        # Biaya gas
        gas_limit = 21000
        gas_cost = SLOW_GAS_PRICE * gas_limit

        # Periksa apakah saldo cukup untuk gas
        amount_to_send = balance - gas_cost
        if amount_to_send <= 0:
            print(f"[Thread {wallet_index}] Saldo tidak cukup untuk gas, melewati...")
            return {"success": False, "error": "Saldo tidak cukup untuk gas", "from": from_address, "index": wallet_index}

        # Membuat transaksi
        transaction = {
            "to": destination_address,
            "value": amount_to_send,
            "gas": gas_limit,
            "gasPrice": SLOW_GAS_PRICE,
            "nonce": web3.eth.get_transaction_count(from_address),
            "chainId": CHAIN_ID
        }

        # Tanda tangani dan kirim transaksi
        signed_tx = web3.eth.account.sign_transaction(transaction, private_key)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        print(f"[Thread {wallet_index}] Transaksi dikirim: {tx_hash.hex()}")
        print(f"[Thread {wallet_index}] Lihat di explorer: {EXPLORER_URL}/tx/{tx_hash.hex()}")

        # Tunggu konfirmasi jika diaktifkan
        if WAIT_FOR_CONFIRMATION:
            print(f"[Thread {wallet_index}] Menunggu konfirmasi...")
            receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
            print(f"[Thread {wallet_index}] Transaksi dikonfirmasi!")

        return {"success": True, "amount": amount_to_send, "from": from_address, "txHash": tx_hash.hex(), "index": wallet_index}

    except Exception as e:
        print(f"[Thread {wallet_index}] ERROR: {str(e)}")
        return {"success": False, "error": str(e), "from": "unknown", "index": wallet_index}

async def process_batch(private_keys, destination_address, start_index):
    """Memproses transaksi dalam batch."""
    batch = private_keys[start_index:start_index + MAX_CONCURRENT_TASKS]
    if not batch:
        return []

    print(f"\nMemproses batch {start_index + 1} - {start_index + len(batch)} dari {len(private_keys)} dompet...")

    tasks = [send_aogi(pk, destination_address, start_index + idx + 1) for idx, pk in enumerate(batch)]
    return await asyncio.gather(*tasks)

async def main():
    """Fungsi utama untuk memproses transaksi multi-threaded."""
    print(f"===== {CURRENCY_SYMBOL} Transfer Bot (Multi-threaded) =====")
    print(f"Network: OG-Newton-Testnet (Chain ID: {CHAIN_ID})")
    print(f"RPC: {RPC_URL}")
    print(f"Explorer: {EXPLORER_URL}")
    print(f"Gas Price: SLOW ({Web3.from_wei(SLOW_GAS_PRICE, 'gwei')} Gwei)")
    print(f"Wait for confirmation: {'Yes' if WAIT_FOR_CONFIRMATION else 'No'}")
    print("="*40 + "\n")

    # Meminta alamat tujuan
    destination_address = input(f"Masukkan alamat tujuan untuk menerima {CURRENCY_SYMBOL}: ").strip()
    if not is_valid_address(destination_address):
        print("Format alamat tidak valid! Harap masukkan alamat Ethereum yang benar.")
        return

    # Membaca file pk.txt
    print("\nMembaca file pk.txt...")
    try:
        with open("pk.txt", "r") as file:
            private_keys = [line.strip() for line in file.readlines() if line.strip()]
    except FileNotFoundError:
        print("File pk.txt tidak ditemukan!")
        return

    if not private_keys:
        print("Tidak ada private key dalam pk.txt!")
        return

    print(f"Ditemukan {len(private_keys)} private keys.")
    print(f"Memproses dengan maksimum {MAX_CONCURRENT_TASKS} transaksi sekaligus.")

    results = {
        "total": len(private_keys),
        "successful": 0,
        "failed": 0,
        "totalAmount": 0,
        "failedWallets": []
    }

    for i in range(0, len(private_keys), MAX_CONCURRENT_TASKS):
        batch_results = await process_batch(private_keys, destination_address, i)

        for result in batch_results:
            if result["success"]:
                results["successful"] += 1
                results["totalAmount"] += result["amount"]
            else:
                results["failed"] += 1
                results["failedWallets"].append({"line": result["index"], "address": result["from"], "error": result["error"]})

        if i + MAX_CONCURRENT_TASKS < len(private_keys):
            print("\nMenunggu 1 detik sebelum batch berikutnya...")
            time.sleep(1)

    # Ringkasan hasil
    print("\n========== RINGKASAN ==========")
    print(f"Total dompet diproses: {results['total']}")
    print(f"Transaksi berhasil: {results['successful']}")
    print(f"Transaksi gagal: {results['failed']}")
    print(f"Total {CURRENCY_SYMBOL} dikirim: {Web3.from_wei(results['totalAmount'], 'ether')}")

    if results["failed"] > 0:
        print("\nDompet gagal:")
        for wallet in results["failedWallets"]:
            print(f"- Baris {wallet['line']} ({wallet['address']}): {wallet['error']}")

    print("="*40)

if __name__ == "__main__":
    asyncio.run(main())
