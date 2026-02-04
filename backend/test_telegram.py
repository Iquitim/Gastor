#!/usr/bin/env python3
"""
Script de teste para verificar conexão com Telegram Bot.
Execute: python test_telegram.py
"""

import asyncio
import httpx
import os
from dotenv import load_dotenv

# Carrega variáveis do .env
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_DEFAULT_CHAT_ID", "")


async def send_test_message():
    """Envia mensagem de teste para o Telegram."""
    
    if not TELEGRAM_BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN não configurado no .env")
        return False
    
    if not TELEGRAM_CHAT_ID:
        print("❌ TELEGRAM_DEFAULT_CHAT_ID não configurado no .env")
        return False
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    message = """🤖 <b>Gastor - Teste de Conexão</b>

✅ Bot conectado com sucesso!

📊 Você receberá notificações de:
• Trades (BUY/SELL)
• Início/Fim de sessões
• Depósitos/Saques
• Erros

<i>Configuração OK!</i>"""
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json={
                    "chat_id": TELEGRAM_CHAT_ID,
                    "text": message,
                    "parse_mode": "HTML",
                },
                timeout=10.0,
            )
            
            if response.status_code == 200:
                print("✅ Mensagem enviada com sucesso!")
                print(f"   Chat ID: {TELEGRAM_CHAT_ID}")
                return True
            else:
                error = response.json()
                print(f"❌ Erro {response.status_code}: {error.get('description', 'Unknown')}")
                return False
                
    except httpx.TimeoutException:
        print("❌ Timeout ao conectar com Telegram")
        return False
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False


if __name__ == "__main__":
    print("📱 Testando conexão com Telegram...")
    print(f"   Token: {TELEGRAM_BOT_TOKEN[:20]}..." if TELEGRAM_BOT_TOKEN else "   Token: NÃO CONFIGURADO")
    print(f"   Chat ID: {TELEGRAM_CHAT_ID}" if TELEGRAM_CHAT_ID else "   Chat ID: NÃO CONFIGURADO")
    print()
    
    asyncio.run(send_test_message())
