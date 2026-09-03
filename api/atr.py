from http.server import BaseHTTPRequestHandler
import json
import pandas as pd
import numpy as np
import yfinance as yf
import requests

SESSION_YAHOO = requests.Session()
SESSION_YAHOO.headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'

# Activos categorizados para aplicar multiplicadores dinámicos
ACTIVOS = {
    "Forex": {"AUD/JPY": "AUDJPY=X", "AUD/USD": "AUDUSD=X", "EUR/USD": "EURUSD=X", "GBP/USD": "GBPUSD=X", "USD/CAD": "USDCAD=X", "USD/JPY": "USDJPY=X"},
    "Crypto": {"BTC/JPY": "BTC-JPY", "BTC/USD": "BTC-USD", "ETH/BTC": "ETH-BTC", "ETH/USD": "ETH-USD"},
    "Indices": {"AUS 200": "EWA", "HK 50": "EWH", "Japan 225": "EWJ", "UK 100": "ISF.L", "US 30": "DIA", "US 500": "SPY", "US Tech": "QQQ"},
    "Materias": {"Brent": "BZ=F", "WTI": "CL=F", "Oro": "GC=F", "Plata": "SI=F", "Gas": "NG=F"}
}

# Multiplicadores de SL dinámicos según el mercado (Punto 2)
MULTIPLICADORES = {
    "Forex": 1.5,     # Mercado más estable
    "Crypto": 2.0,    # Alta volatilidad, necesita más respiro
    "Indices": 1.8,   # Volatilidad media-alta
    "Materias": 1.7
}

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        resultados = []
        periodo_atr = 14

        for categoria, activos_dict in ACTIVOS.items():
            multiplicador = MULTIPLICADORES[categoria]
            for nombre, simbolo in activos_dict.items():
                try:
                    ticker = yf.Ticker(simbolo, session=SESSION_YAHOO)
                    df = ticker.history(period="5d", interval="15m")
                    
                    if df is not None and not df.empty:
                        df = df.dropna().rename(columns={'High': 'high', 'Low': 'low', 'Close': 'close'})
                        
                        prev_close = df['close'].shift(1)
                        tr = pd.concat([
                            df['high'] - df['low'],
                            (df['high'] - prev_close).abs(),
                            (df['low'] - prev_close).abs(),
                        ], axis=1).max(axis=1)
                        
                        atr = tr.ewm(alpha=1/periodo_atr, adjust=False).mean().iloc[-1]
                        precio_actual = df['close'].iloc[-1]
                        
                        # Solo enviamos la distancia base, el frontend calculará el resto
                        distancia_sl = atr * multiplicador
                        
                        resultados.append({
                            "activo": nombre,
                            "categoria": categoria,
                            "precio": round(float(precio_actual), 4),
                            "atr": round(float(atr), 4),
                            "distancia_sl": round(float(distancia_sl), 4)
                        })
                except Exception:
                    pass

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(resultados).encode('utf-8'))
