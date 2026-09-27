"""
data_fetcher.py
Busca dados de preço histórico e indicadores fundamentalistas
de ações da B3 usando a biblioteca yfinance (dados do Yahoo Finance).

Observação: no Yahoo Finance, tickers da B3 usam o sufixo ".SA"
Ex: PETR4.SA, VALE3.SA, ITUB4.SA
"""

import yfinance as yf
import pandas as pd


# Lista ampla de ações da B3, organizada por setor (pode editar/expandir à vontade).
# Cobre a grande maioria das ações com liquidez relevante na bolsa brasileira.
# Alguns tickers mudaram de código recentemente (ex: Eletrobras ELET3 -> AXIA3,
# Embraer EMBR3 -> EMBJ3, Natura NTCO3 -> NATU3, Guararapes GUAR3 -> RIAA3);
# a lista já usa os códigos mais recentes conhecidos. Se algum ticker tiver sido
# alterado ou deslistado após a criação deste projeto, ele simplesmente aparecerá
# com erro na tabela de análise, sem quebrar o restante do app.
DEFAULT_TICKERS = [
    # Bancos e Serviços Financeiros
    "ITUB4.SA", "ITUB3.SA", "BBDC4.SA", "BBDC3.SA", "BBAS3.SA",
    "SANB11.SA", "SANB3.SA", "SANB4.SA", "BPAC11.SA",
    "ABCB4.SA", "BRSR6.SA", "BMGB4.SA", "PINE4.SA", "BAZA3.SA",
    "BEES3.SA", "ITSA4.SA", "ITSA3.SA", "B3SA3.SA", "WIZC3.SA", "BRBI11.SA",

    # Seguros e Previdência
    "BBSE3.SA", "PSSA3.SA", "IRBR3.SA", "CXSE3.SA", "APER3.SA",

    # Energia Elétrica e Saneamento
    "AXIA3.SA", "CMIG4.SA", "CMIG3.SA",
    "CPLE3.SA", "TAEE11.SA", "EQTL3.SA", "ENGI11.SA", "CPFE3.SA",
    "EGIE3.SA", "AURE3.SA", "CSMG3.SA", "SBSP3.SA",
    "SAPR11.SA", "ALUP11.SA", "LIGT3.SA", "ENEV3.SA", "ORVR3.SA", "RNEW11.SA",

    # Petróleo, Gás e Biocombustíveis
    "PETR3.SA", "PETR4.SA", "PRIO3.SA", "RECV3.SA", "UGPA3.SA",
    "VBBR3.SA", "CSAN3.SA", "RAIZ4.SA", "BRAV3.SA",

    # Mineração e Siderurgia
    "VALE3.SA", "CSNA3.SA", "GGBR4.SA", "GGBR3.SA", "GOAU4.SA",
    "USIM5.SA", "USIM3.SA", "CMIN3.SA", "BRAP4.SA", "FESA4.SA", "PATI3.SA",

    # Papel, Celulose e Química
    "SUZB3.SA", "KLBN11.SA", "KLBN4.SA", "RANI3.SA", "BRKM5.SA", "UNIP6.SA",
    "FHER3.SA", "DEXP3.SA",

    # Bens de Capital e Industrial
    "WEGE3.SA", "EMBJ3.SA", "RAPT4.SA", "POMO4.SA", "TUPY3.SA",
    "KEPL3.SA", "LEVE3.SA", "FRAS3.SA", "MYPK3.SA", "SHUL4.SA",
    "ROMI3.SA", "EALT4.SA",

    # Agronegócio
    "SLCE3.SA", "SOJA3.SA", "AGRO3.SA", "SMTO3.SA", "JALL3.SA", "TTEN3.SA",

    # Alimentos e Bebidas
    "ABEV3.SA", "BEEF3.SA", "CAML3.SA", "MDIA3.SA", "SMFT3.SA", "BAUH4.SA",

    # Varejo e Consumo
    "MGLU3.SA", "LREN3.SA", "RENT3.SA", "VIVA3.SA",
    "SBFG3.SA", "CEAB3.SA", "RIAA3.SA", "LJQQ3.SA",
    "PCAR3.SA", "ASAI3.SA", "GMAT3.SA", "ALPA4.SA", "AMER3.SA",
    "TFCO4.SA", "VULC3.SA", "GRND3.SA", "TECN3.SA", "CEDO4.SA", "SGPS3.SA",

    # Saúde
    "HAPV3.SA", "RDOR3.SA", "FLRY3.SA", "QUAL3.SA",
    "HYPE3.SA", "RADL3.SA", "PNVL3.SA", "BIOM3.SA", "ONCO3.SA",
    "MATD3.SA", "AALR3.SA", "BLAU3.SA", "PGMN3.SA", "DASA3.SA",

    # Educação
    "YDUQ3.SA", "COGN3.SA", "SEER3.SA", "ANIM3.SA",

    # Tecnologia
    "TOTS3.SA", "LWSA3.SA", "POSI3.SA", "IFCM3.SA",
    "CASH3.SA", "TRAD3.SA", "NGRD3.SA", "ENJU3.SA", "MLAS3.SA", "DOTZ3.SA",

    # Telecomunicações
    "VIVT3.SA", "TIMS3.SA", "OIBR3.SA", "OIBR4.SA",
    "DESK3.SA", "BRIT3.SA", "FIQE3.SA",

    # Construção Civil e Imobiliário
    "CYRE3.SA", "EZTC3.SA", "MRVE3.SA", "TEND3.SA", "DIRR3.SA",
    "EVEN3.SA", "HBOR3.SA", "TRIS3.SA", "CURY3.SA", "PLPL3.SA",
    "LAVV3.SA", "JHSF3.SA", "GFSA3.SA", "MELK3.SA",

    # Shoppings e Propriedades Comerciais
    "MULT3.SA", "IGTI11.SA", "ALOS3.SA",

    # Logística e Transporte
    "RAIL3.SA", "ECOR3.SA", "JSLG3.SA",
    "SIMH3.SA", "VAMO3.SA", "MOVI3.SA", "TGMA3.SA", "HBSA3.SA", "PORT3.SA",

    # Outros / Diversos
    "CVCB3.SA", "LOGG3.SA", "NATU3.SA", "WLMM4.SA",
]


def normalize_ticker(ticker: str) -> str:
    """Garante que o ticker tenha o sufixo .SA (bolsa brasileira)."""
    ticker = ticker.strip().upper()
    if not ticker.endswith(".SA"):
        ticker += ".SA"
    return ticker


def get_price_history(ticker: str, months: int = 12, interval: str = "1d") -> pd.DataFrame:
    """
    Retorna DataFrame com colunas: Open, High, Low, Close, Volume
    months: quantidade de meses de histórico a buscar (ex: 3, 6, 12, 24, 60)
    interval: ex. '1d', '1wk'
    """
    ticker = normalize_ticker(ticker)
    end = pd.Timestamp.today()
    start = end - pd.DateOffset(months=months)
    df = yf.Ticker(ticker).history(start=start, end=end, interval=interval, auto_adjust=True)
    if df is None or df.empty:
        raise ValueError(f"Não foi possível obter dados para {ticker}. Verifique o código da ação.")
    df.index = pd.to_datetime(df.index)
    return df


def get_fundamentals(ticker: str) -> dict:
    """
    Retorna um dicionário com os principais indicadores fundamentalistas
    disponíveis via yfinance. Campos ausentes retornam None.
    """
    ticker = normalize_ticker(ticker)
    info = {}
    try:
        info = yf.Ticker(ticker).info or {}
    except Exception:
        info = {}

    def g(key):
        return info.get(key, None)

    return {
        "ticker": ticker,
        "nome": g("longName") or g("shortName"),
        "setor": g("sector"),
        "industria": g("industry"),
        "preco_atual": g("currentPrice") or g("regularMarketPrice"),
        "pl": g("trailingPE"),                 # Preço/Lucro
        "p_vp": g("priceToBook"),              # Preço/Valor Patrimonial
        "dividend_yield": g("dividendYield"),  # em fração (ex: 0.05 = 5%)
        "roe": g("returnOnEquity"),
        "margem_liquida": g("profitMargins"),
        "divida_patrimonio": g("debtToEquity"),
        "valor_mercado": g("marketCap"),
        "beta": g("beta"),
        "crescimento_receita": g("revenueGrowth"),
        "recomendacao_analistas": g("recommendationKey"),
    }
