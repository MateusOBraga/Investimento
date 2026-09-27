"""
recommender.py
Combina indicadores técnicos e fundamentalistas em uma pontuação (0-100)
e gera uma recomendação: COMPRAR, MANTER ou VENDER.

IMPORTANTE: Isso é uma ferramenta educacional de apoio à análise.
NÃO constitui recomendação de investimento profissional.
Sempre faça sua própria análise (ou consulte um profissional certificado - CVM/CFP)
antes de investir.
"""

import pandas as pd
from indicators import sma, rsi, macd, bollinger_bands, volume_trend
from data_fetcher import get_price_history, get_fundamentals


def _score_technical(df: pd.DataFrame) -> dict:
    """Calcula sub-pontuações técnicas (0-100 cada) a partir do histórico de preços."""
    close = df["Close"]

    sma20 = sma(close, 20)
    sma50 = sma(close, 50)
    sma200 = sma(close, 200)
    rsi14 = rsi(close, 14)
    macd_line, signal_line, hist = macd(close)
    upper_bb, mid_bb, lower_bb = bollinger_bands(close)
    vol_trend = volume_trend(df["Volume"])

    preco = close.iloc[-1]
    scores = {}
    detalhes = []

    # 1) Tendência (médias móveis) - peso maior
    score_tendencia = 50
    if not pd.isna(sma50.iloc[-1]) and not pd.isna(sma200.iloc[-1]):
        if sma50.iloc[-1] > sma200.iloc[-1]:
            score_tendencia += 25
            detalhes.append("Média de 50 dias acima da de 200 dias (tendência de alta / 'golden cross').")
        else:
            score_tendencia -= 25
            detalhes.append("Média de 50 dias abaixo da de 200 dias (tendência de baixa / 'death cross').")
    if not pd.isna(sma20.iloc[-1]):
        if preco > sma20.iloc[-1]:
            score_tendencia += 10
        else:
            score_tendencia -= 10
    scores["tendencia"] = max(0, min(100, score_tendencia))

    # 2) RSI (sobrecompra/sobrevenda)
    rsi_atual = rsi14.iloc[-1]
    if rsi_atual < 30:
        score_rsi = 80
        detalhes.append(f"RSI em {rsi_atual:.1f}: ativo em zona de sobrevenda (possível oportunidade de compra).")
    elif rsi_atual > 70:
        score_rsi = 20
        detalhes.append(f"RSI em {rsi_atual:.1f}: ativo em zona de sobrecompra (risco de correção).")
    else:
        score_rsi = 50 + (50 - abs(rsi_atual - 50))  # quanto mais perto de 50, mais neutro/positivo
        detalhes.append(f"RSI em {rsi_atual:.1f}: zona neutra.")
    scores["rsi"] = max(0, min(100, score_rsi))

    # 3) MACD
    score_macd = 50
    if hist.iloc[-1] > 0 and hist.iloc[-2] <= 0:
        score_macd = 80
        detalhes.append("MACD acabou de cruzar para cima da linha de sinal (sinal de compra).")
    elif hist.iloc[-1] < 0 and hist.iloc[-2] >= 0:
        score_macd = 20
        detalhes.append("MACD acabou de cruzar para baixo da linha de sinal (sinal de venda).")
    elif hist.iloc[-1] > 0:
        score_macd = 65
        detalhes.append("Histograma do MACD positivo (momentum de alta).")
    else:
        score_macd = 35
        detalhes.append("Histograma do MACD negativo (momentum de baixa).")
    scores["macd"] = score_macd

    # 4) Bandas de Bollinger
    score_bb = 50
    if not pd.isna(lower_bb.iloc[-1]) and preco <= lower_bb.iloc[-1]:
        score_bb = 75
        detalhes.append("Preço tocando ou abaixo da banda inferior de Bollinger (possível barganha).")
    elif not pd.isna(upper_bb.iloc[-1]) and preco >= upper_bb.iloc[-1]:
        score_bb = 25
        detalhes.append("Preço tocando ou acima da banda superior de Bollinger (possível sobrevalorização de curto prazo).")
    scores["bollinger"] = score_bb

    # 5) Volume
    score_vol = 50
    if not pd.isna(vol_trend.iloc[-1]):
        if vol_trend.iloc[-1] > 1.5 and close.iloc[-1] > close.iloc[-2]:
            score_vol = 70
            detalhes.append("Alta recente com volume acima da média (confirma força do movimento).")
        elif vol_trend.iloc[-1] > 1.5 and close.iloc[-1] < close.iloc[-2]:
            score_vol = 30
            detalhes.append("Queda recente com volume acima da média (confirma pressão vendedora).")
    scores["volume"] = score_vol

    pesos = {"tendencia": 0.35, "rsi": 0.2, "macd": 0.25, "bollinger": 0.1, "volume": 0.1}
    score_final = sum(scores[k] * pesos[k] for k in pesos)

    return {
        "score_tecnico": round(score_final, 1),
        "sub_scores": scores,
        "detalhes_tecnicos": detalhes,
        "preco_atual": round(float(preco), 2),
        "rsi": round(float(rsi_atual), 1) if not pd.isna(rsi_atual) else None,
    }


def _score_fundamental(fund: dict) -> dict:
    """Calcula pontuação fundamentalista (0-100) a partir dos dados da empresa."""
    score = 50
    detalhes = []

    pl = fund.get("pl")
    if pl is not None and pl > 0:
        if pl < 10:
            score += 15
            detalhes.append(f"P/L de {pl:.1f}x é considerado baixo (ação possivelmente barata).")
        elif pl > 25:
            score -= 15
            detalhes.append(f"P/L de {pl:.1f}x é considerado alto (ação possivelmente cara).")
        else:
            detalhes.append(f"P/L de {pl:.1f}x está em faixa razoável.")
    elif pl is not None and pl <= 0:
        score -= 10
        detalhes.append("P/L negativo (empresa com prejuízo nos últimos 12 meses).")

    dy = fund.get("dividend_yield")
    if dy is not None:
        dy_pct = dy * 100 if dy < 1 else dy  # yfinance às vezes já retorna em %
        if dy_pct >= 6:
            score += 15
            detalhes.append(f"Dividend Yield de {dy_pct:.1f}% é atrativo.")
        elif dy_pct >= 3:
            score += 5
            detalhes.append(f"Dividend Yield de {dy_pct:.1f}% é moderado.")

    roe = fund.get("roe")
    if roe is not None:
        roe_pct = roe * 100 if abs(roe) < 1 else roe
        if roe_pct >= 15:
            score += 15
            detalhes.append(f"ROE de {roe_pct:.1f}% indica boa rentabilidade sobre o patrimônio.")
        elif roe_pct < 0:
            score -= 15
            detalhes.append(f"ROE negativo ({roe_pct:.1f}%) indica prejuízo sobre o patrimônio.")

    dte = fund.get("divida_patrimonio")
    if dte is not None:
        if dte > 150:
            score -= 10
            detalhes.append(f"Relação Dívida/Patrimônio elevada ({dte:.0f}%), indica maior alavancagem/risco.")
        elif dte < 50:
            score += 5
            detalhes.append(f"Relação Dívida/Patrimônio baixa ({dte:.0f}%), indica menor risco financeiro.")

    margem = fund.get("margem_liquida")
    if margem is not None:
        margem_pct = margem * 100 if abs(margem) < 1 else margem
        if margem_pct >= 15:
            score += 10
            detalhes.append(f"Margem líquida saudável de {margem_pct:.1f}%.")
        elif margem_pct < 0:
            score -= 10
            detalhes.append("Margem líquida negativa.")

    score = max(0, min(100, score))
    return {"score_fundamental": round(score, 1), "detalhes_fundamentais": detalhes}


def _classificar(score: float) -> str:
    if score >= 70:
        return "COMPRAR"
    elif score >= 45:
        return "MANTER"
    else:
        return "VENDER"


def analyze_ticker(ticker: str, months: int = 12, peso_tecnico: float = 0.6) -> dict:
    """
    Executa a análise completa de um ticker e retorna um dicionário com:
    score final, recomendação e detalhamento técnico/fundamentalista.

    months: quantidade de meses de histórico de preços a considerar.
    peso_tecnico: peso do score técnico na nota final (0 a 1).
                  O restante (1 - peso_tecnico) vai para o score fundamentalista.
    """
    df = get_price_history(ticker, months=months)
    fund = get_fundamentals(ticker)

    tecnico = _score_technical(df)
    fundamental = _score_fundamental(fund)

    score_final = (
        tecnico["score_tecnico"] * peso_tecnico
        + fundamental["score_fundamental"] * (1 - peso_tecnico)
    )
    recomendacao = _classificar(score_final)

    return {
        "ticker": fund["ticker"],
        "nome": fund.get("nome"),
        "setor": fund.get("setor"),
        "preco_atual": tecnico["preco_atual"],
        "score_final": round(score_final, 1),
        "recomendacao": recomendacao,
        "score_tecnico": tecnico["score_tecnico"],
        "score_fundamental": fundamental["score_fundamental"],
        "rsi": tecnico["rsi"],
        "pl": fund.get("pl"),
        "dividend_yield": fund.get("dividend_yield"),
        "roe": fund.get("roe"),
        "detalhes_tecnicos": tecnico["detalhes_tecnicos"],
        "detalhes_fundamentais": fundamental["detalhes_fundamentais"],
        "dataframe_precos": df,
    }


def analyze_multiple(tickers: list, months: int = 12, peso_tecnico: float = 0.6) -> pd.DataFrame:
    """Analisa uma lista de tickers e retorna um DataFrame resumo, ordenado pelo score final."""
    linhas = []
    for t in tickers:
        try:
            r = analyze_ticker(t, months=months, peso_tecnico=peso_tecnico)
            linhas.append({
                "Ticker": r["ticker"],
                "Nome": r["nome"],
                "Setor": r["setor"],
                "Preço": r["preco_atual"],
                "Score Final": r["score_final"],
                "Recomendação": r["recomendacao"],
                "Score Técnico": r["score_tecnico"],
                "Score Fundamental": r["score_fundamental"],
                "RSI": r["rsi"],
                "P/L": r["pl"],
                "Div. Yield": r["dividend_yield"],
                "ROE": r["roe"],
            })
        except Exception as e:
            linhas.append({"Ticker": t, "Nome": None, "Setor": None, "Preço": None,
                            "Score Final": None, "Recomendação": f"Erro: {e}",
                            "Score Técnico": None, "Score Fundamental": None,
                            "RSI": None, "P/L": None, "Div. Yield": None, "ROE": None})
    resultado = pd.DataFrame(linhas)
    if "Score Final" in resultado.columns:
        resultado = resultado.sort_values("Score Final", ascending=False, na_position="last")
    return resultado.reset_index(drop=True)
