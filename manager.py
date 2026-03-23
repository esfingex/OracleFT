#!/usr/bin/env python3
import os
import sys
import subprocess
import argparse
import signal
from pathlib import Path


class Manager:
    def __init__(self):
        self.base_path = Path(__file__).parent.absolute()
        self.venv_path = self.base_path / ".venv"
        self.python_bin = self.base_path / ".venv" / "bin" / "python3" if os.name != "nt" else self.venv_path / "Scripts" / "python.exe"
        self.pid_file = self.base_path / "oracleft.pid"

        # Auto-switch to venv if available and not already in it
        if self.python_bin.exists() and sys.executable != str(self.python_bin):
            if os.environ.get("ORACLEFT_VENV_MANAGED") != "1":
                os.environ["ORACLEFT_VENV_MANAGED"] = "1"
                os.execv(str(self.python_bin), [str(self.python_bin)] + sys.argv)

    def setup(self):
        print("🚀 Setting up OracleFT environment...")
        
        # 1. Virtual Environment
        if not self.venv_path.exists():
            print("📦 Creating virtual environment with system site-packages...")
            subprocess.run([sys.executable, "-m", "venv", "--system-site-packages", str(self.venv_path)], check=True)
        
        # 2. Dependencies
        print("🛠️ Installing dependencies...")
        subprocess.run([str(self.python_bin), "-m", "pip", "install", "--upgrade", "pip"], check=True)
        subprocess.run([str(self.python_bin), "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        
        # 3. SSH Keys
        pub_key = self.base_path / "id_rsa.pub"
        priv_key = self.base_path / "id_rsa"
        if not pub_key.exists() or not priv_key.exists():
            print("🔑 Generating SSH keys for OCI instance...")
            subprocess.run(["ssh-keygen", "-t", "rsa", "-b", "4096", "-f", str(priv_key), "-N", ""], check=True)
            priv_key.chmod(0o600)
            print(f"✅ Keys generated: {priv_key.name}, {pub_key.name}")
        
        # 4. Configuration Check
        from core.config import config
        oci_config_path = Path(config.get("OCI_CONFIG", "./oci_config")).expanduser()
        if not oci_config_path.exists():
            print(f"⚠️ Warning: OCI config not found at {oci_config_path}")
            print("Please ensure you have your OCI API keys configured. You can use 'sample_oci_config' as a template.")

        print("\n✨ Setup complete! Next steps:")
        print("1. Edit 'oci.env' with your OCI details.")
        print("2. Run 'python3 manager.py start' to begin.")

    def validate_config(self):
        from core.config import config
        required = ["OCI_CONFIG", "OCT_FREE_AD"]
        missing = [r for r in required if not config.get(r)]
        if missing:
            print(f"❌ Error: Missing required configuration keys: {', '.join(missing)}")
            return False
        
        # Check permissions
        if config.env_path.exists():
            stats = config.env_path.stat()
            if oct(stats.st_mode)[-3:] != "600":
                print(f"⚠️ Warning: {config.env_path.name} has loose permissions. Setting to 600...")
                config.env_path.chmod(0o600)
        return True

    def update_setting(self, key):
        from core.config import config
        current_val = config.get(key, "")
        try:
            cmd = f'zenity --entry --title="OracleFT Config" --text="Enter value for {key}:" --entry-text="{current_val}"'
            new_val = subprocess.check_output(cmd, shell=True).decode().strip()
            if new_val:
                config.set(key, new_val)
                print(f"✅ Updated {key} to {new_val}")
        except subprocess.CalledProcessError:
            print("❌ Canceled or failed to get input.")

    def start(self):
        if self.is_running():
            print(f"⚠️ Script is already running (PID: {self.get_pid()}).")
            return
        
        if not self.validate_config():
            return

        print("🚀 Starting Oracle Instance Creation script in background...")
        log_file = open("launch_instance.log", "a")
        # Use -u for unbuffered output
        proc = subprocess.Popen([str(self.python_bin), "-u", "main.py"], 
                                stdout=log_file, stderr=log_file, 
                                start_new_session=True)
        
        print(f"✅ Script started with PID {proc.pid}. Check logs for progress.")
        
        # Also try to launch the tray if not already running
        try:
            subprocess.Popen([str(self.python_bin), str(self.base_path / "manager.py"), "tray"], 
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        except Exception:
            pass

    def stop(self):
        pid = self.get_pid()
        if not pid:
            print("⚠️ Script is not running.")
            return

        print(f"🛑 Stopping process {pid}...")
        try:
            os.kill(pid, signal.SIGTERM)
            if self.pid_file.exists():
                self.pid_file.unlink()
            print("✅ Script stopped.")
        except ProcessLookupError:
            print("⚠️ Process not found, cleaning up PID file.")
            if self.pid_file.exists():
                self.pid_file.unlink()

    def get_pid(self):
        if self.pid_file.exists():
            try:
                pid = int(self.pid_file.read_text().strip())
                # Verify if process still exists
                os.kill(pid, 0)
                return pid
            except (ValueError, ProcessLookupError):
                return None
        return None

    def is_running(self):
        return self.get_pid() is not None

    def check_system(self):
        print("🔍 Checking System for OracleFT Integration...")
        argos_dir = Path("~/.config/argos/").expanduser()
        argos_exists = argos_dir.exists()
        
        # 1. Argos Check
        if argos_exists:
            print("✅ Argos directory found.")
            target = argos_dir / "oracle_status.1m.py"
            if target.exists():
                print(f"✅ Argos plugin is linked: {target}")
            else:
                print("❌ Argos plugin is NOT linked. Run: python3 manager.py link-argos")
        else:
            print("❌ Argos directory NOT found (~/.config/argos/).")
            print("💡 Tip: Install the Argos extension (https://ext.gnome.org/extension/1176/argos/) first.")

        # 2. Config Check
        config_ok = self.validate_config()
        if config_ok:
            print("✅ Configuration is valid.")
        
        # 3. Running check
        pid = self.get_pid()
        if pid:
            print(f"✅ OracleFT is running in background (PID: {pid}).")
        else:
            print("ℹ️ OracleFT is not currently running.")

    def run_gui(self):
        try:
            from core.tray import OracleTray
            print("🖥️ Launching GUI Dashboard...")
            tray = OracleTray(self)
            tray.run_dashboard()
        except Exception as e:
            print(f"❌ Error during GUI launch: {e}")

    def run_tray(self):
        try:
            from core.tray import OracleTray
            tray = OracleTray(self)
            tray.run()
        except ImportError:
            print("❌ Error: Required libraries not found. Run 'oracleft setup'")

    def link_argos(self):
        argos_dir = Path("~/.config/argos/").expanduser()
        argos_dir.mkdir(parents=True, exist_ok=True)
        target = argos_dir / "oracle_status.1m.py"
        source = self.base_path / "argos" / "oracle_status.1m.py"
        
        if target.exists():
            target.unlink()
        target.symlink_to(source)
        source.chmod(0o755)
        print(f"✅ Linked Argos plugin to {target}")

    def schedule(self, action="show"):
        from core import config
        interval = config.get("OCI_CRON_INTERVAL", "*/30 * * * *")
        cron_cmd = f"{interval} {self.python_bin} {self.base_path}/main.py >> {self.base_path}/launch_instance.log 2>&1"
        
        if action == "show":
            print("\n⏰ Suggested Crontab entry (runs every 30 mins):")
            print(f"   {cron_cmd}")
            print("\nTo add it, run: crontab -e")
        elif action == "install":
            try:
                current_cron = subprocess.check_output("crontab -l", shell=True).decode()
            except subprocess.CalledProcessError:
                current_cron = ""
            
            if str(self.base_path) in current_cron:
                print("⚠️ OracleFT is already in crontab.")
                return

            new_cron = current_cron + f"\n{cron_cmd}\n"
            process = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE)
            process.communicate(input=new_cron.encode())
            print("✅ Successfully added OracleFT to crontab (30m interval).")
        elif action == "remove":
            try:
                current_cron = subprocess.check_output("crontab -l", shell=True).decode()
                lines = [line for line in current_cron.splitlines() if str(self.base_path) not in line]
                new_cron = "\n".join(lines) + "\n"
                process = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE)
                process.communicate(input=new_cron.encode())
                print("✅ Removed OracleFT from crontab.")
            except subprocess.CalledProcessError:
                print("⚠️ No crontab found.")

    def install(self):
        """Professional installation to /opt/oracleft with systemd and autostart."""
        target_dir = Path("/opt/oracleft")
        print(f"🚀 Installing OracleFT to {target_dir}...")
        
        # 1. Create directory and copy files
        if self.base_path != target_dir:
            try:
                subprocess.run(["sudo", "mkdir", "-p", str(target_dir)], check=True)
                subprocess.run(["sudo", "cp", "-r", str(self.base_path) + "/.", str(target_dir)], check=True)
                subprocess.run(["sudo", "chown", "-R", f"{os.getlogin()}:{os.getlogin()}", str(target_dir)], check=True)
            except Exception as e:
                print(f"❌ Failed to copy files: {e}")
                return
        else:
            print("ℹ️  Already running from target directory, skipping copy.")

        # 2. Create Systemd Service
        self.create_systemd_service(target_dir)
        
        # 3. Create Desktop Autostart
        self.create_autostart_entry(target_dir)

        print(f"\n✨ Installation complete! OracleFT is now in {target_dir}")
        print("💡 The service is enabled and the Tray will start automatically.")
        
        # Launch tray immediately in background
        try:
            subprocess.Popen([str(target_dir / ".venv" / "bin" / "python3"), str(target_dir / "manager.py"), "tray"], 
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
            print("🚀 Tray icon triggered!")
        except Exception:
            pass

    def create_systemd_service(self, target_dir):
        service_content = f"""[Unit]
Description=Oracle Free Tier Automator
After=network.target

[Service]
Type=simple
User={os.getlogin()}
WorkingDirectory={target_dir}
ExecStart={target_dir}/.venv/bin/python3 {target_dir}/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
        service_path = Path("/tmp/oracleft.service")
        service_path.write_text(service_content)
        
        try:
            subprocess.run(["sudo", "mv", str(service_path), "/etc/systemd/system/oracleft.service"], check=True)
            subprocess.run(["sudo", "systemctl", "daemon-reload"], check=True)
            subprocess.run(["sudo", "systemctl", "enable", "oracleft.service"], check=True)
            print("✅ Systemd service installed and enabled.")
        except Exception as e:
            print(f"⚠️ Failed to install systemd service: {e}")

    def create_autostart_entry(self, target_dir):
        autostart_dir = Path("~/.config/autostart").expanduser()
        autostart_dir.mkdir(parents=True, exist_ok=True)
        
        desktop_content = f"""[Desktop Entry]
Type=Application
Exec={target_dir}/.venv/bin/python3 {target_dir}/manager.py tray
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Name=OracleFT Tray
Comment=Monitoring Oracle Free Tier availability
Icon={target_dir}/core/assets/oracle_icon.png
"""
        (autostart_dir / "oracleft.desktop").write_text(desktop_content)
        print("✅ Autostart entry created in ~/.config/autostart/")

    def reset(self):
        sentinel = self.base_path / ".instance_created"
        if sentinel.exists():
            sentinel.unlink()
            print("✅ Status reset. You can now run the creation script again.")
        else:
            print("ℹ️ No sentinel file found. Status is already reset.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Oracle Free Tier Manager")
    parser.add_argument(
        "command", 
        nargs="?", 
        choices=["setup", "start", "stop", "status", "restart", "schedule", "reset", "tray", "install"],
        default="tray",
        help="Command to perform (default: tray)"
    )
    parser.add_argument("key", nargs="?", help="Key to update or schedule action (show/install/remove)")

    args = parser.parse_args()
    mgr = Manager()

    if args.command == "setup":
        mgr.setup()
    elif args.command == "install":
        mgr.install()
    elif args.command == "update-setting":
        if not args.key:
            print("Error: update-setting requires a key.")
        else:
            mgr.update_setting(args.key)
    elif args.command == "start":
        mgr.start()
    elif args.command == "stop":
        mgr.stop()
    elif args.command == "restart":
        mgr.stop()
        mgr.start()
    elif args.command == "status":
        pid = mgr.get_pid()
        if pid:
            print(f"Status: Running (PID: {pid})")
        else:
            print("Status: Stopped")
        
        if (mgr.base_path / ".instance_created").exists():
            print("ℹ️ Instance already created (.instance_created found)")
    elif args.command == "link-argos":
        mgr.link_argos()
    elif args.command == "schedule":
        mgr.schedule(args.key or "show")
    elif args.command == "reset":
        mgr.reset()
    elif args.command == "check-system":
        mgr.check_system()
    elif args.command == "tray":
        mgr.run_tray()
    elif args.command == "gui":
        mgr.run_gui()
