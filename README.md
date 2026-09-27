# 📈 Análise de Ações da B3 com Recomendações de Investimento

Ferramenta em Python para analisar ações da bolsa brasileira (B3) combinando
**análise técnica** (médias móveis, RSI, MACD, Bandas de Bollinger, volume) e
**análise fundamentalista** (P/L, Dividend Yield, ROE, margem, endividamento),
gerando uma pontuação de 0 a 100 e uma recomendação: **COMPRAR / MANTER / VENDER**.

Os dados vêm do Yahoo Finance através da biblioteca `yfinance` (gratuita, sem necessidade de API key).

> ⚠️ **Aviso importante:** esta ferramenta é educacional. Ela **não** é uma recomendação
> de investimento profissional. Os dados podem ter atraso ou imprecisões. Sempre faça
> sua própria análise ou consulte um profissional certificado (CVM/CFP) antes de investir.

---

## 📁 Estrutura do projeto

```
analise-acoes-br/
├── app.py              # App web interativo (Streamlit) — análise online
├── cli.py              # Versão de linha de comando (terminal)
├── recommender.py      # Lógica de pontuação e recomendações
├── indicators.py        # Cálculo dos indicadores técnicos
├── data_fetcher.py      # Busca de preços e dados fundamentalistas
├── requirements.txt     # Dependências do projeto
└── README.md
```

---

## 🚀 1. Rodando localmente

```bash
# 1. Clone o repositório (depois de subir no GitHub)
git clone https://github.com/SEU-USUARIO/analise-acoes-br.git
cd analise-acoes-br

# 2. Crie um ambiente virtual (recomendado)
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 3. Instale as dependências
pip install -r requirements.txt

# 4a. Rode o app web interativo
streamlit run app.py

# 4b. OU rode pelo terminal (sem interface web)
python cli.py PETR4 VALE3 ITUB4
```

O comando `streamlit run app.py` abre automaticamente o navegador em
`http://localhost:8501` com o painel interativo.

---

## ☁️ 2. Subindo no GitHub

```bash
cd analise-acoes-br
git init
git add .
git commit -m "Primeira versão: análise de ações da B3"
git branch -M main
git remote add origin https://github.com/SEU-USUARIO/analise-acoes-br.git
git push -u origin main
```

(Crie antes o repositório vazio em github.com/new, sem README, para evitar conflitos.)

---

## 🌐 3. Deixando online e grátis (Streamlit Community Cloud)

Depois que o projeto estiver no GitHub, você pode publicá-lo como um site que
qualquer pessoa acessa pelo navegador, sem precisar rodar nada localmente:

1. Acesse **https://share.streamlit.io** e faça login com sua conta GitHub.
2. Clique em **"New app"**.
3. Selecione o repositório `analise-acoes-br`, branch `main`.
4. Em **"Main file path"**, coloque `app.py`.
5. Clique em **Deploy**.
6. Em poucos minutos você terá uma URL pública, tipo:
   `https://seu-usuario-analise-acoes-br.streamlit.app`

Qualquer atualização que você fizer (`git push`) no repositório atualiza o site
automaticamente.

### Alternativas de deploy
- **Render.com** ou **Railway.app**: também suportam apps Streamlit gratuitamente/com camada free.
- **Hugging Face Spaces**: crie um Space do tipo "Streamlit" e suba os mesmos arquivos.

---

## 🧠 Como funciona a pontuação

**Score Técnico (peso padrão 60%)** combina:
- Tendência via médias móveis (SMA 20/50/200 — cruzamentos "golden/death cross")
- RSI (sobrecompra/sobrevenda)
- MACD (cruzamentos e momentum)
- Posição em relação às Bandas de Bollinger
- Confirmação por volume

**Score Fundamentalista (peso padrão 40%)** combina:
- P/L (Preço/Lucro)
- Dividend Yield
- ROE (Retorno sobre o Patrimônio)
- Margem líquida
- Relação Dívida/Patrimônio

**Score Final = Score Técnico × peso_técnico + Score Fundamentalista × (1 − peso_técnico)**

| Score Final | Recomendação |
|---|---|
| ≥ 70 | COMPRAR |
| 45–69 | MANTER |
| < 45 | VENDER |

Você pode ajustar o peso técnico/fundamentalista diretamente na barra lateral do app,
ou pelo parâmetro `--peso-tecnico` no `cli.py`.

---

## ✏️ Personalizando

- **Lista de ações padrão:** edite `DEFAULT_TICKERS` em `data_fetcher.py`.
- **Pesos e regras de pontuação:** edite `recommender.py` (`_score_technical` e `_score_fundamental`).
- **Novos indicadores:** adicione funções em `indicators.py` e utilize-as em `recommender.py`.
- Tickers da B3 no Yahoo Finance sempre levam o sufixo `.SA` (ex: `PETR4.SA`) — o
  código já adiciona isso automaticamente se você digitar só `PETR4`.

---

## 📦 Dependências

- `yfinance` — coleta de dados de mercado
- `pandas` / `numpy` — manipulação de dados
- `streamlit` — interface web interativa
- `plotly` — gráficos interativos (candlestick, RSI, etc.)

---

## Licença

Uso livre para fins pessoais e educacionais.
