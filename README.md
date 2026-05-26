# Financial Market Analytics System

A Python-based financial market analytics system for market data processing, equity screening, investment signal generation, portfolio monitoring, and backtesting.

This project was developed as a personal finance and data analytics project to build a structured workflow for analyzing listed equities, generating market-based signals, and evaluating signal performance through systematic backtesting.

> **Disclaimer:** This project is for educational and portfolio purposes only. It does not constitute financial advice, investment advice, or a trading recommendation.

---

## 1. Project Overview

The **Financial Market Analytics System** combines market data processing, technical indicator analysis, portfolio tracking, console-based monitoring, Discord alerting, and backtesting into a modular Python application.

The system is designed to support the following investment analytics workflow:

1. Load historical market data and watchlist symbols.
2. Fetch updated market data from the data provider.
3. Clean and standardize market data.
4. Calculate technical indicators and market breadth metrics.
5. Identify potential buy and sell signals based on predefined rules.
6. Monitor portfolio status and risk levels.
7. Display market conditions and signals through a console dashboard.
8. Send optional alerts through Discord.
9. Validate the signal logic using a backtesting module.

The project focuses on building a practical investment analytics pipeline rather than providing direct investment recommendations.

---

## 2. Key Features

### 2.1 Market Data Processing

The system includes a dedicated data engine for loading and updating market data.

Key functions include:

- Loading historical stock and VN-Index data from local CSV files.
- Fetching recent market data using the `vnstock` library.
- Applying request throttling to reduce API request issues.
- Handling retry and backoff logic when data fetching fails.
- Standardizing market data fields such as:
  - `time`
  - `symbol`
  - `open`
  - `high`
  - `low`
  - `close`
  - `volume`

---

### 2.2 Technical Indicator Engine

The project calculates multiple technical indicators and market context variables for screening and signal generation.

Main indicators include:

- Williams %R
- RSI
- Stochastic RSI
- ATR
- VN-Index moving average regime
- Market breadth
- Percentage of stocks above MA20
- Percentage of stocks above MA50

These indicators are used to identify oversold conditions, evaluate market strength, and provide context for stock-level signals.

---

### 2.3 Signal Generation

The signal logic is rule-based and designed to detect potential market opportunities using technical and liquidity conditions.

The system filters buy candidates using:

- Oversold technical indicators
- Minimum liquidity requirement
- Minimum price requirement
- Signal cooldown period
- Existing portfolio holdings
- Available portfolio room

The goal is to avoid generating excessive or low-quality signals and to make the screening process more structured.

---

### 2.4 Portfolio Monitoring

The system tracks a simulated portfolio with key position-level information, including:

- Entry price
- Entry date
- Stop-loss level
- Dynamic stop-loss level
- First take-profit target
- Final take-profit target
- Highest close after entry
- TP1 status

This allows the system to monitor active positions and update portfolio status based on predefined exit rules.

---

### 2.5 Risk Management Logic

The portfolio engine includes several risk control rules:

- ATR-based stop-loss
- First take-profit level
- Final take-profit level
- Dynamic stop-loss adjustment
- Time-stop exit for weak positions
- Signal cooldown after stop-loss events
- Maximum portfolio size control

These rules help make the signal workflow more disciplined and closer to a practical investment monitoring process.

---

### 2.6 Console Dashboard

The system includes a console-based dashboard that displays market and portfolio information in real time.

The dashboard shows:

- VN-Index level
- VN-Index market regime
- Market breadth
- Number of advancing and declining stocks
- Percentage of stocks above MA20 and MA50
- Current portfolio size
- Available portfolio room
- Buy signals
- Sell signals
- Closed trade statistics
- Win rate summary

---

### 2.7 Discord Alerting

The project includes an optional Discord alert module.

The alert system can send:

- Buy signal alerts
- Sell signal alerts
- End-of-day summaries
- VN-Index regime updates
- Market breadth information
- Portfolio status updates

Sensitive credentials such as Discord webhook URLs should not be committed to GitHub.

---

### 2.8 Backtesting Module

The project includes a backtesting module to evaluate the historical behavior of the signal logic.

The backtest simulates portfolio activity and calculates key performance metrics such as:

- Total return
- Annualized return
- Sharpe ratio
- Maximum drawdown
- Win rate
- Average win
- Average loss
- Profit factor

Backtesting is used to assess whether the signal logic is stable, risk-aware, and worth further refinement.

---

## 3. Project Architecture

```text
financial-market-analytics-system/
│
├── main.py
├── config.py
├── data_engine.py
├── indicators.py
├── portfolio_engine.py
├── ui_engine.py
├── discord_engine.py
├── backtest.py
├── get_history_whitelist_hsx.py
├── utils.py
├── requirements.txt
├── README.md
└── .gitignore
```

---

## 4. Module Description

| File | Description |
|---|---|
| `main.py` | Main execution script for the real-time dashboard and signal workflow. |
| `config.py` | Stores project parameters, portfolio settings, indicator parameters, and local file paths. |
| `data_engine.py` | Handles historical data loading, recent data fetching, API throttling, retry logic, and data cleaning. |
| `indicators.py` | Calculates technical indicators, VN-Index regime, and market breadth metrics. |
| `portfolio_engine.py` | Processes buy/sell logic, portfolio updates, stop-loss rules, and take-profit conditions. |
| `ui_engine.py` | Renders the console-based market dashboard. |
| `discord_engine.py` | Sends signal alerts and end-of-day summaries to Discord. |
| `backtest.py` | Runs historical backtests and calculates performance metrics. |
| `get_history_whitelist_hsx.py` | Downloads historical stock data for a predefined watchlist. |
| `utils.py` | Provides helper functions for JSON handling, console display, formatting, and portfolio updates. |

---

## 5. System Workflow

```text
Historical Data + Updated Market Data
              │
              ▼
        Data Cleaning
              │
              ▼
    Technical Indicator Engine
              │
              ▼
 Market Regime & Breadth Analysis
              │
              ▼
      Signal Generation Logic
              │
              ▼
 Portfolio Management & Risk Rules
              │
              ▼
 Console Dashboard / Discord Alerts
              │
              ▼
       Backtesting & Review
```

---

## 6. Signal Logic Summary

The system uses a rule-based signal framework. The logic is mainly designed around technical indicators, liquidity filters, and risk management rules.

### Buy Signal Logic

Potential buy candidates are identified using oversold technical conditions from indicators such as Williams %R and Stochastic RSI.

The raw signals are then filtered using:

- Minimum liquidity requirement
- Minimum price requirement
- Signal cooldown period
- Existing portfolio holdings
- Available portfolio room

This process helps reduce noise and focuses the system on candidates that meet basic trading and screening conditions.

---

### Sell Signal Logic

The sell logic includes multiple exit conditions:

- ATR-based stop-loss
- First take-profit level
- Final take-profit level
- Dynamic stop-loss update
- Time-based exit for weak positions

The purpose of the sell logic is to provide a more structured risk management process rather than relying only on simple fixed exits.

---

### Market Context

The system also monitors VN-Index regime and market breadth to provide broader market context.

This helps avoid viewing individual stock signals in isolation. For example, a stock-level signal may be interpreted differently depending on whether the overall market is in an uptrend, downtrend, or sideways condition.

---

## 7. Technologies Used

- Python
- Pandas
- NumPy
- vnstock
- Requests
- tqdm
- Tabulate
- Backtrader
- Matplotlib
- Seaborn

---

## 8. Installation

Clone the repository:

```bash
git clone https://github.com/VinhPhat2/financial-market-analytics-system.git
cd financial-market-analytics-system
```

Install required packages:

```bash
pip install -r requirements.txt
```

---

## 9. Configuration

Before running the project, update the configuration in `config.py`.

Example:

```python
DISCORD_WEBHOOK_URL = ""
VNSTOCK_API_KEY = ""
DATA_FOLDER = r"path_to_your_data_folder"
```

For security reasons, API keys, tokens, and webhook URLs should not be committed to GitHub.

Recommended practice:

- Keep API keys outside the source code.
- Use environment variables or a local `.env` file.
- Add sensitive files to `.gitignore`.

---

## 10. How to Run

### Run the real-time dashboard

```bash
python main.py
```

### Run the backtesting module

```bash
python backtest.py
```

### Download historical data

```bash
python get_history_whitelist_hsx.py
```

---

## 11. Backtesting and Performance Evaluation

The backtesting module is used to evaluate the historical behavior of the signal logic.

It simulates portfolio activity, records trade logs, tracks portfolio equity, and calculates performance metrics.

Key metrics include:

- Total return
- Annualized return
- Sharpe ratio
- Maximum drawdown
- Win rate
- Profit factor

These metrics are useful for assessing whether the signal framework is stable, risk-aware, and suitable for further development.

---

## 12. Learning Outcomes

Through this project, I applied finance, programming, and data analytics concepts to build a practical market analytics system.

The project helped strengthen my experience in:

- Financial market data processing
- Technical indicator construction
- Rule-based signal generation
- Portfolio monitoring
- Backtesting and performance evaluation
- Risk management logic
- Modular Python project design
- Data-driven investment research workflow

---

## 13. Limitations

This project is a personal educational project and has several limitations:

- The signal logic is rule-based and does not guarantee future performance.
- Backtest results may be affected by data quality, transaction cost assumptions, and market regime changes.
- The system does not account for all real-world execution constraints.
- The project does not include a full production-level trading infrastructure.
- The project should not be used as a live trading system without further validation, risk controls, and compliance review.

---

## 14. Future Improvements

Potential improvements include:

- Add environment-variable support for API keys and webhooks.
- Improve data validation and missing-data handling.
- Add logging instead of relying mainly on console output.
- Add unit tests for indicator and portfolio modules.
- Build a Streamlit dashboard for better visualization.
- Add more robust backtesting assumptions.
- Include factor-based screening and fundamental data integration.
- Improve documentation with screenshots and sample output.
- Add configuration templates for easier setup.

---

## 15. Disclaimer

This repository is created for educational and portfolio demonstration purposes only.

The project does not provide financial advice, investment recommendations, or guaranteed trading performance. Any use of the code, strategy logic, or signal framework should be independently reviewed and tested.
