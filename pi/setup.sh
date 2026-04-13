#!/usr/bin/env bash
# ╔══════════════════════════════════════════════════════════════╗
# ║   SENTINEL PHANTOM — Setup Script (Raspberry Pi 3B)         ║
# ║   Escuela Militar de Ingeniería (EMI) — Open House 2026     ║
# ╚══════════════════════════════════════════════════════════════╝
# Uso: sudo bash setup.sh
# Instala dependencias del sistema, Python y configura el entorno.

set -euo pipefail

# ── Colores ───────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

info()    { echo -e "${CYAN}[INFO]${RESET}  $*"; }
success() { echo -e "${GREEN}[OK]${RESET}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${RESET}  $*"; }
error()   { echo -e "${RED}[ERROR]${RESET} $*"; exit 1; }
section() { echo -e "\n${BOLD}${CYAN}══ $* ══${RESET}"; }

# ── Verificaciones iniciales ──────────────────────────────────────────────────
[[ "$EUID" -ne 0 ]] && error "Ejecutar como root: sudo bash setup.sh"

section "SENTINEL PHANTOM — Instalación"
info "Sistema: $(uname -a)"
info "Usuario efectivo: $(id)"

# ── Variables configurables ───────────────────────────────────────────────────
PHANTOM_USER="${SUDO_USER:-phantom}"
PHANTOM_HOME="/home/${PHANTOM_USER}"
PROJECT_DIR="${PHANTOM_HOME}/centinel-phantom"
PI_DIR="${PROJECT_DIR}/pi"
VENV_DIR="${PI_DIR}/.venv"
LOG_DIR="${PI_DIR}/logs"
DB_DIR="${PI_DIR}/database"
PYTHON_BIN="python3"

# ── 1. Actualizar sistema ─────────────────────────────────────────────────────
section "1. Actualización del sistema"
apt-get update -qq
apt-get upgrade -y -qq
success "Sistema actualizado"

# ── 2. Dependencias del sistema ───────────────────────────────────────────────
section "2. Dependencias del sistema"

SYSTEM_PKGS=(
    # Python
    python3 python3-pip python3-venv python3-dev
    # Build tools
    build-essential git curl wget
    # WiFi / monitor mode
    aircrack-ng iw wireless-tools net-tools
    # Librerías I2C / SPI (OLED, RFID)
    python3-smbus i2c-tools libgpiod2
    # PN532 / SPI
    raspi-config
    # SQLite
    sqlite3
    # Serial (ESP32, Pico)
    minicom screen
    # Hostapd + dnsmasq para Evil Twin
    hostapd dnsmasq
    # Libcap para Scapy sin root
    libpcap-dev
    # Utilidades
    tmux htop nano jq
)

info "Instalando ${#SYSTEM_PKGS[@]} paquetes del sistema..."
apt-get install -y -qq "${SYSTEM_PKGS[@]}"
success "Dependencias del sistema instaladas"

# ── 3. Configurar interfaces ──────────────────────────────────────────────────
section "3. Configuración de hardware"

# Habilitar I2C y SPI via raspi-config (no interactivo)
raspi-config nonint do_i2c 0  2>/dev/null || warn "I2C ya habilitado o raspi-config no disponible"
raspi-config nonint do_spi 0  2>/dev/null || warn "SPI ya habilitado o raspi-config no disponible"
raspi-config nonint do_serial_hw 0 2>/dev/null || warn "Serial HW no configurado"
success "I2C y SPI habilitados"

# Agregar usuario al grupo dialout (acceso serial)
usermod -aG dialout "${PHANTOM_USER}" 2>/dev/null || true
usermod -aG gpio    "${PHANTOM_USER}" 2>/dev/null || true
usermod -aG spi     "${PHANTOM_USER}" 2>/dev/null || true
usermod -aG i2c     "${PHANTOM_USER}" 2>/dev/null || true
success "Usuario '${PHANTOM_USER}' agregado a grupos de hardware"

# ── 4. Configurar modo monitor WiFi (MT7601U) ─────────────────────────────────
section "4. Modo monitor WiFi"

# Evitar que NetworkManager tome control de wlan1
NM_CONF="/etc/NetworkManager/conf.d/phantom-unmanaged.conf"
if command -v NetworkManager &>/dev/null; then
    cat > "${NM_CONF}" <<'EOF'
[keyfile]
unmanaged-devices=interface-name:wlan1
EOF
    success "wlan1 excluida de NetworkManager"
else
    warn "NetworkManager no encontrado — omitiendo"
fi

# Cargar driver mt7601u
modprobe mt7601u 2>/dev/null || warn "Driver mt7601u no disponible (¿adaptador conectado?)"

# ── 5. Crear estructura de directorios ────────────────────────────────────────
section "5. Estructura de directorios"

mkdir -p "${LOG_DIR}"
mkdir -p "${DB_DIR}"
mkdir -p "${PI_DIR}/tmp"

chown -R "${PHANTOM_USER}:${PHANTOM_USER}" "${PROJECT_DIR}" 2>/dev/null || true
success "Directorios creados"

# ── 6. Entorno virtual Python ─────────────────────────────────────────────────
section "6. Entorno virtual Python"

if [[ ! -d "${VENV_DIR}" ]]; then
    sudo -u "${PHANTOM_USER}" ${PYTHON_BIN} -m venv "${VENV_DIR}"
    success "Virtualenv creado en ${VENV_DIR}"
else
    warn "Virtualenv ya existe — reutilizando"
fi

VENV_PIP="${VENV_DIR}/bin/pip"
VENV_PYTHON="${VENV_DIR}/bin/python"

sudo -u "${PHANTOM_USER}" "${VENV_PIP}" install --upgrade pip setuptools wheel -q
success "pip actualizado"

# ── 7. Instalar dependencias Python ───────────────────────────────────────────
section "7. Dependencias Python"

if [[ -f "${PI_DIR}/requirements.txt" ]]; then
    sudo -u "${PHANTOM_USER}" "${VENV_PIP}" install -r "${PI_DIR}/requirements.txt" -q
    success "requirements.txt instalado"
else
    warn "requirements.txt no encontrado — instalando paquetes base"
    sudo -u "${PHANTOM_USER}" "${VENV_PIP}" install -q \
        flask flask-socketio flask-cors python-socketio eventlet \
        scapy bleak requests python-dotenv pyserial \
        luma.oled Pillow RPi.GPIO spidev
fi

# ── 8. Archivo .env ───────────────────────────────────────────────────────────
section "8. Configuración .env"

ENV_FILE="${PI_DIR}/.env"
ENV_EXAMPLE="${PI_DIR}/.env.example"

if [[ ! -f "${ENV_FILE}" ]]; then
    if [[ -f "${ENV_EXAMPLE}" ]]; then
        cp "${ENV_EXAMPLE}" "${ENV_FILE}"
        chown "${PHANTOM_USER}:${PHANTOM_USER}" "${ENV_FILE}"
        success ".env creado desde .env.example"
        warn "⚠  Edita ${ENV_FILE} con la IP del servidor antes de iniciar"
    else
        warn ".env.example no encontrado — creando .env mínimo"
        cat > "${ENV_FILE}" <<EOF
DEVICE_ID=PHANTOM-PI-01
DEVICE_NAME=Sentinel Phantom Unit 1
API_HOST=0.0.0.0
API_PORT=5000
API_DEBUG=false
SECRET_KEY=phantom-secret-2026-change-me
DB_PATH=${DB_DIR}/phantom.db
SERVER_URL=http://192.168.1.100:8000
SYNC_INTERVAL_S=60
ESP32_PORT=/dev/ttyUSB0
ESP32_BAUD=115200
PICO_PORT=/dev/ttyUSB1
PICO_BAUD=115200
WIFI_IFACE_MONITOR=wlan1
WIFI_IFACE_AP=wlan0
LOG_LEVEL=INFO
LOG_FILE=${LOG_DIR}/phantom.log
MOD_WIFI=true
MOD_BLUETOOTH=true
MOD_RFID=true
MOD_TSCM=true
MOD_IR=true
MOD_NRF24=true
EOF
        chown "${PHANTOM_USER}:${PHANTOM_USER}" "${ENV_FILE}"
    fi
else
    warn ".env ya existe — no se sobreescribe"
fi

# ── 9. Permisos especiales (Scapy sin root) ───────────────────────────────────
section "9. Capacidades de red (Scapy sin root)"

PYTHON_EXEC="${VENV_PYTHON}"
if [[ -f "${PYTHON_EXEC}" ]]; then
    setcap cap_net_raw,cap_net_admin=eip "${PYTHON_EXEC}" 2>/dev/null \
        && success "cap_net_raw asignada a ${PYTHON_EXEC}" \
        || warn "No se pudo asignar cap_net_raw (ejecutar como root en producción)"
fi

# ── 10. Servicio systemd ──────────────────────────────────────────────────────
section "10. Servicio systemd"

SERVICE_FILE="/etc/systemd/system/sentinel-phantom.service"
cat > "${SERVICE_FILE}" <<EOF
[Unit]
Description=SENTINEL PHANTOM — Sistema Portátil de Auditoría Táctica
After=network.target
Wants=network.target

[Service]
Type=simple
User=${PHANTOM_USER}
WorkingDirectory=${PI_DIR}
ExecStart=${VENV_DIR}/bin/python main.py
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=sentinel-phantom
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
success "Servicio systemd registrado: sentinel-phantom"
info "  Iniciar:    sudo systemctl start sentinel-phantom"
info "  Habilitar:  sudo systemctl enable sentinel-phantom"
info "  Estado:     sudo systemctl status sentinel-phantom"
info "  Logs:       sudo journalctl -u sentinel-phantom -f"

# ── 11. Alias útiles ──────────────────────────────────────────────────────────
section "11. Alias de desarrollo"

BASHRC="${PHANTOM_HOME}/.bashrc"
ALIAS_BLOCK="# ── SENTINEL PHANTOM aliases ──"

if ! grep -q "${ALIAS_BLOCK}" "${BASHRC}" 2>/dev/null; then
    cat >> "${BASHRC}" <<EOF

${ALIAS_BLOCK}
alias phantom-start='cd ${PI_DIR} && ${VENV_PYTHON} main.py'
alias phantom-log='tail -f ${LOG_DIR}/phantom.log'
alias phantom-db='sqlite3 ${DB_DIR}/phantom.db'
alias phantom-service-start='sudo systemctl start sentinel-phantom'
alias phantom-service-stop='sudo systemctl stop sentinel-phantom'
alias phantom-service-log='sudo journalctl -u sentinel-phantom -f'
alias phantom-monitor='sudo ip link set wlan1 down && sudo iw wlan1 set type monitor && sudo ip link set wlan1 up'
alias phantom-managed='sudo ip link set wlan1 down && sudo iw wlan1 set type managed && sudo ip link set wlan1 up'
EOF
    success "Aliases agregados a ${BASHRC}"
else
    warn "Aliases ya existen en .bashrc"
fi

# ── Resumen final ─────────────────────────────────────────────────────────────
section "Instalación completada"

echo ""
echo -e "${BOLD}${GREEN}╔══════════════════════════════════════════════════════════╗${RESET}"
echo -e "${BOLD}${GREEN}║   SENTINEL PHANTOM — Setup exitoso ✓                     ║${RESET}"
echo -e "${BOLD}${GREEN}╚══════════════════════════════════════════════════════════╝${RESET}"
echo ""
echo -e "  ${BOLD}Próximos pasos:${RESET}"
echo -e "  1. Edita ${YELLOW}${ENV_FILE}${RESET} con la IP real del servidor"
echo -e "  2. Conecta el hardware (ESP32, Pico, adaptador WiFi)"
echo -e "  3. Activa el modo monitor:"
echo -e "     ${CYAN}sudo ip link set wlan1 down${RESET}"
echo -e "     ${CYAN}sudo iw wlan1 set type monitor${RESET}"
echo -e "     ${CYAN}sudo ip link set wlan1 up${RESET}"
echo -e "  4. Inicia el sistema:"
echo -e "     ${CYAN}cd ${PI_DIR} && source .venv/bin/activate && python main.py${RESET}"
echo -e "     — o vía systemd —"
echo -e "     ${CYAN}sudo systemctl enable --now sentinel-phantom${RESET}"
echo ""
warn "Reiniciar la Pi para aplicar cambios de I2C/SPI y grupos de usuario"
echo ""