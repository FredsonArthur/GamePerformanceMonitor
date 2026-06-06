"""
fps_capture.py - Captura de FPS em tempo real de jogos
Suporte: MangoHud, processos de jogos, Steam, Lutris, Heroic
"""

import subprocess
import re
import os
import glob
from typing import Dict, Optional, List
from datetime import datetime

class FPSCapture:
    """Captura FPS de jogos em execução"""
    
    def __init__(self):
        self.mangohud_available = self._check_mangohud()
        self.current_game = None
        self.current_fps = 0
        self.fps_history = []
        self.max_history = 300  # 5 minutos com 1 FPS por segundo
        
    def _check_mangohud(self) -> bool:
        """Verifica se MangoHud está instalado"""
        try:
            result = subprocess.run(['which', 'mangohud'], 
                                  capture_output=True, text=True)
            return result.returncode == 0
        except:
            return False
    
    def detect_games(self) -> List[Dict]:
        """Detecta jogos em execução"""
        games = []
        
        # Processos comuns de jogos
        game_processes = [
            'steam', 'lutris', 'heroic', 'wine', 'wine64',
            'game', 'cs2', 'hl2', 'eldenring', 'cyberpunk'
        ]
        
        try:
            # Listar processos
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            lines = result.stdout.split('\n')
            
            for line in lines:
                for proc in game_processes:
                    if proc in line.lower():
                        # Extrair nome do processo
                        parts = line.split()
                        if len(parts) > 10:
                            proc_name = parts[10] if len(parts) > 10 else parts[0]
                            games.append({
                                'pid': parts[1],
                                'name': proc_name,
                                'cmd': ' '.join(parts[10:])
                            })
                        break
        except Exception as e:
            print(f"Erro ao detectar jogos: {e}")
        
        return games
    
    def get_fps_from_mangohud(self) -> Optional[float]:
        """Tenta obter FPS do MangoHud (via arquivo de log)"""
        # MangoHud pode escrever logs em /tmp
        log_files = glob.glob('/tmp/mangohud*.log')
        
        if log_files:
            # Pegar o log mais recente
            latest_log = max(log_files, key=os.path.getmtime)
            
            try:
                with open(latest_log, 'r') as f:
                    lines = f.readlines()
                    if lines:
                        # Última linha com FPS
                        last_line = lines[-1].strip()
                        # Formato típico: "FPS: 60.2"
                        match = re.search(r'FPS:\s*(\d+\.?\d*)', last_line)
                        if match:
                            return float(match.group(1))
            except:
                pass
        
        return None
    
    def estimate_fps_from_screen(self) -> float:
        """Estima FPS baseado em captura de tela simples (fallback)"""
        # Esta é uma estimativa simples, não precisa ser precisa
        # Podemos melhorar depois com integração real
        import time
        
        # Simular FPS baseado em carga da GPU
        # Quanto maior uso da GPU, maior potencial de FPS
        try:
            import psutil
            # Placeholder - depois integramos com métricas reais
            return 60.0  # Valor padrão
        except:
            return 60.0
    
    def get_current_fps(self, gpu_percent: float = 0) -> float:
        """
        Obtém FPS atual usando múltiplas fontes
        Prioridade: MangoHud > Estimativa baseada em GPU
        """
        # Tentar MangoHud primeiro
        fps = self.get_fps_from_mangohud()
        
        if fps is not None:
            self.current_fps = fps
        else:
            # Estimativa baseada no uso da GPU
            if gpu_percent > 80:
                fps = 60
            elif gpu_percent > 60:
                fps = 45
            elif gpu_percent > 30:
                fps = 30
            else:
                fps = 0
            
            self.current_fps = fps
        
        # Adicionar ao histórico
        self.fps_history.append({
            'timestamp': datetime.now(),
            'fps': self.current_fps
        })
        
        # Manter histórico limitado
        if len(self.fps_history) > self.max_history:
            self.fps_history.pop(0)
        
        return self.current_fps
    
    def get_average_fps(self, seconds: int = 60) -> float:
        """Calcula FPS médio dos últimos X segundos"""
        if not self.fps_history:
            return 0
        
        # Filtrar por tempo
        cutoff = datetime.now().timestamp() - seconds
        recent = [f['fps'] for f in self.fps_history 
                 if f['timestamp'].timestamp() > cutoff]
        
        if not recent:
            return self.current_fps
        
        return sum(recent) / len(recent)
    
    def get_fps_rating(self, fps: float) -> str:
        """Classifica a performance baseada no FPS"""
        if fps >= 60:
            return "Excelente 🟢"
        elif fps >= 45:
            return "Bom 🟡"
        elif fps >= 30:
            return "Regular 🟠"
        else:
            return "Ruim 🔴"
    
    def is_game_running(self) -> bool:
        """Verifica se algum jogo está em execução"""
        games = self.detect_games()
        return len(games) > 0

# Teste rápido
if __name__ == "__main__":
    fps_capture = FPSCapture()
    print(f"MangoHud disponível: {fps_capture.mangohud_available}")
    print(f"Jogos detectados: {fps_capture.detect_games()}")
    print(f"FPS atual: {fps_capture.get_current_fps()}")