---
name: Crypto Pulse
description: Monitora o pulso das APIs de criptomoedas - verifica conectividade, latência e status das exchanges em tempo real.
---

# Skill: Crypto Pulse 📈

## Descrição
Monitora o "pulso" do ecossistema de criptomoedas, verificando:
- Conectividade com APIs de trading (Binance, CoinGecko, CryptoCompare)
- Latência de rede para cada exchange
- Uso de recursos do sistema (CPU, RAM, Disco)
- Status dos containers Docker (se aplicável)

## Quando usar
- **Antes de iniciar uma sessão de trading** - Garantir que as exchanges estão acessíveis
- **Após falha na execução de uma ordem** - Diagnosticar problemas de conectividade
- **Se detectar lentidão nas respostas** - Identificar gargalos de rede
- **Diagnóstico periódico** - Recomendado a cada 1 hora durante operação

## Comandos de Execução

### Diagnóstico Completo
```bash
python .agent/skills/crypto_pulse/check_system.py
```

### Via Docker (se estiver usando containers)
```bash
docker exec gastor-backend python /app/.agent/skills/crypto_pulse/check_system.py
```

## Interpretação de Resultados

| Status | Significado | Ação |
|--------|-------------|------|
| ✅ **OK** | Exchanges respondendo normalmente | Continue as operações |
| ⚠️ **Warning** | Latência elevada (>200ms) | Risco de slippage - opere com cautela |
| ❌ **Error** | API desconectada ou timeout | Interrompa trades e aguarde reconexão |

## Limiares Configurados

| Métrica | Normal | Warning | Crítico |
|---------|--------|---------|---------|
| Latência API | < 200ms | 200-500ms | > 500ms |
| CPU | < 80% | 80-90% | > 90% |
| RAM | < 85% | 85-95% | > 95% |
| Disco | < 80% | 80-90% | > 90% |

## Dependências
```bash
pip install requests psutil
```
