#!/usr/bin/env python3
# Author: cbk914
import argparse
import hashlib
import requests

def display_help():
    print("Usage: python download-smartcontract.py -s smartcontract [-i integrity_hash] [-h]")
    print("Downloads a smart contract .bin file from a trusted source and verifies its integrity using a provided hash")
    print("  -s smartcontract      name of the smart contract to download")
    print("  -i integrity_hash     hash of the expected smart contract file (e.g. SHA256)")
    print("  -h help               display this help and exit")
    exit(0)

parser = argparse.ArgumentParser(description="Downloads a smart contract .bin file from a trusted source and verifies its integrity using a provided hash")
parser.add_argument("-s", "--smartcontract", type=str, required=True, help="name of the smart contract to download")
parser.add_argument("-i", "--integrity_hash", type=str, help="hash of the expected smart contract file (e.g. SHA256)")
args = parser.parse_args()

# Define a dictionary of trusted sources and their respective smart contract URLs
trusted_sources = {
    "MyToken": "https://example.com/smartcontracts/MyToken.bin",
    "MyExchange": "https://example.com/smartcontracts/MyExchange.bin"
}

# Check if the provided smart contract is in the trusted sources dictionary
if args.smartcontract not in trusted_sources:
    print("Error: Provided smart contract is not in the list of trusted sources.")
    exit(1)

# Download the smart contract file from the trusted source
try:
    response = requests.get(trusted_sources[args.smartcontract])
    response.raise_for_status()
    open(args.smartcontract+".bin", "wb").write(response.content)
    print(f"Successfully downloaded {args.smartcontract}.bin")
except requests.exceptions.RequestException as e:
    print("Error: Failed to download smart contract file.")
    print(e)
    exit(1)

# If an integrity hash was provided, verify the downloaded file
if args.integrity_hash:
    # Read the downloaded file
    with open(args.smartcontract+".bin", "rb") as file:
        file_hash = hashlib.new(args.integrity_hash)
        file_hash.update(file.read())
        file_hash = file_hash.hexdigest()
    if file_hash == args.integrity_hash:
        print(f"Successfully verified {args.smartcontract}.bin integrity using {args.integrity_hash} hash.")
    else:
        print(f"Error: {args.smartcontract}.bin integrity verification failed using {args.integrity_hash} hash.")
        exit(1)
