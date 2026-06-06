"""
overlay.py - Overlay transparente que não atrapalha os cliques
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
                print(f"Erro: {e}")
                
    def stop(self):
        self.running = False
        self.wait()


class TransparentOverlay(QWidget):
    def __init__(self):
        super().__init__()
        self.monitor = SystemMonitor()
        self.monitor_thread = None
        self.is_monitoring = False
        
        self.setup_overlay()
        self.setup_ui()
        
    def setup_overlay(self):
        """Configura overlay totalmente transparente"""
        # Janela sem bordas, sempre no topo
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        
        # FUNDO TOTALMENTE TRANSPARENTE
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # PERMITIR CLICAR ATRAVÉS (IMPORTANTE!)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        
        # Posição e tamanho
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen.width() - 400, 50, 380, 60)
        
    def setup_ui(self):
        # Layout principal
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        self.setLayout(layout)
        
        # Container com fundo levemente escuro (visível mas não atrapalha)
        self.container = QFrame()
        self.container.setStyleSheet("""
            QFrame {
                background-color: rgba(0, 0, 0, 160);
                border-radius: 30px;
                border: 1px solid rgba(76, 159, 112, 150);
            }
        """)
        
        container_layout = QHBoxLayout(self.container)
        container_layout.setContentsMargins(18, 8, 18, 8)
        container_layout.setSpacing(20)
        
        # Botão de menu (único elemento clicável)
        self.menu_btn = QPushButton("⚙️")
        self.menu_btn.setFixedSize(32, 32)
        self.menu_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(76, 159, 112, 100);
                color: #4c9f70;
                border-radius: 16px;
                font-size: 16px;
                border: none;
            }
            QPushButton:hover {
                background-color: rgba(76, 159, 112, 200);
                color: white;
            }
        """)
        self.menu_btn.clicked.connect(self.show_menu)
        container_layout.addWidget(self.menu_btn)
        
        # FPS
        self.fps_widget = self.create_metric("🎮", "FPS", "")
        container_layout.addWidget(self.fps_widget)
        
        # CPU
        self.cpu_widget = self.create_metric("🖥️", "CPU", "%")
        container_layout.addWidget(self.cpu_widget)
        
        # RAM
        self.ram_widget = self.create_metric("💾", "RAM", "%")
        container_layout.addWidget(self.ram_widget)
        
        # GPU
        self.gpu_widget = self.create_metric("🎮", "GPU", "%")
        container_layout.addWidget(self.gpu_widget)
        
        # Rede
        self.net_widget = self.create_metric("🌐", "NET", "")
        container_layout.addWidget(self.net_widget)
        
        # Botão fechar
        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(28, 28)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 68, 68, 120);
                color: #ff8888;
                border-radius: 14px;
                font-size: 14px;
                border: none;
            }
            QPushButton:hover {
                background-color: rgba(255, 68, 68, 220);
                color: white;
            }
        """)
        self.close_btn.clicked.connect(self.close_app)
        container_layout.addWidget(self.close_btn)
        
        layout.addWidget(self.container)
        
        # Somente o container pode ser arrastado (para não interferir)
        self.container.mousePressEvent = self.mouse_press_event
        self.container.mouseMoveEvent = self.mouse_move_event
        self.container.mouseReleaseEvent = self.mouse_release_event
        
        self.dragging = False
        self.drag_position = QPoint()
        
        # Timer para brilho do FPS
        self.glow_timer = QTimer()
        self.glow_timer.timeout.connect(self.update_glow)
        self.glow_timer.start(500)
        self.has_game = False
        self.glow = False
        
    def create_metric(self, icon, label, unit):
        """Cria widget de métrica"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        
        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet("font-size: 13px;")
        layout.addWidget(icon_lbl)
        
        name_lbl = QLabel(label)
        name_lbl.setStyleSheet("color: #aaaaaa; font-size: 9px;")
        layout.addWidget(name_lbl)
        
        value_lbl = QLabel("0")
        value_lbl.setStyleSheet("color: #4c9f70; font-size: 14px; font-weight: bold;")
        layout.addWidget(value_lbl)
        
        if unit:
            unit_lbl = QLabel(unit)
            unit_lbl.setStyleSheet("color: #666666; font-size: 9px;")
            layout.addWidget(unit_lbl)
        
        widget.value_label = value_lbl
        return widget
    
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
    
    def update_glow(self):
        """Efeito de brilho no FPS quando jogo ativo"""
        if self.has_game:
            self.glow = not self.glow
            color = "#6cff90" if self.glow else "#4cff70"
            self.fps_widget.value_label.setStyleSheet(f"color: {color}; font-size: 16px; font-weight: bold;")
    
    def show_menu(self):
        """Menu de configurações"""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #1e1e2e;
                color: #ffffff;
                border: 1px solid #4c9f70;
                border-radius: 12px;
                padding: 8px;
            }
            QMenu::item {
                padding: 8px 25px 8px 15px;
                border-radius: 6px;
            }
            QMenu::item:selected {
                background-color: #4c9f70;
            }
        """)
        
        # Posição
        pos_menu = menu.addMenu("📌 Posição")
        
        positions = [
            ("Superior Direito", "top-right"),
            ("Superior Esquerdo", "top-left"),
            ("Inferior Direito", "bottom-right"),
            ("Inferior Esquerdo", "bottom-left")
        ]
        
        for name, pos in positions:
            action = QAction(name, pos_menu)
            action.triggered.connect(lambda checked, p=pos: self.change_position(p))
            pos_menu.addAction(action)
        
        menu.addSeparator()
        
        # Transparência
        trans_menu = menu.addMenu("🎨 Transparência")
        for opacity in [100, 130, 160, 190, 220]:
            action = QAction(f"{int((opacity/255)*100)}%", trans_menu)
            action.triggered.connect(lambda checked, o=opacity: self.change_opacity(o))
            trans_menu.addAction(action)
        
        menu.addSeparator()
        
        # Fechar
        quit_action = QAction("❌ Fechar", menu)
        quit_action.triggered.connect(self.close_app)
        menu.addAction(quit_action)
        
        menu.exec_(self.menu_btn.mapToGlobal(self.menu_btn.rect().bottomLeft()))
    
    def change_position(self, position):
        """Muda posição do overlay"""
        screen = QApplication.primaryScreen().geometry()
        width, height = self.width(), self.height()
        
        if position == "top-right":
            x, y = screen.width() - width - 20, 50
        elif position == "top-left":
            x, y = 20, 50
        elif position == "bottom-right":
            x, y = screen.width() - width - 20, screen.height() - height - 60
        elif position == "bottom-left":
            x, y = 20, screen.height() - height - 60
        else:
            x, y = screen.width() - width - 20, 50
        
        self.move(x, y)
    
    def change_opacity(self, opacity):
        """Muda transparência"""
        self.container.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(0, 0, 0, {opacity});
                border-radius: 30px;
                border: 1px solid rgba(76, 159, 112, 150);
            }}
        """)
    
    def update_metrics(self, metrics):
        try:
            # FPS
            if metrics.get('fps'):
                game = metrics['fps'].get('game_running', False)
                fps = metrics['fps'].get('current', 0)
                
                if game and fps > 0:
                    self.fps_widget.value_label.setText(f"{fps:.0f}")
                    self.has_game = True
                    
                    if fps >= 60:
                        self.fps_widget.value_label.setStyleSheet("color: #4cff70; font-size: 16px; font-weight: bold;")
                    elif fps >= 30:
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
            down = metrics['network']['download_speed_mb_s'] * 1024
            up = metrics['network']['upload_speed_mb_s'] * 1024
            if down > 0 or up > 0:
                self.net_widget.value_label.setText(f"↓{down:.0f}↑{up:.0f}")
                self.net_widget.value_label.setStyleSheet("color: #4c9f70; font-size: 11px;")
            else:
                self.net_widget.value_label.setText("0")
                self.net_widget.value_label.setStyleSheet("color: #666666; font-size: 11px;")
                
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
    
    print("🎮 Overlay Transparente Iniciado!")
    print("✨ O overlay é totalmente transparente e você pode clicar através dele!")
    print("⚙️ Clique na engrenagem para configurar posição e transparência")
    print("📌 Arraste pelo fundo semi-transparente para mover")
    
    overlay = TransparentOverlay()
    overlay.start_monitoring()
    
    sys.exit(app.exec_())