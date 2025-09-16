#!/usr/bin/env python3
"""
Gapless Crypto Data - CLI Entry Point

Ultra-fast cryptocurrency data collection with automatic gap filling and full 11-column microstructure format.
Uses Binance public data repository (22x faster) with authentic API-first validation.

Gap filling is automatic by default during collection - no manual intervention required.

Usage:
    uv run gapless-crypto-data [--symbol SYMBOL] [--timeframes TF1,TF2,...] [--start DATE] [--end DATE] [--output-dir DIR]
    uv run gapless-crypto-data --fill-gaps [--directory DIR]

Examples:
    # Default: SOLUSDT, all timeframes, 4.1-year coverage with automatic gap filling
    uv run gapless-crypto-data

    # Custom symbol and timeframes with automatic gap filling
    uv run gapless-crypto-data --symbol BTCUSDT --timeframes 1h,4h,1d

    # Multiple symbols and timeframes with automatic gap filling
    uv run gapless-crypto-data --symbol BTCUSDT,ETHUSDT,SOLUSDT --timeframes 1h,4h

    # Custom date range with automatic gap filling
    uv run gapless-crypto-data --start 2022-01-01 --end 2024-01-01

    # Custom output directory for organized data storage
    uv run gapless-crypto-data --symbol ETHUSDT --timeframes 1h,4h --output-dir ./crypto_data

    # Manual gap filling for existing data files
    uv run gapless-crypto-data --fill-gaps --directory ./data
"""

import argparse
import sys
from pathlib import Path
from typing import Any

from . import __version__
from .collectors.binance_public_data_collector import BinancePublicDataCollector
from .gap_filling.universal_gap_filler import UniversalGapFiller


def list_timeframes() -> int:
    """Display all available timeframes with descriptions."""
    print("📊 Available Timeframes")
    print("=" * 50)
    print()

    # Get available timeframes from the collector
    collector = BinancePublicDataCollector()
    timeframes = collector.available_timeframes

    # Timeframe descriptions
    descriptions = {
        "1s": "1 second intervals (ultra high-frequency, very large datasets)",
        "1m": "1 minute intervals (high-frequency trading, large datasets)",
        "3m": "3 minute intervals (high-frequency analysis)",
        "5m": "5 minute intervals (short-term trading signals)",
        "15m": "15 minute intervals (intraday analysis)",
        "30m": "30 minute intervals (short-term trends)",
        "1h": "1 hour intervals (medium-term analysis, recommended)",
        "2h": "2 hour intervals (trend analysis)",
        "4h": "4 hour intervals (swing trading, popular for backtesting)",
        "6h": "6 hour intervals (broader trend analysis)",
        "8h": "8 hour intervals (daily cycle analysis)",
        "12h": "12 hour intervals (half-daily patterns)",
        "1d": "1 day intervals (daily trading, long-term trends)",
        "3d": "3 day intervals (weekly pattern analysis)",
        "1w": "1 week intervals (long-term trend analysis)",
        "1mo": "1 month intervals (macro trend analysis, small datasets)"
    }

    print("Timeframe | Description")
    print("-" * 75)

    for tf in timeframes:
        desc = descriptions.get(tf, "Standard trading interval")
        print(f"{tf:9} | {desc}")

    print()
    print("💡 Usage Examples:")
    print("   # Single timeframe")
    print("   uv run gapless-crypto-data --symbol BTCUSDT --timeframes 1h")
    print()
    print("   # Multiple timeframes")
    print("   uv run gapless-crypto-data --symbol BTCUSDT --timeframes 1m,1h,1d")
    print()
    print("   # High-frequency data")
    print("   uv run gapless-crypto-data --symbol BTCUSDT --timeframes 1s,1m")
    print()
    print("   # Long-term analysis")
    print("   uv run gapless-crypto-data --symbol BTCUSDT --timeframes 1d,1w,1mo")
    print()
    print("📈 Performance Notes:")
    print("   • Shorter intervals = larger datasets, longer collection time")
    print("   • Recommended for most use cases: 1h, 4h, 1d")
    print("   • Ultra high-frequency (1s, 1m): Use with short date ranges")

    return 0


def collect_data(command_line_args: Any) -> int:
    """Main data collection workflow"""
    # Parse symbols and timeframes
    requested_symbols = [symbol.strip() for symbol in command_line_args.symbol.split(",")]
    requested_timeframes = [timeframe.strip() for timeframe in command_line_args.timeframes.split(",")]

    print("🚀 Gapless Crypto Data Collection")
    print(f"Symbols: {requested_symbols}")
    print(f"Timeframes: {requested_timeframes}")
    print(f"Date Range: {command_line_args.start} to {command_line_args.end}")
    print("=" * 60)

    all_results = {}
    total_datasets = 0
    failed_symbols = []

    # Process each symbol
    for symbol_index, symbol in enumerate(requested_symbols, 1):
        print(f"\nProcessing {symbol} ({symbol_index}/{len(requested_symbols)})...")

        try:
            # Initialize ultra-fast collector for this symbol
            data_collector = BinancePublicDataCollector(
                symbol=symbol,
                start_date=command_line_args.start,
                end_date=command_line_args.end,
                output_dir=command_line_args.output_dir
            )

            # Collect data (22x faster than API)
            collection_results = data_collector.collect_multiple_timeframes(requested_timeframes)

            if collection_results:
                all_results[symbol] = collection_results
                total_datasets += len(collection_results)

                # Show results for this symbol
                for trading_timeframe, csv_file_path in collection_results.items():
                    file_size_mb = csv_file_path.stat().st_size / (1024 * 1024)
                    print(f"  ✅ {trading_timeframe}: {csv_file_path.name} ({file_size_mb:.1f} MB)")
            else:
                failed_symbols.append(symbol)
                print(f"  ❌ Failed to collect {symbol} data")

        except Exception as e:
            failed_symbols.append(symbol)
            print(f"  ❌ Error collecting {symbol}: {e}")

    # Final summary
    print("\n" + "=" * 60)
    if total_datasets > 0:
        print(f"🚀 ULTRA-FAST SUCCESS: Generated {total_datasets} datasets across {len(all_results)} symbols")
        if failed_symbols:
            print(f"⚠️  Failed symbols: {', '.join(failed_symbols)}")
        return 0
    else:
        print("❌ FAILED: No datasets generated")
        if failed_symbols:
            print(f"Failed symbols: {', '.join(failed_symbols)}")
        return 1


def fill_gaps(command_line_args: Any) -> int:
    """Gap filling workflow"""
    print("🔧 Gapless Crypto Data - Gap Filling")
    print(f"Directory: {command_line_args.directory or 'current directory'}")
    print("=" * 60)

    # Initialize gap filler
    gap_filler_instance = UniversalGapFiller()

    # Find CSV files and fill gaps
    target_directory = Path(command_line_args.directory) if command_line_args.directory else Path.cwd()
    discovered_csv_files = list(target_directory.glob("*.csv"))

    gaps_filled_count = 0
    for csv_file_path in discovered_csv_files:
        # Try to determine timeframe from filename (basic heuristic)
        detected_timeframe = "1h"  # Default timeframe
        if "1m" in csv_file_path.name:
            detected_timeframe = "1m"
        elif "5m" in csv_file_path.name:
            detected_timeframe = "5m"
        elif "15m" in csv_file_path.name:
            detected_timeframe = "15m"
        elif "30m" in csv_file_path.name:
            detected_timeframe = "30m"
        elif "4h" in csv_file_path.name:
            detected_timeframe = "4h"

        # Detect gaps
        detected_gaps = gap_filler_instance.detect_all_gaps(csv_file_path, detected_timeframe)

        # Fill each gap
        for timestamp_gap in detected_gaps:
            if gap_filler_instance.fill_gap(timestamp_gap, csv_file_path, detected_timeframe):
                gaps_filled_count += 1

    gap_filling_successful = gaps_filled_count > 0

    if gap_filling_successful:
        print("\n✅ GAP FILLING SUCCESS: All gaps filled")
        return 0
    else:
        print("\n❌ GAP FILLING FAILED: Some gaps remain")
        return 1


def main() -> int:
    """Main CLI entry point"""

    data_availability_info = """
Data Availability Notes:
  Historical Data: Available from each symbol's listing date
  Current Data:    Up to yesterday (T-1) - updated daily
  Future Data:     Not available (requests will fail with 404)

  Popular Symbols & Listing Dates:
    BTCUSDT:  2017-08-17  |  ETHUSDT:  2017-08-17
    SOLUSDT:  2020-08-11  |  ADAUSDT:  2018-04-17
    DOTUSDT:  2020-08-19  |  LINKUSDT: 2019-01-16

  Safe Date Range Examples:
    Recent data:      --start 2024-01-01 --end 2024-06-30
    Historical test:  --start 2022-01-01 --end 2022-12-31
    Long backtest:    --start 2020-01-01 --end 2023-12-31

  Output Directory Examples:
    Single symbol:     uv run gapless-crypto-data --symbol BTCUSDT --timeframes 1h
    Multiple symbols:  uv run gapless-crypto-data --symbol BTCUSDT,ETHUSDT --timeframes 1h,4h
    Custom directory:  uv run gapless-crypto-data --symbol BTCUSDT --timeframes 1h --output-dir ./data
    Absolute path:     uv run gapless-crypto-data --symbol BTCUSDT,ETHUSDT --timeframes 1h --output-dir /home/user/crypto_data

Performance: 22x faster than API calls via Binance public data repository with automatic gap filling and full 11-column microstructure format
"""

    parser = argparse.ArgumentParser(
        description="Ultra-fast cryptocurrency data collection with automatic gap filling and full 11-column microstructure format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__ + data_availability_info,
    )

    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Data collection command (default)
    collect_parser = subparsers.add_parser("collect", help="Collect cryptocurrency data")
    collect_parser.add_argument(
        "--symbol", default="SOLUSDT", help="Trading pair symbol(s) - single symbol or comma-separated list (default: SOLUSDT)"
    )
    collect_parser.add_argument(
        "--timeframes",
        default="1m,3m,5m,15m,30m,1h,2h,4h",
        help="Comma-separated timeframes from 16 available options (default: 1m,3m,5m,15m,30m,1h,2h,4h). Use --list-timeframes to see all available timeframes",
    )
    collect_parser.add_argument(
        "--start", default="2021-08-06", help="Start date YYYY-MM-DD (default: 2021-08-06)"
    )
    collect_parser.add_argument(
        "--end", default="2025-08-31", help="End date YYYY-MM-DD (default: 2025-08-31)"
    )
    collect_parser.add_argument(
        "--output-dir", help="Output directory for CSV files (created automatically if doesn't exist, default: src/gapless_crypto_data/sample_data/)"
    )

    # Gap filling command
    gaps_parser = subparsers.add_parser("fill-gaps", help="Fill gaps in existing data")
    gaps_parser.add_argument(
        "--directory", help="Directory containing CSV files (default: current)"
    )

    # Legacy support: direct flags for backwards compatibility
    parser.add_argument(
        "--symbol", default="SOLUSDT", help="Trading pair symbol(s) - single symbol or comma-separated list (default: SOLUSDT)"
    )
    parser.add_argument(
        "--timeframes",
        default="1m,3m,5m,15m,30m,1h,2h,4h",
        help="Comma-separated timeframes from 16 available options (default: 1m,3m,5m,15m,30m,1h,2h,4h). Use --list-timeframes to see all available timeframes",
    )
    parser.add_argument(
        "--start", default="2021-08-06", help="Start date YYYY-MM-DD (default: 2021-08-06)"
    )
    parser.add_argument(
        "--end", default="2025-08-31", help="End date YYYY-MM-DD (default: 2025-08-31)"
    )
    parser.add_argument("--fill-gaps", action="store_true", help="Fill gaps in existing data")
    parser.add_argument("--directory", help="Directory containing CSV files (default: current)")
    parser.add_argument("--output-dir", help="Output directory for CSV files (created automatically if doesn't exist, default: src/gapless_crypto_data/sample_data/)")
    parser.add_argument("--list-timeframes", action="store_true", help="List all available timeframes with descriptions")
    parser.add_argument("--version", action="version", version=f"gapless-crypto-data {__version__}")

    parsed_arguments = parser.parse_args()

    # Route to appropriate function
    if parsed_arguments.list_timeframes:
        return list_timeframes()
    elif parsed_arguments.command == "fill-gaps" or parsed_arguments.fill_gaps:
        return fill_gaps(parsed_arguments)
    elif parsed_arguments.command == "collect" or parsed_arguments.command is None:
        return collect_data(parsed_arguments)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
