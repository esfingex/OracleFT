#!/usr/bin/env python3
import os
import signal
from pathlib import Path

# Important: This script is run by GNOME Shell/Argos.
# It should use its absolute path to find the manager.

BASE_DIR = Path(__file__).parent.parent.absolute()
MANAGER_BIN = BASE_DIR / ".venv" / "bin" / "python3"
MANAGER_SCRIPT = BASE_DIR / "manager.py"
LOG_FILE = BASE_DIR / "launch_instance.log"
PID_FILE = BASE_DIR / "oracleft.pid"

def get_status():
    if PID_FILE.exists():
        try:
            pid = int(PID_FILE.read_text().strip())
            os.kill(pid, 0)
            return "Running", "green", pid
        except (ValueError, ProcessLookupError):
            return "Stopped", "red", None
    return "Stopped", "red", None

def get_last_logs(count=3):
    if LOG_FILE.exists():
        try:
            with open(LOG_FILE, 'r') as f:
                lines = f.readlines()
                return [line.strip() for line in lines[-count:]]
        except:
            return ["Error reading logs"]
    return ["No logs yet"]

# Check if venv exists
if not MANAGER_BIN.exists():
    print("❌ Oracle: Venv missing | color=red")
    print("---")
    print(f"Please run ./install.sh in {BASE_DIR}")
    exit(0)

# --- ARGOS OUTPUT ---
status, color, pid = get_status()
created = (BASE_DIR / ".instance_created").exists()

if created:
    print(f"🎉 OracleFT: Instance Created! | color=gold")
else:
    print(f"☁️ OracleFT: {status} | color={color}")

print("---")

if created:
    print(f"✨ Success! Instance is now running. | iconName=emblem-system-symbolic")
    print(f"🧹 Reset Status | bash='{MANAGER_BIN} {MANAGER_SCRIPT} reset' refresh=true")
else:
    logs = get_last_logs()
    for log in logs:
        print(f"📝 {log}")

print("---")

if status == "Stopped":
    print(f"▶️ Start Service | bash='{MANAGER_BIN} {MANAGER_SCRIPT} start' refresh=true")
else:
    print(f"🛑 Stop Service | bash='{MANAGER_BIN} {MANAGER_SCRIPT} stop' refresh=true")
    print(f"🔄 Restart Service | bash='{MANAGER_BIN} {MANAGER_SCRIPT} restart' refresh=true")

print("---")
print("Configuration")
settings = [
    ("Instance Name", "DISPLAY_NAME"),
    ("Shape", "OCI_COMPUTE_SHAPE"),
    ("Wait Time", "REQUEST_WAIT_TIME_SECS"),
    ("Email Notifications", "NOTIFY_EMAIL"),
]

for label, key in settings:
    print(f"⚙️ {label} | bash='{MANAGER_BIN} {MANAGER_SCRIPT} update-setting {key}' refresh=true")

print("---")
print(f"📂 Open Project | bash='nautilus {BASE_DIR}'")
print(f"📄 Full Logs | bash='gedit {LOG_FILE}' terminal=false")
