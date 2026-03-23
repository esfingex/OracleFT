import os
import sys
import subprocess
import threading
from pathlib import Path
from PIL import Image, ImageDraw
import pystray
from pystray import MenuItem as item

# Add parent dir to path
sys.path.append(str(Path(__file__).parent.parent))
from core.config import config

class OracleTray:
    def __init__(self, manager):
        self.manager = manager
        self.base_path = Path(__file__).parent.parent
        self.assets_dir = self.base_path / "core" / "assets"
        self.assets_dir.mkdir(parents=True, exist_ok=True)
        self.icon_path = str(self.assets_dir / "oracle_icon.png")
        self._ensure_icon()
        
        # Following the official documentation pattern exactly
        self.icon = pystray.Icon(
            "OracleFT",
            self._get_icon_image(),
            "Oracle Free Tier Automator",
            menu=self._create_menu()
        )

    def _ensure_icon(self):
        # High quality white cloud icon
        size = 64
        image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        color = (255, 255, 255, 255)
        # Professional cloud shape
        draw.ellipse((5, 25, 25, 45), fill=color)
        draw.ellipse((20, 15, 45, 40), fill=color)
        draw.ellipse((35, 25, 55, 45), fill=color)
        draw.rectangle((15, 30, 45, 45), fill=color)
        image.save(self.icon_path)

    def _get_icon_image(self):
        return Image.open(self.icon_path).convert('RGBA')

    def _create_menu(self):
        return pystray.Menu(
            item('🚀 Start Automator', self.on_start),
            item('🛑 Stop Automator', self.on_stop),
            item('🔄 Restart', self.on_restart),
            item('🧪 Connection Test', self.on_test_connection),
            pystray.Menu.SEPARATOR,
            item('📊 Check Status', self.on_status),
            item('📝 View Logs', self.on_logs),
            item('🧹 Reset Status', self.on_reset),
            pystray.Menu.SEPARATOR,
            item('⚙️ Edit oci.env', self.on_edit_env),
            item('🛠️ Config Assistant', self.on_config),
            pystray.Menu.SEPARATOR,
            item('❌ Exit Tray', self.on_exit)
        )

    def on_start(self, icon=None, item=None):
        self.manager.start()

    def on_stop(self, icon=None, item=None):
        self.manager.stop()

    def on_restart(self, icon=None, item=None):
        self.manager.stop()
        self.manager.start()

    def on_test_connection(self, icon=None, item=None):
        icon.notify("Iniciando prueba de conexión...", "OracleFT Test")
        # Run main.py in dry-run mode
        subprocess.Popen([str(self.base_path / ".venv" / "bin" / "python3"), str(self.base_path / "main_test.py")])

    def on_status(self, icon=None, item=None):
        pid = self.manager.get_pid()
        created = (self.base_path / ".instance_created").exists()
        msg = f"Status: {'Running (PID: ' + str(pid) + ')' if pid else 'Stopped'}"
        if created:
            msg += "\n🎉 Instance already created!"
        subprocess.run(['zenity', '--info', '--text', msg, '--title', 'OracleFT Status'])

    def on_logs(self, icon=None, item=None):
        log_file = self.base_path / "launch_instance.log"
        if log_file.exists():
            if log_file.stat().st_size == 0:
                subprocess.run(['zenity', '--info', '--text', '📝 El archivo de log está vacío por ahora.\nEspere a que la automatización genere actividad.', '--title', 'OracleFT Logs'])
            else:
                subprocess.run(['zenity', '--text-info', '--filename', str(log_file), '--title', 'OracleFT Logs', '--width=700', '--height=500', '--font=Monospace'])
        else:
            subprocess.run(['zenity', '--error', '--text', '❌ No se encontró el archivo de log.', '--title', 'Error'])

    def on_reset(self, icon=None, item=None):
        self.manager.reset()

    def on_edit_env(self, icon=None, item=None):
        subprocess.run(['xdg-open', str(self.base_path / "oci.env")])

    def on_config(self, icon=None, item=None):
        # Guided configuration via dialogs
        self._check_initial_setup(force=True)

    def on_exit(self, icon, item):
        print("👋 Exiting OracleFT Tray...")
        icon.stop()
        # Ensure we kill the background automator if running
        self.manager.stop()
        os._exit(0)

    def run(self):
        # Initial check for credentials
        self._check_initial_setup()
        
        # We need to run the icon in a setup context to show a notification on start
        def setup(icon):
            icon.visible = True
            icon.notify("OracleFT está activo y vigilando.", "Cloud Automator")

        # Always run in the main thread for pystray compatibility
        self.icon.run(setup=setup)

    def _check_initial_setup(self, force=False):
        critical_keys = ["OCI_USER_ID", "OCI_TENANCY_ID", "OCI_FINGERPRINT", "OCI_REGION"]
        is_configured = all(config.get(k) for k in critical_keys)
        
        if not is_configured or force:
            if not force:
                msg = "⚠️ Faltan credenciales de Oracle Cloud.\n¿Deseas configurarlas ahora?"
                res = subprocess.run(['zenity', '--question', '--text', msg, '--title', 'Setup Requerido'])
                if res.returncode != 0: return

            keys_to_config = [
                ("DISPLAY_NAME", "Nombre de la Instancia"),
                ("EMAIL", "Tu Email (Notificaciones)"),
                ("EMAIL_PASSWORD", "Contraseña de App para Email"),
                ("OCI_COMPUTE_SHAPE", "Shape (ej: VM.Standard.A1.Flex)"),
                ("OCI_ARM_OCPUS", "OCPUs (para ARM)"),
                ("OCI_ARM_MEMORY_GB", "Memoria GB (para ARM)")
            ]
            
            for key, label in keys_to_config:
                current = config.get(key, "")
                cmd = ['zenity', '--entry', '--title', f'Configurar {label}', '--text', f'Ingresa {label}:']
                if "PASSWORD" in key:
                    cmd[1] = '--password'
                else:
                    cmd.extend(['--entry-text', current])
                
                try:
                    new_val = subprocess.check_output(cmd).decode().strip()
                    if new_val:
                        config.set(key, new_val)
                except subprocess.CalledProcessError:
                    break
            
            subprocess.run(['zenity', '--info', '--text', '✅ Configuración actualizada con éxito.', '--title', 'OracleFT'])
