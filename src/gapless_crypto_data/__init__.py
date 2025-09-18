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
    from gapless_crypto_data import BinancePublicDataCollector, UniversalGapFiller

    # Collect USDT spot data only
    collector = BinancePublicDataCollector()
    collector.collect_data(
        symbol="SOLUSDT",  # USDT spot pairs only
        timeframes=["1m", "5m", "1h"],
        start_date="2023-01-01",
        end_date="2023-12-31"
    )

    # Fill gaps with authentic spot data
    gap_filler = UniversalGapFiller()
    gap_filler.fill_gaps(directory="./data")

CLI Usage:
    uv run gapless-crypto-data --symbol SOLUSDT --timeframes 1m,3m,5m
    uv run gapless-crypto-data --fill-gaps --directory ./data

Supported Symbols (USDT Spot Only):
    BTCUSDT, ETHUSDT, SOLUSDT, ADAUSDT, DOTUSDT, LINKUSDT, MATICUSDT,
    AVAXUSDT, ATOMUSDT, NEARUSDT, FTMUSDT, SANDUSDT, MANAUSDT, etc.
"""

__version__ = "2.6.0"
__author__ = "Eon Labs"
__email__ = "terry@eonlabs.ai"

from .collectors.binance_public_data_collector import BinancePublicDataCollector
from .gap_filling.safe_file_operations import AtomicCSVOperations, SafeCSVMerger
from .gap_filling.universal_gap_filler import UniversalGapFiller

__all__ = [
    "BinancePublicDataCollector",
    "UniversalGapFiller",
    "AtomicCSVOperations",
    "SafeCSVMerger",
]
