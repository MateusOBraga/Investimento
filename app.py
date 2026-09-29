"""
app.py
Aplicação web (Streamlit) para análise de ações da B3 com recomendações
de investimento, glossário, perfil de investidor, simulador de aportes
e filtros de busca (screener).

Como rodar localmente:
    streamlit run app.py

Como publicar online (grátis):
    1. Suba este projeto para um repositório no GitHub.
    2. Acesse https://share.streamlit.io (Streamlit Community Cloud).
    3. Conecte sua conta GitHub e selecione o repositório.
    4. Defina "app.py" como arquivo principal e clique em Deploy.
    Veja o README.md para o passo a passo completo.
"""

import datetime

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from data_fetcher import DEFAULT_TICKERS, DEFAULT_FIIS, DEFAULT_ETFS, normalize_ticker
from recommender import analyze_ticker, analyze_multiple
from fii_recommender import analyze_multiple_fiis
from etf_analyzer import analyze_multiple_etfs
from indicators import sma, rsi, macd, bollinger_bands
from glossary import GLOSSARIO
from investor_profile import PERGUNTAS, calcular_perfil
from simulador import simulate_dca

st.set_page_config(page_title="Análise de Ações B3", page_icon="📈", layout="wide")

# Se o usuário acabou de preencher o Perfil de Investidor, aplica os valores
# sugeridos ANTES de os widgets correspondentes serem criados (o Streamlit não
# permite alterar st.session_state de um widget depois que ele já foi
# instanciado na mesma execução do script).
if "_perfil_pendente" in st.session_state:
    for _chave, _valor in st.session_state.pop("_perfil_pendente").items():
        st.session_state[_chave] = _valor


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


@st.cache_data(ttl=CACHE_TTL_SEGUNDOS, show_spinner=False)
def simulate_dca_cached(ticker: str, aporte_mensal: float, meses: int):
    return simulate_dca(ticker, aporte_mensal, meses)


@st.cache_data(ttl=CACHE_TTL_SEGUNDOS, show_spinner=False)
def analyze_multiple_fiis_cached(tickers: tuple, months: int, peso_tecnico: float):
    return analyze_multiple_fiis(list(tickers), months=months, peso_tecnico=peso_tecnico)


@st.cache_data(ttl=CACHE_TTL_SEGUNDOS, show_spinner=False)
def analyze_multiple_etfs_cached(tickers: tuple, months: int):
    return analyze_multiple_etfs(list(tickers), months=months)


def dy_para_pct(valor):
    """Converte dividend yield (fração ou %) para percentual, tratando None."""
    if valor is None or pd.isna(valor):
        return 0.0
    return valor * 100 if valor < 1 else valor


st.title("Análise de Ações da B3 com Recomendações de Investimento")
st.caption(
    "BOA SORTE MANA"
)

# ---------------------------------------------------------------------------
# Configurações gerais (substitui a barra lateral)
# ---------------------------------------------------------------------------
with st.expander("⚙️ Configurações gerais", expanded=True):
    col_cfg1, col_cfg2, col_cfg3 = st.columns([2, 1.3, 1])

    with col_cfg1:
        selecionar_todas = st.checkbox(
            f"Selecionar todas as {len(DEFAULT_TICKERS)} ações da lista",
            value=False,
            help="Cuidado: analisar muitas ações de uma vez demora mais e pode "
                 "esbarrar em limites de requisição do Yahoo Finance.",
        )
        tickers_selecionados = st.multiselect(
            "Ações da B3",
            options=DEFAULT_TICKERS,
            default=DEFAULT_TICKERS if selecionar_todas else DEFAULT_TICKERS[:6],
        )
        tickers_customizados = st.text_input(
            "Adicionar outros tickers (separados por vírgula)",
            placeholder="Ex: TOTS3, CYRE3, RAIL3",
        )

    with col_cfg2:
        unidade_periodo = st.radio(
            "Unidade do período histórico", options=["Meses", "Anos"], horizontal=True,
        )
        if unidade_periodo == "Meses":
            quantidade_periodo = st.slider("Quantidade de meses", 1, 24, 12)
            meses_historico = quantidade_periodo
        else:
            quantidade_periodo = st.slider("Quantidade de anos", 1, 10, 1)
            meses_historico = quantidade_periodo * 12

    with col_cfg3:
        peso_tecnico = st.slider(
            "Peso técnico no score",
            min_value=0.0, max_value=1.0, value=0.6, step=0.1,
            key="peso_tecnico_slider",
            help="O restante do peso vai para a Análise Fundamentalista. Ajustado "
                 "automaticamente se você preencher o Perfil de Investidor.",
        )
        if st.button("🔄 Atualizar dados agora"):
            st.cache_data.clear()
            st.rerun()

lista_final = list(tickers_selecionados)
if tickers_customizados.strip():
    extras = [normalize_ticker(t) for t in tickers_customizados.split(",") if t.strip()]
    lista_final += extras

if not lista_final:
    st.warning("Selecione ao menos uma ação nas configurações acima para começar.")
    st.stop()

st.caption(
    f"🕒 Dados buscados nesta sessão às {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')} "
    f"(cache de até {CACHE_TTL_SEGUNDOS // 60} min)."
)

# ---------------------------------------------------------------------------
# Abas
# ---------------------------------------------------------------------------
tab_ranking, tab_detalhe, tab_fiis, tab_etfs, tab_perfil, tab_simulador, tab_glossario, tab_sobre = st.tabs(
    ["🏆 Ranking", "🔎 Análise Detalhada", "🏢 FIIs", "📊 ETFs", "🎯 Perfil de Investidor",
     "💰 Simulador de Aportes", "📖 Glossário", "ℹ️ Sobre"]
)

# ===================== ABA: RANKING (com filtros de busca) =====================
with tab_ranking:
    with st.spinner("Analisando ações selecionadas..."):
        tabela = analyze_multiple_cached(tuple(lista_final), meses_historico, peso_tecnico)

    st.markdown("#### 🔍 Filtros de busca")
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    with col_f1:
        recs_disponiveis = ["COMPRAR", "MANTER", "VENDER"]
        rec_filtro = st.multiselect("Recomendação", recs_disponiveis, default=recs_disponiveis)
    with col_f2:
        setores_disponiveis = sorted([s for s in tabela["Setor"].dropna().unique()])
        setor_filtro = st.multiselect("Setor", setores_disponiveis, default=[])
    with col_f3:
        score_min = st.slider("Score final mínimo", 0, 100, 0, key="score_min_slider")
    with col_f4:
        dy_min_pct = st.number_input(
            "Dividend Yield mínimo (%)", min_value=0.0, value=0.0, step=0.5,
            key="dy_min_input",
            help=GLOSSARIO.get("Dividend Yield"),
        )

    tabela_filtrada = tabela.copy()
    if rec_filtro:
        tabela_filtrada = tabela_filtrada[tabela_filtrada["Recomendação"].isin(rec_filtro)]
    if setor_filtro:
        tabela_filtrada = tabela_filtrada[tabela_filtrada["Setor"].isin(setor_filtro)]
    tabela_filtrada = tabela_filtrada[tabela_filtrada["Score Final"].fillna(0) >= score_min]
    if dy_min_pct > 0:
        tabela_filtrada = tabela_filtrada[
            tabela_filtrada["Div. Yield"].apply(dy_para_pct) >= dy_min_pct
        ]

    st.caption(f"Mostrando {len(tabela_filtrada)} de {len(tabela)} ações analisadas.")

    def cor_recomendacao(val):
        cores = {"COMPRAR": "background-color: #1e5c2a; color: white;",
                 "MANTER": "background-color: #7a6a1e; color: white;",
                 "VENDER": "background-color: #7a1e1e; color: white;"}
        return cores.get(val, "")

    styler = tabela_filtrada.style
    if hasattr(styler, "map"):
        styler = styler.map(cor_recomendacao, subset=["Recomendação"])
    else:
        styler = styler.applymap(cor_recomendacao, subset=["Recomendação"])

    st.dataframe(styler, use_container_width=True, hide_index=True)

# ===================== ABA: ANÁLISE DETALHADA =====================
with tab_detalhe:
    ticker_detalhe = st.selectbox(
        "Escolha uma ação para ver os detalhes", options=lista_final, key="ticker_detalhe",
    )

    with st.spinner(f"Carregando detalhes de {ticker_detalhe}..."):
        try:
            resultado = analyze_ticker_cached(ticker_detalhe, meses_historico, peso_tecnico)
        except Exception as e:
            st.error(f"Erro ao analisar {ticker_detalhe}: {e}")
            resultado = None

    if resultado:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Preço Atual", f"R$ {resultado['preco_atual']:.2f}")
        col2.metric("Score Final", f"{resultado['score_final']:.0f}/100", help=GLOSSARIO.get("Score Final"))
        col3.metric("Recomendação", resultado["recomendacao"])
        col4.metric(
            "RSI (14)",
            f"{resultado['rsi']:.1f}" if resultado["rsi"] else "N/D",
            help=GLOSSARIO.get("RSI (Índice de Força Relativa)"),
        )

        col5, col6, col7 = st.columns(3)
        col5.metric("Score Técnico", f"{resultado['score_tecnico']:.0f}/100", help=GLOSSARIO.get("Score Técnico"))
        col6.metric("Score Fundamental", f"{resultado['score_fundamental']:.0f}/100", help=GLOSSARIO.get("Score Fundamental"))
        pl_txt = f"{resultado['pl']:.1f}x" if resultado.get("pl") else "N/D"
        col7.metric("P/L", pl_txt, help=GLOSSARIO.get("P/L (Preço/Lucro)"))

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

# ===================== ABA: FIIs =====================
with tab_fiis:
    st.subheader("🏢 Fundos Imobiliários (FIIs)")
    st.caption(
        "Aqui os indicadores são adaptados: o que mais importa para um FII é o "
        "**P/VP** (preço da cota vs. valor patrimonial) e o **Dividend Yield** — "
        "não existe P/L nem ROE como em uma ação normal."
    )

    col_fii1, col_fii2 = st.columns([3, 1])
    with col_fii1:
        fiis_selecionados = st.multiselect(
            "FIIs", options=DEFAULT_FIIS, default=DEFAULT_FIIS[:8], key="fiis_sel",
        )
        fiis_custom = st.text_input(
            "Adicionar outros FIIs (separados por vírgula)",
            placeholder="Ex: RECT11, VRTA11", key="fiis_custom",
        )
    with col_fii2:
        peso_tecnico_fii = st.slider(
            "Peso técnico (FIIs)", min_value=0.0, max_value=1.0, value=0.3, step=0.1,
            key="peso_fii",
            help="Para FIIs, costuma fazer sentido dar mais peso ao fundamento "
                 "(P/VP e Dividend Yield) do que ao gráfico.",
        )

    lista_fiis = list(fiis_selecionados)
    if fiis_custom.strip():
        lista_fiis += [normalize_ticker(t) for t in fiis_custom.split(",") if t.strip()]

    if lista_fiis:
        with st.spinner("Analisando FIIs..."):
            tabela_fii = analyze_multiple_fiis_cached(tuple(lista_fiis), meses_historico, peso_tecnico_fii)

        styler_fii = tabela_fii.style
        if hasattr(styler_fii, "map"):
            styler_fii = styler_fii.map(cor_recomendacao, subset=["Recomendação"])
        else:
            styler_fii = styler_fii.applymap(cor_recomendacao, subset=["Recomendação"])
        st.dataframe(styler_fii, use_container_width=True, hide_index=True)
    else:
        st.info("Selecione ao menos um FII acima para ver a análise.")

# ===================== ABA: ETFs =====================
with tab_etfs:
    st.subheader("📊 ETFs (fundos de índice)")
    st.caption(
        "ETFs replicam um índice inteiro (Ibovespa, S&P 500, small caps...), "
        "então a recomendação aqui é só **técnica** (tendência, RSI, MACD) — "
        "não existe 'fundamento de empresa' para um fundo passivo."
    )

    col_etf1, col_etf2 = st.columns([3, 1])
    with col_etf1:
        etfs_selecionados = st.multiselect(
            "ETFs", options=DEFAULT_ETFS, default=DEFAULT_ETFS[:6], key="etfs_sel",
        )
        etfs_custom = st.text_input(
            "Adicionar outros ETFs (separados por vírgula)",
            placeholder="Ex: ACWI11, EURP11", key="etfs_custom",
        )

    lista_etfs = list(etfs_selecionados)
    if etfs_custom.strip():
        lista_etfs += [normalize_ticker(t) for t in etfs_custom.split(",") if t.strip()]

    if lista_etfs:
        with st.spinner("Analisando ETFs..."):
            tabela_etf = analyze_multiple_etfs_cached(tuple(lista_etfs), meses_historico)

        styler_etf = tabela_etf.style
        if hasattr(styler_etf, "map"):
            styler_etf = styler_etf.map(cor_recomendacao, subset=["Recomendação"])
        else:
            styler_etf = styler_etf.applymap(cor_recomendacao, subset=["Recomendação"])
        st.dataframe(styler_etf, use_container_width=True, hide_index=True)
    else:
        st.info("Selecione ao menos um ETF acima para ver a análise.")

# ===================== ABA: PERFIL DE INVESTIDOR =====================
with tab_perfil:
    st.subheader("Descubra seu perfil de investidor")
    st.caption(
        "Responda algumas perguntas rápidas para receber sugestões de "
        "configuração adequadas ao seu perfil."
    )

    respostas = {}
    with st.form("form_perfil"):
        for pergunta in PERGUNTAS:
            escolha = st.radio(
                pergunta["pergunta"], list(pergunta["opcoes"].keys()),
                key=f"perfil_{pergunta['id']}",
            )
            respostas[pergunta["id"]] = pergunta["opcoes"][escolha]
        enviado = st.form_submit_button("Ver meu perfil")

    if enviado:
        resultado_perfil = calcular_perfil(respostas)
        st.session_state["perfil_resultado"] = resultado_perfil
        st.session_state["_perfil_pendente"] = {
            "peso_tecnico_slider": resultado_perfil["peso_tecnico_sugerido"],
            "score_min_slider": resultado_perfil["filtro_sugerido"]["score_min"],
            "dy_min_input": resultado_perfil["filtro_sugerido"]["dy_min"],
        }
        st.rerun()

    if "perfil_resultado" in st.session_state:
        rp = st.session_state["perfil_resultado"]
        st.success(f"Seu perfil estimado: **{rp['perfil']}**")
        st.write(rp["descricao"])
        st.caption(f"Pontuação: {rp['pontuacao']} de {rp['pontuacao_maxima']}")
        st.info(
            f"✅ Já apliquei automaticamente na aba **Ranking**: peso técnico "
            f"ajustado para **{rp['peso_tecnico_sugerido']:.1f}**, Score mínimo de "
            f"**{rp['filtro_sugerido']['score_min']}** e Dividend Yield mínimo de "
            f"**{rp['filtro_sugerido']['dy_min']}%** nos filtros de busca. Você pode "
            f"ajustar qualquer um desses valores manualmente a qualquer momento."
        )

# ===================== ABA: SIMULADOR DE APORTES =====================
with tab_simulador:
    st.subheader("Simulador de aportes mensais")
    st.caption(
        "Simula quanto você teria hoje se investisse um valor fixo todo mês na "
        "ação escolhida, comprando sempre ao preço de fechamento do mês "
        "(estratégia de aportes regulares / 'preço médio')."
    )

    col_s1, col_s2, col_s3 = st.columns(3)
    with col_s1:
        ticker_sim = st.selectbox("Ação", options=lista_final, key="ticker_simulador")
    with col_s2:
        aporte_mensal = st.number_input("Aporte mensal (R$)", min_value=10.0, value=200.0, step=50.0)
    with col_s3:
        meses_sim = st.slider("Quantos meses simular", 3, 60, 24)

    if st.button("Simular"):
        with st.spinner("Simulando..."):
            try:
                st.session_state["sim_resultado"] = simulate_dca_cached(ticker_sim, aporte_mensal, meses_sim)
            except Exception as e:
                st.error(f"Não foi possível simular: {e}")
                st.session_state.pop("sim_resultado", None)

    if "sim_resultado" in st.session_state:
        sim = st.session_state["sim_resultado"]
        col_r1, col_r2, col_r3, col_r4 = st.columns(4)
        col_r1.metric("Total investido", f"R$ {sim['total_investido']:.2f}")
        col_r2.metric("Valor hoje", f"R$ {sim['valor_atual']:.2f}")
        col_r3.metric("Resultado", f"R$ {sim['lucro']:.2f}", f"{sim['rentabilidade_pct']:.1f}%")
        col_r4.metric("Preço médio pago", f"R$ {sim['preco_medio']:.2f}")

        hist = sim["historico"]
        fig_sim = go.Figure()
        fig_sim.add_trace(go.Scatter(x=hist["data"], y=hist["total_investido"], name="Total investido", line=dict(dash="dot")))
        fig_sim.add_trace(go.Scatter(x=hist["data"], y=hist["valor_carteira"], name="Valor da carteira"))
        fig_sim.update_layout(height=380, legend=dict(orientation="h"))
        st.plotly_chart(fig_sim, use_container_width=True)

        st.caption(
            "⚠️ Simulação baseada em cotações históricas reais, mas simplificada: "
            "não considera taxas de corretagem, impostos, nem dividendos reinvestidos."
        )

# ===================== ABA: GLOSSÁRIO =====================
with tab_glossario:
    st.subheader("📖 Glossário — termos usados na análise")
    st.caption(
        "Passe o mouse nos ícones de ajuda (❓) espalhados pelo app para ver "
        "explicações rápidas, ou consulte a lista completa abaixo."
    )
    for termo, explicacao in GLOSSARIO.items():
        with st.expander(termo):
            st.write(explicacao)

# ===================== ABA: SOBRE =====================
with tab_sobre:
    st.subheader("Sobre esta ferramenta")
    st.write(
        "VAI DAR BOM"
    )
    st.warning(
        "SE FICAR RICA ME AJUDA"
    )
