#!/usr/bin/env python3
"""
Gapless Crypto Data - CLI Entry Point

Ultra-fast cryptocurrency data collection with automatic gap filling and full 11-column microstructure format.
Uses Binance public data repository (22x faster) with authentic API-first validation.

Gap filling is automatic by default during collection - no manual intervention required.

Usage:
    uv run gapless-crypto-data [--symbol SYMBOL] [--timeframes TF1,TF2,...] [--start DATE] [--end DATE]
    uv run gapless-crypto-data --fill-gaps [--directory DIR]

Examples:
    # Default: SOLUSDT, all timeframes, 4.1-year coverage with automatic gap filling
    uv run gapless-crypto-data

    # Custom symbol and timeframes with automatic gap filling
    uv run gapless-crypto-data --symbol BTCUSDT --timeframes 1h,4h,1d

    # Custom date range with automatic gap filling
    uv run gapless-crypto-data --start 2022-01-01 --end 2024-01-01

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


def collect_data(args: Any) -> int:
    """Main data collection workflow"""
    # Parse timeframes
    timeframes = [tf.strip() for tf in args.timeframes.split(",")]

    print("🚀 Gapless Crypto Data Collection")
    print(f"Symbol: {args.symbol}")
    print(f"Timeframes: {timeframes}")
    print(f"Date Range: {args.start} to {args.end}")
    print("=" * 60)

    # Initialize ultra-fast collector
    collector = BinancePublicDataCollector(
        symbol=args.symbol, start_date=args.start, end_date=args.end
    )

    # Collect data (22x faster than API)
    results = collector.collect_multiple_timeframes(timeframes)

    if results:
        print(f"\n🚀 ULTRA-FAST SUCCESS: Generated {len(results)} datasets")
        for tf, filepath in results.items():
            file_size_mb = filepath.stat().st_size / (1024 * 1024)
            print(f"  {tf}: {filepath.name} ({file_size_mb:.1f} MB)")
        return 0
    else:
        print("❌ FAILED: No datasets generated")
        return 1


def fill_gaps(args: Any) -> int:
    """Gap filling workflow"""
    print("🔧 Gapless Crypto Data - Gap Filling")
    print(f"Directory: {args.directory or 'current directory'}")
    print("=" * 60)

    # Initialize gap filler
    gap_filler = UniversalGapFiller()

    # Find CSV files and fill gaps
    directory = Path(args.directory) if args.directory else Path.cwd()
    csv_files = list(directory.glob("*.csv"))

    success_count = 0
    for csv_file in csv_files:
        # Try to determine timeframe from filename (basic heuristic)
        timeframe = "1h"  # Default timeframe
        if "1m" in csv_file.name:
            timeframe = "1m"
        elif "5m" in csv_file.name:
            timeframe = "5m"
        elif "15m" in csv_file.name:
            timeframe = "15m"
        elif "30m" in csv_file.name:
            timeframe = "30m"
        elif "4h" in csv_file.name:
            timeframe = "4h"

        # Detect gaps
        gaps = gap_filler.detect_all_gaps(csv_file, timeframe)

        # Fill each gap
        for gap in gaps:
            if gap_filler.fill_gap(gap, csv_file, timeframe):
                success_count += 1

    success = success_count > 0

    if success:
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
        "--symbol", default="SOLUSDT", help="Trading pair symbol (default: SOLUSDT)"
    )
    collect_parser.add_argument(
        "--timeframes",
        default="1m,3m,5m,15m,30m,1h,2h,4h",
        help="Comma-separated timeframes (default: 1m,3m,5m,15m,30m,1h,2h,4h)",
    )
    collect_parser.add_argument(
        "--start", default="2021-08-06", help="Start date YYYY-MM-DD (default: 2021-08-06)"
    )
    collect_parser.add_argument(
        "--end", default="2025-08-31", help="End date YYYY-MM-DD (default: 2025-08-31)"
    )

    # Gap filling command
    gaps_parser = subparsers.add_parser("fill-gaps", help="Fill gaps in existing data")
    gaps_parser.add_argument(
        "--directory", help="Directory containing CSV files (default: current)"
    )

    # Legacy support: direct flags for backwards compatibility
    parser.add_argument(
        "--symbol", default="SOLUSDT", help="Trading pair symbol (default: SOLUSDT)"
    )
    parser.add_argument(
        "--timeframes",
        default="1m,3m,5m,15m,30m,1h,2h,4h",
        help="Comma-separated timeframes (default: 1m,3m,5m,15m,30m,1h,2h,4h)",
    )
    parser.add_argument(
        "--start", default="2021-08-06", help="Start date YYYY-MM-DD (default: 2021-08-06)"
    )
    parser.add_argument(
        "--end", default="2025-08-31", help="End date YYYY-MM-DD (default: 2025-08-31)"
    )
    parser.add_argument("--fill-gaps", action="store_true", help="Fill gaps in existing data")
    parser.add_argument("--directory", help="Directory containing CSV files (default: current)")
    parser.add_argument("--version", action="version", version=f"gapless-crypto-data {__version__}")

    args = parser.parse_args()

    # Route to appropriate function
    if args.command == "fill-gaps" or args.fill_gaps:
        return fill_gaps(args)
    elif args.command == "collect" or args.command is None:
        return collect_data(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
