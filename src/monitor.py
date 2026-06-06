"""
monitor.py - Coleta todas as métricas do sistema em tempo real
Suporta: CPU, RAM, GPU, Disco, Rede, Temperaturas
"""

import psutil
import time
from datetime import datetime
from typing import Dict, List, Optional
from hardware_detector import HardwareDetector

class SystemMonitor:
    """Monitor principal que coleta todas as métricas do sistema"""
    
    def __init__(self):
        self.hardware = HardwareDetector()
        self.previous_net = psutil.net_io_counters()
        self.previous_disk = psutil.disk_io_counters()
        self.last_net_time = time.time()
        self.last_disk_time = time.time()
        
    def get_cpu_metrics(self) -> Dict[str, any]:
        """Coleta métricas da CPU"""
        metrics = {
            'percent': psutil.cpu_percent(interval=0.1),
            'percent_per_core': psutil.cpu_percent(percpu=True),
            'frequency': psutil.cpu_freq().current if psutil.cpu_freq() else 0,
            'temperature': 0.0,
            'load_average': psutil.getloadavg()
        }
        
        # Tentar obter temperatura da CPU
        try:
            temps = psutil.sensors_temperatures()
            if 'coretemp' in temps:  # Intel/AMD via coretemp
                metrics['temperature'] = temps['coretemp'][0].current
            elif 'cpu_thermal' in temps:  # Raspberry Pi / alguns sistemas
                metrics['temperature'] = temps['cpu_thermal'][0].current
            elif 'k10temp' in temps:  # AMD
                metrics['temperature'] = temps['k10temp'][0].current
        except:
            pass  # Temperatura não disponível
        
        return metrics
    
    def get_ram_metrics(self) -> Dict[str, any]:
        """Coleta métricas da RAM"""
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        metrics = {
            'total_gb': mem.total / (1024**3),
            'available_gb': mem.available / (1024**3),
            'used_gb': mem.used / (1024**3),
            'percent': mem.percent,
            'swap_total_gb': swap.total / (1024**3),
            'swap_used_gb': swap.used / (1024**3),
            'swap_percent': swap.percent
        }
        
        return metrics
    
    def get_disk_metrics(self) -> Dict[str, any]:
        """Coleta métricas de disco (velocidade de leitura/escrita)"""
        current_time = time.time()
        current_disk = psutil.disk_io_counters()
        
        # Calcular velocidade (bytes por segundo)
        time_diff = current_time - self.last_disk_time
        if time_diff > 0:
            read_speed = (current_disk.read_bytes - self.previous_disk.read_bytes) / time_diff
            write_speed = (current_disk.write_bytes - self.previous_disk.write_bytes) / time_diff
        else:
            read_speed = 0
            write_speed = 0
        
        # Atualizar para próxima leitura
        self.previous_disk = current_disk
        self.last_disk_time = current_time
        
        metrics = {
            'read_speed_mb_s': read_speed / (1024**2),
            'write_speed_mb_s': write_speed / (1024**2),
            'total_read_gb': current_disk.read_bytes / (1024**3),
            'total_write_gb': current_disk.write_bytes / (1024**3),
            'read_count': current_disk.read_count,
            'write_count': current_disk.write_count
        }
        
        return metrics
    
    def get_network_metrics(self) -> Dict[str, any]:
        """Coleta métricas de rede (velocidade de download/upload)"""
        current_time = time.time()
        current_net = psutil.net_io_counters()
        
        # Calcular velocidade (bytes por segundo)
        time_diff = current_time - self.last_net_time
        if time_diff > 0:
            download_speed = (current_net.bytes_recv - self.previous_net.bytes_recv) / time_diff
            upload_speed = (current_net.bytes_sent - self.previous_net.bytes_sent) / time_diff
        else:
            download_speed = 0
            upload_speed = 0
        
        # Atualizar para próxima leitura
        self.previous_net = current_net
        self.last_net_time = current_time
        
        metrics = {
            'download_speed_mb_s': download_speed / (1024**2),
            'upload_speed_mb_s': upload_speed / (1024**2),
            'total_download_gb': current_net.bytes_recv / (1024**3),
            'total_upload_gb': current_net.bytes_sent / (1024**3),
            'packets_sent': current_net.packets_sent,
            'packets_recv': current_net.packets_recv
        }
        
        return metrics
    
    def get_process_metrics(self, top_n: int = 5) -> List[Dict]:
        """Coleta métricas dos processos com maior uso de CPU"""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                proc_info = proc.info
                if proc_info['cpu_percent'] > 0:  # Só processos ativos
                    processes.append({
                        'pid': proc_info['pid'],
                        'name': proc_info['name'],
                        'cpu_percent': proc_info['cpu_percent'],
                        'memory_percent': proc_info['memory_percent']
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # Ordenar por uso de CPU e pegar os top N
        processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
        return processes[:top_n]
    
    def get_all_metrics(self) -> Dict[str, any]:
        """Coleta TODAS as métricas de uma vez"""
        cpu = self.get_cpu_metrics()
        ram = self.get_ram_metrics()
        gpu = self.hardware.get_gpu_metrics()
        disk = self.get_disk_metrics()
        network = self.get_network_metrics()
        processes = self.get_process_metrics()
        
        metrics = {
            'timestamp': datetime.now(),
            'cpu': cpu,
            'ram': ram,
            'gpu': gpu,
            'disk': disk,
            'network': network,
            'processes': processes,
            'system_info': {
                'hostname': psutil.users()[0].host if psutil.users() else 'unknown',
                'boot_time': datetime.fromtimestamp(psutil.boot_time()),
                'users': len(psutil.users())
            }
        }
        
        return metrics
    
    def print_metrics(self, metrics: Dict[str, any]):
        """Exibe métricas formatadas no console (para debug)"""
        print(f"\n{'='*60}")
        print(f"[{metrics['timestamp'].strftime('%H:%M:%S')}]")
        print(f"{'='*60}")
        
        # CPU
        print(f"CPU: {metrics['cpu']['percent']}% ", end='')
        if metrics['cpu']['temperature'] > 0:
            print(f"🌡️ {metrics['cpu']['temperature']:.0f}°C ", end='')
        print(f"⚡ {metrics['cpu']['frequency']:.0f}MHz")
        
        # RAM
        print(f"RAM: {metrics['ram']['percent']}% ({metrics['ram']['used_gb']:.1f}/{metrics['ram']['total_gb']:.1f} GB)")
        
        # GPU
        if metrics['gpu']['percent'] > 0:
            print(f"GPU: {metrics['gpu']['percent']}% ", end='')
            if metrics['gpu']['temp'] > 0:
                print(f"🌡️ {metrics['gpu']['temp']:.0f}°C ", end='')
            if metrics['gpu']['vram_total_mb'] > 0:
                print(f"💾 {metrics['gpu']['vram_used_mb']:.0f}/{metrics['gpu']['vram_total_mb']:.0f} MB")
            else:
                print()
        
        # Disco
        print(f"💾 Disco: ↓{metrics['disk']['read_speed_mb_s']:.1f} MB/s ↑{metrics['disk']['write_speed_mb_s']:.1f} MB/s")
        
        # Rede
        print(f"🌐 Rede: ↓{metrics['network']['download_speed_mb_s']:.1f} MB/s ↑{metrics['network']['upload_speed_mb_s']:.1f} MB/s")
        
        # Top processos
        print(f"\n📊 Top processos (CPU):")
        for i, proc in enumerate(metrics['processes'], 1):
            print(f"  {i}. {proc['name']:<20} CPU: {proc['cpu_percent']:.1f}%  RAM: {proc['memory_percent']:.1f}%")

# Teste rápido se executado diretamente
if __name__ == "__main__":
    print("Iniciando monitor de sistema...")
    monitor = SystemMonitor()
    
    try:
        while True:
            metrics = monitor.get_all_metrics()
            monitor.print_metrics(metrics)
            time.sleep(2)  # Atualiza a cada 2 segundos
    except KeyboardInterrupt:
        print("\n\nMonitoramento encerrado.")