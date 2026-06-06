"""
overlay.py - Overlay transparente com design moderno (Glassmorphism)
"""

import sys
import os
import time
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# Adiciona o diretório raiz ao path para encontrar os módulos
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from monitor import SystemMonitor
from config_loader import ConfigLoader

class OverlayThread(QThread):
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
                print(f"Erro no thread de monitoramento: {e}")
                
    def stop(self):
        self.running = False
        self.wait()

class TransparentOverlay(QWidget):
    def __init__(self):
        super().__init__()
        self.config = ConfigLoader()
        self.monitor = SystemMonitor()
        self.monitor_thread = None
        self.is_monitoring = False
        
        self.setup_overlay()
        self.setup_ui()
        
    def get_stylesheet(self):
        """Estilo visual moderno (QSS - Qt Style Sheets)"""
        return """
        QWidget {
            background-color: rgba(20, 20, 20, 200);
            border: 1px solid rgba(80, 80, 80, 150);
            border-radius: 12px;
            color: #ffffff;
            font-family: 'Segoe UI', sans-serif;
            padding: 5px;
        }
        QLabel {
            background: transparent;
            font-weight: bold;
        }
        QPushButton {
            background-color: rgba(60, 60, 60, 150);
            border-radius: 6px;
            color: white;
            border: none;
        }
        QPushButton:hover {
            background-color: rgba(80, 80, 80, 200);
        }
        """

    def setup_overlay(self):
        opacity = float(self.config.get("overlay", "opacity") or 0.8)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowOpacity(opacity)
            
    def setup_ui(self):
        self.setStyleSheet(self.get_stylesheet())
        
        # Layout principal
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        self.setLayout(layout)
        
        # Botão de Menu
        self.menu_btn = QPushButton("⚙️")
        self.menu_btn.setFixedSize(30, 30)
        self.menu_btn.clicked.connect(self.show_menu)
        layout.addWidget(self.menu_btn)
        
        # Métricas
        self.fps_widget = self.create_metric("FPS", "")
        self.cpu_widget = self.create_metric("CPU", "%")
        self.ram_widget = self.create_metric("RAM", "%")
        self.gpu_widget = self.create_metric("GPU", "%")
        
        layout.addWidget(self.fps_widget)
        layout.addWidget(self.cpu_widget)
        layout.addWidget(self.ram_widget)
        layout.addWidget(self.gpu_widget)
        
        # Botão fechar
        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(30, 30)
        self.close_btn.clicked.connect(self.close_app)
        layout.addWidget(self.close_btn)
        
        # Habilitar arrastar a janela
        self.dragging = False
        self.drag_position = QPoint()
        
    def create_metric(self, label, unit):
        widget = QWidget()
        l = QHBoxLayout(widget)
        l.setContentsMargins(5, 0, 5, 0)
        
        name_lbl = QLabel(f"{label}:")
        name_lbl.setStyleSheet("color: #aaaaaa; font-size: 10px;")
        
        value_lbl = QLabel("0")
        value_lbl.setStyleSheet("color: #4c9f70; font-size: 13px;")
        
        l.addWidget(name_lbl)
        l.addWidget(value_lbl)
        widget.value_label = value_lbl
        return widget
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            
    def mouseMoveEvent(self, event):
        if self.dragging:
            self.move(event.globalPos() - self.drag_position)
            
    def mouseReleaseEvent(self, event):
        self.dragging = False
    
    def show_menu(self):
        menu = QMenu(self)
        quit_action = menu.addAction("❌ Fechar Overlay")
        quit_action.triggered.connect(self.close_app)
        menu.exec_(self.menu_btn.mapToGlobal(self.menu_btn.rect().bottomLeft()))
    
    def update_metrics(self, metrics):
        try:
            # Atualiza FPS
            fps = metrics['fps'].get('current', 0)
            self.fps_widget.value_label.setText(f"{fps:.0f}")
            
            # Atualiza CPU
            cpu = metrics['cpu']['percent']
            self.cpu_widget.value_label.setText(f"{cpu:.0f}")
            
            # Atualiza RAM
            ram = metrics['ram']['percent']
            self.ram_widget.value_label.setText(f"{ram:.0f}")
            
            # Atualiza GPU
            gpu = metrics['gpu']['percent']
            self.gpu_widget.value_label.setText(f"{gpu:.0f}")
        except Exception as e:
            print(f"Erro ao atualizar métricas: {e}")
    
    def start_monitoring(self):
        if self.is_monitoring: return
        self.is_monitoring = True
        self.show()
        self.monitor_thread = OverlayThread(self.monitor)
        self.monitor_thread.metrics_updated.connect(self.update_metrics)
        self.monitor_thread.start()
        
    def close_app(self):
        if self.monitor_thread: self.monitor_thread.stop()
        self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    overlay = TransparentOverlay()
    overlay.start_monitoring()
    sys.exit(app.exec_())