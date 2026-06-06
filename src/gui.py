"""
gui.py - Interface gráfica do GamePerformanceMonitor usando PyQt5
"""

import sys
import os
import threading
import time
from datetime import datetime
from pathlib import Path

# Adiciona o diretório src ao path
sys.path.insert(0, os.path.dirname(__file__))

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from monitor import SystemMonitor
from logger import PerformanceLogger

class MonitorThread(QThread):
    """Thread separada para monitoramento"""
    metrics_updated = pyqtSignal(dict)
    
    def __init__(self, monitor, interval=2):
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

class GamePerformanceMonitorGUI(QMainWindow):
    """Interface gráfica principal com PyQt5"""
    
    def __init__(self):
        super().__init__()
        self.monitor = SystemMonitor()
        self.logger = PerformanceLogger()
        self.monitor_thread = None
        self.is_monitoring = False
        self.current_session = None
        
        self.setup_ui()
        self.apply_dark_theme()
        
    def apply_dark_theme(self):
        """Aplica tema escuro"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
            }
            QTabWidget::pane {
                background-color: #3c3c3c;
                border: 1px solid #555;
            }
            QTabBar::tab {
                background-color: #3c3c3c;
                color: white;
                padding: 8px 16px;
                margin: 2px;
            }
            QTabBar::tab:selected {
                background-color: #4c9f70;
            }
            QGroupBox {
                color: white;
                border: 1px solid #555;
                margin-top: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QLabel {
                color: white;
            }
            QProgressBar {
                border: 1px solid #555;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4c9f70;
                border-radius: 5px;
            }
            QPushButton {
                background-color: #4c9f70;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5dbd85;
            }
            QPushButton:disabled {
                background-color: #555;
            }
            QListWidget {
                background-color: #3c3c3c;
                color: white;
                border: 1px solid #555;
            }
            QTextEdit {
                background-color: #3c3c3c;
                color: white;
                border: 1px solid #555;
            }
        """)
    
    def setup_ui(self):
        """Configura a interface"""
        self.setWindowTitle("GamePerformanceMonitor v0.2.0")
        self.setGeometry(100, 100, 900, 700)
        self.setMinimumSize(800, 600)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Criar abas
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Criar cada aba
        self.setup_monitoring_tab()
        self.setup_history_tab()
        self.setup_settings_tab()
        self.setup_sessions_tab()
        
        # Barra de status
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("✅ Pronto para monitorar")
    
    def setup_monitoring_tab(self):
        """Configura aba de monitoramento"""
        tab = QWidget()
        self.tab_widget.addTab(tab, "📊 Monitoramento")
        layout = QVBoxLayout(tab)
        
        # Frame de controle
        control_frame = QFrame()
        control_layout = QHBoxLayout(control_frame)
        layout.addWidget(control_frame)
        
        self.start_btn = QPushButton("▶️ Iniciar Monitoramento")
        self.start_btn.clicked.connect(self.start_monitoring)
        control_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("⏸️ Parar Monitoramento")
        self.stop_btn.clicked.connect(self.stop_monitoring)
        self.stop_btn.setEnabled(False)
        control_layout.addWidget(self.stop_btn)
        
        self.save_btn = QPushButton("💾 Salvar Log")
        self.save_btn.clicked.connect(self.save_current_log)
        self.save_btn.setEnabled(False)
        control_layout.addWidget(self.save_btn)
        
        control_layout.addStretch()
        
        # Grid para métricas
        grid = QGridLayout()
        layout.addLayout(grid)
        
        # CPU
        cpu_group = QGroupBox("🖥️ CPU")
        cpu_layout = QVBoxLayout(cpu_group)
        self.cpu_label = QLabel("Uso: 0%")
        self.cpu_label.setFont(QFont("Arial", 24))
        cpu_layout.addWidget(self.cpu_label)
        self.cpu_progress = QProgressBar()
        cpu_layout.addWidget(self.cpu_progress)
        self.cpu_temp_label = QLabel("Temperatura: 0°C")
        cpu_layout.addWidget(self.cpu_temp_label)
        self.cpu_freq_label = QLabel("Frequência: 0 MHz")
        cpu_layout.addWidget(self.cpu_freq_label)
        grid.addWidget(cpu_group, 0, 0)
        
        # RAM
        ram_group = QGroupBox("💾 RAM")
        ram_layout = QVBoxLayout(ram_group)
        self.ram_label = QLabel("Uso: 0%")
        self.ram_label.setFont(QFont("Arial", 24))
        ram_layout.addWidget(self.ram_label)
        self.ram_progress = QProgressBar()
        ram_layout.addWidget(self.ram_progress)
        self.ram_used_label = QLabel("Usado: 0 GB")
        ram_layout.addWidget(self.ram_used_label)
        self.ram_total_label = QLabel("Total: 0 GB")
        ram_layout.addWidget(self.ram_total_label)
        grid.addWidget(ram_group, 0, 1)
        
        # GPU
        gpu_group = QGroupBox("🎮 GPU")
        gpu_layout = QVBoxLayout(gpu_group)
        self.gpu_name_label = QLabel("Modelo: Detectando...")
        gpu_layout.addWidget(self.gpu_name_label)
        self.gpu_label = QLabel("Uso: 0%")
        self.gpu_label.setFont(QFont("Arial", 20))
        gpu_layout.addWidget(self.gpu_label)
        self.gpu_progress = QProgressBar()
        gpu_layout.addWidget(self.gpu_progress)
        self.gpu_temp_label = QLabel("Temperatura: 0°C")
        gpu_layout.addWidget(self.gpu_temp_label)
        self.gpu_vram_label = QLabel("VRAM: 0 MB")
        gpu_layout.addWidget(self.gpu_vram_label)
        grid.addWidget(gpu_group, 1, 0, 1, 2)
        
        # Disco e Rede
        stats_frame = QFrame()
        stats_layout = QHBoxLayout(stats_frame)
        
        disk_group = QGroupBox("💽 Disco")
        disk_layout = QVBoxLayout(disk_group)
        self.disk_read_label = QLabel("Leitura: 0 MB/s")
        disk_layout.addWidget(self.disk_read_label)
        self.disk_write_label = QLabel("Escrita: 0 MB/s")
        disk_layout.addWidget(self.disk_write_label)
        stats_layout.addWidget(disk_group)
        
        network_group = QGroupBox("🌐 Rede")
        network_layout = QVBoxLayout(network_group)
        self.net_download_label = QLabel("Download: 0 MB/s")
        network_layout.addWidget(self.net_download_label)
        self.net_upload_label = QLabel("Upload: 0 MB/s")
        network_layout.addWidget(self.net_upload_label)
        stats_layout.addWidget(network_group)
        
        layout.addWidget(stats_frame)
        layout.addStretch()
    
    def setup_history_tab(self):
        """Aba de histórico (placeholder)"""
        tab = QWidget()
        self.tab_widget.addTab(tab, "📈 Histórico")
        layout = QVBoxLayout(tab)
        
        label = QLabel("📊 Gráficos de Performance (em desenvolvimento)")
        label.setFont(QFont("Arial", 18))
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        
        label2 = QLabel("Em breve: gráficos históricos de CPU, RAM, GPU e temperatura")
        label2.setAlignment(Qt.AlignCenter)
        layout.addWidget(label2)
        
        layout.addStretch()
    
    def setup_settings_tab(self):
        """Aba de configurações"""
        tab = QWidget()
        self.tab_widget.addTab(tab, "⚙️ Configurações")
        layout = QVBoxLayout(tab)
        
        # Intervalo
        interval_group = QGroupBox("Monitoramento")
        interval_layout = QVBoxLayout(interval_group)
        
        interval_row = QHBoxLayout()
        interval_row.addWidget(QLabel("Intervalo de atualização (segundos):"))
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 10)
        self.interval_spin.setValue(2)
        interval_row.addWidget(self.interval_spin)
        interval_layout.addLayout(interval_row)
        layout.addWidget(interval_group)
        
        # Informações do sistema
        info_group = QGroupBox("Informações do Sistema")
        info_layout = QVBoxLayout(info_group)
        self.sys_info_text = QTextEdit()
        self.sys_info_text.setReadOnly(True)
        info_layout.addWidget(self.sys_info_text)
        layout.addWidget(info_group)
        
        refresh_btn = QPushButton("🔄 Atualizar Informações")
        refresh_btn.clicked.connect(self.update_system_info)
        layout.addWidget(refresh_btn)
        
        layout.addStretch()
        
        # Carregar informações
        self.update_system_info()
    
    def setup_sessions_tab(self):
        """Aba de sessões salvas"""
        tab = QWidget()
        self.tab_widget.addTab(tab, "📁 Sessões")
        layout = QVBoxLayout(tab)
        
        self.sessions_list = QListWidget()
        layout.addWidget(self.sessions_list)
        
        btn_frame = QFrame()
        btn_layout = QHBoxLayout(btn_frame)
        
        refresh_btn = QPushButton("🔄 Atualizar")
        refresh_btn.clicked.connect(self.refresh_sessions_list)
        btn_layout.addWidget(refresh_btn)
        
        load_btn = QPushButton("📊 Carregar Sessão")
        load_btn.clicked.connect(self.load_selected_session)
        btn_layout.addWidget(load_btn)
        
        layout.addWidget(btn_frame)
        
        self.refresh_sessions_list()
    
    def update_system_info(self):
        """Atualiza informações do sistema"""
        import platform
        
        info = f"""
Sistema Operacional: {platform.system()} {platform.release()}
Arquitetura: {platform.machine()}
Python: {platform.python_version()}

GPU Detectada: {self.monitor.hardware.gpu_type}
Informações GPU: {self.monitor.hardware.get_gpu_info()}

Diretório de Logs: {Path('logs').absolute()}
        """
        
        self.sys_info_text.setText(info)
    
    def refresh_sessions_list(self):
        """Atualiza lista de sessões"""
        self.sessions_list.clear()
        sessions = self.logger.list_sessions()
        for session in sessions:
            self.sessions_list.addItem(
                f"{session['name']} - {session['modified'].strftime('%Y-%m-%d %H:%M')} ({session['size_mb']} MB)"
            )
    
    def load_selected_session(self):
        """Carrega sessão selecionada"""
        selected = self.sessions_list.currentItem()
        if not selected:
            QMessageBox.warning(self, "Aviso", "Selecione uma sessão primeiro!")
            return
        
        session_name = selected.text().split(" - ")[0]
        
        try:
            summary = self.logger.get_session_summary(session_name)
            
            QMessageBox.information(
                self,
                "Resumo da Sessão",
                f"Sessão: {session_name}\n"
                f"Duração: {summary['duration_seconds']} segundos\n\n"
                f"CPU - Média: {summary['cpu']['avg']}% | Máx: {summary['cpu']['max']}%\n"
                f"GPU - Média: {summary['gpu']['avg']}% | Máx: {summary['gpu']['max']}%\n"
                f"RAM - Média: {summary['ram']['avg']}% | Máx: {summary['ram']['max']}%"
            )
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar sessão: {e}")
    
    def update_metrics_display(self, metrics):
        """Atualiza display com métricas"""
        # CPU
        cpu = metrics['cpu']['percent']
        self.cpu_label.setText(f"Uso: {cpu:.1f}%")
        self.cpu_progress.setValue(int(cpu))
        
        if metrics['cpu']['temperature'] > 0:
            self.cpu_temp_label.setText(f"Temperatura: {metrics['cpu']['temperature']:.0f}°C")
        
        if metrics['cpu']['frequency'] > 0:
            self.cpu_freq_label.setText(f"Frequência: {metrics['cpu']['frequency']:.0f} MHz")
        
        # RAM
        ram = metrics['ram']['percent']
        self.ram_label.setText(f"Uso: {ram:.1f}%")
        self.ram_progress.setValue(int(ram))
        self.ram_used_label.setText(f"Usado: {metrics['ram']['used_gb']:.1f} GB")
        self.ram_total_label.setText(f"Total: {metrics['ram']['total_gb']:.1f} GB")
        
        # GPU
        if metrics['gpu']['percent'] > 0:
            gpu = metrics['gpu']['percent']
            self.gpu_label.setText(f"Uso: {gpu:.1f}%")
            self.gpu_progress.setValue(int(gpu))
            
            if metrics['gpu']['temp'] > 0:
                self.gpu_temp_label.setText(f"Temperatura: {metrics['gpu']['temp']:.0f}°C")
            
            if metrics['gpu']['vram_total_mb'] > 0:
                self.gpu_vram_label.setText(f"VRAM: {metrics['gpu']['vram_used_mb']:.0f}/{metrics['gpu']['vram_total_mb']:.0f} MB")
        
        # Disco
        self.disk_read_label.setText(f"Leitura: {metrics['disk']['read_speed_mb_s']:.1f} MB/s")
        self.disk_write_label.setText(f"Escrita: {metrics['disk']['write_speed_mb_s']:.1f} MB/s")
        
        # Rede
        self.net_download_label.setText(f"Download: {metrics['network']['download_speed_mb_s']:.1f} MB/s")
        self.net_upload_label.setText(f"Upload: {metrics['network']['upload_speed_mb_s']:.1f} MB/s")
        
        # Cores das barras
        if cpu > 80:
            self.cpu_progress.setStyleSheet("QProgressBar::chunk { background-color: red; }")
        elif cpu > 60:
            self.cpu_progress.setStyleSheet("QProgressBar::chunk { background-color: orange; }")
        else:
            self.cpu_progress.setStyleSheet("QProgressBar::chunk { background-color: #4c9f70; }")
        
        if ram > 80:
            self.ram_progress.setStyleSheet("QProgressBar::chunk { background-color: red; }")
        elif ram > 60:
            self.ram_progress.setStyleSheet("QProgressBar::chunk { background-color: orange; }")
        else:
            self.ram_progress.setStyleSheet("QProgressBar::chunk { background-color: #4c9f70; }")
    
    def start_monitoring(self):
        """Inicia monitoramento"""
        if self.is_monitoring:
            return
        
        # Perguntar sobre salvar log
        reply = QMessageBox.question(
            self,
            "Salvar Log",
            "Deseja salvar as métricas em um arquivo CSV?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            session_name = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.current_session = self.logger.start_session(session_name)
            self.statusBar.showMessage(f"📝 Monitorando e salvando em: {session_name}.csv")
        else:
            self.statusBar.showMessage("🖥️ Monitorando (sem salvar log)")
        
        self.is_monitoring = True
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.save_btn.setEnabled(reply == QMessageBox.Yes)
        
        # Iniciar thread
        interval = self.interval_spin.value()
        self.monitor_thread = MonitorThread(self.monitor, interval)
        self.monitor_thread.metrics_updated.connect(self.update_metrics_display)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Para monitoramento"""
        self.is_monitoring = False
        
        if self.monitor_thread:
            self.monitor_thread.stop()
            self.monitor_thread = None
        
        if self.current_session:
            self.logger.stop_session()
            self.statusBar.showMessage(f"✅ Monitoramento parado. Log salvo com sucesso!")
            self.current_session = None
        else:
            self.statusBar.showMessage("⏹️ Monitoramento parado")
        
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.save_btn.setEnabled(False)
    
    def save_current_log(self):
        """Salva log atual"""
        if self.current_session:
            self.logger.stop_session()
            QMessageBox.information(self, "Sucesso", f"Log salvo com sucesso!\n{self.current_session}")
            self.current_session = None
            self.save_btn.setEnabled(False)
            self.statusBar.showMessage("✅ Log salvo manualmente")


def main():
    app = QApplication(sys.argv)
    window = GamePerformanceMonitorGUI()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()