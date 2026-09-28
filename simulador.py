"""
simulador.py
Simulador simples de aportes mensais (estratégia de aportes regulares /
"preço médio", também chamada de Dollar-Cost Averaging) em uma ação da B3.
"""

import pandas as pd
import yfinance as yf
from data_fetcher import normalize_ticker


def simulate_dca(ticker: str, aporte_mensal: float, meses: int) -> dict:
    """
    Simula aportes mensais de valor fixo em uma ação, comprando ao preço de
    fechamento de cada mês, e retorna o resultado comparado ao total investido.

    ticker: código da ação (ex: 'PETR4' ou 'PETR4.SA')
    aporte_mensal: valor em R$ investido todo mês
    meses: quantidade de meses a simular (olhando para o histórico)
    """
    ticker = normalize_ticker(ticker)
    end = pd.Timestamp.today()
    start = end - pd.DateOffset(months=meses + 1)
    df = yf.Ticker(ticker).history(start=start, end=end, interval="1mo", auto_adjust=True)
    if df is None or df.empty:
        raise ValueError(f"Não foi possível obter dados para {ticker}.")

    df = df.tail(meses)  # garante no máximo 'meses' aportes
    unidades = 0.0
    total_investido = 0.0
    historico = []

    for data, linha in df.iterrows():
        preco = linha["Close"]
        if pd.isna(preco) or preco <= 0:
            continue
        unidades += aporte_mensal / preco
        total_investido += aporte_mensal
        historico.append({
            "data": data,
            "preco": round(float(preco), 2),
            "total_investido": round(total_investido, 2),
            "valor_carteira": round(unidades * preco, 2),
        })

    if not historico:
        raise ValueError(f"Não há dados suficientes de {ticker} para simular esse período.")

    preco_atual = float(df["Close"].iloc[-1])
    valor_atual = unidades * preco_atual
    lucro = valor_atual - total_investido
    rentabilidade_pct = (lucro / total_investido * 100) if total_investido > 0 else 0.0

    return {
        "ticker": ticker,
        "aporte_mensal": aporte_mensal,
        "meses_aportados": len(historico),
        "total_investido": round(total_investido, 2),
        "unidades_compradas": round(unidades, 4),
        "preco_medio": round(total_investido / unidades, 2) if unidades > 0 else 0,
        "preco_atual": round(preco_atual, 2),
        "valor_atual": round(valor_atual, 2),
        "lucro": round(lucro, 2),
        "rentabilidade_pct": round(rentabilidade_pct, 2),
        "historico": pd.DataFrame(historico),
    }
