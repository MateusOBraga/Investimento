"""
fii_recommender.py
Análise e recomendações para Fundos Imobiliários (FIIs) listados na B3.

FIIs têm uma lógica fundamentalista diferente da de ações: não existe
P/L nem ROE no sentido tradicional (o fundo não "dá lucro" como uma
empresa — ele distribui o resultado dos aluguéis/juros que recebe).
O que mais importa costuma ser:
  - P/VP: preço da cota em relação ao valor patrimonial por cota
  - Dividend Yield: a maioria dos FIIs distribui quase todo o resultado
    mensalmente, e essa distribuição é isenta de Imposto de Renda para
    pessoa física (dentro das regras vigentes).

IMPORTANTE: ferramenta educacional. Não constitui recomendação de
investimento. Consulte um profissional certificado antes de investir.
"""

import pandas as pd
from data_fetcher import get_price_history, get_fundamentals
from recommender import _score_technical, _classificar


def _score_fundamental_fii(fund: dict) -> dict:
    """Calcula pontuação fundamentalista (0-100) adaptada para FIIs."""
    score = 50
    detalhes = []

    pvp = fund.get("p_vp")
    if pvp is not None and pvp > 0:
        if pvp < 0.95:
            score += 20
            detalhes.append(f"P/VP de {pvp:.2f} sugere cota negociada com desconto sobre o patrimônio.")
        elif pvp <= 1.05:
            score += 5
            detalhes.append(f"P/VP de {pvp:.2f} está próximo do valor patrimonial (preço considerado justo).")
        elif pvp <= 1.15:
            detalhes.append(f"P/VP de {pvp:.2f} indica um pequeno ágio sobre o patrimônio.")
        else:
            score -= 15
            detalhes.append(f"P/VP de {pvp:.2f} indica ágio elevado — cota pode estar cara.")
    else:
        detalhes.append("P/VP não disponível para este fundo no momento.")

    dy = fund.get("dividend_yield")
    if dy is not None:
        dy_pct = dy * 100 if dy < 1 else dy
        if dy_pct >= 12:
            score += 10
            detalhes.append(f"Dividend Yield de {dy_pct:.1f}% é bem alto — vale checar se é sustentável (pode incluir venda de ativos).")
        elif dy_pct >= 8:
            score += 20
            detalhes.append(f"Dividend Yield de {dy_pct:.1f}% é bastante atrativo para o setor de FIIs.")
        elif dy_pct >= 5:
            score += 10
            detalhes.append(f"Dividend Yield de {dy_pct:.1f}% é razoável.")
        else:
            detalhes.append(f"Dividend Yield de {dy_pct:.1f}% está abaixo da média típica do setor de FIIs.")
    else:
        detalhes.append("Dividend Yield não disponível para este fundo no momento.")

    score = max(0, min(100, score))
    return {"score_fundamental": round(score, 1), "detalhes_fundamentais": detalhes}


def analyze_fii(ticker: str, months: int = 12, peso_tecnico: float = 0.4) -> dict:
    """
    Executa a análise completa de um FII.
    peso_tecnico: peso do score técnico (gráfico) na nota final. Para FIIs,
                  costuma fazer sentido usar um peso técnico menor (ex: 0.3-0.4),
                  já que P/VP e Dividend Yield tendem a pesar mais na decisão.
    """
    df = get_price_history(ticker, months=months)
    fund = get_fundamentals(ticker)

    tecnico = _score_technical(df)
    fundamental = _score_fundamental_fii(fund)

    score_final = (
        tecnico["score_tecnico"] * peso_tecnico
        + fundamental["score_fundamental"] * (1 - peso_tecnico)
    )
    recomendacao = _classificar(score_final)

    return {
        "ticker": fund["ticker"],
        "nome": fund.get("nome") or fund["ticker"],
        "segmento": fund.get("setor") or "Fundo Imobiliário",
        "preco_atual": tecnico["preco_atual"],
        "score_final": round(score_final, 1),
        "recomendacao": recomendacao,
        "score_tecnico": tecnico["score_tecnico"],
        "score_fundamental": fundamental["score_fundamental"],
        "rsi": tecnico["rsi"],
        "p_vp": fund.get("p_vp"),
        "dividend_yield": fund.get("dividend_yield"),
        "detalhes_tecnicos": tecnico["detalhes_tecnicos"],
        "detalhes_fundamentais": fundamental["detalhes_fundamentais"],
        "dataframe_precos": df,
    }


def analyze_multiple_fiis(tickers: list, months: int = 12, peso_tecnico: float = 0.4) -> pd.DataFrame:
    """Analisa uma lista de FIIs e retorna um DataFrame resumo, ordenado pelo score final."""
    linhas = []
    for t in tickers:
        try:
            r = analyze_fii(t, months=months, peso_tecnico=peso_tecnico)
            linhas.append({
                "Ticker": r["ticker"],
                "Nome": r["nome"],
                "Segmento": r["segmento"],
                "Preço": r["preco_atual"],
                "Score Final": r["score_final"],
                "Recomendação": r["recomendacao"],
                "Score Técnico": r["score_tecnico"],
                "Score Fundamental": r["score_fundamental"],
                "P/VP": r["p_vp"],
                "Div. Yield": r["dividend_yield"],
            })
        except Exception as e:
            linhas.append({"Ticker": t, "Nome": None, "Segmento": None, "Preço": None,
                            "Score Final": None, "Recomendação": f"Erro: {e}",
                            "Score Técnico": None, "Score Fundamental": None,
                            "P/VP": None, "Div. Yield": None})
    resultado = pd.DataFrame(linhas)
    if "Score Final" in resultado.columns:
        resultado = resultado.sort_values("Score Final", ascending=False, na_position="last")
    return resultado.reset_index(drop=True)
