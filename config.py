# Konfiguracja aplikacji GemStrategy

# Słownik mapujący nazwy ETF-ów na ich tickery w serwisie Stooq.
# Klucze to przyjazne nazwy, a wartości to tickery używane w API.
TICKERS = {
    "IWDA": "iwda.uk",
    "EIMI": "eimi.uk",
    "CNDX": "cndx.uk",
    "IB01": "ib01.uk",
    "CBU0": "cbu0.uk",
}

# Ticker dla benchmarku (S&P 500) do celów porównawczych.
BENCHMARK_TICKER = "spy.us"

# Listy ETF-ów podzielone na kategorie (akcyjne i obligacyjne).
# Używane w logice strategii GEM do wyboru odpowiedniego typu aktywów.
EQUITY_ETFS = ["IWDA", "EIMI", "CNDX"]
BOND_ETFS = ["IB01", "CBU0"]
