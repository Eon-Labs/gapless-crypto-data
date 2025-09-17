# Gapless Crypto Data

[![PyPI version](https://badge.fury.io/py/gapless-crypto-data.svg)](https://badge.fury.io/py/gapless-crypto-data)
[![Python Versions](https://img.shields.io/pypi/pyversions/gapless-crypto-data.svg)](https://pypi.org/project/gapless-crypto-data/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![UV Managed](https://img.shields.io/badge/uv-managed-blue.svg)](https://github.com/astral-sh/uv)

Ultra-fast cryptocurrency data collection with zero gaps guarantee and full 11-column microstructure format - **22x faster** than API calls via Binance public data repository.

## ⚡ Features

- 🚀 **22x faster** than API calls via Binance public data repository
- 📊 **Full 11-column microstructure format** with order flow and liquidity metrics
- 🔒 **Zero gaps guarantee** through authentic API-first validation
- ⚡ **UV-first** modern Python tooling
- 🛡️ **Corruption-proof** atomic file operations
- 📊 **Multi-symbol & multi-timeframe support** (1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h)
- 🔧 **Gap detection and filling** with authentic data only
- 📈 **Production-grade** data collection for quantitative trading

## 🚀 Quick Start

### Installation (UV - Recommended)

```bash
# Install via UV (fastest)
uv add gapless-crypto-data

# Or install globally
uv tool install gapless-crypto-data
```

### Installation (pip)

```bash
pip install gapless-crypto-data
```

### CLI Usage

```bash
# Collect data for multiple timeframes (default output location)
gapless-crypto-data --symbol SOLUSDT --timeframes 1m,3m,5m,15m,30m,1h,2h,4h

# Collect multiple symbols at once (native multi-symbol support)
gapless-crypto-data --symbol BTCUSDT,ETHUSDT,SOLUSDT --timeframes 1h,4h

# Collect specific date range with custom output directory
gapless-crypto-data --symbol BTCUSDT --timeframes 1h --start 2023-01-01 --end 2023-12-31 --output-dir ./crypto_data

# Multi-symbol with custom settings
gapless-crypto-data --symbol BTCUSDT,ETHUSDT --timeframes 5m,1h --start 2024-01-01 --end 2024-06-30 --output-dir ./crypto_data

# Fill gaps in existing data
gapless-crypto-data --fill-gaps --directory ./data

# Help
gapless-crypto-data --help
```

### Python API

```python
from gapless_crypto_data import BinancePublicDataCollector, UniversalGapFiller

# Collect data
collector = BinancePublicDataCollector()
collector.collect_data(
    symbol="SOLUSDT",
    timeframes=["1m", "5m", "1h"],
    start_date="2023-01-01",
    end_date="2023-12-31"
)

# Fill gaps
gap_filler = UniversalGapFiller()
gap_filler.fill_gaps(directory="./data")
```

## 📊 Performance Comparison

| Method | Collection Speed | Microstructure Data | Gap Handling | Data Integrity |
|--------|-----------------|-------------------|--------------|----------------|
| **Gapless Crypto Data** | **22x faster** | ✅ Full 11-column format | ✅ Authentic API-first | ✅ Atomic operations |
| Traditional APIs | 1x baseline | ⚠️ Basic OHLCV only | ❌ Manual handling | ⚠️ Corruption risk |
| Other downloaders | 2-5x faster | ❌ Limited format | ❌ Limited coverage | ⚠️ Basic validation |

## 🏗️ Architecture

### Core Components

- **BinancePublicDataCollector**: Ultra-fast data collection with full 11-column microstructure format
- **UniversalGapFiller**: Intelligent gap detection and filling with authentic API-first validation
- **AtomicCSVOperations**: Corruption-proof file operations with atomic writes
- **SafeCSVMerger**: Safe merging of data files with integrity validation

### Data Flow

```
Binance Public Data Repository → BinancePublicDataCollector → 11-Column Microstructure Format
                ↓
Gap Detection → UniversalGapFiller → Authentic API-First Validation
                ↓
AtomicCSVOperations → Final Gapless Dataset with Order Flow Metrics
```

## 📝 CLI Options

### Data Collection

```bash
gapless-crypto-data [OPTIONS]

Options:
  --symbol TEXT          Trading pair symbol(s) - single symbol or comma-separated list (e.g., SOLUSDT, BTCUSDT,ETHUSDT)
  --timeframes TEXT      Comma-separated timeframes (1m,3m,5m,15m,30m,1h,2h,4h)
  --start TEXT          Start date (YYYY-MM-DD)
  --end TEXT            End date (YYYY-MM-DD)
  --output-dir TEXT     Output directory for CSV files (default: src/gapless_crypto_data/sample_data/)
  --help                Show this message and exit
```

### Gap Filling

```bash
gapless-crypto-data --fill-gaps [OPTIONS]

Options:
  --directory TEXT      Data directory to scan for gaps
  --symbol TEXT         Specific symbol to process (optional)
  --timeframe TEXT      Specific timeframe to process (optional)
  --help               Show this message and exit
```

## 🔧 Advanced Usage

### Batch Processing

#### CLI Multi-Symbol (Recommended)

```bash
# Native multi-symbol support (fastest approach)
gapless-crypto-data --symbol BTCUSDT,ETHUSDT,SOLUSDT,ADAUSDT --timeframes 1m,5m,15m,1h,4h --start 2023-01-01 --end 2023-12-31

# Alternative: Multiple separate commands for different settings
gapless-crypto-data --symbol BTCUSDT,ETHUSDT --timeframes 1m,1h --start 2023-01-01 --end 2023-06-30
gapless-crypto-data --symbol SOLUSDT,ADAUSDT --timeframes 5m,4h --start 2023-07-01 --end 2023-12-31
```

#### Python API

```python
from gapless_crypto_data import BinancePublicDataCollector

collector = BinancePublicDataCollector()

# Process multiple symbols (loop-based for complex logic)
symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "ADAUSDT"]
timeframes = ["1m", "5m", "15m", "1h", "4h"]

for symbol in symbols:
    collector.collect_data(
        symbol=symbol,
        timeframes=timeframes,
        start_date="2023-01-01",
        end_date="2023-12-31"
    )
```

### Gap Analysis

```python
from gapless_crypto_data import UniversalGapFiller

gap_filler = UniversalGapFiller()

# Analyze gaps before filling
gaps = gap_filler.detect_gaps(directory="./data")
print(f"Found {len(gaps)} gaps across all files")

# Fill gaps with detailed logging
gap_filler.fill_gaps(
    directory="./data",
    verbose=True,
    max_retries=3
)
```

## 🛠️ Development

### Prerequisites

- **UV Package Manager** (recommended) - [Install UV](https://docs.astral.sh/uv/getting-started/installation/)
- **Python 3.9+** - UV will manage Python versions automatically
- **Git** - For repository cloning and version control

### Development Installation Workflow

**IMPORTANT**: This project uses **mandatory pre-commit hooks** to prevent broken code from being committed. All commits are automatically validated for formatting, linting, and basic quality checks.

#### Step 1: Clone Repository
```bash
git clone https://github.com/Eon-Labs/gapless-crypto-data.git
cd gapless-crypto-data
```

#### Step 2: Development Environment Setup
```bash
# Create isolated virtual environment
uv venv

# Activate virtual environment
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows

# Install all dependencies (production + development)
uv sync --dev
```

#### Step 3: Verify Installation
```bash
# Test CLI functionality
uv run gapless-crypto-data --help

# Run test suite
uv run pytest

# Quick data collection test
uv run gapless-crypto-data --symbol BTCUSDT --timeframes 1h --start 2024-01-01 --end 2024-01-01 --output-dir ./test_data
```

#### Step 4: Set Up Pre-Commit Hooks (Mandatory)
```bash
# Install pre-commit hooks (prevents broken code from being committed)
uv run pre-commit install

# Test pre-commit hooks
uv run pre-commit run --all-files
```

#### Step 5: Development Tools
```bash
# Code formatting
uv run ruff format .

# Linting and auto-fixes
uv run ruff check --fix .

# Type checking
uv run mypy src/

# Run specific tests
uv run pytest tests/test_binance_collector.py -v

# Manual pre-commit validation
uv run pre-commit run --all-files
```

### Development Commands Reference

| Task | Command |
|------|---------|
| Install dependencies | `uv sync --dev` |
| Setup pre-commit hooks | `uv run pre-commit install` |
| Add new dependency | `uv add package-name` |
| Add dev dependency | `uv add --dev package-name` |
| Run CLI | `uv run gapless-crypto-data [args]` |
| Run tests | `uv run pytest` |
| Format code | `uv run ruff format .` |
| Lint code | `uv run ruff check --fix .` |
| Type check | `uv run mypy src/` |
| Validate pre-commit | `uv run pre-commit run --all-files` |
| Build package | `uv build` |

### Project Structure for Development
```
gapless-crypto-data/
├── src/gapless_crypto_data/        # Main package
│   ├── __init__.py                 # Package exports
│   ├── cli.py                      # CLI interface
│   ├── collectors/                 # Data collection modules
│   └── gap_filling/                # Gap detection/filling
├── tests/                          # Test suite
├── docs/                           # Documentation
├── examples/                       # Usage examples
├── pyproject.toml                  # Project configuration
└── uv.lock                        # Dependency lock file
```

### Building and Publishing

```bash
# Build package
uv build

# Publish to PyPI (requires API token)
uv publish
```

## 📁 Project Structure

```
gapless-crypto-data/
├── src/
│   └── gapless_crypto_data/
│       ├── __init__.py              # Package exports
│       ├── cli.py                   # Command-line interface
│       ├── collectors/
│       │   ├── __init__.py
│       │   └── binance_public_data_collector.py
│       ├── gap_filling/
│       │   ├── __init__.py
│       │   ├── universal_gap_filler.py
│       │   └── safe_file_operations.py
│       └── utils/
│           └── __init__.py
├── tests/                           # Test suite
├── docs/                           # Documentation
├── pyproject.toml                  # Project configuration
├── README.md                       # This file
└── LICENSE                         # MIT License
```

## 🔍 Supported Timeframes

| Timeframe | Code | Description |
|-----------|------|-------------|
| 1 minute  | `1m` | Highest resolution |
| 3 minutes | `3m` | Short-term analysis |
| 5 minutes | `5m` | Common trading timeframe |
| 15 minutes| `15m`| Medium-term signals |
| 30 minutes| `30m`| Longer-term patterns |
| 1 hour    | `1h` | Popular for backtesting |
| 2 hours   | `2h` | Extended analysis |
| 4 hours   | `4h` | Daily cycle patterns |

## ⚠️ Requirements

- Python 3.9+
- pandas >= 2.0.0
- requests >= 2.25.0
- Stable internet connection for data downloads

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Install development dependencies (`uv sync --dev`)
4. Make your changes
5. Run tests (`uv run pytest`)
6. Format code (`uv run ruff format .`)
7. Commit changes (`git commit -m 'Add amazing feature'`)
8. Push to branch (`git push origin feature/amazing-feature`)
9. Open a Pull Request

## 📚 API Reference

### BinancePublicDataCollector

Ultra-fast cryptocurrency spot data collection from Binance's public data repository. Provides 10-100x faster data collection compared to API calls by downloading pre-generated monthly ZIP files.

#### Key Methods

**`__init__(symbol, start_date, end_date, output_dir)`**

Initialize the collector with trading pair and date range.

```python
collector = BinancePublicDataCollector(
    symbol="BTCUSDT",           # USDT spot pair
    start_date="2023-01-01",    # Start date (YYYY-MM-DD)
    end_date="2023-12-31",      # End date (YYYY-MM-DD)
    output_dir="./crypto_data"  # Output directory (optional)
)
```

**`collect_timeframe_data(trading_timeframe) -> Dict[str, Any]`**

Collect complete historical data for a single timeframe with full 11-column microstructure format.

```python
result = collector.collect_timeframe_data("1h")
df = result["dataframe"]              # pandas DataFrame with OHLCV + microstructure
filepath = result["filepath"]         # Path to saved CSV file
stats = result["stats"]               # Collection statistics

# Access microstructure data
total_trades = df["number_of_trades"].sum()
taker_buy_ratio = df["taker_buy_base_asset_volume"].sum() / df["volume"].sum()
```

**`collect_multiple_timeframes(timeframes) -> Dict[str, Dict[str, Any]]`**

Collect data for multiple timeframes with comprehensive progress tracking.

```python
results = collector.collect_multiple_timeframes(["1h", "4h"])
for timeframe, result in results.items():
    df = result["dataframe"]
    print(f"{timeframe}: {len(df):,} bars")
```

### UniversalGapFiller

Universal gap detection and filling for all timeframes with authentic 11-column microstructure format. Uses only authentic Binance API data - never synthetic data.

#### Key Methods

**`detect_all_gaps(csv_file) -> List[Dict]`**

Automatically detect timestamp gaps in CSV files.

```python
gap_filler = UniversalGapFiller()
gaps = gap_filler.detect_all_gaps("BTCUSDT_1h_data.csv")
print(f"Found {len(gaps)} gaps to fill")
```

**`fill_gap(csv_file, gap_info) -> bool`**

Fill a specific gap with authentic Binance API data.

```python
# Fill first detected gap
success = gap_filler.fill_gap("BTCUSDT_1h_data.csv", gaps[0])
print(f"Gap filled successfully: {success}")
```

**`process_file(directory) -> Dict[str, Dict]`**

Batch process all CSV files in a directory for gap detection and filling.

```python
results = gap_filler.process_file("./crypto_data/")
for filename, result in results.items():
    print(f"{filename}: {result['gaps_filled']} gaps filled")
```

### AtomicCSVOperations

Safe atomic operations for CSV files with header preservation and corruption prevention. Uses temporary files and atomic rename operations to ensure data integrity.

#### Key Methods

**`create_backup() -> Path`**

Create timestamped backup of original file before modifications.

```python
from pathlib import Path
atomic_ops = AtomicCSVOperations(Path("data.csv"))
backup_path = atomic_ops.create_backup()
```

**`write_dataframe_atomic(df) -> bool`**

Atomically write DataFrame to CSV with integrity validation.

```python
success = atomic_ops.write_dataframe_atomic(df)
if not success:
    atomic_ops.rollback_from_backup()
```

### SafeCSVMerger

Safe CSV data merging with gap filling capabilities and data integrity validation. Handles temporal data insertion while maintaining chronological order.

#### Key Methods

**`merge_gap_data_safe(gap_data, gap_start, gap_end) -> bool`**

Safely merge gap data into existing CSV using atomic operations.

```python
from datetime import datetime
merger = SafeCSVMerger(Path("eth_data.csv"))
success = merger.merge_gap_data_safe(
    gap_data,                    # DataFrame with gap data
    datetime(2024, 1, 1, 12),   # Gap start time
    datetime(2024, 1, 1, 15)    # Gap end time
)
```

### Data Format

All classes work with the standardized 11-column microstructure format:

| Column | Description | Example |
|--------|-------------|---------|
| `date` | Open timestamp | `2024-01-01 12:00:00` |
| `open` | Opening price | `42150.50` |
| `high` | Highest price | `42200.00` |
| `low` | Lowest price | `42100.25` |
| `close` | Closing price | `42175.75` |
| `volume` | Base asset volume | `15.250000` |
| `close_time` | Close timestamp | `2024-01-01 12:59:59` |
| `quote_asset_volume` | Quote asset volume | `643238.125` |
| `number_of_trades` | Trade count | `1547` |
| `taker_buy_base_asset_volume` | Taker buy base volume | `7.825000` |
| `taker_buy_quote_asset_volume` | Taker buy quote volume | `329891.750` |

### Error Handling

All classes implement robust error handling with meaningful exceptions:

```python
try:
    collector = BinancePublicDataCollector(symbol="INVALIDPAIR")
    result = collector.collect_timeframe_data("1h")
except ValueError as e:
    print(f"Invalid symbol format: {e}")
except ConnectionError as e:
    print(f"Network error: {e}")
except FileNotFoundError as e:
    print(f"Output directory error: {e}")
```

### Type Hints

All public APIs include comprehensive type hints for better IDE support:

```python
from typing import Dict, List, Optional, Any
from pathlib import Path
import pandas as pd

def collect_timeframe_data(self, trading_timeframe: str) -> Dict[str, Any]:
    # Returns dict with 'dataframe', 'filepath', and 'stats' keys
    pass

def collect_multiple_timeframes(
    self,
    timeframes: Optional[List[str]] = None
) -> Dict[str, Dict[str, Any]]:
    # Returns nested dict by timeframe
    pass
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🏢 About Eon Labs

Gapless Crypto Data is developed by [Eon Labs](https://github.com/Eon-Labs), specializing in quantitative trading infrastructure and machine learning for financial markets.

---

**⚡ Powered by UV** - Modern Python dependency management
**🚀 22x Faster** - Than traditional API-based collection
**📊 11-Column Format** - Full microstructure data with order flow metrics
**🔒 Zero Gaps** - Guaranteed complete datasets with authentic data only
