import yfinance as yf
import pandas as pd

# Lista de ações que você quer analisar (pode colocar quantas quiser)
carteira = ["PETR4.SA", "VALE3.SA", "ITUB4.SA", "BBAS3.SA", "WEGE3.SA", "TAEE11.SA"]

dados_empresas = []

print("Coletando dados financeiros. Isso pode levar alguns segundos...")

for ticker in carteira:
    acao = yf.Ticker(ticker)
    info = acao.info
    
    # Coletando os indicadores usando .get() para evitar erros se o dado não existir
    # O P/L (Preço/Lucro) indica quão "cara" ou "barata" a ação está
    pl = info.get('trailingPE', 0)
    
    # Dividend Yield (Transformando em % para facilitar a leitura)
    dy = info.get('dividendYield', 0)
    dy_percentual = (dy * 100) if dy else 0
    
    # ROE (Retorno sobre o Patrimônio Líquido - Mede a eficiência da empresa)
    roe = info.get('returnOnEquity', 0)
    roe_percentual = (roe * 100) if roe else 0
    
    # Guarda os dados na nossa lista
    dados_empresas.append({
        'Ação': ticker,
        'P/L': round(pl, 2),
        'Div. Yield (%)': round(dy_percentual, 2),
        'ROE (%)': round(roe_percentual, 2)
    })

# Transforma a lista em uma tabela organizada (DataFrame)
df = pd.DataFrame(dados_empresas)

print("\n--- TODOS OS DADOS COLETADOS ---")
print(df.to_string(index=False))

# ==========================================
# A INTELIGÊNCIA: APLICANDO SEUS FILTROS
# ==========================================

# Regra: P/L positivo e menor que 15 | Pagou mais de 6% de dividendos | ROE maior que 10%
acoes_aprovadas = df[
    (df['P/L'] > 0) & (df['P/L'] < 15) & 
    (df['Div. Yield (%)'] >= 6.0) & 
    (df['ROE (%)'] >= 10.0)
]

print("\n🎯 --- AÇÕES APROVADAS NO SEU FILTRO --- 🎯")
if acoes_aprovadas.empty:
    print("Nenhuma ação passou nos critérios hoje.")
else:
    print(acoes_aprovadas.to_string(index=False))