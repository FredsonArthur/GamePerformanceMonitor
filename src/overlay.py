"""
overlay.py - Janela flutuante transparente para mostrar métricas durante o jogo
Suporta: Posição arrastável, sempre no topo, fundo transparente
"""

import sys
import os
import time
from datetime import datetime

# Adiciona o diretório src ao path
sys.path.insert(0, os.path.dirname(__file__))

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from monitor import SystemMonitor
from logger import PerformanceLogger

class OverlayThread(QThread):
    """Thread separada para monitoramento no overlay"""
    metrics_updated = pyqtSignal(dict)
    
    def __init__(self, monitor, interval=1):
        super().__init__()
        self.monitor = monitor
        self.interval = interval
        self.running = False
        
    def run(self):
        self.running = True
        while self.running:
            try:
                metrics = self.monitor.get_all_metrics()
                self.metrics_updated.emit(metrics)
                time.sleep(self.interval)
            except Exception as e:
                print(f"Erro no monitoramento do overlay: {e}")
                
    def stop(self):
        self.running = False
        self.wait()

class OverlayWindow(QWidget):
    """Janela flutuante transparente para overlay de jogos"""
    
    def __init__(self):
        super().__init__()
        self.monitor = SystemMonitor()
        self.monitor_thread = None
        self.is_monitoring = False
        self.dragging = False
        self.drag_position = QPoint()
        
        self.setup_overlay_properties()
        self.setup_ui()
        
    def setup_overlay_properties(self):
        """Configura propriedades da janela overlay"""
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen.width() - 300, 100, 280, 220)
        
    def setup_ui(self):
        """Configura os elementos da interface do overlay"""
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)
        self.setLayout(layout)
        
        self.frame = QFrame()
        self.frame.setStyleSheet("""
            QFrame {
                background-color: rgba(0, 0, 0, 180);
                border-radius: 10px;
                border: 1px solid #4c9f70;
            }
            QLabel {
                color: #4c9f70;
                font-family: 'Monospace';
                font-size: 11px;
                padding: 2px;
            }
        """)
        
        frame_layout = QVBoxLayout(self.frame)
        frame_layout.setContentsMargins(10, 10, 10, 10)
        
        # Título
        title_layout = QHBoxLayout()
        title_label = QLabel("🎮 GamePerformanceMonitor")
        title_label.setStyleSheet("font-weight: bold; font-size: 12px; color: #4c9f70;")
        title_layout.addWidget(title_label)
        
        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(20, 20)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff4444;
                color: white;
                border-radius: 10px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ff6666;
            }
        """)
        self.close_btn.clicked.connect(self.hide_overlay)
        title_layout.addWidget(self.close_btn)
        
        frame_layout.addLayout(title_layout)
        
        # Linha separadora
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #4c9f70; max-height: 1px;")
        frame_layout.addWidget(line)
        
        # Labels para métricas
        self.fps_label = QLabel("🎮 FPS: --")
        self.fps_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        frame_layout.addWidget(self.fps_label)
        
        self.cpu_label = QLabel("CPU: --%  🌡️ --°C")
        frame_layout.addWidget(self.cpu_label)
        
        self.ram_label = QLabel("RAM: --%  💾 --/-- GB")
        frame_layout.addWidget(self.ram_label)
        
        self.gpu_label = QLabel("GPU: --%  🌡️ --°C")
        frame_layout.addWidget(self.gpu_label)
        
        self.vram_label = QLabel("VRAM: --/-- MB")
        frame_layout.addWidget(self.vram_label)
        
        self.net_label = QLabel("🌐 ↓-- KB/s  ↑-- KB/s")
        frame_layout.addWidget(self.net_label)
        
        self.recording_label = QLabel("⚪ Não gravando")
        self.recording_label.setStyleSheet("color: #888888; font-size: 9px;")
        frame_layout.addWidget(self.recording_label)
        
        layout.addWidget(self.frame)
        
        # Tornar arrastável
        self.frame.mousePressEvent = self.mouse_press_event
        self.frame.mouseMoveEvent = self.mouse_move_event
        self.frame.mouseReleaseEvent = self.mouse_release_event
        title_label.mousePressEvent = self.mouse_press_event
        title_label.mouseMoveEvent = self.mouse_move_event
        title_label.mouseReleaseEvent = self.mouse_release_event
        
    def mouse_press_event(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
            
    def mouse_move_event(self, event):
        if self.dragging:
            self.move(event.globalPos() - self.drag_position)
            event.accept()
            
    def mouse_release_event(self, event):
        self.dragging = False
        event.accept()
        
    def update_metrics(self, metrics):
        """Atualiza as métricas no overlay"""
        try:
            # CPU
            cpu_percent = metrics['cpu']['percent']
            cpu_temp = metrics['cpu'].get('temperature', 0)
            self.cpu_label.setText(f"CPU: {cpu_percent:.0f}%  🌡️ {cpu_temp:.0f}°C")
            
            if cpu_percent > 80:
                self.cpu_label.setStyleSheet("color: #ff4444;")
            elif cpu_percent > 60:
                self.cpu_label.setStyleSheet("color: #ffaa44;")
            else:
                self.cpu_label.setStyleSheet("color: #4c9f70;")
            
            # RAM
            ram_percent = metrics['ram']['percent']
            ram_used = metrics['ram']['used_gb']
            ram_total = metrics['ram']['total_gb']
            self.ram_label.setText(f"RAM: {ram_percent:.0f}%  💾 {ram_used:.1f}/{ram_total:.1f} GB")
            
            if ram_percent > 80:
                self.ram_label.setStyleSheet("color: #ff4444;")
            elif ram_percent > 60:
                self.ram_label.setStyleSheet("color: #ffaa44;")
            else:
                self.ram_label.setStyleSheet("color: #4c9f70;")
            
            # FPS
            if metrics.get('fps') and metrics['fps'].get('game_running', False):
                fps_current = metrics['fps'].get('current', 0)
                self.fps_label.setText(f"🎮 FPS: {fps_current:.1f}")
                self.fps_label.setVisible(True)
                
                if fps_current >= 60:
                    self.fps_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #4c9f70;")
                elif fps_current >= 45:
                    self.fps_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #ffaa44;")
                elif fps_current >= 30:
                    self.fps_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #ff8844;")
                else:
                    self.fps_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #ff4444;")
            else:
                self.fps_label.setText("🎮 FPS: --")
                self.fps_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #888888;")
                self.fps_label.setVisible(True)
            
            # GPU
            gpu_percent = metrics['gpu']['percent']
            gpu_temp = metrics['gpu']['temp']
            if gpu_percent > 0:
                self.gpu_label.setText(f"GPU: {gpu_percent:.0f}%  🌡️ {gpu_temp:.0f}°C")
                self.gpu_label.setVisible(True)
                self.vram_label.setVisible(True)
                
                if gpu_percent > 80:
                    self.gpu_label.setStyleSheet("color: #ff4444;")
                elif gpu_percent > 60:
                    self.gpu_label.setStyleSheet("color: #ffaa44;")
                else:
                    self.gpu_label.setStyleSheet("color: #4c9f70;")
                
                if metrics['gpu']['vram_total_mb'] > 0:
                    vram_used = metrics['gpu']['vram_used_mb']
                    vram_total = metrics['gpu']['vram_total_mb']
                    self.vram_label.setText(f"VRAM: {vram_used:.0f}/{vram_total:.0f} MB")
                    self.vram_label.setVisible(True)
                else:
                    self.vram_label.setVisible(False)
            else:
                self.gpu_label.setVisible(False)
                self.vram_label.setVisible(False)
            
            # Rede
            download = metrics['network']['download_speed_mb_s'] * 1024
            upload = metrics['network']['upload_speed_mb_s'] * 1024
            self.net_label.setText(f"🌐 ↓{download:.0f} KB/s  ↑{upload:.0f} KB/s")
            
            if download < 1 and upload < 1:
                self.net_label.setStyleSheet("color: #888888;")
            else:
                self.net_label.setStyleSheet("color: #4c9f70;")
                
        except Exception as e:
            print(f"Erro ao atualizar overlay: {e}")
    
    def set_recording_status(self, is_recording, session_name=None):
        """Atualiza status de gravação no overlay"""
        if is_recording:
            self.recording_label.setText(f"🔴 Gravando: {session_name}")
            self.recording_label.setStyleSheet("color: #ff4444; font-size: 9px;")
        else:
            self.recording_label.setText("⚪ Não gravando")
            self.recording_label.setStyleSheet("color: #888888; font-size: 9px;")
    
    def start_monitoring(self, save_logs=False):
        """Inicia o monitoramento em thread separada"""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        self.show()
        
        self.monitor_thread = OverlayThread(self.monitor, interval=1)
        self.monitor_thread.metrics_updated.connect(self.update_metrics)
        self.monitor_thread.start()
        
    def stop_monitoring(self):
        """Para o monitoramento"""
        self.is_monitoring = False
        
        if self.monitor_thread:
            self.monitor_thread.stop()
            self.monitor_thread = None
        
        self.hide()
    
    def hide_overlay(self):
        """Esconde o overlay"""
        self.stop_monitoring()


class OverlayController:
    """Controlador para gerenciar o overlay e logging"""
    
    def __init__(self):
        self.overlay = None
        self.logger = None
        self.is_recording = False
        self.current_session = None
        
    def start(self, save_logs=False, session_name=None):
        """Inicia o overlay com opção de salvar logs"""
        if self.overlay is None:
            self.overlay = OverlayWindow()
        
        if save_logs:
            if self.logger is None:
                self.logger = PerformanceLogger()
            
            if session_name is None:
                session_name = f"overlay_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            self.current_session = self.logger.start_session(session_name)
            self.is_recording = True
            self.overlay.set_recording_status(True, session_name)
        else:
            self.overlay.set_recording_status(False)
        
        self.overlay.start_monitoring(save_logs)
        return self.current_session
    
    def stop(self):
        """Para o overlay e finaliza logging"""
        if self.overlay:
            self.overlay.stop_monitoring()
        
        if self.is_recording and self.logger:
            self.logger.stop_session()
            self.is_recording = False
            
        self.current_session = None
    
    def show(self):
        """Mostra o overlay"""
        if self.overlay:
            self.overlay.show()
    
    def hide(self):
        """Esconde o overlay"""
        if self.overlay:
            self.overlay.hide()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    controller = OverlayController()
    controller.start(save_logs=False)
    print("Overlay iniciado! Clique e arraste para mover.")
    print("Pressione Ctrl+C no terminal para fechar.")
    sys.exit(app.exec_())