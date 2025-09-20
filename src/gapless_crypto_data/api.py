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
    timeframe: Optional[str] = None,
    limit: Optional[int] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    output_dir: Optional[Union[str, Path]] = None,
    *,
    interval: Optional[str] = None,
) -> pd.DataFrame:
    """Fetch cryptocurrency data with simple function-based API.

    Args:
        symbol: Trading pair symbol (e.g., "BTCUSDT", "ETHUSDT")
        timeframe: Timeframe interval (e.g., "1m", "5m", "1h", "4h", "1d")
        limit: Maximum number of recent bars to return (optional)
        start: Start date in YYYY-MM-DD format (optional)
        end: End date in YYYY-MM-DD format (optional)
        output_dir: Directory to save CSV files (optional)
        interval: Legacy parameter name for timeframe (deprecated, use timeframe)

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

        # Legacy interval parameter (deprecated)
        df = fetch_data("BTCUSDT", interval="1h", limit=1000)
    """
    # Dual parameter validation with exception-only failures
    if timeframe is None and interval is None:
        raise ValueError(
            "Must specify 'timeframe' parameter. "
            "CCXT-compatible 'timeframe' is preferred over legacy 'interval'."
        )

    if timeframe is not None and interval is not None:
        raise ValueError(
            "Cannot specify both 'timeframe' and 'interval' parameters. "
            "Use 'timeframe' (CCXT-compatible) or 'interval' (legacy), not both."
        )

    # Use timeframe if provided, otherwise use interval (legacy)
    period = timeframe if timeframe is not None else interval

    # Handle limit by calculating date range
    if limit and not start and not end:
        # Calculate start date based on limit and interval
        interval_minutes = {
            "1s": 1 / 60,  # 1 second = 1/60 minute
            "1m": 1,
            "3m": 3,
            "5m": 5,
            "15m": 15,
            "30m": 30,
            "1h": 60,
            "2h": 120,
            "4h": 240,
            "6h": 360,
            "8h": 480,
            "12h": 720,
            "1d": 1440,
        }

        if period in interval_minutes:
            minutes_total = limit * interval_minutes[period]
            start_date = datetime.now() - timedelta(minutes=minutes_total)
            start = start_date.strftime("%Y-%m-%d")
            end = datetime.now().strftime("%Y-%m-%d")
        else:
            # Default fallback for unknown periods
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
    result = collector.collect_timeframe_data(period)

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
    timeframe: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    output_dir: Optional[Union[str, Path]] = None,
    *,
    interval: Optional[str] = None,
) -> pd.DataFrame:
    """Download cryptocurrency data (alias for fetch_data).

    Provides familiar API patterns for intuitive data collection.

    Args:
        symbol: Trading pair symbol (e.g., "BTCUSDT")
        timeframe: Timeframe interval (default: "1h" if neither specified)
        start: Start date in YYYY-MM-DD format
        end: End date in YYYY-MM-DD format
        output_dir: Directory to save CSV files
        interval: Legacy parameter name for timeframe (deprecated)

    Returns:
        pandas.DataFrame with complete OHLCV and microstructure data

    Examples:
        # Simple data download
        df = download("BTCUSDT", "1h", start="2024-01-01", end="2024-06-30")

        # Simple recent data
        df = download("ETHUSDT", "4h")

        # Legacy interval parameter
        df = download("BTCUSDT", interval="1h")
    """
    # Apply default if neither parameter specified
    if timeframe is None and interval is None:
        timeframe = "1h"

    return fetch_data(
        symbol=symbol,
        timeframe=timeframe,
        start=start,
        end=end,
        output_dir=output_dir,
        interval=interval,
    )


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
        for tf in ["1s", "1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d"]:
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


def get_supported_intervals() -> List[str]:
    """Get list of supported timeframe intervals (legacy alias).

    Deprecated: Use get_supported_timeframes() instead.
    Maintained for backward compatibility with existing code.

    Returns:
        List of timeframe strings (e.g., ["1m", "5m", "1h", "4h", ...])

    Examples:
        >>> intervals = get_supported_intervals()  # deprecated
        >>> timeframes = get_supported_timeframes()  # preferred
    """
    import warnings

    warnings.warn(
        "get_supported_intervals() is deprecated. Use get_supported_timeframes() instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return get_supported_timeframes()


def save_parquet(df: pd.DataFrame, path: str) -> None:
    """Save DataFrame to Parquet format with optimized compression.

    Args:
        df: DataFrame to save
        path: Output file path (should end with .parquet)

    Raises:
        FileNotFoundError: If output directory doesn't exist
        PermissionError: If cannot write to path
        ValueError: If DataFrame is invalid

    Examples:
        >>> df = fetch_data("BTCUSDT", "1h", limit=1000)
        >>> save_parquet(df, "btc_data.parquet")
    """
    if df is None or df.empty:
        raise ValueError("Cannot save empty DataFrame to Parquet")

    df.to_parquet(path, engine="pyarrow", compression="snappy", index=False)


def load_parquet(path: str) -> pd.DataFrame:
    """Load DataFrame from Parquet file.

    Args:
        path: Parquet file path

    Returns:
        DataFrame with original structure and data types

    Raises:
        FileNotFoundError: If file doesn't exist
        ParquetError: If file is corrupted or invalid

    Examples:
        >>> df = load_parquet("btc_data.parquet")
        >>> print(f"Loaded {len(df)} bars")
    """
    return pd.read_parquet(path, engine="pyarrow")
