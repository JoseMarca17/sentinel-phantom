#!/bin/bash
# CENTINELA MK1 — Setup modo monitor TL-WN722N v1
# Ejecutar como root antes de iniciar el sistema
# Uso: sudo bash scripts/wifi_monitor_setup.sh [up|down]

IFACE="wlan1"
MON_IFACE="wlan1mon"
ACTION="${1:-up}"

if [[ "$ACTION" == "up" ]]; then
    echo "[+] Activando modo monitor en $IFACE..."

    # Matar procesos que interfieren
    airmon-ng check kill 2>/dev/null

    # Bajar interfaz, cambiar a modo monitor, levantar
    ip link set "$IFACE" down
    iw dev "$IFACE" set type monitor
    ip link set "$IFACE" name "$MON_IFACE"
    ip link set "$MON_IFACE" up

    echo "[+] Interfaz $MON_IFACE en modo monitor activa"
    iw dev "$MON_IFACE" info

elif [[ "$ACTION" == "down" ]]; then
    echo "[+] Restaurando $MON_IFACE a modo managed..."

    ip link set "$MON_IFACE" down
    iw dev "$MON_IFACE" set type managed
    ip link set "$MON_IFACE" name "$IFACE"
    ip link set "$IFACE" up

    echo "[+] $IFACE restaurada"
fi
