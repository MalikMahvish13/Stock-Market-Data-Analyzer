# Architecture and workflow

## Component diagram

```mermaid
flowchart LR
    subgraph Inputs
      Y[Yahoo Finance historical download]
      C[CSV upload / local CSV]
    end
    subgraph Core[Python analysis package]
      L[Load and validate]
      X[Clean and sort]
      I[Calculate returns, SMA 20/50, volatility]
      S[Summarize and report]
      B[SMA crossover backtest]
      V[Matplotlib charts and CSV artifacts]
    end
    subgraph Interfaces
      CLI[main.py CLI]
      API[FastAPI]
      UI[Streamlit dashboard]
    end
    Y --> L
    C --> L
    CLI --> L
    API --> L
    UI --> L
    L --> X --> I
    I --> S
    I --> B
    I --> V
    S --> CLI
    S --> API
    S --> UI
    B --> API
    B --> UI
    V --> CLI
    V --> UI
```

## Data flow

1. The CLI, API, or dashboard selects a ticker/date interval or CSV.
2. `analyzer.load_data()` requests Yahoo Finance historical prices or reads the explicitly chosen CSV. Download failures raise an error; the sample is never substituted silently.
3. `clean_data()` normalizes column names, parses dates and numeric fields, requires `Date` and `Close`, removes unusable closing prices, deduplicates dates and sorts observations.
4. `calculate_metrics()` appends daily percent return, SMA 20, SMA 50, and a 20-session annualized rolling standard deviation of daily returns.
5. `summarize()` derives period return, range/average prices, latest averages, full-period and latest 20-session volatility, trend text and observations from those prices.
6. `save_outputs()` writes CSV, summary text, price/SMA/return/distribution charts and a volume chart when valid volume exists.
7. `backtesting.run_sma_backtest()` marks crossover dates and applies the prior session's position to the current session's return.
8. FastAPI returns JSON and accepts CSV uploads; Streamlit displays the same calculations and provides CSV/report downloads.

## API sequence

```mermaid
sequenceDiagram
    actor User
    participant Client as CLI / Streamlit / HTTP client
    participant API as FastAPI (optional)
    participant Analyzer as analyzer.py
    participant Source as Yahoo Finance or CSV
    User->>Client: Select ticker or upload CSV
    Client->>API: Request (or call analyzer directly)
    API->>Analyzer: Validate and load
    Analyzer->>Source: Download/read selected source
    Source-->>Analyzer: Historical observations
    Analyzer->>Analyzer: Clean, calculate and summarize
    Analyzer-->>API: Summary / backtest result
    API-->>Client: JSON response
    Client-->>User: Charts, metrics and downloads
```

## Design notes

- Pandas handles time-indexed observations and rolling calculations; NumPy provides annualization with `sqrt(252)` sessions per year.
- The project uses a single analysis package to keep the course version approachable. `backtesting.py` is separate because it has its own signal and position timing logic.
- Generated outputs are local artifacts, not a database. The API `/latest` endpoint is an in-memory process cache and resets on restart.
- Yahoo Finance `end` is exclusive. The dashboard treats the selected end date as inclusive by adding one day before requesting data.
- The workflow uses historical downloads; it does not provide guaranteed real-time streaming.
