#!/bin/bash
# CLI Usage Examples for Gapless Crypto Data
#
# This script demonstrates various ways to use the gapless-crypto-data CLI tool
# for ultra-fast cryptocurrency data collection and gap filling.
#
# IMPORTANT: All examples use safe historical date ranges to avoid 404 errors.
# Avoid using future dates or dates before symbol listing dates.

echo "🚀 Gapless Crypto Data - CLI Usage Examples"
echo "=========================================="
echo

echo "📋 Basic Usage Examples:"
echo

echo "1. Default collection (SOLUSDT, all timeframes, full coverage):"
echo "   uv run gapless-crypto-data"
echo

echo "2. Custom symbol and timeframes:"
echo "   uv run gapless-crypto-data --symbol BTCUSDT --timeframes 1h,4h"
echo

echo "3. Safe historical date range (recommended):"
echo "   uv run gapless-crypto-data --symbol ETHUSDT --timeframes 1m,5m --start 2022-01-01 --end 2022-01-31"
echo

echo "4. Multiple timeframes with safe range:"
echo "   uv run gapless-crypto-data --symbol ADAUSDT --timeframes 1m,3m,5m,15m,30m,1h,2h,4h --start 2023-01-01 --end 2023-06-30"
echo

echo "5. Gap filling in current directory:"
echo "   uv run gapless-crypto-data --fill-gaps"
echo

echo "6. Gap filling in specific directory:"
echo "   uv run gapless-crypto-data --fill-gaps --directory ./data"
echo

echo "🔧 Advanced Examples:"
echo

echo "7. High-frequency data collection:"
echo "   uv run gapless-crypto-data --symbol BTCUSDT --timeframes 1m --start 2024-01-01 --end 2024-01-07"
echo

echo "8. Multi-asset collection (run separately for each symbol):"
echo "   for symbol in BTCUSDT ETHUSDT SOLUSDT ADAUSDT; do"
echo "     uv run gapless-crypto-data --symbol \$symbol --timeframes 1h,4h --start 2024-01-01 --end 2024-01-31"
echo "   done"
echo

echo "📊 Performance Benchmarks:"
echo

echo "9. Quick demo (small date range for testing):"
echo "   uv run gapless-crypto-data --symbol BTCUSDT --timeframes 1h --start 2024-01-01 --end 2024-01-02"
echo

echo "10. Full month collection (typical production use):"
echo "    uv run gapless-crypto-data --symbol SOLUSDT --timeframes 1m,5m,1h --start 2024-01-01 --end 2024-01-31"
echo

echo "🎯 Workflow Examples:"
echo

echo "11. Complete data pipeline:"
echo "    # Step 1: Collect data"
echo "    uv run gapless-crypto-data --symbol ETHUSDT --timeframes 1h --start 2024-01-01 --end 2024-01-31"
echo "    "
echo "    # Step 2: Fill any gaps"
echo "    uv run gapless-crypto-data --fill-gaps"
echo "    "
echo "    # Step 3: Verify results"
echo "    ls -la *.csv"
echo

echo "12. Batch processing with gap filling:"
echo "    # Collect data for multiple symbols"
echo "    symbols=(BTCUSDT ETHUSDT SOLUSDT ADAUSDT DOTUSDT)"
echo "    for symbol in \"\${symbols[@]}\"; do"
echo "      echo \"Collecting \$symbol...\""
echo "      uv run gapless-crypto-data --symbol \$symbol --timeframes 1h,4h --start 2024-01-01 --end 2024-01-31"
echo "    done"
echo "    "
echo "    # Fill gaps for all collected data"
echo "    echo \"Filling gaps...\""
echo "    uv run gapless-crypto-data --fill-gaps"
echo

echo "💡 Pro Tips:"
echo

echo "13. Use environment variables for repeated parameters:"
echo "    export GAPLESS_SYMBOL=BTCUSDT"
echo "    export GAPLESS_START=2024-01-01"
echo "    export GAPLESS_END=2024-01-31"
echo "    # Note: Environment variable support would need to be implemented"
echo

echo "14. Pipe output for logging:"
echo "    uv run gapless-crypto-data --symbol BTCUSDT --timeframes 1h | tee collection.log"
echo

echo "15. Background processing:"
echo "    nohup uv run gapless-crypto-data --symbol BTCUSDT --timeframes 1m --start 2023-01-01 --end 2023-12-31 > collection.log 2>&1 &"
echo

echo "🚀 Performance Notes:"
echo "- Ultra-fast: 22x faster than API-based collection"
echo "- Parallel downloads: Multiple monthly files downloaded concurrently"
echo "- Zero gaps: Automatic gap detection and multi-exchange fallback"
echo "- Production ready: Atomic file operations prevent corruption"
echo

echo "📚 Getting Help:"
echo "   uv run gapless-crypto-data --help"
echo

echo "Demo completed! Try running any of the above commands to see the tool in action."