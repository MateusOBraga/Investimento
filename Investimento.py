import yfinance as yf
import matplotlib.pyplot as plt

# Defina a ação que deseja analisar (adicione '.SA' para ações brasileiras)
ticker = "PETR4.SA"

# Baixa os dados dos últimos 6 meses
print(f"Baixando dados de {ticker}...")
dados = yf.download(ticker, period="6m")

# Calcula a Média Móvel de 20 dias
dados['Media_Movel_20'] = dados['Close'].rolling(window=20).mean()

# Configura o gráfico
plt.figure(figsize=(12, 6))
plt.plot(dados.index, dados['Close'], label='Preço de Fechamento', color='blue')
plt.plot(dados.index, dados['Media_Movel_20'], label='Média Móvel (20 dias)', color='orange', linestyle='--')

# Estilização
plt.title(f'Análise de {ticker} - Últimos 6 Meses', fontsize=16)
plt.xlabel('Data', fontsize=12)
plt.ylabel('Preço (R$)', fontsize=12)
plt.legend()
plt.grid(alpha=0.3)

# Exibe o gráfico
plt.show()