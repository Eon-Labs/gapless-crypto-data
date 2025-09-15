#!/usr/bin/env python3
"""
Basic Data Collection Example

This example demonstrates how to collect cryptocurrency data using the
BinancePublicDataCollector for ultra-fast downloads (22x faster than APIs).
"""

from gapless_crypto_data import BinancePublicDataCollector


def main():
    """Demonstrate basic data collection"""
    print("🚀 Gapless Crypto Data - Basic Collection Example")
    print("=" * 60)

    # Initialize collector
    collector = BinancePublicDataCollector(
        symbol="BTCUSDT",
        start_date="2024-01-01",
        end_date="2024-01-31"
    )

    # Collect data for multiple timeframes
    timeframes = ["1h", "4h"]

    print(f"Collecting {collector.symbol} data for {timeframes}")
    print(f"Date range: {collector.start_date.strftime('%Y-%m-%d')} to {collector.end_date.strftime('%Y-%m-%d')}")
    print()

    # Collect the data
    results = collector.collect_multiple_timeframes(timeframes)

    if results:
        print("✅ Collection completed successfully!")
        print()
        print("Generated files:")
        for timeframe, filepath in results.items():
            file_size_mb = filepath.stat().st_size / (1024*1024)
            print(f"  {timeframe}: {filepath.name} ({file_size_mb:.1f} MB)")

            # Show first few rows
            import pandas as pd
            df = pd.read_csv(filepath)
            print(f"    Rows: {len(df)}")
            print(f"    Date range: {df.iloc[0]['date']} to {df.iloc[-1]['date']}")
            print()
    else:
        print("❌ Collection failed")

if __name__ == "__main__":
    main()
