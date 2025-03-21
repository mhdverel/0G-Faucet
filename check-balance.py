from web3 import Web3

RPC_URL = "https://og-testnet-evm.itrocket.net"
web3 = Web3(Web3.HTTPProvider(RPC_URL))

if not web3.is_connected():
    print("❌ Unable to connect to RPC.")
    exit(1)

wallet_file = "wallets.txt"
try:
    with open(wallet_file, "r") as file:
        wallets = [line.strip() for line in file if line.strip()]
except FileNotFoundError:
    print("❌ wallets.txt file not found.")
    exit(1)

if not wallets:
    print("❌ The wallets.txt file does not contain valid wallet addresses.")
    exit(1)

print("🔹 Checking A0GI balance...")

total_balance = 0.0
has_balance = []
no_balance = []

for idx, wallet in enumerate(wallets, start=1):
    try:
        checksum_wallet = web3.to_checksum_address(wallet)
        balance_wei = web3.eth.get_balance(checksum_wallet)
        balance_eth_decimal = web3.from_wei(balance_wei, "ether") 
        balance_eth = float(balance_eth_decimal)  
        
        total_balance += balance_eth
        
        if balance_eth > 0:
            has_balance.append(wallet)
        else:
            no_balance.append(wallet)
        
        print(f"{idx}. 🟢 Wallet: {wallet} | Balance: {balance_eth:.6f} A0GI")
    except Exception as e:
        print(f"{idx}. ❌ Error checking {wallet}: {str(e)}")

print(f"\n🔹 Total A0GI balance across wallets: {total_balance:.6f} A0GI")

with open("has_balance.txt", "w") as f:
    for wallet in has_balance:
        f.write(wallet + "\n")

with open("no_balance.txt", "w") as f:
    for wallet in no_balance:
        f.write(wallet + "\n")