# Financial Market Analytics System

A Python-based financial market analytics system for market data processing, equity screening, investment signal generation, portfolio monitoring, and backtesting.

> Disclaimer: This project is for educational and portfolio purposes only. It does not constitute financial advice or investment recommendation.

## Overview

This project was developed to support a structured investment analytics workflow. It combines historical and near real-time market data, technical indicators, portfolio state tracking, signal filtering, dashboard monitoring, Discord alerts, and a backtesting module.

The system focuses on:

- collecting and processing Vietnamese stock market data;
- calculating technical indicators and market breadth;
- screening potential investment signals;
- monitoring portfolio entries, exits, stop-loss, and take-profit levels;
- evaluating signal logic through backtesting.

## Key Features

- Historical data loading and daily market data updates
- Watchlist-based equity screening
- Technical indicator calculation, including Williams %R, RSI, StochRSI, ATR, moving-average breadth, and VN-Index regime analysis
- Signal filtering based on liquidity, price, cooldown rules, and portfolio capacity
- Portfolio state management using local JSON files
- Console dashboard for market regime, breadth, open portfolio, and buy/sell signals
- Optional Discord alert integration
- Backtesting module with portfolio simulation and performance metrics

## Project Structure

```text
Trading_real_time/
├── main.py                         # Main real-time dashboard workflow
├── config.py                       # Project parameters and local configuration
├── data_engine.py                  # Market data loading and vnstock data fetching
├── indicators.py                   # Technical indicators and market regime logic
├── portfolio_engine.py             # Buy/sell logic and portfolio state updates
├── ui_engine.py                    # Console dashboard rendering
├── discord_engine.py               # Optional Discord alert integration
├── backtest.py                     # Historical backtesting workflow
├── get_history_whitelist_hsx.py    # Historical data downloader for whitelist symbols
├── utils.py                        # Utility functions for JSON, console, and parsing
├── requirements.txt                # Python dependencies
└── README.md                       # Project documentation
```

## Installation

Clone the repository:

```bash
git clone https://github.com/<your-username>/financial-market-analytics-system.git
cd financial-market-analytics-system
```

Create and activate a virtual environment:

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

Before running the project, update `config.py` with your local settings:

```python
DISCORD_WEBHOOK_URL = ""
VNSTOCK_API_KEY = ""
DATA_FOLDER = r"path_to_your_market_data_folder"
```

For a public GitHub repository, do not upload real API keys, tokens, Discord webhooks, or private data files.

Recommended sensitive files to exclude:

```text
.env
*.json
*.csv
*.xlsx
__pycache__/
```

## Usage

Run the real-time dashboard:

```bash
python main.py
```

Run the backtesting module:

```bash
python backtest.py
```

Download/update historical data for the watchlist:

```bash
python get_history_whitelist_hsx.py
```

## Methodology

The system screens listed equities using a combination of market data filters and technical indicators. It calculates indicators such as Williams %R, StochRSI, RSI, ATR, moving-average breadth, and VN-Index regime. Buy candidates are filtered by liquidity, price level, cooldown period, and available portfolio capacity.

The portfolio engine manages entry signals, take-profit levels, dynamic stop-loss levels, time-stop rules, and trade statistics. The backtesting module simulates the strategy on historical data to evaluate signal performance and portfolio behavior.

## Technologies Used

- Python
- Pandas
- NumPy
- vnstock
- Requests
- tqdm
- tabulate
- Matplotlib
- Seaborn

## Learning Outcomes

Through this project, I applied financial market knowledge, data processing, technical analysis, portfolio monitoring, and backtesting to build a structured investment analytics workflow. The project strengthened practical experience in financial data analysis, signal evaluation, and systematic investment research.

## Notes for Recruiters

This is a personal portfolio project developed for learning and demonstration purposes. It shows practical exposure to market data processing, investment signal design, portfolio monitoring logic, and performance evaluation.
