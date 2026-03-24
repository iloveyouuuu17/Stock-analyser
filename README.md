# Indian Stock Analyzer

A Python-based tool to analyze Indian stocks listed on NSE (National Stock Exchange) and BSE (Bombay Stock Exchange).

## Features

- Fetch real-time and historical stock data for NSE/BSE listed stocks
- Calculate key technical indicators (SMA, EMA, RSI, MACD, Bollinger Bands)
- Display candlestick charts and trend visualizations
- Fundamental analysis: PE ratio, market cap, dividend yield, and more
- Portfolio tracker with gain/loss summary
- Export analysis reports to CSV

## Prerequisites

- Python 3.8+
- pip

## Installation

```bash
git clone https://github.com/iloveyouuuu17/indian-stock-analyzer.git
cd indian-stock-analyzer
pip install -r requirements.txt
```

## Usage

### Analyze a single stock

```bash
python main.py --ticker RELIANCE --period 1y
```

### Run interactive CLI

```bash
python main.py
```

### Example

```python
from analyzer import StockAnalyzer

analyzer = StockAnalyzer("TCS")
analyzer.fetch_data(period="6mo")
print(analyzer.summary())
analyzer.plot_chart()
```

## Supported Exchanges

- **NSE**: Append `.NS` suffix (handled automatically)
- **BSE**: Append `.BO` suffix (handled automatically)

## Popular Indian Stocks

| Symbol   | Company                         |
|----------|---------------------------------|
| RELIANCE | Reliance Industries             |
| TCS      | Tata Consultancy Services       |
| INFY     | Infosys                         |
| HDFCBANK | HDFC Bank                       |
| WIPRO    | Wipro                           |
| SBIN     | State Bank of India             |
| TATAMOTORS | Tata Motors                   |

## Project Structure

```
indian-stock-analyzer/
├── main.py            # Entry point / CLI
├── analyzer.py        # Core stock analysis logic
├── portfolio.py       # Portfolio tracking
├── utils.py           # Helper utilities
├── requirements.txt   # Python dependencies
└── README.md
```

## License

MIT
