import json
import os

class ConfigLoader:
    def __init__(self, config_path="config.json"):
        self.config_path = config_path
        self.config = self.load_config()

    def load_config(self):
        root_config = os.path.join(os.path.dirname(__file__), "..", self.config_path)
        
        # Valores padrão caso o arquivo não exista
        default_config = {
            "monitor": {"interval_seconds": 1.0, "log_enabled": False},
            "overlay": {
                "font_size": 12,
                "opacity": 0.8,
                "color_normal": "#ffffff"
            }
        }

        if not os.path.exists(root_config):
            print("⚠️ config.json não encontrado. Criando arquivo padrão...")
            try:
                with open(root_config, 'w') as f:
                    json.dump(default_config, f, indent=4)
                return default_config
            except Exception as e:
                print(f"Erro ao criar config.json: {e}")
                return default_config

        try:
            with open(root_config, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, Exception) as e:
            print(f"Erro ao ler config.json: {e}. Usando padrões.")
            return default_config

    def get(self, section, key):
        return self.config.get(section, {}).get(key)