"""
overlay.py - Overlay horizontal elegante para monitoramento de jogos
"""

import sys
import os
import json
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from monitor import SystemMonitor
from logger import PerformanceLogger

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
                print(f"Erro no monitoramento: {e}")
                
    def stop(self):
        self.running = False
        self.wait()


class ModernOverlayWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.monitor = SystemMonitor()
        self.monitor_thread = None
        self.is_monitoring = False
        self.dragging = False
        self.drag_position = QPoint()
        
        # Configurações
        self.metrics_enabled = {
            'fps': True,
            'cpu': True,
            'ram': True,
            'gpu': True,
            'network': True
        }
        
        self.setup_overlay_properties()
        self.setup_ui()
        
    def setup_overlay_properties(self):
        # Janela totalmente transparente, sem bordas
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool |
            Qt.WindowTransparentForInput  # Clica através da janela
        )
        
        # Remover essa linha se quiser interagir com o overlay
        # self.setAttribute(Qt.WA_TranslucentBackground)
        
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen.width() - 450, 60, 440, 50)
        
    def setup_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)
        
        # Container principal com fundo semi-transparente
        self.container = QFrame()
        self.container.setStyleSheet("""
            QFrame {
                background-color: rgba(20, 20, 30, 180);
                border-radius: 25px;
                border: 1px solid rgba(76, 159, 112, 100);
            }
        """)
        
        container_layout = QHBoxLayout(self.container)
        container_layout.setContentsMargins(15, 8, 15, 8)
        container_layout.setSpacing(20)
        
        # Botão de menu
        self.menu_btn = QPushButton("⚙️")
        self.menu_btn.setFixedSize(32, 32)
        self.menu_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(76, 159, 112, 80);
                color: #4c9f70;
                border-radius: 16px;
                font-size: 16px;
                border: none;
            }
            QPushButton:hover {
                background-color: rgba(76, 159, 112, 150);
                color: white;
            }
        """)
        self.menu_btn.clicked.connect(self.show_menu)
        container_layout.addWidget(self.menu_btn)
        
        # Separador
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setStyleSheet("background-color: rgba(76, 159, 112, 80); max-width: 1px;")
        container_layout.addWidget(sep)
        
        # FPS
        self.fps_widget = self.create_metric_widget("🎮", "FPS", "0")
        container_layout.addWidget(self.fps_widget)
        
        # CPU
        self.cpu_widget = self.create_metric_widget("🖥️", "CPU", "0%")
        container_layout.addWidget(self.cpu_widget)
        
        # RAM
        self.ram_widget = self.create_metric_widget("💾", "RAM", "0%")
        container_layout.addWidget(self.ram_widget)
        
        # GPU
        self.gpu_widget = self.create_metric_widget("🎮", "GPU", "0%")
        container_layout.addWidget(self.gpu_widget)
        
        # Rede
        self.net_widget = self.create_metric_widget("🌐", "NET", "0KB/s")
        container_layout.addWidget(self.net_widget)
        
        # Botão fechar
        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(28, 28)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 68, 68, 100);
                color: #ff8888;
                border-radius: 14px;
                font-size: 14px;
                border: none;
            }
            QPushButton:hover {
                background-color: rgba(255, 68, 68, 200);
                color: white;
            }
        """)
        self.close_btn.clicked.connect(self.close_app)
        container_layout.addWidget(self.close_btn)
        
        layout.addWidget(self.container)
        
        # Tornar arrastável
        self.container.mousePressEvent = self.mouse_press_event
        self.container.mouseMoveEvent = self.mouse_move_event
        self.container.mouseReleaseEvent = self.mouse_release_event
        
        # Atualizar visibilidade
        self.update_visibility()
        
        # Timer para efeito de brilho
        self.glow_timer = QTimer()
        self.glow_timer.timeout.connect(self.update_glow)
        self.glow_timer.start(500)
        self.glow = False
        
    def create_metric_widget(self, icon, label, unit):
        """Cria um widget de métrica horizontal"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(5, 0, 5, 0)
        layout.setSpacing(6)
        
        # Ícone
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 14px;")
        layout.addWidget(icon_label)
        
        # Nome
        name_label = QLabel(label)
        name_label.setStyleSheet("color: #aaaaaa; font-size: 10px; font-weight: 500;")
        layout.addWidget(name_label)
        
        # Valor
        value_label = QLabel("0")
        value_label.setStyleSheet("color: #4c9f70; font-size: 14px; font-weight: bold; font-family: 'Monospace';")
        layout.addWidget(value_label)
        
        # Unidade
        unit_label = QLabel(unit)
        unit_label.setStyleSheet("color: #666666; font-size: 9px;")
        layout.addWidget(unit_label)
        
        widget.value_label = value_label
        widget.unit = unit
        
        return widget
    
    def update_visibility(self):
        """Atualiza visibilidade dos widgets"""
        self.fps_widget.setVisible(self.metrics_enabled.get('fps', True))
        self.cpu_widget.setVisible(self.metrics_enabled.get('cpu', True))
        self.ram_widget.setVisible(self.metrics_enabled.get('ram', True))
        self.gpu_widget.setVisible(self.metrics_enabled.get('gpu', True))
        self.net_widget.setVisible(self.metrics_enabled.get('network', True))
        
        # Ajustar largura
        self.adjustSize()
    
    def update_glow(self):
        """Efeito de brilho no FPS quando jogo está rodando"""
        self.glow = not self.glow
        if hasattr(self, 'has_game') and self.has_game:
            color = "#4cff70" if self.glow else "#4c9f70"
            self.fps_widget.value_label.setStyleSheet(f"color: {color}; font-size: 16px; font-weight: bold;")
    
    def show_menu(self):
        """Mostra menu de configurações"""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #1e1e2e;
                color: white;
                border: 1px solid #4c9f70;
                border-radius: 12px;
                padding: 8px;
            }
            QMenu::item {
                padding: 8px 30px 8px 15px;
                border-radius: 6px;
            }
            QMenu::item:selected {
                background-color: #4c9f70;
            }
            QMenu::item:checked {
                background-color: #4c9f70;
            }
        """)
        
        # Seção de métricas
        metrics_menu = menu.addMenu("📊 Métricas")
        metrics_menu.setStyleSheet(menu.styleSheet())
        
        fps_action = QAction("🎮 FPS", metrics_menu)
        fps_action.setCheckable(True)
        fps_action.setChecked(self.metrics_enabled.get('fps', True))
        fps_action.triggered.connect(lambda: self.toggle_metric('fps'))
        metrics_menu.addAction(fps_action)
        
        cpu_action = QAction("🖥️ CPU", metrics_menu)
        cpu_action.setCheckable(True)
        cpu_action.setChecked(self.metrics_enabled.get('cpu', True))
        cpu_action.triggered.connect(lambda: self.toggle_metric('cpu'))
        metrics_menu.addAction(cpu_action)
        
        ram_action = QAction("💾 RAM", metrics_menu)
        ram_action.setCheckable(True)
        ram_action.setChecked(self.metrics_enabled.get('ram', True))
        ram_action.triggered.connect(lambda: self.toggle_metric('ram'))
        metrics_menu.addAction(ram_action)
        
        gpu_action = QAction("🎮 GPU", metrics_menu)
        gpu_action.setCheckable(True)
        gpu_action.setChecked(self.metrics_enabled.get('gpu', True))
        gpu_action.triggered.connect(lambda: self.toggle_metric('gpu'))
        metrics_menu.addAction(gpu_action)
        
        net_action = QAction("🌐 Rede", metrics_menu)
        net_action.setCheckable(True)
        net_action.setChecked(self.metrics_enabled.get('network', True))
        net_action.triggered.connect(lambda: self.toggle_metric('network'))
        metrics_menu.addAction(net_action)
        
        menu.addSeparator()
        
        # Transparência
        opacity_menu = menu.addMenu("🎨 Transparência")
        for op in [180, 200, 220, 240]:
            action = QAction(f"{int((op/255)*100)}%", opacity_menu)
            action.triggered.connect(lambda checked, o=op: self.change_opacity(o))
            opacity_menu.addAction(action)
        
        menu.addSeparator()
        
        # Sair
        quit_action = QAction("❌ Fechar Overlay", menu)
        quit_action.triggered.connect(self.close_app)
        menu.addAction(quit_action)
        
        menu.exec_(self.menu_btn.mapToGlobal(self.menu_btn.rect().bottomLeft()))
    
    def toggle_metric(self, metric):
        self.metrics_enabled[metric] = not self.metrics_enabled[metric]
        self.update_visibility()
        self.save_settings()
    
    def change_opacity(self, opacity):
        self.container.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(20, 20, 30, {opacity});
                border-radius: 25px;
                border: 1px solid rgba(76, 159, 112, 100);
            }}
        """)
        self.save_settings()
    
    def save_settings(self):
        settings = {
            'metrics': self.metrics_enabled,
            'opacity': 180
        }
        try:
            with open(os.path.expanduser("~/.gamemonitor_settings.json"), 'w') as f:
                json.dump(settings, f)
        except:
            pass
    
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
        try:
            # FPS - CORRIGIDO
            if metrics.get('fps'):
                game_running = metrics['fps'].get('game_running', False)
                current_fps = metrics['fps'].get('current', 0)
                
                if game_running and current_fps > 0:
                    self.fps_widget.value_label.setText(f"{current_fps:.0f}")
                    self.has_game = True
                    
                    if current_fps >= 60:
                        self.fps_widget.value_label.setStyleSheet("color: #4cff70; font-size: 16px; font-weight: bold;")
                    elif current_fps >= 30:
                        self.fps_widget.value_label.setStyleSheet("color: #ffaa44; font-size: 16px; font-weight: bold;")
                    else:
                        self.fps_widget.value_label.setStyleSheet("color: #ff4444; font-size: 16px; font-weight: bold;")
                else:
                    self.fps_widget.value_label.setText("0")
                    self.fps_widget.value_label.setStyleSheet("color: #666666; font-size: 14px;")
                    self.has_game = False
            
            # CPU
            cpu = metrics['cpu']['percent']
            self.cpu_widget.value_label.setText(f"{cpu:.0f}")
            if cpu > 80:
                self.cpu_widget.value_label.setStyleSheet("color: #ff4444; font-size: 14px; font-weight: bold;")
            elif cpu > 60:
                self.cpu_widget.value_label.setStyleSheet("color: #ffaa44; font-size: 14px; font-weight: bold;")
            else:
                self.cpu_widget.value_label.setStyleSheet("color: #4c9f70; font-size: 14px; font-weight: bold;")
            
            # RAM
            ram = metrics['ram']['percent']
            self.ram_widget.value_label.setText(f"{ram:.0f}")
            if ram > 80:
                self.ram_widget.value_label.setStyleSheet("color: #ff4444; font-size: 14px; font-weight: bold;")
            elif ram > 60:
                self.ram_widget.value_label.setStyleSheet("color: #ffaa44; font-size: 14px; font-weight: bold;")
            else:
                self.ram_widget.value_label.setStyleSheet("color: #4c9f70; font-size: 14px; font-weight: bold;")
            
            # GPU
            gpu = metrics['gpu']['percent']
            if gpu > 0:
                self.gpu_widget.value_label.setText(f"{gpu:.0f}")
                if gpu > 80:
                    self.gpu_widget.value_label.setStyleSheet("color: #ff4444; font-size: 14px; font-weight: bold;")
                elif gpu > 60:
                    self.gpu_widget.value_label.setStyleSheet("color: #ffaa44; font-size: 14px; font-weight: bold;")
                else:
                    self.gpu_widget.value_label.setStyleSheet("color: #4c9f70; font-size: 14px; font-weight: bold;")
            else:
                self.gpu_widget.value_label.setText("0")
                self.gpu_widget.value_label.setStyleSheet("color: #666666; font-size: 14px;")
            
            # Rede
            download = metrics['network']['download_speed_mb_s'] * 1024
            upload = metrics['network']['upload_speed_mb_s'] * 1024
            if download > 0 or upload > 0:
                self.net_widget.value_label.setText(f"↓{download:.0f}↑{upload:.0f}")
                self.net_widget.value_label.setStyleSheet("color: #4c9f70; font-size: 12px;")
            else:
                self.net_widget.value_label.setText("0")
                self.net_widget.value_label.setStyleSheet("color: #666666; font-size: 12px;")
                
        except Exception as e:
            print(f"Erro: {e}")
    
    def start_monitoring(self):
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        self.show()
        
        self.monitor_thread = OverlayThread(self.monitor, interval=1)
        self.monitor_thread.metrics_updated.connect(self.update_metrics)
        self.monitor_thread.start()
        
    def stop_monitoring(self):
        self.is_monitoring = False
        
        if self.monitor_thread:
            self.monitor_thread.stop()
            self.monitor_thread = None
        
        self.hide()
    
    def close_app(self):
        self.stop_monitoring()
        self.close()
        QApplication.quit()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Garantir que o FPS seja detectado
    print("Iniciando overlay horizontal...")
    print("Abra um jogo para ver o FPS!")
    
    window = ModernOverlayWindow()
    window.start_monitoring()
    
    sys.exit(app.exec_())