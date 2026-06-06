import json
import os

class ConfigLoader:
    def __init__(self, config_path="config.json"):
        self.config_path = config_path
        self.config = self.load_config()

    def load_config(self):
        # Tenta carregar o config.json da raiz (um nível acima de src)
        root_config = os.path.join(os.path.dirname(__file__), "..", self.config_path)
        
        try:
            with open(root_config, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # Fallback com valores padrão se o arquivo sumir
            return {
                "monitor": {"interval_seconds": 1.0, "log_enabled": false},
                "overlay": {"font_size": 12, "opacity": 0.8}
            }

    def get(self, section, key):
        return self.config.get(section, {}).get(key)