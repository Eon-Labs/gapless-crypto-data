"""
Gapless Crypto Data - USDT spot market data collection with zero gaps guarantee

Market Compatibility:
- USDT SPOT PAIRS ONLY (BTCUSDT, ETHUSDT, SOLUSDT, etc.)
- NO futures, perpetuals, or derivatives support
- NO non-USDT pairs (BTC/ETH, etc.)
- NO margin trading data

Core Features:
- Data collection via Binance public data repository (22x performance vs API calls)
- Full 11-column microstructure format with order flow and liquidity metrics
- Zero gaps guarantee through authentic API-first validation
- UV-based Python tooling
- Atomic file operations
- Complete 13-timeframe support (1s, 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d)
- Ultra-high frequency (1s) to daily (1d) data collection
- Intelligent monthly-to-daily fallback for seamless recent data access
- Gap detection and filling with authentic data only
- CCXT-compatible dual parameter support (timeframe/interval)
- Backward compatibility with 5-year deprecation period

Data Source:
    Binance Spot Market: https://data.binance.vision/data/spot/monthly/klines/
    Market Type: SPOT only (no futures/derivatives)
    Supported Pairs: USDT-quoted spot pairs exclusively

Usage:
    # Function-based API
    import gapless_crypto_data as gcd

    # Fetch recent data (CCXT-compatible timeframe parameter)
    df = gcd.fetch_data("BTCUSDT", timeframe="1h", limit=1000)

    # Backward compatibility (legacy interval parameter)
    df = gcd.fetch_data("BTCUSDT", interval="1h", limit=1000)  # DeprecationWarning

    # Download with date range
    df = gcd.download("ETHUSDT", timeframe="4h", start="2024-01-01", end="2024-06-30")

    # Get available symbols and timeframes
    symbols = gcd.get_supported_symbols()
    timeframes = gcd.get_supported_timeframes()

    # Fill gaps in existing data
    results = gcd.fill_gaps("./data")

    # Class-based API (for complex workflows)
    from gapless_crypto_data import BinancePublicDataCollector, UniversalGapFiller

    collector = BinancePublicDataCollector()
    result = collector.collect_timeframe_data("1h")
    df = result["dataframe"]

CLI Usage:
    uv run gapless-crypto-data --symbol SOLUSDT --timeframes 1s,1m,5m,1h,4h,1d
    uv run gapless-crypto-data --symbol BTCUSDT --timeframes 1s,6h,8h,12h,1d
    uv run gapless-crypto-data --fill-gaps --directory ./data

Supported Symbols (USDT Spot Only):
    BTCUSDT, ETHUSDT, SOLUSDT, ADAUSDT, DOTUSDT, LINKUSDT, MATICUSDT,
    AVAXUSDT, ATOMUSDT, NEARUSDT, FTMUSDT, SANDUSDT, MANAUSDT, etc.
"""

__version__ = "2.10.0"
__author__ = "Eon Labs"
__email__ = "terry@eonlabs.com"

# Core classes (advanced/power-user API)
# Convenience functions (simple/intuitive API)
from .api import (
    download,
    fetch_data,
    fill_gaps,
    get_info,
    get_supported_intervals,
    get_supported_symbols,
    get_supported_timeframes,
    load_parquet,
    save_parquet,
)
from .collectors.binance_public_data_collector import BinancePublicDataCollector
from .gap_filling.safe_file_operations import AtomicCSVOperations, SafeCSVMerger
from .gap_filling.universal_gap_filler import UniversalGapFiller

__all__ = [
    # Simple function-based API (recommended for most users)
    "fetch_data",
    "download",
    "get_supported_symbols",
    "get_supported_timeframes",
    "get_supported_intervals",  # Legacy compatibility
    "fill_gaps",
    "get_info",
    "save_parquet",
    "load_parquet",
    # Advanced class-based API (for complex workflows)
    "BinancePublicDataCollector",
    "UniversalGapFiller",
    "AtomicCSVOperations",
    "SafeCSVMerger",
]
