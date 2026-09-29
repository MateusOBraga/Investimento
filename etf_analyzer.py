"""
etf_analyzer.py
Análise de ETFs (fundos de índice) listados na B3.

ETFs replicam um índice (Ibovespa, S&P 500, small caps etc), então não faz
sentido usar indicadores fundamentalistas de empresa individual (P/L, ROE,
dívida...). A análise aqui foca no comportamento técnico do preço
(tendência, RSI, MACD) e no retorno acumulado no período escolhido.

IMPORTANTE: ferramenta educacional. Não constitui recomendação de
investimento. Consulte um profissional certificado antes de investir.
"""

import pandas as pd
from data_fetcher import get_price_history, get_fundamentals
from recommender import _score_technical, _classificar


def analyze_etf(ticker: str, months: int = 12) -> dict:
    """Executa a análise técnica de um ETF (não há score fundamentalista aqui)."""
    df = get_price_history(ticker, months=months)
    fund = get_fundamentals(ticker)
    tecnico = _score_technical(df)

    preco_inicial = float(df["Close"].iloc[0])
    preco_final = float(df["Close"].iloc[-1])
    retorno_periodo_pct = ((preco_final / preco_inicial) - 1) * 100 if preco_inicial else 0.0

    # ETFs: a recomendação usa só o score técnico, já que não existe
    # "fundamento de empresa" para um fundo que replica um índice inteiro.
    recomendacao = _classificar(tecnico["score_tecnico"])

    return {
        "ticker": fund["ticker"],
        "nome": fund.get("nome") or fund["ticker"],
        "preco_atual": tecnico["preco_atual"],
        "score_tecnico": tecnico["score_tecnico"],
        "recomendacao": recomendacao,
        "rsi": tecnico["rsi"],
        "retorno_periodo_pct": round(retorno_periodo_pct, 2),
        "detalhes_tecnicos": tecnico["detalhes_tecnicos"],
        "dataframe_precos": df,
    }


def analyze_multiple_etfs(tickers: list, months: int = 12) -> pd.DataFrame:
    """Analisa uma lista de ETFs e retorna um DataFrame resumo, ordenado pelo score técnico."""
    linhas = []
    for t in tickers:
        try:
            r = analyze_etf(t, months=months)
            linhas.append({
                "Ticker": r["ticker"],
                "Nome": r["nome"],
                "Preço": r["preco_atual"],
                "Retorno no Período (%)": r["retorno_periodo_pct"],
                "Score Técnico": r["score_tecnico"],
                "Recomendação": r["recomendacao"],
                "RSI": r["rsi"],
            })
        except Exception as e:
            linhas.append({"Ticker": t, "Nome": None, "Preço": None,
                            "Retorno no Período (%)": None, "Score Técnico": None,
                            "Recomendação": f"Erro: {e}", "RSI": None})
    resultado = pd.DataFrame(linhas)
    if "Score Técnico" in resultado.columns:
        resultado = resultado.sort_values("Score Técnico", ascending=False, na_position="last")
    return resultado.reset_index(drop=True)
