# Composer Tools

[![CI](https://github.com/dvf/composer-tools/actions/workflows/ci.yml/badge.svg)](https://github.com/dvf/composer-tools/actions/workflows/ci.yml)

A small library of useful tools for [Composer](https://composer.trade)

## 📦 Installation

```bash
pip install composer-tools
```

## 🚀 Quick Example

```python
from composer_tools.converters.short_codes import generate_symphony_code

# When SPY's RSI drops below 30, switch to GLD, otherwise stay in BIL
code = generate_symphony_code("RSI_14_SPY_LT_30", "GLD", "BIL")
```

This generates:
```clojure
(defsymphony
 "RSI_14_SPY_LT_30"
 {:asset-class "EQUITIES", :rebalance-frequency :daily}
 (weight-equal
  [(if
      (< (rsi "SPY" {:window 14}) 30.0)
      [(asset "GLD")]
      [(asset "BIL")])])
)
```

## ⚙️ How It Works 

The format has three parameters:
- **condition**: The condition string (e.g., "RSI_14_SPY_LT_30")
- **then_branch**: What to buy when condition is true
- **else_branch**: What to buy when condition is false

## 📊 Condition Types

### Absolute Conditions
Compare a metric to a fixed value:
```python
generate_symphony_code("RSI_14_SPY_LT_30", "GLD", "BIL")          # RSI below 30
generate_symphony_code("STD_20_XLU_GT_0.02", "TLT", "SPY")       # Volatility above 2%
generate_symphony_code("CUMRET_10_SPY_LT_0", "CASH", "SPY")      # Negative returns
```

### Relative Conditions
Compare metrics between assets:
```python
generate_symphony_code("MA_50_SPY_LT_MA_20_SPY", "CASH", "SPY")        # Death cross
generate_symphony_code("CUMRET_30_XLK_GT_CUMRET_30_XLU", "XLK", "XLU") # Sector rotation
```

### Nested Conditions
Chain conditions with `__` (all must be true):
```python
generate_symphony_code("RSI_14_SPY_LT_30__STD_20_SPY_GT_0.02__CUMRET_5_SPY_LT_0", "GLD", "SPY")
```

## 📈 Supported Metrics 

- [X] `RSI` - Relative Strength Index
- [X] `STD` - Standard deviation of returns  
- [X] `CUMRET` - Cumulative return
- [X] `MA` - Moving average
- there are more from Composer which need to be added!

## 💡Real Examples 

```python
# Momentum strategy
generate_symphony_code("RSI_14_QQQ_GT_70", "QQQ", "TLT")

# Volatility protection  
generate_symphony_code("STD_20_SPY_GT_0.025", "TLT", "SPY")

# Trend following
generate_symphony_code("MA_20_SPY_GT_MA_50_SPY", "SPY", "CASH")

# Nested statement
generate_symphony_code("RSI_14_SPY_LT_30__STD_20_VIX_GT_25__CUMRET_10_SPY_LT_-0.05", "GLD", "SPY")
```

## 🔧 API

```python
generate_symphony_code(condition: str, then_branch: str, else_branch: str) -> str
# Converts condition notation to Composer code with specified assets.
```

```python
parse_condition(condition_str: str) -> dict
# Parses condition strings into structured data (useful for debugging).

parse_condition("RSI_14_SPY_LT_30")
# Returns: {'type': 'absolute', 'metric': 'RSI', 'window': '14', 'ticker': 'SPY', 'operator': 'LT', 'value': '30'}
```

## 🤝 Contributing

This project is new and contributors are welcome.
**Please submit a PR!**

There's a lot of interesting work to do:

- **More metrics and functions**: The rest of the Composer functions
- **Better conditions**: OR logic, more complex nesting
- **Performance**: Optimization and caching
- **Documentation**: More examples and tutorials

### Development Setup 🛠️

```bash
git clone https://github.com/your-repo/composer-tools
cd composer-tools
uv sync
uv run pytest
```

All contributions welcome, from typo fixes to major features. The codebase is clean and the tests are comprehensive, so it's easy to jump in.

## 📄 License

MIT License - use this code however you want.
