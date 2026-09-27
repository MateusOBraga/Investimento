"""
app.py
Aplicação web (Streamlit) para análise de ações da B3 com recomendações
de investimento baseadas em indicadores técnicos e fundamentalistas.

Como rodar localmente:
    streamlit run app.py

Como publicar online (grátis):
    1. Suba este projeto para um repositório no GitHub.
    2. Acesse https://share.streamlit.io (Streamlit Community Cloud).
    3. Conecte sua conta GitHub e selecione o repositório.
    4. Defina "app.py" como arquivo principal e clique em Deploy.
    Veja o README.md para o passo a passo completo.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from data_fetcher import DEFAULT_TICKERS, normalize_ticker
from recommender import analyze_ticker, analyze_multiple
from indicators import sma, rsi, macd, bollinger_bands

st.set_page_config(page_title="Análise de Ações B3", page_icon="📈", layout="wide")


# ---------------------------------------------------------------------------
# Cache dos dados: evita bater no Yahoo Finance a cada clique, mas garante que
# os dados fiquem "velhos" no máximo por CACHE_TTL_SEGUNDOS.
# ---------------------------------------------------------------------------
CACHE_TTL_SEGUNDOS = 5 * 60  # 5 minutos


@st.cache_data(ttl=CACHE_TTL_SEGUNDOS, show_spinner=False)
def analyze_ticker_cached(ticker: str, months: int, peso_tecnico: float):
    return analyze_ticker(ticker, months=months, peso_tecnico=peso_tecnico)


@st.cache_data(ttl=CACHE_TTL_SEGUNDOS, show_spinner=False)
def analyze_multiple_cached(tickers: tuple, months: int, peso_tecnico: float):
    return analyze_multiple(list(tickers), months=months, peso_tecnico=peso_tecnico)


st.title("📈 Análise de Ações da B3 com Recomendações de Investimento")
st.caption(
    "BOA SORTE MANA"
)

# ---------------------------------------------------------------------------
# Barra lateral - configurações
# ---------------------------------------------------------------------------
st.sidebar.header("Configurações")

if st.sidebar.button("🔄 Atualizar dados agora"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.caption(
    f"Dados ficam em cache por até {CACHE_TTL_SEGUNDOS // 60} min antes de serem "
    "buscados de novo no Yahoo Finance."
)
st.sidebar.divider()

selecionar_todas = st.sidebar.checkbox(
    f"Selecionar todas as {len(DEFAULT_TICKERS)} ações da lista",
    value=False,
    help="Cuidado: analisar muitas ações de uma vez demora mais e pode esbarrar em "
         "limites de requisição do Yahoo Finance.",
)

tickers_selecionados = st.sidebar.multiselect(
    "Ações da B3",
    options=DEFAULT_TICKERS,
    default=DEFAULT_TICKERS if selecionar_todas else DEFAULT_TICKERS[:6],
)

tickers_customizados = st.sidebar.text_input(
    "Adicionar outros tickers (separados por vírgula)",
    placeholder="Ex: TOTS3, CYRE3, RAIL3",
)

unidade_periodo = st.sidebar.radio(
    "Unidade do período histórico",
    options=["Meses", "Anos"],
    horizontal=True,
)

if unidade_periodo == "Meses":
    quantidade_periodo = st.sidebar.slider(
        "Quantidade de meses de histórico", min_value=1, max_value=24, value=12,
    )
    meses_historico = quantidade_periodo
else:
    quantidade_periodo = st.sidebar.slider(
        "Quantidade de anos de histórico", min_value=1, max_value=10, value=1,
    )
    meses_historico = quantidade_periodo * 12

peso_tecnico = st.sidebar.slider(
    "Peso da Análise Técnica no Score Final",
    min_value=0.0, max_value=1.0, value=0.6, step=0.1,
    help="O restante do peso vai para a Análise Fundamentalista.",
)

lista_final = list(tickers_selecionados)
if tickers_customizados.strip():
    extras = [normalize_ticker(t) for t in tickers_customizados.split(",") if t.strip()]
    lista_final += extras

if not lista_final:
    st.warning("Selecione ao menos uma ação na barra lateral para começar.")
    st.stop()

# ---------------------------------------------------------------------------
# Resumo comparativo
# ---------------------------------------------------------------------------
st.subheader("🏆 Ranking Comparativo")

with st.spinner("Analisando ações selecionadas..."):
    tabela = analyze_multiple_cached(tuple(lista_final), meses_historico, peso_tecnico)


def cor_recomendacao(val):
    cores = {"COMPRAR": "background-color: #1e5c2a; color: white;",
             "MANTER": "background-color: #7a6a1e; color: white;",
             "VENDER": "background-color: #7a1e1e; color: white;"}
    return cores.get(val, "")


styler = tabela.style
if hasattr(styler, "map"):
    styler = styler.map(cor_recomendacao, subset=["Recomendação"])
else:
    # Compatibilidade com versões mais antigas do pandas
    styler = styler.applymap(cor_recomendacao, subset=["Recomendação"])

st.dataframe(
    styler,
    use_container_width=True,
    hide_index=True,
)

st.divider()

# ---------------------------------------------------------------------------
# Análise detalhada por ação
# ---------------------------------------------------------------------------
st.subheader("🔎 Análise Detalhada por Ação")

ticker_detalhe = st.selectbox("Escolha uma ação para ver os detalhes", options=lista_final)

with st.spinner(f"Carregando detalhes de {ticker_detalhe}..."):
    try:
        resultado = analyze_ticker_cached(ticker_detalhe, meses_historico, peso_tecnico)
    except Exception as e:
        st.error(f"Erro ao analisar {ticker_detalhe}: {e}")
        st.stop()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Preço Atual", f"R$ {resultado['preco_atual']:.2f}")
col2.metric("Score Final", f"{resultado['score_final']:.0f}/100")
col3.metric("Recomendação", resultado["recomendacao"])
col4.metric("RSI (14)", f"{resultado['rsi']:.1f}" if resultado["rsi"] else "N/D")

col5, col6, col7 = st.columns(3)
col5.metric("Score Técnico", f"{resultado['score_tecnico']:.0f}/100")
col6.metric("Score Fundamental", f"{resultado['score_fundamental']:.0f}/100")
pl_txt = f"{resultado['pl']:.1f}x" if resultado.get("pl") else "N/D"
col7.metric("P/L", pl_txt)

# Gráfico de preços com médias móveis e Bollinger + RSI
df = resultado["dataframe_precos"]
close = df["Close"]
sma20 = sma(close, 20)
sma50 = sma(close, 50)
upper_bb, mid_bb, lower_bb = bollinger_bands(close)
rsi14 = rsi(close, 14)

fig = make_subplots(
    rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3],
    vertical_spacing=0.05, subplot_titles=("Preço e Médias Móveis", "RSI"),
)

fig.add_trace(go.Candlestick(
    x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"],
    name="Preço",
), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=sma20, name="SMA 20", line=dict(width=1)), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=sma50, name="SMA 50", line=dict(width=1)), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=upper_bb, name="Banda Superior", line=dict(width=1, dash="dot")), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=lower_bb, name="Banda Inferior", line=dict(width=1, dash="dot")), row=1, col=1)

fig.add_trace(go.Scatter(x=df.index, y=rsi14, name="RSI", line=dict(color="orange")), row=2, col=1)
fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)

fig.update_layout(height=650, xaxis_rangeslider_visible=False, legend=dict(orientation="h"))
st.plotly_chart(fig, use_container_width=True)

# Justificativas
col_a, col_b = st.columns(2)
with col_a:
    st.markdown("#### 📊 Justificativa Técnica")
    for d in resultado["detalhes_tecnicos"]:
        st.markdown(f"- {d}")

with col_b:
    st.markdown("#### 🏢 Justificativa Fundamentalista")
    if resultado["detalhes_fundamentais"]:
        for d in resultado["detalhes_fundamentais"]:
            st.markdown(f"- {d}")
    else:
        st.markdown("- Dados fundamentalistas insuficientes para esta ação no momento.")

st.divider()
import datetime
st.caption(f"🕒 Última busca de dados nesta sessão: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
st.caption(
    "SE FICAR RICA ME AJUDA MANA"
)
