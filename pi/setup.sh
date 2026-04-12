#!/bin/bash
echo "[*] Configurando entorno SENTINEL PHANTOM..."

# Crear entorno virtual para no ensuciar el sistema
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt

echo "[+] Entorno listo. Usa 'source venv/bin/activate' antes de correr main.py"