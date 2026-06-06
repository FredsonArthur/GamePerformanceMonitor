"""
logger.py - Sistema de logging para salvar métricas em CSV
Permite salvar, carregar e analisar dados de performance
"""

import csv
import os
import json
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

class PerformanceLogger:
    """Gerencia o salvamento e carregamento de métricas de performance"""
    
    def __init__(self, log_dir: str = "logs"):
        """
        Inicializa o logger
        
        Args:
            log_dir: Diretório onde os logs serão salvos
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.current_session_file = None
        self.csv_writer = None
        self.csv_file = None
        self.is_logging = False
        
    def start_session(self, session_name: Optional[str] = None) -> str:
        """
        Inicia uma nova sessão de logging
        
        Args:
            session_name: Nome da sessão (opcional)
        
        Returns:
            Nome do arquivo criado
        """
        if session_name is None:
            session_name = f"performance_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.current_session_file = self.log_dir / f"{session_name}.csv"
        
        # Criar arquivo CSV com cabeçalhos
        self.csv_file = open(self.current_session_file, 'w', newline='', encoding='utf-8')
        fieldnames = self._get_csv_headers()
        self.csv_writer = csv.DictWriter(self.csv_file, fieldnames=fieldnames)
        self.csv_writer.writeheader()
        
        self.is_logging = True
        print(f"✅ Sessão de logging iniciada: {self.current_session_file}")
        return str(self.current_session_file)
    
    def _get_csv_headers(self) -> List[str]:
        """Retorna os cabeçalhos do arquivo CSV"""
        return [
            'timestamp',
            # CPU
            'cpu_percent',
            'cpu_temperature',
            'cpu_frequency',
            # RAM
            'ram_percent',
            'ram_used_gb',
            'ram_total_gb',
            # GPU
            'gpu_percent',
            'gpu_temperature',
            'gpu_vram_percent',
            'gpu_vram_used_mb',
            'gpu_vram_total_mb',
            'gpu_clock_mhz',
            # Disco
            'disk_read_speed_mb_s',
            'disk_write_speed_mb_s',
            # Rede
            'network_download_speed_mb_s',
            'network_upload_speed_mb_s',
            # Sistema
            'load_average_1min',
            'load_average_5min',
            'load_average_15min'
        ]
    
    def log_metrics(self, metrics: Dict[str, any]) -> None:
        """
        Salva um conjunto de métricas no CSV
        
        Args:
            metrics: Dicionário com métricas do SystemMonitor
        """
        if not self.is_logging:
            print("⚠️ Logger não está ativo. Use start_session() primeiro.")
            return
        
        # Extrair métricas de forma plana para CSV
        row = {
            'timestamp': metrics['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
            
            # CPU
            'cpu_percent': metrics['cpu']['percent'],
            'cpu_temperature': metrics['cpu'].get('temperature', 0),
            'cpu_frequency': metrics['cpu'].get('frequency', 0),
            
            # RAM
            'ram_percent': metrics['ram']['percent'],
            'ram_used_gb': round(metrics['ram']['used_gb'], 2),
            'ram_total_gb': round(metrics['ram']['total_gb'], 2),
            
            # GPU
            'gpu_percent': metrics['gpu']['percent'],
            'gpu_temperature': metrics['gpu']['temp'],
            'gpu_vram_percent': round(metrics['gpu']['vram_percent'], 2),
            'gpu_vram_used_mb': round(metrics['gpu']['vram_used_mb'], 2),
            'gpu_vram_total_mb': round(metrics['gpu']['vram_total_mb'], 2),
            'gpu_clock_mhz': metrics['gpu']['clock_mhz'],
            
            # Disco
            'disk_read_speed_mb_s': round(metrics['disk']['read_speed_mb_s'], 2),
            'disk_write_speed_mb_s': round(metrics['disk']['write_speed_mb_s'], 2),
            
            # Rede
            'network_download_speed_mb_s': round(metrics['network']['download_speed_mb_s'], 2),
            'network_upload_speed_mb_s': round(metrics['network']['upload_speed_mb_s'], 2),
            
            # Sistema
            'load_average_1min': round(metrics['cpu']['load_average'][0], 2),
            'load_average_5min': round(metrics['cpu']['load_average'][1], 2),
            'load_average_15min': round(metrics['cpu']['load_average'][2], 2)
        }
        
        self.csv_writer.writerow(row)
        self.csv_file.flush()  # Garante que os dados sejam escritos no disco
        
    def stop_session(self) -> None:
        """Finaliza a sessão atual de logging"""
        if self.csv_file:
            self.csv_file.close()
            self.is_logging = False
            print(f"✅ Sessão de logging finalizada: {self.current_session_file}")
    
    def list_sessions(self) -> List[Dict[str, any]]:
        """
        Lista todas as sessões de log disponíveis
        
        Returns:
            Lista de dicionários com informações das sessões
        """
        sessions = []
        for file in self.log_dir.glob("*.csv"):
            stat = file.stat()
            sessions.append({
                'name': file.stem,
                'file': str(file),
                'size_mb': round(stat.st_size / (1024 * 1024), 2),
                'modified': datetime.fromtimestamp(stat.st_mtime)
            })
        
        # Ordenar por data (mais recente primeiro)
        sessions.sort(key=lambda x: x['modified'], reverse=True)
        return sessions
    
    def load_session(self, session_name: str) -> List[Dict]:
        """
        Carrega os dados de uma sessão específica
        
        Args:
            session_name: Nome do arquivo (sem extensão)
        
        Returns:
            Lista de dicionários com os dados
        """
        file_path = self.log_dir / f"{session_name}.csv"
        
        if not file_path.exists():
            raise FileNotFoundError(f"Sessão {session_name} não encontrada")
        
        data = []
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                data.append(row)
        
        return data
    
    def get_session_summary(self, session_name: str) -> Dict[str, any]:
        """
        Gera um resumo estatístico de uma sessão
        
        Args:
            session_name: Nome da sessão
        
        Returns:
            Dicionário com estatísticas da sessão
        """
        data = self.load_session(session_name)
        
        if not data:
            return {}
        
        summary = {
            'session': session_name,
            'duration_seconds': len(data),
            'start_time': data[0]['timestamp'],
            'end_time': data[-1]['timestamp'],
            'cpu': {
                'avg': 0,
                'max': 0,
                'min': 100
            },
            'gpu': {
                'avg': 0,
                'max': 0,
                'min': 100
            },
            'ram': {
                'avg': 0,
                'max': 0,
                'min': 100
            }
        }
        
        # Calcular estatísticas
        for row in data:
            cpu_val = float(row['cpu_percent'])
            gpu_val = float(row['gpu_percent'])
            ram_val = float(row['ram_percent'])
            
            summary['cpu']['avg'] += cpu_val
            summary['cpu']['max'] = max(summary['cpu']['max'], cpu_val)
            summary['cpu']['min'] = min(summary['cpu']['min'], cpu_val)
            
            summary['gpu']['avg'] += gpu_val
            summary['gpu']['max'] = max(summary['gpu']['max'], gpu_val)
            summary['gpu']['min'] = min(summary['gpu']['min'], gpu_val)
            
            summary['ram']['avg'] += ram_val
            summary['ram']['max'] = max(summary['ram']['max'], ram_val)
            summary['ram']['min'] = min(summary['ram']['min'], ram_val)
        
        # Calcular médias
        count = len(data)
        summary['cpu']['avg'] = round(summary['cpu']['avg'] / count, 2)
        summary['gpu']['avg'] = round(summary['gpu']['avg'] / count, 2)
        summary['ram']['avg'] = round(summary['ram']['avg'] / count, 2)
        
        return summary
    
    def export_to_json(self, session_name: str) -> str:
        """
        Exporta uma sessão para formato JSON
        
        Args:
            session_name: Nome da sessão
        
        Returns:
            Caminho do arquivo JSON criado
        """
        data = self.load_session(session_name)
        json_path = self.log_dir / f"{session_name}.json"
        
        with open(json_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=2, ensure_ascii=False)
        
        print(f"✅ Dados exportados para JSON: {json_path}")
        return str(json_path)


# Teste rápido se executado diretamente
if __name__ == "__main__":
    print("Testando PerformanceLogger...")
    
    # Criar logger
    logger = PerformanceLogger()
    
    # Iniciar sessão de teste
    logger.start_session("test_session")
    
    # Simular alguns dados
    import time
    from datetime import datetime
    
    for i in range(5):
        # Criar métricas de exemplo
        test_metrics = {
            'timestamp': datetime.now(),
            'cpu': {
                'percent': 20 + i * 5,
                'temperature': 45 + i,
                'frequency': 2400,
                'load_average': (1.5, 1.2, 1.0)
            },
            'ram': {
                'percent': 40,
                'used_gb': 6.4,
                'total_gb': 16.0
            },
            'gpu': {
                'percent': 15 + i * 3,
                'temp': 50 + i,
                'vram_percent': 30,
                'vram_used_mb': 1843,
                'vram_total_mb': 6144,
                'clock_mhz': 1500
            },
            'disk': {
                'read_speed_mb_s': 10.5,
                'write_speed_mb_s': 5.2
            },
            'network': {
                'download_speed_mb_s': 2.3,
                'upload_speed_mb_s': 0.8
            }
        }
        
        logger.log_metrics(test_metrics)
        print(f"  ✅ Log {i+1} salvo")
        time.sleep(1)
    
    # Finalizar sessão
    logger.stop_session()
    
    # Listar sessões
    print("\n📁 Sessões disponíveis:")
    sessions = logger.list_sessions()
    for session in sessions:
        print(f"  - {session['name']} ({session['size_mb']} MB) - {session['modified'].strftime('%Y-%m-%d %H:%M')}")
    
    # Mostrar resumo
    print("\n📊 Resumo da sessão de teste:")
    summary = logger.get_session_summary("test_session")
    if summary:
        print(f"  Duração: {summary['duration_seconds']} segundos")
        print(f"  CPU: média {summary['cpu']['avg']}% (max {summary['cpu']['max']}%)")
        print(f"  GPU: média {summary['gpu']['avg']}% (max {summary['gpu']['max']}%)")
        print(f"  RAM: média {summary['ram']['avg']}% (max {summary['ram']['max']}%)")
    
    print("\n✅ Teste concluído!")