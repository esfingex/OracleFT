# ☁️ OracleFT - Oracle Free Tier Automator

A professional, modular Python-based tool to automate the creation of Oracle Cloud "Always Free" instances.

## 🚀 Instalación Profesional

Para desplegar OracleFT como un servicio del sistema en `/opt/oracleft`:

```bash
sudo ./install.sh
```

Este comando configurará:
1.  **Entorno**: `/opt/oracleft` con su propio `venv`.
2.  **Servicio**: Un servicio de Systemd (`oracleft.service`) que se reinicia solo.
3.  **Autostart**: El icono del Systray aparecerá al iniciar sesión.
4.  **Acceso rápido**: Comando `oracleft-manager` disponible en todo el sistema.

---

## 🛠️ Gestión Diaria

Una vez instalado, puedes gestionar el automador mediante el icono en la barra de tareas o por terminal:

```bash
oracleft-manager status
oracleft-manager logs
```

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
