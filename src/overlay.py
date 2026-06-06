"""
overlay.py - Janela flutuante moderna com menu de configurações
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

class MetricsMenu(QMenu):
    """Menu para selecionar quais métricas exibir"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setup_menu()
        
    def setup_menu(self):
        self.setStyleSheet("""
            QMenu {
                background-color: #2b2b2b;
                color: white;
                border: 1px solid #4c9f70;
                border-radius: 8px;
                padding: 5px;
            }
            QMenu::item {
                padding: 8px 30px 8px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #4c9f70;
            }
            QMenu::item:checked {
                background-color: #4c9f70;
            }
        """)
        
        # Adicionar ações com checkboxes
        self.fps_action = QAction("🎮 FPS", self)
        self.fps_action.setCheckable(True)
        self.fps_action.setChecked(self.parent.metrics_enabled.get('fps', True))
        self.fps_action.triggered.connect(lambda: self.toggle_metric('fps'))
        self.addAction(self.fps_action)
        
        self.cpu_action = QAction("🖥️ CPU", self)
        self.cpu_action.setCheckable(True)
        self.cpu_action.setChecked(self.parent.metrics_enabled.get('cpu', True))
        self.cpu_action.triggered.connect(lambda: self.toggle_metric('cpu'))
        self.addAction(self.cpu_action)
        
        self.ram_action = QAction("💾 RAM", self)
        self.ram_action.setCheckable(True)
        self.ram_action.setChecked(self.parent.metrics_enabled.get('ram', True))
        self.ram_action.triggered.connect(lambda: self.toggle_metric('ram'))
        self.addAction(self.ram_action)
        
        self.gpu_action = QAction("🎮 GPU", self)
        self.gpu_action.setCheckable(True)
        self.gpu_action.setChecked(self.parent.metrics_enabled.get('gpu', True))
        self.gpu_action.triggered.connect(lambda: self.toggle_metric('gpu'))
        self.addAction(self.gpu_action)
        
        self.vram_action = QAction("💾 VRAM", self)
        self.vram_action.setCheckable(True)
        self.vram_action.setChecked(self.parent.metrics_enabled.get('vram', True))
        self.vram_action.triggered.connect(lambda: self.toggle_metric('vram'))
        self.addAction(self.vram_action)
        
        self.network_action = QAction("🌐 Rede", self)
        self.network_action.setCheckable(True)
        self.network_action.setChecked(self.parent.metrics_enabled.get('network', True))
        self.network_action.triggered.connect(lambda: self.toggle_metric('network'))
        self.addAction(self.network_action)
        
        self.addSeparator()
        
        # Opções de aparência
        self.opacity_menu = QMenu("🎨 Transparência", self)
        self.opacity_menu.setStyleSheet(self.styleSheet())
        
        for opacity in [70, 80, 85, 90, 95]:
            action = QAction(f"{opacity}%", self.opacity_menu)
            action.triggered.connect(lambda checked, o=opacity: self.change_opacity(o))
            self.opacity_menu.addAction(action)
        
        self.addMenu(self.opacity_menu)
        
        # Posição
        self.position_menu = QMenu("📌 Posição", self)
        self.position_menu.setStyleSheet(self.styleSheet())
        
        positions = [
            ("Canto Superior Esquerdo", "top-left"),
            ("Canto Superior Direito", "top-right"),
            ("Canto Inferior Esquerdo", "bottom-left"),
            ("Canto Inferior Direito", "bottom-right")
        ]
        
        for pos_name, pos_key in positions:
            action = QAction(pos_name, self.position_menu)
            action.triggered.connect(lambda checked, p=pos_key: self.change_position(p))
            self.position_menu.addAction(action)
        
        self.addMenu(self.position_menu)
        
        self.addSeparator()
        
        # Sair
        quit_action = QAction("❌ Fechar", self)
        quit_action.triggered.connect(self.parent.close_app)
        self.addAction(quit_action)
    
    def toggle_metric(self, metric):
        """Alterna visibilidade de uma métrica"""
        self.parent.metrics_enabled[metric] = not self.parent.metrics_enabled[metric]
        self.parent.update_metrics_visibility()
        self.parent.save_settings()
    
    def change_opacity(self, opacity):
        """Muda a opacidade do overlay"""
        self.parent.opacity = opacity / 100
        self.parent.apply_opacity()
        self.parent.save_settings()
    
    def change_position(self, position):
        """Muda a posição do overlay"""
        self.parent.position_preset = position
        self.parent.update_position()
        self.parent.save_settings()


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
    """Janela flutuante moderna com menu de configurações"""
    
    def __init__(self):
        super().__init__()
        self.monitor = SystemMonitor()
        self.monitor_thread = None
        self.is_monitoring = False
        self.dragging = False
        self.drag_position = QPoint()
        
        # Configurações padrão
        self.metrics_enabled = {
            'fps': True,
            'cpu': True,
            'ram': True,
            'gpu': True,
            'vram': True,
            'network': True
        }
        self.opacity = 0.85
        self.position_preset = "top-right"
        self.font_size = 11
        
        # Carregar configurações salvas
        self.load_settings()
        
        self.setup_overlay_properties()
        self.setup_ui()
        self.apply_opacity()
        
    def load_settings(self):
        """Carrega configurações salvas"""
        settings_file = os.path.expanduser("~/.gamemonitor_settings.json")
        if os.path.exists(settings_file):
            try:
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
                    self.metrics_enabled.update(settings.get('metrics', {}))
                    self.opacity = settings.get('opacity', 0.85)
                    self.position_preset = settings.get('position', "top-right")
                    self.font_size = settings.get('font_size', 11)
            except:
                pass
    
    def save_settings(self):
        """Salva configurações"""
        settings_file = os.path.expanduser("~/.gamemonitor_settings.json")
        settings = {
            'metrics': self.metrics_enabled,
            'opacity': self.opacity,
            'position': self.position_preset,
            'font_size': self.font_size
        }
        try:
            with open(settings_file, 'w') as f:
                json.dump(settings, f)
        except:
            pass
    
    def setup_overlay_properties(self):
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        
        self.update_position()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(0)
        self.setLayout(layout)
        
        # Frame principal
        self.frame = QFrame()
        self.frame.setStyleSheet("""
            QFrame {
                background-color: rgba(0, 0, 0, 200);
                border-radius: 12px;
                border: 1px solid #4c9f70;
            }
        """)
        
        frame_layout = QVBoxLayout(self.frame)
        frame_layout.setContentsMargins(12, 10, 12, 10)
        frame_layout.setSpacing(8)
        
        # Header com botão de menu
        header_layout = QHBoxLayout()
        
        title_label = QLabel("🎮 Game Monitor")
        title_label.setStyleSheet("""
            color: #4c9f70;
            font-weight: bold;
            font-size: 11px;
        """)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Botão de menu (engrenagem)
        self.menu_btn = QPushButton("⚙️")
        self.menu_btn.setFixedSize(28, 28)
        self.menu_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(76, 159, 112, 30);
                color: #4c9f70;
                border-radius: 14px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: rgba(76, 159, 112, 60);
            }
        """)
        self.menu_btn.clicked.connect(self.show_menu)
        header_layout.addWidget(self.menu_btn)
        
        # Botão de fechar
        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(28, 28)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 68, 68, 150);
                color: white;
                border-radius: 14px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(255, 68, 68, 220);
            }
        """)
        self.close_btn.clicked.connect(self.close_app)
        header_layout.addWidget(self.close_btn)
        
        frame_layout.addLayout(header_layout)
        
        # Linha separadora
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #4c9f70; max-height: 1px;")
        frame_layout.addWidget(line)
        
        # Container para métricas
        self.metrics_container = QWidget()
        self.metrics_layout = QVBoxLayout(self.metrics_container)
        self.metrics_layout.setSpacing(5)
        self.metrics_layout.setContentsMargins(0, 5, 0, 5)
        
        # Criar widgets para cada métrica
        self.metric_widgets = {}
        
        # FPS
        self.metric_widgets['fps'] = self.create_metric_row("🎮", "FPS", "")
        self.metrics_layout.addWidget(self.metric_widgets['fps'])
        
        # CPU
        self.metric_widgets['cpu'] = self.create_metric_row("🖥️", "CPU", "%")
        self.metrics_layout.addWidget(self.metric_widgets['cpu'])
        
        # RAM
        self.metric_widgets['ram'] = self.create_metric_row("💾", "RAM", "%")
        self.metrics_layout.addWidget(self.metric_widgets['ram'])
        
        # GPU
        self.metric_widgets['gpu'] = self.create_metric_row("🎮", "GPU", "%")
        self.metrics_layout.addWidget(self.metric_widgets['gpu'])
        
        # VRAM
        self.metric_widgets['vram'] = self.create_metric_row("💾", "VRAM", "MB")
        self.metrics_layout.addWidget(self.metric_widgets['vram'])
        
        # Rede
        self.metric_widgets['network'] = self.create_metric_row("🌐", "REDE", "KB/s")
        self.metrics_layout.addWidget(self.metric_widgets['network'])
        
        frame_layout.addWidget(self.metrics_container)
        
        # Status
        self.status_label = QLabel("⚪ Aguardando jogo...")
        self.status_label.setStyleSheet("color: #888888; font-size: 9px;")
        self.status_label.setAlignment(Qt.AlignCenter)
        frame_layout.addWidget(self.status_label)
        
        layout.addWidget(self.frame)
        
        # Tornar arrastável
        self.frame.mousePressEvent = self.mouse_press_event
        self.frame.mouseMoveEvent = self.mouse_move_event
        self.frame.mouseReleaseEvent = self.mouse_release_event
        title_label.mousePressEvent = self.mouse_press_event
        title_label.mouseMoveEvent = self.mouse_move_event
        title_label.mouseReleaseEvent = self.mouse_release_event
        
        # Atualizar visibilidade
        self.update_metrics_visibility()
    
    def create_metric_row(self, icon, name, unit):
        """Cria uma linha de métrica"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(8)
        
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 12px;")
        layout.addWidget(icon_label)
        
        name_label = QLabel(name)
        name_label.setStyleSheet("color: #aaaaaa; font-size: 10px;")
        layout.addWidget(name_label)
        
        layout.addStretch()
        
        value_label = QLabel("--")
        value_label.setStyleSheet("color: #4c9f70; font-weight: bold; font-size: 11px;")
        layout.addWidget(value_label)
        
        if unit:
            unit_label = QLabel(unit)
            unit_label.setStyleSheet("color: #666666; font-size: 9px;")
            layout.addWidget(unit_label)
        
        widget.value_label = value_label
        return widget
    
    def update_metrics_visibility(self):
        """Mostra/esconde métricas baseado nas configurações"""
        for key, widget in self.metric_widgets.items():
            widget.setVisible(self.metrics_enabled.get(key, True))
        
        # Ajustar altura da janela
        self.adjustSize()
    
    def apply_opacity(self):
        """Aplica a opacidade atual"""
        self.frame.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(0, 0, 0, {int(self.opacity * 255)});
                border-radius: 12px;
                border: 1px solid #4c9f70;
            }}
        """)
    
    def update_position(self):
        """Atualiza posição da janela"""
        screen = QApplication.primaryScreen().geometry()
        
        if self.position_preset == "top-left":
            x, y = 20, 20
        elif self.position_preset == "top-right":
            x, y = screen.width() - self.width() - 20, 20
        elif self.position_preset == "bottom-left":
            x, y = 20, screen.height() - self.height() - 60
        elif self.position_preset == "bottom-right":
            x, y = screen.width() - self.width() - 20, screen.height() - self.height() - 60
        else:
            x, y = screen.width() - self.width() - 20, 20
        
        self.move(x, y)
    
    def show_menu(self):
        """Mostra o menu de configurações"""
        menu = MetricsMenu(self)
        menu.exec_(self.menu_btn.mapToGlobal(self.menu_btn.rect().bottomRight()))
    
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
    
    def update_metrics_display(self, metrics):
        """Atualiza os valores das métricas"""
        try:
            # FPS
            if metrics.get('fps') and metrics['fps'].get('game_running', False):
                fps = metrics['fps']['current']
                self.metric_widgets['fps'].value_label.setText(f"{fps:.0f}")
                self.status_label.setText("🎮 JOGO ATIVO")
                self.status_label.setStyleSheet("color: #4cff70; font-size: 9px;")
            else:
                self.metric_widgets['fps'].value_label.setText("--")
                self.status_label.setText("⚪ Aguardando jogo...")
                self.status_label.setStyleSheet("color: #888888; font-size: 9px;")
            
            # CPU
            cpu = metrics['cpu']['percent']
            self.metric_widgets['cpu'].value_label.setText(f"{cpu:.0f}")
            if cpu > 80:
                self.metric_widgets['cpu'].value_label.setStyleSheet("color: #ff4444; font-weight: bold; font-size: 11px;")
            elif cpu > 60:
                self.metric_widgets['cpu'].value_label.setStyleSheet("color: #ffaa44; font-weight: bold; font-size: 11px;")
            else:
                self.metric_widgets['cpu'].value_label.setStyleSheet("color: #4c9f70; font-weight: bold; font-size: 11px;")
            
            # RAM
            ram = metrics['ram']['percent']
            self.metric_widgets['ram'].value_label.setText(f"{ram:.0f}")
            if ram > 80:
                self.metric_widgets['ram'].value_label.setStyleSheet("color: #ff4444; font-weight: bold; font-size: 11px;")
            elif ram > 60:
                self.metric_widgets['ram'].value_label.setStyleSheet("color: #ffaa44; font-weight: bold; font-size: 11px;")
            else:
                self.metric_widgets['ram'].value_label.setStyleSheet("color: #4c9f70; font-weight: bold; font-size: 11px;")
            
            # GPU
            gpu = metrics['gpu']['percent']
            if gpu > 0:
                self.metric_widgets['gpu'].value_label.setText(f"{gpu:.0f}")
                if gpu > 80:
                    self.metric_widgets['gpu'].value_label.setStyleSheet("color: #ff4444; font-weight: bold; font-size: 11px;")
                elif gpu > 60:
                    self.metric_widgets['gpu'].value_label.setStyleSheet("color: #ffaa44; font-weight: bold; font-size: 11px;")
                else:
                    self.metric_widgets['gpu'].value_label.setStyleSheet("color: #4c9f70; font-weight: bold; font-size: 11px;")
            else:
                self.metric_widgets['gpu'].value_label.setText("--")
            
            # VRAM
            if metrics['gpu']['vram_total_mb'] > 0:
                vram_used = metrics['gpu']['vram_used_mb']
                vram_total = metrics['gpu']['vram_total_mb']
                self.metric_widgets['vram'].value_label.setText(f"{vram_used:.0f}/{vram_total:.0f}")
            else:
                self.metric_widgets['vram'].value_label.setText("--")
            
            # Rede
            download = metrics['network']['download_speed_mb_s'] * 1024
            upload = metrics['network']['upload_speed_mb_s'] * 1024
            if download > 0 or upload > 0:
                self.metric_widgets['network'].value_label.setText(f"↓{download:.0f} ↑{upload:.0f}")
            else:
                self.metric_widgets['network'].value_label.setText("--")
            
        except Exception as e:
            print(f"Erro ao atualizar: {e}")
    
    def start_monitoring(self, save_logs=False):
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        self.show()
        
        self.monitor_thread = OverlayThread(self.monitor, interval=1)
        self.monitor_thread.metrics_updated.connect(self.update_metrics_display)
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


class OverlayController:
    def __init__(self):
        self.overlay = None
        self.logger = None
        self.is_recording = False
        self.current_session = None
        
    def start(self, save_logs=False, session_name=None):
        if self.overlay is None:
            self.overlay = ModernOverlayWindow()
        
        if save_logs:
            if self.logger is None:
                self.logger = PerformanceLogger()
            
            if session_name is None:
                session_name = f"overlay_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            self.current_session = self.logger.start_session(session_name)
            self.is_recording = True
        
        self.overlay.start_monitoring(save_logs)
        return self.current_session
    
    def stop(self):
        if self.overlay:
            self.overlay.stop_monitoring()
        
        if self.is_recording and self.logger:
            self.logger.stop_session()
            self.is_recording = False
            
        self.current_session = None
    
    def show(self):
        if self.overlay:
            self.overlay.show()
    
    def hide(self):
        if self.overlay:
            self.overlay.hide()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    controller = OverlayController()
    controller.start(save_logs=False)
    print("✨ Overlay Moderno Iniciado!")
    print("⚙️ Clique no ícone de engrenagem para abrir o menu")
    print("📌 Selecione quais métricas quer exibir")
    print("❌ Clique no X para fechar")
    sys.exit(app.exec_())