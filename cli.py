"""
cli.py
Versão de linha de comando: analisa ações da B3 direto no terminal,
sem precisar do Streamlit. Útil para rodar em servidor, cron job, etc.

Exemplos de uso:
    python cli.py                                  # usa lista padrão
    python cli.py PETR4 VALE3 ITUB4                # tickers específicos
    python cli.py PETR4 VALE3 --periodo 6mo         # período customizado
    python cli.py PETR4 VALE3 --csv resultado.csv   # exporta para CSV
"""

import argparse
from data_fetcher import DEFAULT_TICKERS
from recommender import analyze_multiple


def main():
    parser = argparse.ArgumentParser(description="Análise de ações da B3 com recomendações de investimento.")
    parser.add_argument("tickers", nargs="*", help="Códigos das ações (ex: PETR4 VALE3). Se vazio, usa lista padrão.")
    parser.add_argument("--periodo", default="1y", help="Período histórico: 6mo, 1y, 2y, 5y (padrão: 1y)")
    parser.add_argument("--peso-tecnico", type=float, default=0.6, help="Peso do score técnico de 0 a 1 (padrão: 0.6)")
    parser.add_argument("--csv", default=None, help="Caminho para exportar o resultado em CSV")
    args = parser.parse_args()

    tickers = args.tickers if args.tickers else DEFAULT_TICKERS

    print(f"\nAnalisando {len(tickers)} ação(ões)... isso pode levar alguns segundos.\n")
    resultado = analyze_multiple(tickers, period=args.periodo, peso_tecnico=args.peso_tecnico)

    with pd_option_context():
        print(resultado.to_string(index=False))

    if args.csv:
        resultado.to_csv(args.csv, index=False, encoding="utf-8-sig")
        print(f"\nResultado exportado para: {args.csv}")

    print(
        "\n⚠️  Aviso: ferramenta educacional. Não constitui recomendação de investimento. "
        "Consulte um profissional certificado antes de investir.\n"
    )


class pd_option_context:
    """Context manager simples para exibir o DataFrame completo no terminal."""
    def __enter__(self):
        import pandas as pd
        self._cm = pd.option_context("display.max_columns", None, "display.width", 200)
        self._cm.__enter__()
        return self

    def __exit__(self, *exc):
        self._cm.__exit__(*exc)


if __name__ == "__main__":
    main()
