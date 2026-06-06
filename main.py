#!/usr/bin/env python3
"""
GamePerformanceMonitor - Monitor de performance para jogos no Linux
Ponto de entrada principal com logging
"""

import sys
import os
import time

# Adiciona o diretório src ao path do Python
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from monitor import SystemMonitor
from logger import PerformanceLogger

def main():
    print("=" * 60)
    print("🎮 GamePerformanceMonitor v0.2.0")
    print("Monitor de performance para jogos no Linux")
    print("=" * 60)
    
    # Inicializar componentes
    monitor = SystemMonitor()
    logger = PerformanceLogger()
    
    # Perguntar se quer salvar logs
    print("\nOpções:")
    print("1. Apenas monitorar (sem salvar)")
    print("2. Monitorar e salvar logs")
    
    choice = input("\nEscolha (1/2): ").strip()
    
    save_logs = (choice == "2")
    
    if save_logs:
        session_name = input("Nome da sessão (Enter para gerar automático): ").strip()
        if not session_name:
            session_name = None
        logger.start_session(session_name)
        print("\n📝 Salvando métricas em CSV...")
    
    print("\n🖥️ Monitorando... Pressione Ctrl+C para parar\n")
    
    try:
        while True:
            # Coletar métricas
            metrics = monitor.get_all_metrics()
            
            # Mostrar no console
            monitor.print_metrics(metrics)
            
            # Salvar se necessário
            if save_logs:
                logger.log_metrics(metrics)
            
            time.sleep(2)  # Atualiza a cada 2 segundos
            
    except KeyboardInterrupt:
        print("\n\n✅ Monitoramento encerrado!")
        
        if save_logs:
            logger.stop_session()
            
            # Mostrar resumo da sessão
            print("\n📊 Resumo da sessão:")
            sessions = logger.list_sessions()
            if sessions:
                latest = sessions[0]
                summary = logger.get_session_summary(latest['name'])
                if summary:
                    print(f"  Duração: {summary['duration_seconds']} segundos")
                    print(f"  CPU: média {summary['cpu']['avg']}% (max {summary['cpu']['max']}%)")
                    print(f"  GPU: média {summary['gpu']['avg']}% (max {summary['gpu']['max']}%)")
                    print(f"  RAM: média {summary['ram']['avg']}% (max {summary['ram']['max']}%)")
                    print(f"\n  📁 Log salvo em: logs/{latest['name']}.csv")

if __name__ == "__main__":
    main()