# Gapless Crypto Data

[![PyPI version](https://badge.fury.io/py/gapless-crypto-data.svg)](https://badge.fury.io/py/gapless-crypto-data)
[![Python Versions](https://img.shields.io/pypi/pyversions/gapless-crypto-data.svg)](https://pypi.org/project/gapless-crypto-data/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![UV Managed](https://img.shields.io/badge/uv-managed-blue.svg)](https://github.com/astral-sh/uv)

Ultra-fast cryptocurrency data collection with zero gaps guarantee. Provides 11-column microstructure format through Binance public data repository with intelligent monthly-to-daily fallback for seamless coverage.

## Features

- **22x faster** data collection via Binance public data repository
- **Zero gaps guarantee** through intelligent monthly-to-daily fallback
- **Complete 13-timeframe support**: 1s, 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d
- **Ultra-high frequency** to daily data collection (1-second to 1-day intervals)
- **11-column microstructure format** with order flow and liquidity metrics
- **Intelligent fallback system** automatically switches to daily files when monthly files unavailable
- **Gap detection and filling** with authentic Binance API data only
- **UV-based Python tooling** for modern dependency management
- **Atomic file operations** ensuring data integrity
- **Multi-symbol & multi-timeframe** concurrent collection
- **CCXT-compatible** dual parameter support (timeframe/interval)
- **Production-grade** with comprehensive test coverage

## Quick Start

### Installation (UV)

```bash
# Install via UV
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
# Collect data for multiple timeframes (all 13 timeframes supported)
gapless-crypto-data --symbol SOLUSDT --timeframes 1s,1m,5m,1h,4h,1d

# Ultra-high frequency data collection (1-second intervals)
gapless-crypto-data --symbol BTCUSDT --timeframes 1s,1m,3m

# Extended timeframes with intelligent fallback
gapless-crypto-data --symbol ETHUSDT --timeframes 6h,8h,12h,1d

# Collect multiple symbols at once (native multi-symbol support)
gapless-crypto-data --symbol BTCUSDT,ETHUSDT,SOLUSDT --timeframes 1h,4h,1d

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

#### Function-based API

```python
import gapless_crypto_data as gcd

# Fetch recent data with date range (CCXT-compatible timeframe parameter)
df = gcd.download("BTCUSDT", timeframe="1h", start="2024-01-01", end="2024-06-30")

# Or with limit
df = gcd.fetch_data("ETHUSDT", timeframe="4h", limit=1000)

# Backward compatibility (legacy interval parameter)
df = gcd.fetch_data("ETHUSDT", interval="4h", limit=1000)  # DeprecationWarning

# Get available symbols and timeframes
symbols = gcd.get_supported_symbols()
timeframes = gcd.get_supported_timeframes()

# Fill gaps in existing data
results = gcd.fill_gaps("./data")
```

#### Class-based API

```python
from gapless_crypto_data import BinancePublicDataCollector, UniversalGapFiller

# Custom collection with full control
collector = BinancePublicDataCollector(
    symbol="SOLUSDT",
    start_date="2023-01-01",
    end_date="2023-12-31"
)

result = collector.collect_timeframe_data("1h")
df = result["dataframe"]

# Manual gap filling
gap_filler = UniversalGapFiller()
gaps = gap_filler.detect_all_gaps(csv_file, "1h")
```

## Data Structure

All functions return pandas DataFrames with complete microstructure data:

```python
import gapless_crypto_data as gcd

# Fetch data
df = gcd.download("BTCUSDT", timeframe="1h", start="2024-01-01", end="2024-06-30")

# DataFrame columns (11-column microstructure format)
print(df.columns.tolist())
# ['date', 'open', 'high', 'low', 'close', 'volume',
#  'close_time', 'quote_asset_volume', 'number_of_trades',
#  'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume']

# Professional microstructure analysis
buy_pressure = df['taker_buy_base_asset_volume'].sum() / df['volume'].sum()
avg_trade_size = df['volume'].sum() / df['number_of_trades'].sum()
market_impact = df['quote_asset_volume'].std() / df['quote_asset_volume'].mean()

print(f"Taker buy pressure: {buy_pressure:.1%}")
print(f"Average trade size: {avg_trade_size:.4f} BTC")
print(f"Market impact volatility: {market_impact:.3f}")
```

## Data Sources

The package supports two data collection methods:
- **Binance Public Repository**: Pre-generated monthly ZIP files for historical data
- **Binance API**: Real-time data for gap filling and recent data collection

## 🏗️ Architecture

### Core Components

- **BinancePublicDataCollector**: Data collection with full 11-column microstructure format
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
# Native multi-symbol support
gapless-crypto-data --symbol BTCUSDT,ETHUSDT,SOLUSDT,ADAUSDT --timeframes 1m,5m,15m,1h,4h --start 2023-01-01 --end 2023-12-31

# Alternative: Multiple separate commands for different settings
gapless-crypto-data --symbol BTCUSDT,ETHUSDT --timeframes 1m,1h --start 2023-01-01 --end 2023-06-30
gapless-crypto-data --symbol SOLUSDT,ADAUSDT --timeframes 5m,4h --start 2023-07-01 --end 2023-12-31
```

#### Simple API (Recommended)

```python
import gapless_crypto_data as gcd

# Process multiple symbols with simple loops
symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "ADAUSDT"]
timeframes = ["1h", "4h"]

for symbol in symbols:
    for timeframe in timeframes:
        df = gcd.fetch_data(symbol, timeframe, start="2023-01-01", end="2023-12-31")
        print(f"{symbol} {timeframe}: {len(df)} bars collected")
```

#### Advanced API (Complex Workflows)

```python
from gapless_crypto_data import BinancePublicDataCollector

# Initialize with custom settings
collector = BinancePublicDataCollector(
    start_date="2023-01-01",
    end_date="2023-12-31",
    output_dir="./crypto_data"
)

# Process multiple symbols with detailed control
symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
for symbol in symbols:
    collector.symbol = symbol
    results = collector.collect_multiple_timeframes(["1m", "5m", "1h", "4h"])
    for timeframe, result in results.items():
        print(f"{symbol} {timeframe}: {result['stats']}")
```

### Gap Analysis

#### Simple API (Recommended)

```python
import gapless_crypto_data as gcd

# Quick gap filling for entire directory
results = gcd.fill_gaps("./data")
print(f"Processed {results['files_processed']} files")
print(f"Filled {results['gaps_filled']}/{results['gaps_detected']} gaps")
print(f"Success rate: {results['success_rate']:.1f}%")

# Gap filling for specific symbols only
results = gcd.fill_gaps("./data", symbols=["BTCUSDT", "ETHUSDT"])
```

#### Advanced API (Detailed Control)

```python
from gapless_crypto_data import UniversalGapFiller

gap_filler = UniversalGapFiller()

# Manual gap detection and analysis
gaps = gap_filler.detect_all_gaps("BTCUSDT_1h.csv", "1h")
print(f"Found {len(gaps)} gaps")

for gap in gaps:
    duration_hours = gap['duration'].total_seconds() / 3600
    print(f"Gap: {gap['start_time']} → {gap['end_time']} ({duration_hours:.1f}h)")

# Fill specific gaps
result = gap_filler.process_file("BTCUSDT_1h.csv", "1h")
```

## 🛠️ Development

### Prerequisites

- **UV Package Manager** - [Install UV](https://docs.astral.sh/uv/getting-started/installation/)
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

All 13 Binance timeframes supported for complete market coverage:

| Timeframe | Code | Description | Use Case |
|-----------|------|-------------|----------|
| 1 second  | `1s` | Ultra-high frequency | HFT, microstructure analysis |
| 1 minute  | `1m` | High resolution | Scalping, order flow |
| 3 minutes | `3m` | Short-term analysis | Quick trend detection |
| 5 minutes | `5m` | Common trading timeframe | Day trading signals |
| 15 minutes| `15m`| Medium-term signals | Swing trading entry |
| 30 minutes| `30m`| Longer-term patterns | Position management |
| 1 hour    | `1h` | Popular for backtesting | Strategy development |
| 2 hours   | `2h` | Extended analysis | Multi-timeframe confluence |
| 4 hours   | `4h` | Daily cycle patterns | Trend following |
| 6 hours   | `6h` | Quarter-day analysis | Position sizing |
| 8 hours   | `8h` | Third-day cycles | Risk management |
| 12 hours  | `12h`| Half-day patterns | Overnight positions |
| 1 day     | `1d` | Daily analysis | Long-term trends |

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

Cryptocurrency spot data collection from Binance's public data repository using pre-generated monthly ZIP files.

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

Gap detection and filling for various timeframes with 11-column microstructure format using Binance API data.

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

## Output Formats

### DataFrame Structure (Python API)

Returns pandas DataFrame with 11-column microstructure format:

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `date` | datetime64[ns] | Open timestamp | `2024-01-01 12:00:00` |
| `open` | float64 | Opening price | `42150.50` |
| `high` | float64 | Highest price | `42200.00` |
| `low` | float64 | Lowest price | `42100.25` |
| `close` | float64 | Closing price | `42175.75` |
| `volume` | float64 | Base asset volume | `15.250000` |
| `close_time` | datetime64[ns] | Close timestamp | `2024-01-01 12:59:59` |
| `quote_asset_volume` | float64 | Quote asset volume | `643238.125` |
| `number_of_trades` | int64 | Trade count | `1547` |
| `taker_buy_base_asset_volume` | float64 | Taker buy base volume | `7.825000` |
| `taker_buy_quote_asset_volume` | float64 | Taker buy quote volume | `329891.750` |

### CSV File Structure

CSV files include header comments with metadata followed by data:

```csv
# Binance Spot Market Data v2.5.0
# Generated: 2025-09-18T23:09:25.391126+00:00Z
# Source: Binance Public Data Repository
# Market: SPOT | Symbol: BTCUSDT | Timeframe: 1h
# Coverage: 48 bars
# Period: 2024-01-01 00:00:00 to 2024-01-02 23:00:00
# Collection: direct_download in 0.0s
# Data Hash: 5fba9d2e5d3db849...
# Compliance: Zero-Magic-Numbers, Temporal-Integrity, Official-Binance-Source
#
date,open,high,low,close,volume,close_time,quote_asset_volume,number_of_trades,taker_buy_base_asset_volume,taker_buy_quote_asset_volume
2024-01-01 00:00:00,42283.58,42554.57,42261.02,42475.23,1271.68108,2024-01-01 00:59:59,53957248.973789,47134,682.57581,28957416.819645
```

### Metadata JSON Structure

Each CSV file includes comprehensive metadata in `.metadata.json`:

```json
{
  "version": "v2.5.0",
  "generator": "BinancePublicDataCollector",
  "data_source": "Binance Public Data Repository",
  "symbol": "BTCUSDT",
  "timeframe": "1h",
  "enhanced_microstructure_format": {
    "total_columns": 11,
    "analysis_capabilities": [
      "order_flow_analysis",
      "liquidity_metrics",
      "market_microstructure",
      "trade_weighted_prices",
      "institutional_data_patterns"
    ]
  },
  "gap_analysis": {
    "total_gaps_detected": 0,
    "data_completeness_score": 1.0,
    "gap_filling_method": "authentic_binance_api"
  },
  "data_integrity": {
    "chronological_order": true,
    "corruption_detected": false
  }
}
```

### Streaming Output (Memory-Efficient)

For large datasets, Polars streaming provides constant memory usage:

```python
from gapless_crypto_data.streaming import StreamingDataProcessor

processor = StreamingDataProcessor(chunk_size=10_000, memory_limit_mb=100)
for chunk in processor.stream_csv_chunks("large_dataset.csv"):
    # Process chunk with constant memory usage
    print(f"Chunk shape: {chunk.shape}")
```

### File Naming Convention

Output files follow consistent naming pattern:

```
binance_spot_{SYMBOL}-{TIMEFRAME}_{START_DATE}-{END_DATE}_v{VERSION}.csv
binance_spot_{SYMBOL}-{TIMEFRAME}_{START_DATE}-{END_DATE}_v{VERSION}.metadata.json
```

Examples:
- `binance_spot_BTCUSDT-1h_20240101-20240102_v2.5.0.csv`
- `binance_spot_ETHUSDT-4h_20240101-20240201_v2.5.0.csv`
- `binance_spot_SOLUSDT-1d_20240101-20241231_v2.5.0.csv`

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

**UV-based** - Python dependency management
**📊 11-Column Format** - Microstructure data with order flow metrics
**🔒 Gap Detection** - Data completeness validation and filling
