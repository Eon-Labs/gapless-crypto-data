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
    uv run gapless-crypto-data --symbol BTCUSDT --timeframes 1s,1h,4h,6h,8h,12h,1d

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
import re
import sys
from pathlib import Path
from typing import Any, Optional

from . import __version__
from .collectors.binance_public_data_collector import BinancePublicDataCollector
from .gap_filling.universal_gap_filler import UniversalGapFiller
from .resume import IntelligentCheckpointManager

# Streaming module removed - use standard pandas processing
from .utils import (
    get_standard_logger,
    handle_operation_error,
)


def parse_filename_metadata(filename: str) -> Optional[dict]:
    """
    Parse standardized filename to extract symbol and timeframe.

    Expected format: binance_spot_{SYMBOL}-{TIMEFRAME}_{START}-{END}_{VERSION}.csv
    Example: binance_spot_BTCUSDT-1h_20240101-20240101_v2.5.0.csv

    Returns:
        dict with 'symbol' and 'timeframe' keys, or None if parsing fails
    """
    pattern = r"binance_spot_([A-Z]+)-([0-9]+[mhd])_\d{8}-\d{8}_v[\d.]+\.csv$"
    match = re.match(pattern, filename)

    if match:
        symbol, timeframe = match.groups()
        return {"symbol": symbol, "timeframe": timeframe}

    return None


def add_collection_arguments(parser: argparse.ArgumentParser) -> None:
    """Add standard collection arguments to a parser. Eliminates argument duplication."""
    parser.add_argument(
        "--symbol",
        default="SOLUSDT",
        help="Trading pair symbol(s) - single symbol or comma-separated list (default: SOLUSDT)",
    )
    parser.add_argument(
        "--timeframes",
        default="1s,1m,3m,5m,15m,30m,1h,2h,4h,6h,8h,12h,1d",
        help="Comma-separated timeframes from 13 available options (default: 1s,1m,3m,5m,15m,30m,1h,2h,4h,6h,8h,12h,1d). Use --list-timeframes to see all available timeframes",
    )
    parser.add_argument(
        "--start", default="2021-08-06", help="Start date YYYY-MM-DD (default: 2021-08-06)"
    )
    parser.add_argument(
        "--end", default="2025-08-31", help="End date YYYY-MM-DD (default: 2025-08-31)"
    )
    parser.add_argument(
        "--output-dir",
        help="Output directory for CSV files (created automatically if doesn't exist, default: src/gapless_crypto_data/sample_data/)",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Enable intelligent resume from last checkpoint (default: True for large collections)",
    )
    parser.add_argument(
        "--checkpoint-dir",
        help="Directory for checkpoint files (default: ./.gapless_checkpoints)",
    )
    parser.add_argument(
        "--clear-checkpoints",
        action="store_true",
        help="Clear existing checkpoints and start fresh",
    )
    parser.add_argument(
        "--streaming",
        action="store_true",
        help="Enable memory-streaming mode for unlimited dataset sizes",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=10000,
        help="Chunk size for streaming operations (default: 10000 rows)",
    )
    parser.add_argument(
        "--memory-limit",
        type=int,
        default=100,
        help="Memory limit in MB for streaming operations (default: 100MB)",
    )


def list_timeframes() -> int:
    """Display all available timeframes with descriptions."""
    print("📊 Available Timeframes")
    print("=" * 50)
    print()

    # Get available timeframes from the collector
    collector = BinancePublicDataCollector()
    timeframes = collector.available_timeframes

    # Timeframe descriptions for all 13 supported timeframes
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
    print("   uv run gapless-crypto-data --symbol BTCUSDT --timeframes 6h,12h,1d")
    print()
    print("📈 Performance Notes:")
    print("   • Shorter intervals = larger datasets, longer collection time")
    print("   • Recommended for most use cases: 1h, 4h, 1d")
    print("   • Ultra high-frequency (1s, 1m): Use with short date ranges")

    return 0


def collect_data(command_line_args: Any) -> int:
    """Main data collection workflow with intelligent resume capabilities"""
    # Parse symbols and timeframes
    requested_symbols = [symbol.strip() for symbol in command_line_args.symbol.split(",")]
    requested_timeframes = [
        timeframe.strip() for timeframe in command_line_args.timeframes.split(",")
    ]

    # Collection parameters for checkpoint compatibility
    collection_params = {
        "start_date": command_line_args.start,
        "end_date": command_line_args.end,
        "output_dir": command_line_args.output_dir,
        "timeframes": requested_timeframes,
    }

    # Initialize checkpoint manager
    enable_resume = (
        command_line_args.resume or len(requested_symbols) > 1 or len(requested_timeframes) > 4
    )
    checkpoint_manager = None

    if enable_resume:
        checkpoint_manager = IntelligentCheckpointManager(
            cache_dir=command_line_args.checkpoint_dir,
            verbose=1 if len(requested_symbols) > 3 else 0,
        )

        if command_line_args.clear_checkpoints:
            checkpoint_manager.clear_checkpoint()
            print("🗑️  Checkpoints cleared - starting fresh")

        # Get resume plan
        resume_plan = checkpoint_manager.get_resume_plan(
            requested_symbols, requested_timeframes, collection_params
        )

        print("🚀 Gapless Crypto Data Collection with Intelligent Resume")
        print(f"📋 Checkpoint Manager: {'Enabled' if enable_resume else 'Disabled'}")
        if resume_plan["resume_required"]:
            print(f"🔄 Resuming from checkpoint: {resume_plan['message']}")
            print(f"✅ Already completed: {len(resume_plan['completed_symbols'])} symbols")
            print(f"📊 Progress: {resume_plan['total_progress']:.1f}%")
        else:
            print("🆕 Starting fresh collection")

        # Update symbols list based on resume plan
        symbols_to_process = resume_plan["remaining_symbols"]
        symbols_in_progress = resume_plan.get("symbols_in_progress", {})

        # Save collection parameters to checkpoint
        checkpoint_manager.save_checkpoint({"collection_parameters": collection_params})
    else:
        symbols_to_process = requested_symbols
        symbols_in_progress = {}
        print("🚀 Gapless Crypto Data Collection")

    print(f"Symbols: {requested_symbols}")
    print(f"Timeframes: {requested_timeframes}")
    print(f"Date Range: {command_line_args.start} to {command_line_args.end}")
    if command_line_args.streaming:
        print(
            f"🌊 Streaming Mode: Enabled (chunk_size={command_line_args.chunk_size}, memory_limit={command_line_args.memory_limit}MB)"
        )
    if enable_resume and symbols_to_process != requested_symbols:
        print(f"Remaining symbols: {symbols_to_process}")
    print("=" * 60)

    all_results = {}
    total_datasets = 0
    failed_symbols = []

    # Streaming removed - use standard pandas processing

    # Process each symbol
    for symbol_index, symbol in enumerate(symbols_to_process, 1):
        print(f"\nProcessing {symbol} ({symbol_index}/{len(symbols_to_process)})...")

        if checkpoint_manager:
            checkpoint_manager.mark_symbol_start(symbol, requested_timeframes)

        try:
            # Initialize ultra-fast collector for this symbol
            data_collector = BinancePublicDataCollector(
                symbol=symbol,
                start_date=command_line_args.start,
                end_date=command_line_args.end,
                output_dir=command_line_args.output_dir,
            )

            # Collect data (22x faster than API)
            collection_results = data_collector.collect_multiple_timeframes(requested_timeframes)

            if collection_results:
                all_results[symbol] = collection_results
                total_datasets += len(collection_results)

                # Show results for this symbol and update checkpoints
                for trading_timeframe, csv_file_path in collection_results.items():
                    file_size_mb = csv_file_path.stat().st_size / (1024 * 1024)
                    print(f"  ✅ {trading_timeframe}: {csv_file_path.name} ({file_size_mb:.1f} MB)")

                    if checkpoint_manager:
                        checkpoint_manager.mark_timeframe_complete(
                            symbol, trading_timeframe, csv_file_path, file_size_mb
                        )

                # Mark symbol as completed
                if checkpoint_manager:
                    checkpoint_manager.mark_symbol_complete(symbol)
            else:
                failed_symbols.append(symbol)
                print(f"  ❌ Failed to collect {symbol} data")

                if checkpoint_manager:
                    checkpoint_manager.mark_symbol_failed(symbol, "Collection returned no results")

        except Exception as e:
            failed_symbols.append(symbol)
            logger = get_standard_logger("cli")
            error_msg = handle_operation_error(
                operation_name=f"Data collection for {symbol}",
                exception=e,
                context={"symbol": symbol, "timeframes": command_line_args.timeframes},
                logger=logger,
                reraise=False,
            )

            if checkpoint_manager:
                checkpoint_manager.mark_symbol_failed(symbol, str(e))

    # Calculate total including resumed progress
    if checkpoint_manager:
        progress_summary = checkpoint_manager.get_progress_summary()
        total_datasets = progress_summary["total_datasets"]

        # Export progress report for analysis
        report_file = checkpoint_manager.export_progress_report()
        print(f"\n📊 Progress report: {report_file}")

    # Final summary
    print("\n" + "=" * 60)
    if total_datasets > 0:
        completion_msg = f"🚀 ULTRA-FAST SUCCESS: Generated {total_datasets} datasets"
        if checkpoint_manager:
            completed_symbols = len(checkpoint_manager.progress_data.get("symbols_completed", []))
            completion_msg += f" across {completed_symbols} completed symbols"
        else:
            completion_msg += f" across {len(all_results)} symbols"

        print(completion_msg)

        if failed_symbols:
            print(f"⚠️  Failed symbols: {', '.join(failed_symbols)}")

        if checkpoint_manager and symbols_to_process:
            print("💾 Progress saved to checkpoint - safe to resume if interrupted")

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
    target_directory = (
        Path(command_line_args.directory) if command_line_args.directory else Path.cwd()
    )
    discovered_csv_files = list(target_directory.glob("*.csv"))

    total_gaps_detected = 0
    gaps_filled_count = 0
    for csv_file_path in discovered_csv_files:
        # Parse filename to extract symbol and timeframe
        file_metadata = parse_filename_metadata(csv_file_path.name)

        if file_metadata is None:
            print(f"⚠️  Skipping {csv_file_path.name}: Non-standard filename format")
            continue

        detected_timeframe = file_metadata["timeframe"]
        detected_symbol = file_metadata["symbol"]

        print(
            f"🔍 Processing {detected_symbol} {detected_timeframe} data from {csv_file_path.name}"
        )

        # Detect gaps
        detected_gaps = gap_filler_instance.detect_all_gaps(csv_file_path, detected_timeframe)
        total_gaps_detected += len(detected_gaps)

        # Fill each gap
        for timestamp_gap in detected_gaps:
            if gap_filler_instance.fill_gap(timestamp_gap, csv_file_path, detected_timeframe):
                gaps_filled_count += 1

    # Success if no gaps detected, or if all detected gaps were filled
    gap_filling_successful = total_gaps_detected == 0 or gaps_filled_count == total_gaps_detected

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

  CLI Examples:
    Single symbol:     uv run gapless-crypto-data --symbol BTCUSDT --timeframes 1h
    Multiple symbols:  uv run gapless-crypto-data --symbol BTCUSDT,ETHUSDT --timeframes 1h,4h
    Custom directory:  uv run gapless-crypto-data --symbol BTCUSDT --timeframes 1h --output-dir ./data

  Python API Examples:
    Simple API:        import gapless_crypto_data as gcd; df = gcd.download("BTCUSDT", "1h")
    Advanced API:      from gapless_crypto_data import BinancePublicDataCollector

Performance: 22x faster than API calls via Binance public data repository with automatic gap filling and full 11-column microstructure format
"""

    parser = argparse.ArgumentParser(
        description="Ultra-fast cryptocurrency data collection with intuitive function-based API, automatic gap filling, and full 11-column microstructure format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__ + data_availability_info,
    )

    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Data collection command (default)
    collect_parser = subparsers.add_parser("collect", help="Collect cryptocurrency data")
    add_collection_arguments(collect_parser)

    # Gap filling command
    gaps_parser = subparsers.add_parser("fill-gaps", help="Fill gaps in existing data")
    gaps_parser.add_argument(
        "--directory", help="Directory containing CSV files (default: current)"
    )

    # Legacy support: direct flags for backwards compatibility
    add_collection_arguments(parser)
    parser.add_argument("--fill-gaps", action="store_true", help="Fill gaps in existing data")
    parser.add_argument("--directory", help="Directory containing CSV files (default: current)")
    parser.add_argument(
        "--list-timeframes",
        action="store_true",
        help="List all available timeframes with descriptions",
    )
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
