# GamePerformanceMonitor 🎮

O **GamePerformanceMonitor** é uma ferramenta de telemetria desenvolvida para Linux, focada em monitorar o desempenho de jogos em tempo real com baixo impacto no sistema.

## 🚀 Funcionalidades

* **Monitoramento em Tempo Real:** Dados de hardware atualizados constantemente[cite: 9].
* **Suporte a Múltiplas GPUs:** Detecção automática via NVML (NVIDIA) ou sysfs (AMD/Intel)[cite: 7].
* **Interface Flexível:** Opções para visualização via console, interface gráfica (`gui.py`) ou um overlay transparente (`overlay.py`)[cite: 6, 9, 10].
* **Logging Completo:** Salva métricas em arquivos CSV para posterior análise estatística.
* **Resumo de Sessão:** Estatísticas automáticas ao finalizar o monitoramento (médias e máximos)[cite: 8].

## 🛠️ Tecnologias Utilizadas

* **Linguagem:** Python 3.10+.
* **Interface:** PyQt5.
* **Telemetria:** psutil, pynvml[cite: 4, 9].
* **Análise:** pandas, matplotlib[cite: 4].

## 📦 Instalação

Certifique-se de estar em um ambiente Linux (otimizado para Fedora)[cite: 1].

1. **Clone o repositório:**
```bash
   git clone [https://github.com/FredsonArthur/GamePerformanceMonitor.git](https://github.com/FredsonArthur/GamePerformanceMonitor.git)
   cd GamePerformanceMonitor

    Dê permissão de execução ao script de instalação:

Bash

   chmod +x install.sh

    Execute a instalação das dependências:

Bash

   ./install.sh

    Ative o ambiente virtual para começar a usar:

Bash

   source venv/bin/activate


---