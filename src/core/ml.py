"""
Gastor v9 - Machine Learning Core

Módulo para treinar modelos de ML baseados em trades manuais.
"""

import pandas as pd
import numpy as np
import joblib
import logging
from typing import Dict, Any, List, Tuple, Optional
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score, precision_score, recall_score
from sklearn.preprocessing import StandardScaler
import xgboost as xgb
import lightgbm as lgb

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("GastorML")


class FeatureExtractor:
    """Extrai features técnicas para o modelo."""
    
    @staticmethod
    def extract_features(df: pd.DataFrame) -> pd.DataFrame:
        """
        Gera features a partir do dataframe de candles.
        Retorna df com features normalizadas e prontas para ML.
        """
        data = df.copy()
        
        # Garante que colunas básicas existem (se não, ignora ou recalcula - idealmente já vêm do app)
        required_cols = ['close', 'ema9', 'ema21', 'ema50', 'rsi', 'bb_upper', 'bb_lower', 'bb_mid', 'macd_hist']
        missing = [c for c in required_cols if c not in data.columns]
        if missing:
            logger.warning(f"Features faltando no DF original: {missing}")
            # Aqui poderíamos recalcular, mas assumiremos que o app passa completo
        
        features = pd.DataFrame(index=data.index)
        
        # 1. Features Relativas (evitar preços absolutos)
        
        # Distância das Médias (%)
        if 'ema9' in data.columns:
            features['dist_ema9'] = (data['close'] - data['ema9']) / data['ema9']
        if 'ema21' in data.columns:
            features['dist_ema21'] = (data['close'] - data['ema21']) / data['ema21']
        if 'ema50' in data.columns:
            features['dist_ema50'] = (data['close'] - data['ema50']) / data['ema50']
        
        # RSI (já é relativo)
        if 'rsi' in data.columns:
            features['rsi'] = data['rsi'] / 100.0  # Normaliza 0-1
        
        # Bollinger (%B e Width)
        if 'bb_upper' in data.columns and 'bb_lower' in data.columns:
            features['bb_pband'] = (data['close'] - data['bb_lower']) / (data['bb_upper'] - data['bb_lower'])
            features['bb_width'] = (data['bb_upper'] - data['bb_lower']) / data['bb_mid']

        # MACD (Histograma já é relativo ao preço de certa forma, mas normalizar é melhor)
        # Vamos manter o raw por enquanto ou escalar pelo preço
        if 'macd_hist' in data.columns:
            features['macd_hist'] = data['macd_hist']

        # 2. Features Temporais (Novas)
        # Convertemos index para datetime se não for
        if not pd.api.types.is_datetime64_any_dtype(data.index):
             data.index = pd.to_datetime(data.index)
             
        features['hour'] = data.index.hour
        features['day_of_week'] = data.index.dayofweek
        
        # Period: 0=Dawn(0-6), 1=Morning(6-12), 2=Afternoon(12-18), 3=Night(18-24)
        # Usamos cut com labels numéricos para o modelo entender
        features['period'] = pd.cut(data.index.hour, bins=[-1, 5, 11, 17, 24], labels=[0, 1, 2, 3]).astype(int)

        # Preenche NaNs resultantes de indicadores (ex: primeiros 50 candles da EMA)
        features.fillna(0, inplace=True)
        
        
        # Retornos Recentes (Momentum)
        features['ret_1h'] = data['close'].pct_change(1)
        features['ret_4h'] = data['close'].pct_change(4)
        features['ret_24h'] = data['close'].pct_change(24)
        
        # Volatilidade
        features['volatility'] = data['close'].pct_change().rolling(24).std()
        
        # Limpeza (Remove NaN gerados por lags/rolling)
        features = features.replace([np.inf, -np.inf], np.nan).dropna()
        
        return features


class TradeModel:
    """Modelo de ML para prever trades."""
    
    SUPPORTED_MODELS = {
        'Random Forest': 'rf',
        'XGBoost': 'xgb',
        'LightGBM': 'lgb',
        'Logistic Regression': 'lr',
        'Gradient Boosting': 'gb'
    }
    
    def __init__(self, model_name='Random Forest'):
        self.model_name = model_name
        self.model_key = self.SUPPORTED_MODELS.get(model_name, 'rf')
        self.model = self._create_model()
        self.scaler = StandardScaler()
        self.features_list = []
        self.metrics = {}  # Armazena métricas do último treino
        
    def _create_model(self):
        """Instancia o modelo baseado na escolha."""
        if self.model_key == 'rf':
            return RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42, class_weight='balanced')
        elif self.model_key == 'xgb':
            return xgb.XGBClassifier(n_estimators=100, max_depth=6, learning_rate=0.1, random_state=42, eval_metric='logloss')
        elif self.model_key == 'lgb':
            return lgb.LGBMClassifier(n_estimators=100, max_depth=6, learning_rate=0.1, random_state=42, verbose=-1)
        elif self.model_key == 'lr':
            return LogisticRegression(random_state=42, max_iter=1000, class_weight='balanced')
        elif self.model_key == 'gb':
            return GradientBoostingClassifier(n_estimators=100, learning_rate=0.1, max_depth=3, random_state=42)
        else:
            return RandomForestClassifier(random_state=42)
    
    def prepare_data(self, df: pd.DataFrame, trades: List[Dict], feature_cols: List[str] = None) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Prepara dataset de treino (X, y).
        """
        features_df = FeatureExtractor.extract_features(df)
        
        # Filtragem de Features
        if feature_cols:
            # Filtra apenas colunas que existem no DF extraído
            valid_cols = [c for c in feature_cols if c in features_df.columns]
            if not valid_cols:
                # Se nenhuma for válida (erro de config), usa todas
                self.features_list = features_df.columns.tolist()
            else:
                features_df = features_df[valid_cols]
                self.features_list = valid_cols
        else:
            self.features_list = features_df.columns.tolist()
        
        # Cria target array (Series)
        y = pd.Series(0, index=features_df.index, name='target')
        
        # Marca pontos
        count_buy = 0
        count_sell = 0
        
        for trade in trades:
            ts = pd.to_datetime(trade['timestamp'])
            
            # Busca index mais próximo
            try:
                # Tolerância de 1h
                idx_loc = features_df.index.get_indexer([ts], method='nearest')[0]
                actual_ts = features_df.index[idx_loc]
                
                if abs(actual_ts - ts) < pd.Timedelta(hours=2):
                    action_code = 1 if trade['action'] == 'BUY' else -1
                    y.loc[actual_ts] = action_code
                    if action_code == 1: count_buy += 1
                    else: count_sell += 1
                    
            except Exception as e:
                pass
                
        logger.info(f"Trades marcados no dataset: BUY={count_buy}, SELL={count_sell}")
        return features_df, y
    
    def train(self, df: pd.DataFrame, trades: List[Dict], feature_cols: List[str] = None):
        """Treina o modelo com os dados fornecidos."""
        X, y_raw = self.prepare_data(df, trades, feature_cols)
        
        # Filtra apenas dados válidos para treino (onde há sinal ou hold explícito)
        # Estratégia: Usar todos os sinais + amostra de holds
        
        mask_signal = y_raw != 0
        mask_hold = y_raw == 0
        
        X_signal = X[mask_signal]
        y_signal = y_raw[mask_signal]
        
        # Balanceamento: 3x Holds para cada Sinal
        n_holds = min(len(X) - len(X_signal), len(X_signal) * 3)
        # Garante mínimo de holds
        n_holds = max(n_holds, 100) 
        
        if len(X[mask_hold]) >= n_holds:
            X_hold = X[mask_hold].sample(n=n_holds, random_state=42)
            y_hold = y_raw[mask_hold].loc[X_hold.index]
        else:
            X_hold = X[mask_hold]
            y_hold = y_raw[mask_hold]
            
        X_train = pd.concat([X_signal, X_hold])
        y_train = pd.concat([y_signal, y_hold])
        
        # Mapeamento para XGBoost/LGBM se necessário (classes 0,1,2)
        # SELL(-1)->0, HOLD(0)->1, BUY(1)->2
        if self.model_key in ['xgb', 'lgb']:
            y_train = y_train.map({-1: 0, 0: 1, 1: 2})
            
        if len(X_train) < 10:
            return {"error": "Dados insuficientes para treino (min 10 amostras)"}
            
        # Scaling
        X_scaled = self.scaler.fit_transform(X_train)
        
        # Fit
        self.model.fit(X_scaled, y_train)
        
        # Métricas (no próprio treino, pois dataset é pequeno demais pra split 70/30 robusto aqui)
        preds = self.model.predict(X_scaled)
        acc = accuracy_score(y_train, preds)
        
        # Calcula precision/recall média macro
        report = classification_report(y_train, preds, output_dict=True, zero_division=0)
        
        self.metrics = {
            "accuracy": acc,
            "precision": report['macro avg']['precision'],
            "recall": report['macro avg']['recall'],
            "support": len(y_train)
        }
        
        return self.metrics
    
    def predict(self, df: pd.DataFrame) -> pd.Series:
        """
        Executa inferência.
        Retorna Series com: 1 (Buy), -1 (Sell), 0 (Hold)
        """
        X = FeatureExtractor.extract_features(df)
        
        # Filtra colunas
        if self.features_list:
            # Adiciona colunas faltantes com 0 se necessário (segurança)
            for col in self.features_list:
                if col not in X.columns:
                    X[col] = 0
            X = X[self.features_list]
            
        X_scaled = self.scaler.transform(X)
        preds = self.model.predict(X_scaled)
        
        # Remapeia se for XGB/LGBM (0->-1, 1->0, 2->1)
        if self.model_key in ['xgb', 'lgb']:
            # De: 0=Sell, 1=Hold, 2=Buy
            # Para: -1=Sell, 0=Hold, 1=Buy
            mapper = {0: -1, 1: 0, 2: 1}
            preds = [mapper.get(x, 0) for x in preds]
            
        return pd.Series(preds, index=X.index)
    
    def save(self, filepath: str):
        joblib.dump({
            'model': self.model,
            'scaler': self.scaler,
            'features': self.features_list,
            'model_name': self.model_name,
            'metrics': self.metrics
        }, filepath)
    
    def load(self, filepath: str):
        data = joblib.load(filepath)
        self.model = data['model']
        self.scaler = data['scaler']
        self.features_list = data['features']
        self.model_name = data.get('model_name', 'Unknown')
        self.metrics = data.get('metrics', {})

