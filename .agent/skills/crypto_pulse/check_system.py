#!/usr/bin/env python3
"""
🔮 Crypto Pulse - Gastor Exchange Monitor
Monitora o pulso das APIs de criptomoedas em tempo real.
"""

import requests
import psutil
import time
from typing import Tuple

# Configurações de limiares
LATENCY_WARNING_MS = 200
LATENCY_CRITICAL_MS = 500
CPU_WARNING = 80
CPU_CRITICAL = 90
RAM_WARNING = 85
RAM_CRITICAL = 95
DISK_WARNING = 80
DISK_CRITICAL = 90

# APIs para verificar conectividade
APIS_TO_CHECK = [
    ("Binance", "https://api.binance.com/api/v3/ping"),
    ("CoinGecko", "https://api.coingecko.com/api/v3/ping"),
    ("CryptoCompare", "https://min-api.cryptocompare.com/data/price?fsym=BTC&tsyms=USD"),
]


def get_status_icon(value: float, warning: float, critical: float, reverse: bool = False) -> str:
    """Retorna o ícone de status baseado nos limiares."""
    if reverse:
        if value > critical:
            return "❌"
        elif value > warning:
            return "⚠️"
        return "✅"
    else:
        if value >= critical:
            return "❌"
        elif value >= warning:
            return "⚠️"
        return "✅"


def check_api_connectivity(name: str, url: str) -> Tuple[str, float]:
    """Verifica conectividade e latência de uma API."""
    try:
        start = time.time()
        response = requests.get(url, timeout=10)
        latency = (time.time() - start) * 1000
        
        if response.status_code == 200:
            icon = get_status_icon(latency, LATENCY_WARNING_MS, LATENCY_CRITICAL_MS)
            return f"{icon} {name}: Conectada (Latência: {latency:.0f}ms)", latency
        else:
            return f"❌ {name}: Erro HTTP {response.status_code}", -1
    except requests.exceptions.Timeout:
        return f"❌ {name}: Timeout (>10s)", -1
    except requests.exceptions.ConnectionError:
        return f"❌ {name}: Sem conexão", -1
    except Exception as e:
        return f"❌ {name}: Erro - {str(e)[:50]}", -1


def check_all_apis() -> Tuple[list, bool]:
    """Verifica todas as APIs configuradas."""
    results = []
    all_ok = True
    
    for name, url in APIS_TO_CHECK:
        result, latency = check_api_connectivity(name, url)
        results.append(result)
        if latency < 0 or latency > LATENCY_CRITICAL_MS:
            all_ok = False
    
    return results, all_ok


def check_cpu() -> Tuple[str, bool]:
    """Verifica uso de CPU."""
    cpu = psutil.cpu_percent(interval=1)
    icon = get_status_icon(cpu, CPU_WARNING, CPU_CRITICAL)
    is_ok = cpu < CPU_CRITICAL
    return f"{icon} CPU: {cpu:.1f}%", is_ok


def check_ram() -> Tuple[str, bool]:
    """Verifica uso de RAM."""
    ram = psutil.virtual_memory()
    percent = ram.percent
    used_gb = ram.used / (1024**3)
    total_gb = ram.total / (1024**3)
    icon = get_status_icon(percent, RAM_WARNING, RAM_CRITICAL)
    is_ok = percent < RAM_CRITICAL
    return f"{icon} RAM: {percent:.1f}% ({used_gb:.1f}/{total_gb:.1f} GB)", is_ok


def check_disk() -> Tuple[str, bool]:
    """Verifica uso de disco."""
    disk = psutil.disk_usage('/')
    percent = disk.percent
    free_gb = disk.free / (1024**3)
    icon = get_status_icon(percent, DISK_WARNING, DISK_CRITICAL)
    is_ok = percent < DISK_CRITICAL
    return f"{icon} Disco: {percent:.1f}% usado ({free_gb:.1f} GB livres)", is_ok


def check_docker_containers() -> Tuple[str, bool]:
    """Verifica se os containers Docker do Gastor estão rodando."""
    try:
        import subprocess
        result = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}:{{.Status}}", "--filter", "name=gastor"],
            capture_output=True, text=True, timeout=5
        )
        
        if result.returncode != 0:
            return "⚠️ Docker: Não disponível", True
        
        containers = result.stdout.strip().split('\n')
        if not containers or containers == ['']:
            return "⚠️ Docker: Nenhum container Gastor encontrado", True
        
        running = sum(1 for c in containers if 'Up' in c)
        total = len(containers)
        
        if running == total:
            return f"✅ Docker: {running}/{total} containers ativos", True
        else:
            return f"⚠️ Docker: {running}/{total} containers ativos", False
            
    except FileNotFoundError:
        return "ℹ️ Docker: Não instalado", True
    except Exception as e:
        return f"⚠️ Docker: Erro - {str(e)[:30]}", True


def run_health_check():
    """Executa verificação completa de saúde do sistema."""
    print("=" * 50)
    print("🔮 CRYPTO PULSE - Exchange Monitor")
    print("=" * 50)
    print(f"⏰ {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    all_checks_passed = True
    
    # Verificar APIs
    print("📡 CONECTIVIDADE APIs")
    print("-" * 30)
    api_results, apis_ok = check_all_apis()
    for result in api_results:
        print(f"   {result}")
    all_checks_passed = all_checks_passed and apis_ok
    print()
    
    # Verificar Recursos
    print("💻 RECURSOS DO SISTEMA")
    print("-" * 30)
    
    cpu_result, cpu_ok = check_cpu()
    print(f"   {cpu_result}")
    all_checks_passed = all_checks_passed and cpu_ok
    
    ram_result, ram_ok = check_ram()
    print(f"   {ram_result}")
    all_checks_passed = all_checks_passed and ram_ok
    
    disk_result, disk_ok = check_disk()
    print(f"   {disk_result}")
    all_checks_passed = all_checks_passed and disk_ok
    print()
    
    # Verificar Docker
    print("🐳 CONTAINERS")
    print("-" * 30)
    docker_result, docker_ok = check_docker_containers()
    print(f"   {docker_result}")
    all_checks_passed = all_checks_passed and docker_ok
    print()
    
    # Resumo
    print("=" * 50)
    if all_checks_passed:
        print("✅ STATUS GERAL: SISTEMA OPERACIONAL")
        print("   Pode prosseguir com as operações de trading.")
    else:
        print("⚠️ STATUS GERAL: ATENÇÃO REQUERIDA")
        print("   Verifique os itens marcados antes de operar.")
    print("=" * 50)
    
    return all_checks_passed


if __name__ == "__main__":
    success = run_health_check()
    exit(0 if success else 1)
