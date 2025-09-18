#!/usr/bin/env python3
"""
Convenience API functions for gapless-crypto-data

Provides function-based API following financial data library conventions.
Intuitive and familiar patterns for data collection and analysis.

Examples:
    import gapless_crypto_data as gcd

    # Simple data fetching
    df = gcd.fetch_data("BTCUSDT", "1h", limit=1000)

    # Get available symbols and timeframes
    symbols = gcd.get_supported_symbols()
    intervals = gcd.get_supported_timeframes()

    # Download with date range
    df = gcd.download("ETHUSDT", "4h", start="2024-01-01", end="2024-06-30")
"""

from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Union

import pandas as pd

from .collectors.binance_public_data_collector import BinancePublicDataCollector
from .gap_filling.universal_gap_filler import UniversalGapFiller


def get_supported_symbols() -> List[str]:
    """Get list of supported USDT spot trading pairs.

    Returns:
        List of supported symbol strings (e.g., ["BTCUSDT", "ETHUSDT", ...])

    Examples:
        >>> symbols = get_supported_symbols()
        >>> print(f"Found {len(symbols)} supported symbols")
        >>> print(f"Bitcoin: {'BTCUSDT' in symbols}")
        Found 6 supported symbols
        Bitcoin: True
    """
    collector = BinancePublicDataCollector()
    return list(collector.known_symbols.keys())


def get_supported_timeframes() -> List[str]:
    """Get list of supported timeframe intervals.

    Returns:
        List of timeframe strings (e.g., ["1m", "5m", "1h", "4h", ...])

    Examples:
        >>> timeframes = get_supported_timeframes()
        >>> print(f"Available timeframes: {timeframes}")
        >>> print(f"1-hour supported: {'1h' in timeframes}")
        Available timeframes: ['1s', '1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1w', '1mo']
        1-hour supported: True
    """
    collector = BinancePublicDataCollector()
    return collector.available_timeframes


def fetch_data(
    symbol: str,
    interval: str,
    limit: Optional[int] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    output_dir: Optional[Union[str, Path]] = None,
) -> pd.DataFrame:
    """Fetch cryptocurrency data with simple function-based API.

    Args:
        symbol: Trading pair symbol (e.g., "BTCUSDT", "ETHUSDT")
        interval: Timeframe interval (e.g., "1m", "5m", "1h", "4h", "1d")
        limit: Maximum number of recent bars to return (optional)
        start: Start date in YYYY-MM-DD format (optional)
        end: End date in YYYY-MM-DD format (optional)
        output_dir: Directory to save CSV files (optional)

    Returns:
        pandas.DataFrame with OHLCV data and microstructure columns:
        - date: Timestamp (open time)
        - open, high, low, close: Price data
        - volume: Base asset volume
        - close_time: Close timestamp
        - quote_asset_volume: Quote asset volume
        - number_of_trades: Trade count
        - taker_buy_base_asset_volume: Taker buy base volume
        - taker_buy_quote_asset_volume: Taker buy quote volume

    Examples:
        # Fetch recent 1000 hourly bars
        df = fetch_data("BTCUSDT", "1h", limit=1000)

        # Fetch specific date range
        df = fetch_data("ETHUSDT", "4h", start="2024-01-01", end="2024-06-30")

        # Save to custom directory
        df = fetch_data("SOLUSDT", "1h", limit=500, output_dir="./crypto_data")
    """
    # Handle limit by calculating date range
    if limit and not start and not end:
        # Calculate start date based on limit and interval
        interval_minutes = {
            "1m": 1,
            "3m": 3,
            "5m": 5,
            "15m": 15,
            "30m": 30,
            "1h": 60,
            "2h": 120,
            "4h": 240,
            "1d": 1440,
        }

        if interval in interval_minutes:
            minutes_total = limit * interval_minutes[interval]
            start_date = datetime.now() - timedelta(minutes=minutes_total)
            start = start_date.strftime("%Y-%m-%d")
            end = datetime.now().strftime("%Y-%m-%d")
        else:
            # Default fallback for unknown intervals
            start = "2024-01-01"
            end = datetime.now().strftime("%Y-%m-%d")

    # Set default date range if not specified
    if not start:
        start = "2021-01-01"
    if not end:
        end = datetime.now().strftime("%Y-%m-%d")

    # Initialize collector
    collector = BinancePublicDataCollector(
        symbol=symbol, start_date=start, end_date=end, output_dir=output_dir
    )

    # Collect data for single timeframe
    result = collector.collect_timeframe_data(interval)

    if result and "dataframe" in result:
        df = result["dataframe"]

        # Apply limit if specified
        if limit and len(df) > limit:
            df = df.tail(limit).reset_index(drop=True)

        return df
    else:
        # Return empty DataFrame with expected columns
        columns = [
            "date",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "close_time",
            "quote_asset_volume",
            "number_of_trades",
            "taker_buy_base_asset_volume",
            "taker_buy_quote_asset_volume",
        ]
        return pd.DataFrame(columns=columns)


def download(
    symbol: str,
    interval: str = "1h",
    start: Optional[str] = None,
    end: Optional[str] = None,
    output_dir: Optional[Union[str, Path]] = None,
) -> pd.DataFrame:
    """Download cryptocurrency data (alias for fetch_data).

    Provides familiar API patterns for intuitive data collection.

    Args:
        symbol: Trading pair symbol (e.g., "BTCUSDT")
        interval: Timeframe interval (default: "1h")
        start: Start date in YYYY-MM-DD format
        end: End date in YYYY-MM-DD format
        output_dir: Directory to save CSV files

    Returns:
        pandas.DataFrame with complete OHLCV and microstructure data

    Examples:
        # Simple data download
        df = download("BTCUSDT", "1h", start="2024-01-01", end="2024-06-30")

        # Simple recent data
        df = download("ETHUSDT", "4h")
    """
    return fetch_data(symbol=symbol, interval=interval, start=start, end=end, output_dir=output_dir)


def fill_gaps(directory: Union[str, Path], symbols: Optional[List[str]] = None) -> dict:
    """Fill gaps in existing CSV data files.

    Args:
        directory: Directory containing CSV files to process
        symbols: Optional list of symbols to process (default: all found)

    Returns:
        dict: Gap filling results with statistics

    Examples:
        # Fill all gaps in directory
        results = fill_gaps("./data")

        # Fill gaps for specific symbols
        results = fill_gaps("./data", symbols=["BTCUSDT", "ETHUSDT"])
    """
    gap_filler = UniversalGapFiller()
    target_dir = Path(directory)

    # Find CSV files
    csv_files = list(target_dir.glob("*.csv"))
    if symbols:
        # Filter by specified symbols
        csv_files = [f for f in csv_files if any(symbol in f.name for symbol in symbols)]

    results = {
        "files_processed": 0,
        "gaps_detected": 0,
        "gaps_filled": 0,
        "success_rate": 0.0,
        "file_results": {},
    }

    for csv_file in csv_files:
        # Extract timeframe from filename
        timeframe = "1h"  # Default
        for tf in ["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h"]:
            if f"-{tf}_" in csv_file.name or f"-{tf}-" in csv_file.name:
                timeframe = tf
                break

        # Process file
        file_result = gap_filler.process_file(csv_file, timeframe)
        results["file_results"][csv_file.name] = file_result
        results["files_processed"] += 1
        results["gaps_detected"] += file_result["gaps_detected"]
        results["gaps_filled"] += file_result["gaps_filled"]

    # Calculate overall success rate
    if results["gaps_detected"] > 0:
        results["success_rate"] = (results["gaps_filled"] / results["gaps_detected"]) * 100
    else:
        results["success_rate"] = 100.0

    return results


def get_info() -> dict:
    """Get library information and capabilities.

    Returns:
        dict: Library metadata and capabilities

    Examples:
        >>> info = get_info()
        >>> print(f"Version: {info['version']}")
        >>> print(f"Supported symbols: {len(info['supported_symbols'])}")
    """
    from . import __version__

    return {
        "version": __version__,
        "name": "gapless-crypto-data",
        "description": "Ultra-fast cryptocurrency data collection with zero gaps guarantee",
        "supported_symbols": get_supported_symbols(),
        "supported_timeframes": get_supported_timeframes(),
        "market_type": "USDT spot pairs only",
        "data_source": "Binance public data repository + API",
        "features": [
            "22x faster than API calls",
            "Full 11-column microstructure format",
            "Automatic gap detection and filling",
            "Production-grade data quality",
        ],
    }
