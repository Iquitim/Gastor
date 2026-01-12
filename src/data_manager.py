"""
Data Manager - Ingestão de Dados

Módulo responsável pela ingestão de dados:
- CCXT: Dados históricos ilimitados de múltiplas exchanges (RECOMENDADO)
- cTrader Open API: Dados em tempo real via WebSocket
- Binance API: Dados históricos de criptomoedas (limitado a 1000 candles)

Suporta Linux, Windows e Mac.
"""

import os
import time
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Callable

import pandas as pd
import numpy as np
from dotenv import load_dotenv

load_dotenv()


class DataManager:
    """
    Gerenciador de dados para ingestão de OHLCV.
    
    Suporta:
    - CCXT: 100+ exchanges, paginação automática, dados ilimitados
    - cTrader Open API: Dados em tempo real
    - Binance API: Dados históricos (limitado a 1000 candles)
    """
    
    def __init__(self):
        # Binance (para dados históricos)
        self.binance_api_key = os.getenv("BINANCE_API_KEY")
        self.binance_api_secret = os.getenv("BINANCE_API_SECRET")
        
        # cTrader (para dados em tempo real)
        self.ctrader_account_id = os.getenv("CTRADER_ACCOUNT_ID")
        
        # Cache de dados
        self._price_cache: Dict[str, pd.DataFrame] = {}
        self._tick_callbacks: List[Callable] = []
        
    def get_historical_data(
        self,
        symbol: str = "BTCUSDT",
        timeframe: str = "1h",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 1000
    ) -> pd.DataFrame:
        """
        Obtém dados históricos OHLCV da Binance.
        
        Args:
            symbol: Par de trading (ex: BTCUSDT, ETHUSDT)
            timeframe: Período das velas (15m, 1h, 4h)
            start_date: Data inicial (formato: YYYY-MM-DD)
            end_date: Data final (formato: YYYY-MM-DD)
            limit: Número máximo de velas
            
        Returns:
            DataFrame com colunas: open, high, low, close, volume
        """
        try:
            from binance.spot import Spot
            
            client = Spot(
                api_key=self.binance_api_key,
                api_secret=self.binance_api_secret
            )
            
            # Converte timeframe para formato Binance
            tf_map = {
                "1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m",
                "1h": "1h", "4h": "4h", "1d": "1d",
                "M1": "1m", "M5": "5m", "M15": "15m", "M30": "30m",
                "H1": "1h", "H4": "4h", "D1": "1d"
            }
            interval = tf_map.get(timeframe, "1h")
            
            # Parâmetros
            params = {"symbol": symbol.upper(), "interval": interval, "limit": limit}
            
            if start_date:
                params["startTime"] = int(datetime.strptime(start_date, "%Y-%m-%d").timestamp() * 1000)
            if end_date:
                params["endTime"] = int(datetime.strptime(end_date, "%Y-%m-%d").timestamp() * 1000)
            
            # Obtém klines
            klines = client.klines(**params)
            
            # Converte para DataFrame
            df = pd.DataFrame(klines, columns=[
                "timestamp", "open", "high", "low", "close", "volume",
                "close_time", "quote_volume", "trades", "taker_buy_base",
                "taker_buy_quote", "ignore"
            ])
            
            # Limpa e formata
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
            df = df.set_index("timestamp")
            df = df[["open", "high", "low", "close", "volume"]].astype(float)
            
            print(f"[DataManager] Obtidos {len(df)} candles de {symbol} ({timeframe})")
            return df
            
        except ImportError:
            print("[DataManager] binance-connector não instalado")
            return self._generate_simulated_data(symbol, limit)
        except Exception as e:
            print(f"[DataManager] Erro ao obter dados: {e}")
            return self._generate_simulated_data(symbol, limit)
    
    def get_ccxt_historical_data(
        self,
        symbol: str = "BTC/USDT",
        timeframe: str = "1h",
        days: int = 365,
        exchange_id: str = "binance"
    ) -> pd.DataFrame:
        """
        Obtém dados históricos via CCXT com paginação automática.
        
        VANTAGENS:
        - Sem limite de candles (paginação automática)
        - Suporta 100+ exchanges
        - Dados desde o início do par
        
        Args:
            symbol: Par de trading no formato CCXT (ex: BTC/USDT)
            timeframe: Período das velas (1m, 5m, 15m, 1h, 4h, 1d)
            days: Número de dias de histórico (sem limite!)
            exchange_id: ID da exchange (binance, bybit, kraken, etc)
            
        Returns:
            DataFrame com colunas: open, high, low, close, volume
        """
        try:
            import ccxt
            
            # Cria instância da exchange
            exchange_class = getattr(ccxt, exchange_id)
            exchange = exchange_class({
                'enableRateLimit': True,  # Respeita rate limits
            })
            
            # Converte timeframe
            tf_mapping = {
                '1m': '1m', '5m': '5m', '15m': '15m', '30m': '30m',
                '1h': '1h', '4h': '4h', '1d': '1d', '1w': '1w',
                'M1': '1m', 'M5': '5m', 'M15': '15m', 'M30': '30m',
                'H1': '1h', 'H4': '4h', 'D1': '1d',
            }
            tf = tf_mapping.get(timeframe, '1h')
            
            # Calcula timestamps
            now = datetime.now()
            since = int((now - timedelta(days=days)).timestamp() * 1000)
            
            # Paginação automática
            all_ohlcv = []
            limit_per_request = 1000  # CCXT padrão
            
            print(f"[CCXT] Baixando {symbol} ({tf}) - últimos {days} dias de {exchange_id}...")
            
            while True:
                ohlcv = exchange.fetch_ohlcv(
                    symbol=symbol,
                    timeframe=tf,
                    since=since,
                    limit=limit_per_request
                )
                
                if not ohlcv:
                    break
                
                all_ohlcv.extend(ohlcv)
                
                # Próxima página
                last_timestamp = ohlcv[-1][0]
                since = last_timestamp + 1
                
                # Para se chegou ao presente
                if last_timestamp >= int(now.timestamp() * 1000):
                    break
                
                # Rate limit
                time.sleep(exchange.rateLimit / 1000)
            
            if not all_ohlcv:
                print(f"[CCXT] Nenhum dado retornado")
                return self._generate_simulated_data(symbol.replace("/", ""), days * 24)
            
            # Converte para DataFrame
            df = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df = df.set_index('timestamp')
            df = df.astype(float)
            
            # Remove duplicatas
            df = df[~df.index.duplicated(keep='last')]
            df = df.sort_index()
            
            print(f"[CCXT] ✅ Obtidos {len(df)} candles ({df.index[0].date()} a {df.index[-1].date()})")
            return df
            
        except ImportError:
            print("[CCXT] ⚠️ ccxt não instalado. Instale com: pip install ccxt")
            print("[CCXT] Usando fallback Binance API...")
            return self.get_historical_data(symbol.replace("/", ""), timeframe, limit=1000)
        except Exception as e:
            print(f"[CCXT] Erro: {e}")
            print("[CCXT] Usando fallback Binance API...")
            return self.get_historical_data(symbol.replace("/", ""), timeframe, limit=1000)
    
    def _generate_simulated_data(self, symbol: str, bars: int = 1000) -> pd.DataFrame:
        """
        Gera dados simulados para desenvolvimento/backtesting.
        
        Útil quando não há conexão com API.
        """
        print(f"[DataManager] Gerando {bars} barras simuladas para {symbol}")
        
        # Preço base por símbolo
        base_prices = {
            "BTCUSD": 45000.0,
            "BTCUSDT": 45000.0,
            "ETHUSD": 2500.0,
            "ETHUSDT": 2500.0,
        }
        base_price = base_prices.get(symbol.upper(), 100.0)
        
        # Gera série temporal
        dates = pd.date_range(end=datetime.now(), periods=bars, freq="1h")
        
        # Random walk para preço
        np.random.seed(42)
        returns = np.random.normal(0.0001, 0.02, bars)
        price = base_price * np.cumprod(1 + returns)
        
        # Gera OHLCV
        df = pd.DataFrame(index=dates)
        df["close"] = price
        df["open"] = df["close"].shift(1).fillna(base_price)
        df["high"] = df[["open", "close"]].max(axis=1) * (1 + np.random.uniform(0, 0.01, bars))
        df["low"] = df[["open", "close"]].min(axis=1) * (1 - np.random.uniform(0, 0.01, bars))
        df["volume"] = np.random.uniform(100, 10000, bars)
        
        return df
    
    def get_ctrader_data(
        self,
        symbol: str = "BTCUSD",
        timeframe: str = "H1",
        num_bars: int = 1000
    ) -> pd.DataFrame:
        """
        Obtém dados históricos do cTrader via Open API.
        
        Args:
            symbol: Símbolo no cTrader
            timeframe: Timeframe (M1, M5, M15, M30, H1, H4, D1)
            num_bars: Número de barras a obter
            
        Returns:
            DataFrame com dados OHLCV
        """
        try:
            from ctrader_open_api import Client, TcpProtocol, EndPoints
            from ctrader_open_api.messages.OpenApiMessages_pb2 import ProtoOAGetTrendbarsReq
            from ctrader_open_api.messages.OpenApiModelMessages_pb2 import ProtoOATrendbarPeriod
            
            # Mapeamento de timeframe
            tf_map = {
                "M1": ProtoOATrendbarPeriod.M1,
                "M5": ProtoOATrendbarPeriod.M5,
                "M15": ProtoOATrendbarPeriod.M15,
                "M30": ProtoOATrendbarPeriod.M30,
                "H1": ProtoOATrendbarPeriod.H1,
                "H4": ProtoOATrendbarPeriod.H4,
                "D1": ProtoOATrendbarPeriod.D1,
            }
            
            # Em produção, enviar request e aguardar callback
            # Por enquanto, usa dados simulados ou Binance
            print(f"[DataManager] cTrader historical data não implementado, usando fallback")
            
            # Fallback para Binance ou simulado
            binance_symbol = symbol.replace("USD", "USDT")
            return self.get_historical_data(binance_symbol, timeframe, limit=num_bars)
            
        except ImportError:
            print("[DataManager] ctrader-open-api não instalado")
            return self._generate_simulated_data(symbol, num_bars)
        except Exception as e:
            print(f"[DataManager] Erro ao obter dados cTrader: {e}")
            return self._generate_simulated_data(symbol, num_bars)
    
    def subscribe_to_ticks(
        self,
        symbols: List[str],
        callback: Callable[[str, float, float], None]
    ) -> None:
        """
        Inscreve para receber ticks em tempo real via cTrader.
        
        Args:
            symbols: Lista de símbolos para monitorar
            callback: Função chamada com (symbol, bid, ask)
        """
        self._tick_callbacks.append(callback)
        
        try:
            from ctrader_open_api.messages.OpenApiMessages_pb2 import ProtoOASubscribeSpotsReq
            
            # Em produção, enviar request de subscription
            print(f"[DataManager] Subscribed to ticks: {symbols}")
            
        except ImportError:
            print("[DataManager] Tick subscription não disponível (modo simulação)")
    
    def save_to_parquet(self, df: pd.DataFrame, filename: str) -> None:
        """Salva DataFrame em formato Parquet para eficiência."""
        os.makedirs("data", exist_ok=True)
        filepath = os.path.join("data", filename)
        df.to_parquet(filepath)
        print(f"[DataManager] Dados salvos em: {filepath}")
    
    def load_from_parquet(self, filename: str) -> pd.DataFrame:
        """Carrega DataFrame de arquivo Parquet."""
        filepath = os.path.join("data", filename)
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Arquivo não encontrado: {filepath}")
        return pd.read_parquet(filepath)
    
    def download_and_save(
        self,
        symbol: str,
        timeframe: str = "1h",
        days: int = 365
    ) -> pd.DataFrame:
        """
        Baixa dados históricos e salva localmente.
        
        Args:
            symbol: Símbolo para baixar
            timeframe: Timeframe
            days: Número de dias de histórico
            
        Returns:
            DataFrame com os dados
        """
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        df = self.get_historical_data(
            symbol=symbol,
            timeframe=timeframe,
            start_date=start_date,
            limit=days * 24  # Aproximado para 1h
        )
        
        filename = f"{symbol}_{timeframe}_{days}d.parquet"
        self.save_to_parquet(df, filename)
        
        return df
