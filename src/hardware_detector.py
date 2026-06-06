"""
hardware_detector.py - Detecção automática de hardware para Linux
Suporta: CPU, RAM, GPU NVIDIA/AMD/Intel
"""

import os
import glob
import subprocess
from typing import Dict, Optional, Tuple

class HardwareDetector:
    """Detecta e fornece métricas de hardware no Linux"""
    
    def __init__(self):
        self.gpu_type = None
        self.gpu_handle = None
        self.nvml_available = False
        
        # Detectar GPU ao inicializar
        self._detect_gpu()
        
    def _detect_gpu(self) -> None:
        """Detecta automaticamente o tipo de GPU e inicializa o handler"""
        
        # 1. Tentar NVIDIA via NVML
        try:
            from pynvml import nvmlInit, nvmlDeviceGetHandleByIndex, nvmlShutdown
            nvmlInit()
            self.gpu_type = 'nvidia'
            self.gpu_handle = nvmlDeviceGetHandleByIndex(0)
            self.nvml_available = True
            print(f"[✓] GPU NVIDIA detectada via NVML")
            return
        except ImportError:
            print("[!] pynvml não instalado. NVIDIA não será monitorada.")
        except Exception as e:
            print(f"[!] Erro ao inicializar NVIDIA: {e}")
        
        # 2. Tentar AMD via sysfs
        amd_paths = glob.glob('/sys/class/drm/card*/device/gpu_busy_percent')
        if amd_paths:
            self.gpu_type = 'amd'
            self.gpu_handle = os.path.dirname(amd_paths[0])
            print(f"[✓] GPU AMD detectada via sysfs")
            return
        
        # 3. Tentar Intel integrada via sysfs
        intel_paths = glob.glob('/sys/class/drm/card*/gt_cur_freq_mhz')
        if intel_paths:
            self.gpu_type = 'intel'
            self.gpu_handle = os.path.dirname(intel_paths[0])
            print(f"[✓] GPU Intel detectada via sysfs")
            return
        
        # 4. Tentar via lspci (fallback)
        try:
            result = subprocess.run(['lspci', '-nn', '-d', '::0300'], 
                                  capture_output=True, text=True)
            if 'NVIDIA' in result.stdout:
                self.gpu_type = 'nvidia_fallback'
                print(f"[!] GPU NVIDIA detectada via lspci (driver pode não estar carregado)")
            elif 'AMD' in result.stdout or 'ATI' in result.stdout:
                self.gpu_type = 'amd_fallback'
                print(f"[!] GPU AMD detectada via lspci (driver pode não estar carregado)")
            elif 'Intel' in result.stdout:
                self.gpu_type = 'intel_fallback'
                print(f"[!] GPU Intel detectada via lspci (driver pode não estar carregado)")
            else:
                self.gpu_type = 'unknown'
                print(f"[!] Nenhuma GPU dedicada detectada. Usando apenas CPU/RAM.")
        except Exception as e:
            self.gpu_type = 'unknown'
            print(f"[!] Erro ao executar lspci: {e}")
    
    def get_gpu_metrics(self) -> Dict[str, any]:
        """
        Retorna métricas da GPU detectada
        Estrutura: {'percent': float, 'temp': float, 'vram_percent': float, 
                   'vram_used_mb': float, 'vram_total_mb': float, 'clock_mhz': int}
        """
        metrics = {
            'percent': 0.0,
            'temp': 0.0,
            'vram_percent': 0.0,
            'vram_used_mb': 0.0,
            'vram_total_mb': 0.0,
            'clock_mhz': 0
        }
        
        if self.gpu_type == 'nvidia' and self.nvml_available:
            try:
                from pynvml import nvmlDeviceGetUtilizationRates, nvmlDeviceGetTemperature
                from pynvml import nvmlDeviceGetMemoryInfo, nvmlDeviceGetClockInfo, NVML_CLOCK_GRAPHICS
                
                # Uso da GPU
                util = nvmlDeviceGetUtilizationRates(self.gpu_handle)
                metrics['percent'] = util.gpu
                
                # Temperatura
                metrics['temp'] = nvmlDeviceGetTemperature(self.gpu_handle, 0)  # 0 = GPU temperature
                
                # Memória VRAM
                mem = nvmlDeviceGetMemoryInfo(self.gpu_handle)
                metrics['vram_total_mb'] = mem.total / (1024**2)
                metrics['vram_used_mb'] = mem.used / (1024**2)
                metrics['vram_percent'] = (mem.used / mem.total) * 100
                
                # Clock
                metrics['clock_mhz'] = nvmlDeviceGetClockInfo(self.gpu_handle, NVML_CLOCK_GRAPHICS)
                
            except Exception as e:
                print(f"[!] Erro ao ler métricas NVIDIA: {e}")
        
        elif self.gpu_type == 'amd':
            try:
                # Uso da GPU
                busy_path = os.path.join(self.gpu_handle, 'gpu_busy_percent')
                if os.path.exists(busy_path):
                    with open(busy_path, 'r') as f:
                        metrics['percent'] = int(f.read().strip())
                
                # Temperatura
                temp_paths = glob.glob(os.path.join(self.gpu_handle, 'hwmon/hwmon*/temp*_input'))
                for temp_path in temp_paths:
                    with open(temp_path, 'r') as f:
                        temp_milli = int(f.read().strip())
                        metrics['temp'] = temp_milli / 1000
                        break  # Pega a primeira temperatura encontrada
                
                # Clock (se disponível)
                clock_path = os.path.join(self.gpu_handle, 'pp_dpm_sclk')
                if os.path.exists(clock_path):
                    # Pega o clock atual (formato complexo, simplificado)
                    with open(clock_path, 'r') as f:
                        lines = f.readlines()
                        for line in lines:
                            if '*' in line:  # Linha com * indica clock atual
                                import re
                                clocks = re.findall(r'(\d+)Mhz', line)
                                if clocks:
                                    metrics['clock_mhz'] = int(clocks[0])
                                    break
                
                # VRAM AMD (aproximado via meminfo)
                mem_path = os.path.join(self.gpu_handle, 'mem_info_vram_used')
                if os.path.exists(mem_path):
                    with open(mem_path, 'r') as f:
                        metrics['vram_used_mb'] = int(f.read().strip()) / (1024**2)
                        
                total_path = os.path.join(self.gpu_handle, 'mem_info_vram_total')
                if os.path.exists(total_path):
                    with open(total_path, 'r') as f:
                        metrics['vram_total_mb'] = int(f.read().strip()) / (1024**2)
                        if metrics['vram_total_mb'] > 0:
                            metrics['vram_percent'] = (metrics['vram_used_mb'] / metrics['vram_total_mb']) * 100
                
            except Exception as e:
                print(f"[!] Erro ao ler métricas AMD: {e}")
        
        elif self.gpu_type == 'intel':
            try:
                # Uso da GPU (Intel via sysfs)
                busy_path = os.path.join(self.gpu_handle, 'gt_busy_percent')
                if os.path.exists(busy_path):
                    with open(busy_path, 'r') as f:
                        metrics['percent'] = int(f.read().strip())
                
                # Clock
                clock_path = os.path.join(self.gpu_handle, 'gt_cur_freq_mhz')
                if os.path.exists(clock_path):
                    with open(clock_path, 'r') as f:
                        metrics['clock_mhz'] = int(f.read().strip())
                
                # Temperatura Intel via hwmon
                temp_paths = glob.glob(os.path.join(self.gpu_handle, 'hwmon/hwmon*/temp*_input'))
                for temp_path in temp_paths:
                    with open(temp_path, 'r') as f:
                        temp_milli = int(f.read().strip())
                        metrics['temp'] = temp_milli / 1000
                        break
                
            except Exception as e:
                print(f"[!] Erro ao ler métricas Intel: {e}")
        
        return metrics
    
    def get_gpu_info(self) -> Dict[str, str]:
        """Retorna informações básicas da GPU"""
        info = {
            'type': self.gpu_type,
            'name': 'Desconhecido',
            'driver': 'Não carregado'
        }
        
        if self.gpu_type == 'nvidia' and self.nvml_available:
            try:
                from pynvml import nvmlDeviceGetName
                info['name'] = nvmlDeviceGetName(self.gpu_handle).decode('utf-8')
                info['driver'] = 'nvidia (NVML)'
            except:
                pass
        
        elif self.gpu_type == 'amd':
            try:
                # Tenta pegar nome via lspci
                result = subprocess.run(['lspci', '-nn', '-d', '::0300'], 
                                      capture_output=True, text=True)
                for line in result.stdout.split('\n'):
                    if 'AMD' in line or 'ATI' in line:
                        info['name'] = line.split(':')[2].strip()
                        break
                info['driver'] = 'amdgpu'
            except:
                pass
        
        elif self.gpu_type == 'intel':
            info['name'] = 'Intel Integrated Graphics'
            info['driver'] = 'i915'
        
        return info
    
    def test_monitoring(self) -> bool:
        """Testa se o monitoramento está funcionando"""
        print("\n--- Teste de Monitoramento de Hardware ---")
        print(f"GPU Detectada: {self.gpu_type}")
        
        gpu_info = self.get_gpu_info()
        print(f"Nome: {gpu_info['name']}")
        print(f"Driver: {gpu_info['driver']}")
        
        print("\nMétricas atuais:")
        metrics = self.get_gpu_metrics()
        print(f"  Uso: {metrics['percent']}%")
        print(f"  Temperatura: {metrics['temp']}°C")
        print(f"  VRAM: {metrics['vram_used_mb']:.0f}/{metrics['vram_total_mb']:.0f} MB ({metrics['vram_percent']:.0f}%)")
        print(f"  Clock: {metrics['clock_mhz']} MHz")
        
        return metrics['percent'] >= 0 or metrics['temp'] > 0


# Teste rápido se executado diretamente
if __name__ == "__main__":
    detector = HardwareDetector()
    detector.test_monitoring()