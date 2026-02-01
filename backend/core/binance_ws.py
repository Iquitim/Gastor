"""
Binance WebSocket Client
========================

Conecta ao stream de Klines da Binance para receber candles em tempo real.
"""

import asyncio
import json
from typing import Callable, Dict, Any, Optional
from datetime import datetime

try:
    import websockets
except ImportError:
    websockets = None


class BinanceKlineStream:
    """
    WebSocket client para stream de Klines da Binance.
    
    Recebe candles em tempo real quando eles fecham.
    
    Exemplo:
        async def on_candle(candle):
            print(f"New candle: {candle}")
        
        stream = BinanceKlineStream("SOLUSDT", "1h", on_candle)
        await stream.connect()
    """
    
    BASE_URL = "wss://stream.binance.com:9443/ws"
    
    def __init__(
        self,
        symbol: str,
        interval: str,
        on_candle: Callable[[Dict[str, Any]], Any],
        on_error: Optional[Callable[[Exception], Any]] = None,
    ):
        """
        Inicializa o stream.
        
        Args:
            symbol: Par de trading (ex: "SOLUSDT")
            interval: Intervalo do candle (1h, 4h, 1d)
            on_candle: Callback chamado quando um candle fecha
            on_error: Callback opcional para erros
        """
        self.symbol = symbol.lower()
        self.interval = interval
        self.on_candle = on_candle
        self.on_error = on_error
        self.ws = None
        self._running = False
        self._reconnect_delay = 5
        self._last_candle_time = 0
    
    @property
    def stream_name(self) -> str:
        """Nome do stream no formato Binance."""
        return f"{self.symbol}@kline_{self.interval}"
    
    @property
    def url(self) -> str:
        """URL completa do WebSocket."""
        return f"{self.BASE_URL}/{self.stream_name}"
    
    async def connect(self):
        """
        Conecta ao WebSocket e processa mensagens.
        
        Reconecta automaticamente em caso de desconexão.
        """
        if websockets is None:
            print("[BinanceWS] websockets library not installed")
            return
        
        self._running = True
        
        while self._running:
            try:
                async with websockets.connect(self.url) as ws:
                    self.ws = ws
                    self._reconnect_delay = 5  # Reset delay on successful connection
                    print(f"[BinanceWS] Connected to {self.stream_name}")
                    
                    async for message in ws:
                        if not self._running:
                            break
                        
                        await self._process_message(message)
                        
            except Exception as e:
                print(f"[BinanceWS] Connection error: {e}")
                if self.on_error:
                    try:
                        await self.on_error(e)
                    except:
                        pass
                
                if self._running:
                    print(f"[BinanceWS] Reconnecting in {self._reconnect_delay}s...")
                    await asyncio.sleep(self._reconnect_delay)
                    # Exponential backoff (max 60s)
                    self._reconnect_delay = min(self._reconnect_delay * 2, 60)
    
    async def _process_message(self, message: str):
        """
        Processa mensagem do WebSocket.
        
        Só processa candles fechados para evitar duplicações.
        """
        try:
            data = json.loads(message)
            kline = data.get("k", {})
            
            # Só processar candle fechado (x = is_final)
            if not kline.get("x", False):
                return
            
            candle_time = int(kline["t"]) // 1000
            
            # Evitar duplicação (mesmo candle)
            if candle_time <= self._last_candle_time:
                return
            
            self._last_candle_time = candle_time
            
            candle = {
                "time": candle_time,  # UNIX timestamp (seconds)
                "open": float(kline["o"]),
                "high": float(kline["h"]),
                "low": float(kline["l"]),
                "close": float(kline["c"]),
                "volume": float(kline["v"]),
                "symbol": self.symbol.upper(),
                "interval": self.interval,
            }
            
            print(f"[BinanceWS] Candle closed: {self.symbol} @ {candle['close']:.4f}")
            
            # Chamar callback (suporta sync e async)
            result = self.on_candle(candle)
            if asyncio.iscoroutine(result):
                await result
            
        except json.JSONDecodeError as e:
            print(f"[BinanceWS] JSON parse error: {e}")
        except Exception as e:
            print(f"[BinanceWS] Process error: {e}")
            if self.on_error:
                try:
                    await self.on_error(e)
                except:
                    pass
    
    async def disconnect(self):
        """
        Desconecta do WebSocket graciosamente.
        """
        self._running = False
        if self.ws:
            try:
                await self.ws.close()
            except:
                pass
            self.ws = None
            print(f"[BinanceWS] Disconnected from {self.stream_name}")
    
    def is_connected(self) -> bool:
        """Retorna True se conectado."""
        return self.ws is not None and self._running


class BinanceMultiStream:
    """
    Gerencia múltiplos streams de Klines simultaneamente.
    
    Útil para rodar várias sessões de Paper Trading ao mesmo tempo.
    """
    
    def __init__(self):
        self.streams: Dict[str, BinanceKlineStream] = {}
        self._tasks: Dict[str, asyncio.Task] = {}
    
    async def add_stream(
        self,
        stream_id: str,
        symbol: str,
        interval: str,
        on_candle: Callable[[Dict[str, Any]], Any],
        on_error: Optional[Callable[[Exception], Any]] = None,
    ):
        """
        Adiciona e inicia um novo stream.
        
        Args:
            stream_id: ID único para identificar o stream
            symbol: Par de trading
            interval: Intervalo do candle
            on_candle: Callback para candles
            on_error: Callback para erros
        """
        # Remover stream existente se houver
        await self.remove_stream(stream_id)
        
        stream = BinanceKlineStream(
            symbol=symbol,
            interval=interval,
            on_candle=on_candle,
            on_error=on_error,
        )
        
        self.streams[stream_id] = stream
        self._tasks[stream_id] = asyncio.create_task(stream.connect())
        
        print(f"[MultiStream] Added stream {stream_id}: {symbol}@{interval}")
    
    async def remove_stream(self, stream_id: str):
        """Remove e desconecta um stream."""
        if stream_id in self.streams:
            await self.streams[stream_id].disconnect()
            del self.streams[stream_id]
        
        if stream_id in self._tasks:
            self._tasks[stream_id].cancel()
            try:
                await self._tasks[stream_id]
            except asyncio.CancelledError:
                pass
            del self._tasks[stream_id]
            
        print(f"[MultiStream] Removed stream {stream_id}")
    
    async def stop_all(self):
        """Para todos os streams."""
        for stream_id in list(self.streams.keys()):
            await self.remove_stream(stream_id)
        print("[MultiStream] All streams stopped")
    
    def get_active_streams(self) -> list:
        """Retorna lista de streams ativos."""
        return [
            {
                "id": stream_id,
                "symbol": stream.symbol,
                "interval": stream.interval,
                "connected": stream.is_connected(),
            }
            for stream_id, stream in self.streams.items()
        ]


# Singleton para gerenciar streams globalmente
_multi_stream: Optional[BinanceMultiStream] = None


def get_multi_stream() -> BinanceMultiStream:
    """Retorna instância singleton do MultiStream."""
    global _multi_stream
    if _multi_stream is None:
        _multi_stream = BinanceMultiStream()
    return _multi_stream
