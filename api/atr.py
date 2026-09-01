from http.server import BaseHTTPRequestHandler
import json
import pandas as pd
import numpy as np
import yfinance as yf
import requests

SESSION_YAHOO = requests.Session()
SESSION_YAHOO.headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'

ACTIVOS = {
    "AUD/JPY": "AUDJPY=X", "AUD/USD": "AUDUSD=X", "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X", "USD/CAD": "USDCAD=X", "USD/JPY": "USDJPY=X",
    "Bitcoin / JPY": "BTC-JPY", "Bitcoin / USD": "BTC-USD", "Ethereum / BTC": "ETH-BTC",
    "Ethereum / USD": "ETH-USD", "IOST Token / USD": "IOST-USD",
    "AUS 200": "EWA", "Hong Kong 50": "EWH", "Japan 225": "EWJ",
    "UK 100": "ISF.L", "US 30 (Dow Jones)": "DIA", "US 500 (S&P 500)": "SPY", "US Tech (US 100)": "QQQ",
    "Crude Oil (Brent)": "BZ=F", "Crude Oil (WTI)": "CL=F",
    "Gold / USD": "GC=F", "Silver / USD": "SI=F", "Natural Gas": "NG=F"
}

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        resultados = []
        periodo_atr = 14

        for nombre, simbolo in ACTIVOS.items():
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
                    
                    resultados.append({
                        "activo": nombre,
                        "precio": round(float(precio_actual), 4),
                        "atr": round(float(atr), 4)
                    })
            except Exception:
                pass

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(resultados).encode('utf-8'))