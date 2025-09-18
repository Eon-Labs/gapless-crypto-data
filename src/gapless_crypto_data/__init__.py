"""
Gapless Crypto Data - Ultra-fast USDT spot market data collection with zero gaps guarantee

Market Compatibility:
- 🎯 USDT SPOT PAIRS ONLY (BTCUSDT, ETHUSDT, SOLUSDT, etc.)
- ❌ NO futures, perpetuals, or derivatives support
- ❌ NO non-USDT pairs (BTC/ETH, etc.)
- ❌ NO margin trading data

Core Features:
- 🚀 22x faster than API calls via Binance public data repository
- 📊 Full 11-column microstructure format with order flow and liquidity metrics
- 🔒 Zero gaps guarantee through authentic API-first validation
- ⚡ UV-first modern Python tooling
- 🛡️ Corruption-proof atomic file operations
- 📊 Multi-timeframe support (1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h)
- 🔧 Gap detection and filling with authentic data only
- 📈 Production-grade data collection for quantitative trading

Data Source:
    Binance Spot Market: https://data.binance.vision/data/spot/monthly/klines/
    Market Type: SPOT only (no futures/derivatives)
    Supported Pairs: USDT-quoted spot pairs exclusively

Usage:
    # Simple function-based API (recommended for most users)
    import gapless_crypto_data as gcd

    # Fetch recent data
    df = gcd.fetch_data("BTCUSDT", "1h", limit=1000)

    # Download with date range
    df = gcd.download("ETHUSDT", "4h", start="2024-01-01", end="2024-06-30")

    # Get available symbols and timeframes
    symbols = gcd.get_supported_symbols()
    timeframes = gcd.get_supported_timeframes()

    # Fill gaps in existing data
    results = gcd.fill_gaps("./data")

    # Advanced class-based API (for complex workflows)
    from gapless_crypto_data import BinancePublicDataCollector, UniversalGapFiller

    collector = BinancePublicDataCollector()
    result = collector.collect_timeframe_data("1h")
    df = result["dataframe"]

CLI Usage:
    uv run gapless-crypto-data --symbol SOLUSDT --timeframes 1m,3m,5m
    uv run gapless-crypto-data --fill-gaps --directory ./data

Supported Symbols (USDT Spot Only):
    BTCUSDT, ETHUSDT, SOLUSDT, ADAUSDT, DOTUSDT, LINKUSDT, MATICUSDT,
    AVAXUSDT, ATOMUSDT, NEARUSDT, FTMUSDT, SANDUSDT, MANAUSDT, etc.
"""

__version__ = "2.6.2"
__author__ = "Eon Labs"
__email__ = "terry@eonlabs.ai"

# Core classes (advanced/power-user API)
# Convenience functions (simple/intuitive API)
from .api import (
    download,
    fetch_data,
    fill_gaps,
    get_info,
    get_supported_symbols,
    get_supported_timeframes,
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
    "fill_gaps",
    "get_info",
    # Advanced class-based API (for complex workflows)
    "BinancePublicDataCollector",
    "UniversalGapFiller",
    "AtomicCSVOperations",
    "SafeCSVMerger",
]
