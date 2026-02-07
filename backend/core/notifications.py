"""
Notification Service
====================

Envio de notificações via Telegram.

Configuração:
1. Crie um bot no Telegram com @BotFather
2. Obtenha o token do bot
3. Configure TELEGRAM_BOT_TOKEN no .env
4. Inicie uma conversa com o bot e envie /start
5. Use /myid para obter seu Chat ID
"""

import httpx
import os
from typing import Optional


from core.config_loader import ConfigLoader

# Carrega token padrão do ambiente/secrets
DEFAULT_BOT_TOKEN = ConfigLoader.get_secret("TELEGRAM_BOT_TOKEN", "")


async def send_telegram(
    chat_id: str, 
    message: str, 
    parse_mode: str = "HTML",
    bot_token: Optional[str] = None
) -> bool:
    """
    Envia mensagem via Telegram Bot.
    
    Args:
        chat_id: ID do chat/grupo do usuário
        message: Texto da mensagem
        parse_mode: Formato do texto (HTML ou Markdown)
        bot_token: Token específico (opcional). Se None, usa o DEFAULT_BOT_TOKEN
        
    Returns:
        True se enviou com sucesso
    """
    token_to_use = bot_token if bot_token else DEFAULT_BOT_TOKEN
    
    if not token_to_use:
        print("[Telegram] Bot token not configured (TELEGRAM_BOT_TOKEN or user override)")
        return False
    
    if not chat_id:
        print("[Telegram] No chat_id provided")
        return False
    
    url = f"https://api.telegram.org/bot{token_to_use}/sendMessage"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json={
                    "chat_id": chat_id,
                    "text": message,
                    "parse_mode": parse_mode,
                },
                timeout=10.0,
            )
            
            if response.status_code == 200:
                print(f"[Telegram] Message sent to {chat_id}")
                return True
            else:
                error = response.json()
                print(f"[Telegram] Error {response.status_code}: {error.get('description', 'Unknown')}")
                return False
                
    except httpx.TimeoutException:
        print("[Telegram] Request timeout")
        return False
    except Exception as e:
        print(f"[Telegram] Exception: {e}")
        return False


async def send_trade_alert(
    chat_id: str,
    trade_type: str,
    symbol: str,
    price: float,
    quantity: float,
    value: float,
    balance: float,
    pnl: Optional[float] = None,
    pnl_pct: Optional[float] = None,
    session_id: Optional[int] = None,
    strategy_name: Optional[str] = None,
    bot_token: Optional[str] = None,
) -> bool:
    """
    Envia alerta formatado de trade.
    
    Args:
        chat_id: ID do chat Telegram
        trade_type: "BUY" ou "SELL"
        symbol: Par de trading (ex: "SOL/USDT")
        price: Preço de execução
        quantity: Quantidade negociada
        value: Valor total
        balance: Saldo após trade
        pnl: Lucro/prejuízo (apenas para SELL)
        pnl_pct: Percentual de lucro/prejuízo
        session_id: ID da sessão
        strategy_name: Nome da estratégia
        bot_token: Token específico (opcional)
    """
    emoji = "🟢" if trade_type == "BUY" else "🔴"
    
    msg = f"{emoji} <b>{trade_type}</b> {symbol}\n"
    
    if strategy_name:
        msg += f"📈 Estratégia: {strategy_name}\n"
    
    msg += f"\n💵 Preço: ${price:,.4f}\n"
    msg += f"📊 Quantidade: {quantity:.6f}\n"
    msg += f"💰 Valor: ${value:,.2f}\n"
    
    if pnl is not None:
        pnl_emoji = "📈" if pnl > 0 else "📉"
        pnl_sign = "+" if pnl > 0 else ""
        msg += f"\n{pnl_emoji} <b>PnL: {pnl_sign}${pnl:,.2f} ({pnl_sign}{pnl_pct:.2f}%)</b>\n"
    
    msg += f"\n💼 Saldo: ${balance:,.2f}"
    
    if session_id:
        msg += f"\n<i>Sessão #{session_id}</i>"
    
    return await send_telegram(chat_id, msg)


async def send_session_started(
    chat_id: str,
    strategy: str,
    coin: str,
    timeframe: str,
    balance: float,
    session_id: int,
) -> bool:
    """Envia notificação de início de sessão."""
    msg = f"🚀 <b>Paper Trading Iniciado!</b>\n\n"
    msg += f"📈 Estratégia: {strategy}\n"
    msg += f"💱 Par: {coin}\n"
    msg += f"⏱️ Timeframe: {timeframe}\n"
    msg += f"💰 Saldo Inicial: ${balance:,.2f}\n"
    msg += f"\n<i>Sessão #{session_id}</i>"
    
    return await send_telegram(chat_id, msg)


async def send_session_stopped(
    chat_id: str,
    strategy: str,
    initial_balance: float,
    final_balance: float,
    total_trades: int,
    session_id: int,
) -> bool:
    """Envia notificação de encerramento de sessão."""
    pnl = final_balance - initial_balance
    pnl_pct = (pnl / initial_balance) * 100
    
    pnl_emoji = "📈" if pnl > 0 else "📉"
    pnl_sign = "+" if pnl > 0 else ""
    
    msg = f"⏹️ <b>Paper Trading Encerrado!</b>\n\n"
    msg += f"📈 Estratégia: {strategy}\n"
    msg += f"💰 Saldo Inicial: ${initial_balance:,.2f}\n"
    msg += f"💼 Saldo Final: ${final_balance:,.2f}\n"
    msg += f"\n{pnl_emoji} <b>PnL Total: {pnl_sign}${pnl:,.2f} ({pnl_sign}{pnl_pct:.2f}%)</b>\n"
    msg += f"📊 Total de Trades: {total_trades}\n"
    msg += f"\n<i>Sessão #{session_id}</i>"
    
    return await send_telegram(chat_id, msg)


async def send_deposit_alert(
    chat_id: str,
    amount: float,
    new_balance: float,
    session_id: int,
) -> bool:
    """Envia notificação de depósito."""
    msg = f"💰 <b>Depósito Realizado!</b>\n\n"
    msg += f"➕ Valor: +${amount:,.2f}\n"
    msg += f"💼 Novo Saldo: ${new_balance:,.2f}\n"
    msg += f"\n<i>Sessão #{session_id}</i>"
    
    return await send_telegram(chat_id, msg)


async def send_withdrawal_alert(
    chat_id: str,
    amount: float,
    new_balance: float,
    session_id: int,
) -> bool:
    """Envia notificação de saque."""
    msg = f"🏦 <b>Saque Realizado!</b>\n\n"
    msg += f"➖ Valor: -${amount:,.2f}\n"
    msg += f"💼 Novo Saldo: ${new_balance:,.2f}\n"
    msg += f"\n<i>Sessão #{session_id}</i>"
    
    return await send_telegram(chat_id, msg)


async def send_error_alert(
    chat_id: str,
    error_message: str,
    session_id: Optional[int] = None,
) -> bool:
    """Envia notificação de erro."""
    msg = f"⚠️ <b>Erro no Paper Trading!</b>\n\n"
    msg += f"❌ {error_message}\n"
    
    if session_id:
        msg += f"\n<i>Sessão #{session_id}</i>"
    
    return await send_telegram(chat_id, msg)


async def send_signal_alert(
    chat_id: str,
    signal: str,
    coin: str,
    price: float,
    session_id: int,
) -> bool:
    """Envia alerta de sinal (sem executar trade)."""
    emoji = "🔔" if signal == "BUY" else "🔕"
    
    msg = f"{emoji} <b>Sinal Detectado: {signal}</b>\n\n"
    msg += f"💱 Par: {coin}\n"
    msg += f"💵 Preço: ${price:,.4f}\n"
    msg += f"\n<i>Sessão #{session_id}</i>"
    
    return await send_telegram(chat_id, msg)


# Utilitário para verificar se Telegram está configurado
def is_telegram_configured() -> bool:
    """Retorna True se o Telegram Bot está configurado (padrão)."""
    return bool(DEFAULT_BOT_TOKEN)
