# ☁️ OracleFT - Oracle Free Tier Automator

A professional, modular Python-based tool to automate the creation of Oracle Cloud "Always Free" instances.

## 💎 GNOME Shell Integration (Top Bar)
Since modern GNOME (45/46+) has limited support for older extensions, OracleFT now includes a **Native System Tray** icon.

### 🚀 Recommended: Native Tray (Works on Ubuntu 24.04)
Run the following command to see a permanent icon in your top bar:
```bash
python3 manager.py tray
```
*This will open a menu where you can Start, Stop, view Logs and Status directly.*

### 🧩 Alternative: Argos Extension
If you prefer using the Argos extension (and it's compatible with your version):
1.  Install [Argos](https://ext.gnome.org/extension/1176/argos/).
2.  Run `python3 manager.py link-argos`.

---

## 🚀 Quick Start

### 🏗️ 1. Setup
Initialize the environment (venv, dependencies, SSH keys):
```bash
python3 manager.py setup
```

### ⚙️ 2. Configuration & Execution
- **Run Tray App**: `python3 manager.py tray` (Highly recommended)
- **Manual Start**: `python3 manager.py start`
- **Reset Success Flag**: `python3 manager.py reset`

---

## 🛡️ Security
- **Local execution**: No data is sent to third-party servers.
- **Auto-Security**: Files are secured with `0600` permissions.
