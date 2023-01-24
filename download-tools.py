#!/usr/bin/env python3
# Author: cbk914
import subprocess
import argparse

def check_installed(tool):
    try:
        subprocess.check_output(f"pip show {tool}", shell=True, stderr=subprocess.DEVNULL)
        print(f"{tool} already installed.")
        return True
    except subprocess.CalledProcessError as e:
        if "not found" in e.output.decode():
            return False
        elif "Permission denied" in e.output.decode():
            print("Permission denied: Please run as root or with elevated privileges.")
            return False

def download_tools(args):
    try:
        if not check_installed("mythril"):
            subprocess.check_call("pip install mythril", shell=True, stderr=subprocess.DEVNULL)
        if not check_installed("oyente"):
            subprocess.check_call("pip install oyente", shell=True, stderr=subprocess.DEVNULL)
        if not check_installed("slither-analyzer"):
            subprocess.check_call("pip install slither-analyzer", shell=True, stderr=subprocess.DEVNULL)
        if not check_installed("smartcheck"):
            subprocess.check_call("pip install smartcheck", shell=True, stderr=subprocess.DEVNULL)
        if not check_installed("securify"):
            subprocess.check_call("pip install securify", shell=True, stderr=subprocess.DEVNULL)
        print("All tools successfully installed.")
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Error: {e}")
