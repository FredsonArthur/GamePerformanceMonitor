#!/bin/bash
# Script de instalação para Fedora

echo "Instalando dependências do sistema..."
sudo dnf install -y python3 python3-pip python3-virtualenv lm_sensors

echo "Criando ambiente virtual..."
python3 -m venv venv
source venv/bin/activate

echo "Instalando dependências Python..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Instalação concluída!"
echo "Para ativar o ambiente virtual: source venv/bin/activate"