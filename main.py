import sys
import os
import json
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from PyQt5.QtWidgets import QApplication
from overlay import TransparentOverlay

def setup_environment():
    """Verifica e cria estruturas necessárias para o funcionamento do app"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    logs_dir = os.path.join(base_dir, "logs")
    config_file = os.path.join(base_dir, "config.json")
    
    # 1. Garante que a pasta logs existe
    if not os.path.exists(logs_dir):
        print("📁 Pasta 'logs' não encontrada. Criando...")
        os.makedirs(logs_dir)
        with open(os.path.join(logs_dir, ".gitkeep"), 'w') as f:
            pass

    # 2. Garante que o config.json existe
    if not os.path.exists(config_file):
        print("⚙️ config.json não encontrado. Criando configuração padrão...")
        default_config = {
            "monitor": {"interval_seconds": 1.0, "log_enabled": False},
            "overlay": {
                "font_size": 12,
                "opacity": 0.8
            }
        }
        with open(config_file, 'w') as f:
            json.dump(default_config, f, indent=4)

def main():
    # Inicializa o ambiente
    setup_environment()
    
    app = QApplication(sys.argv)
    
    # Exibe Banner de inicialização
    print("==========================================")
    print("   GAME PERFORMANCE MONITOR - INICIADO    ")
    print("==========================================")
    print("✨ Status: Pronto para monitorar")
    print("⚙️ Configurações carregadas com sucesso")
    print("==========================================")
    
    # Inicia a aplicação
    overlay = TransparentOverlay()
    overlay.start_monitoring()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()