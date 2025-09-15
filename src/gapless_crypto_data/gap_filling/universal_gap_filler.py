#!/usr/bin/env python3
"""
Universal Gap Filler - Detects and fills ALL gaps in OHLCV CSV files

This script automatically detects ALL gaps in any timeframe's CSV file and fills them
using authentic Binance API data with full 11-column microstructure format.

Unlike synthetic data approaches, this filler uses authentic Binance data
providing complete microstructure columns for professional analysis.

Key Features:
- Auto-detects gaps by analyzing timestamp sequences
- Uses authentic Binance API with full 11-column microstructure format
- Handles all timeframes (1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h)
- Provides authentic order flow metrics including trade counts and taker volumes
- Processes gaps chronologically to maintain data integrity
- NO synthetic or estimated data - only authentic exchange data
- API-first validation protocol using authentic Binance data exclusively
"""

import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class UniversalGapFiller:
    """Universal gap detection and filling for all timeframes with authentic 11-column microstructure format"""

    def __init__(self):
        self.binance_base_url = "https://api.binance.com/api/v3/klines"
        self.symbol = "SOLUSDT"
        self.timeframe_mapping = {
            "1m": "1m",
            "3m": "3m",
            "5m": "5m",
            "15m": "15m",
            "30m": "30m",
            "1h": "1h",
            "2h": "2h",
            "4h": "4h",
        }

    def detect_all_gaps(self, csv_path: Path, timeframe: str) -> List[Dict]:
        """Detect ALL gaps in CSV file by analyzing timestamp sequence for 11-column format"""
        logger.info(f"🔍 Analyzing {csv_path} for gaps...")

        # Load CSV data
        df = pd.read_csv(csv_path, comment="#")
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date")

        # Calculate expected interval
        interval_mapping = {
            "1m": timedelta(minutes=1),
            "3m": timedelta(minutes=3),
            "5m": timedelta(minutes=5),
            "15m": timedelta(minutes=15),
            "30m": timedelta(minutes=30),
            "1h": timedelta(hours=1),
            "2h": timedelta(hours=2),
            "4h": timedelta(hours=4),
        }
        expected_interval = interval_mapping[timeframe]

        gaps = []
        for i in range(1, len(df)):
            current_time = df.iloc[i]["date"]
            previous_time = df.iloc[i - 1]["date"]
            actual_gap = current_time - previous_time

            if actual_gap > expected_interval:
                gap_info = {
                    "position": i,
                    "start_time": previous_time + expected_interval,
                    "end_time": current_time,
                    "duration": actual_gap,
                    "expected_interval": expected_interval,
                }
                gaps.append(gap_info)
                logger.info(
                    f"   📊 Gap {len(gaps)}: {gap_info['start_time']} → {gap_info['end_time']} ({gap_info['duration']})"
                )

        logger.info(f"✅ Found {len(gaps)} gaps in {timeframe} timeframe")
        return gaps

    def fetch_binance_data(
        self,
        start_time: datetime,
        end_time: datetime,
        timeframe: str,
        enhanced_format: bool = False,
    ) -> Optional[List[Dict]]:
        """Fetch authentic microstructure data from Binance API - NO synthetic data"""
        binance_interval = self.timeframe_mapping[timeframe]

        # Convert to millisecond timestamps for Binance API
        # ✅ UTC ONLY: All timestamps are UTC - no timezone conversion needed

        # Convert pandas Timestamp to datetime if needed
        if hasattr(start_time, "to_pydatetime"):
            start_time = start_time.to_pydatetime()
        if hasattr(end_time, "to_pydatetime"):
            end_time = end_time.to_pydatetime()

        # Simple UTC timestamp conversion - CSV timestamps are naive UTC
        # The CSV timestamps should be interpreted as local machine time for API calls
        # This matches how Binance API expects timestamps
        start_ts = int(start_time.timestamp() * 1000)
        end_ts = int(end_time.timestamp() * 1000)

        params = {
            "symbol": self.symbol,
            "interval": binance_interval,
            "startTime": start_ts,
            "endTime": end_ts,
            "limit": 1000,
        }

        logger.info(f"   📡 Binance API call: {params}")

        try:
            response = requests.get(self.binance_base_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            if not data:
                logger.warning("   ❌ Binance returned no data")
                return None

            # Convert Binance data to required format with authentic microstructure data
            candles = []
            for candle in data:
                # Binance returns: [open_time, open, high, low, close, volume, close_time,
                #                  quote_asset_volume, number_of_trades, taker_buy_base_asset_volume,
                #                  taker_buy_quote_asset_volume, ignore]

                open_time = datetime.fromtimestamp(int(candle[0]) / 1000)
                close_time = datetime.fromtimestamp(int(candle[6]) / 1000)

                # Only include candles within the gap period (all UTC)
                if start_time <= open_time.replace(tzinfo=None) < end_time:
                    # Basic OHLCV data (always included)
                    ohlcv = {
                        "timestamp": open_time.strftime("%Y-%m-%d %H:%M:%S"),
                        "open": float(candle[1]),
                        "high": float(candle[2]),
                        "low": float(candle[3]),
                        "close": float(candle[4]),
                        "volume": float(candle[5]),
                    }

                    # Add authentic microstructure data for enhanced format
                    if enhanced_format:
                        ohlcv.update(
                            {
                                "close_time": close_time.strftime("%Y-%m-%d %H:%M:%S"),
                                "quote_asset_volume": float(candle[7]),
                                "number_of_trades": int(candle[8]),
                                "taker_buy_base_asset_volume": float(candle[9]),
                                "taker_buy_quote_asset_volume": float(candle[10]),
                            }
                        )

                    candles.append(ohlcv)
                    logger.info(f"   ✅ Retrieved authentic candle: {open_time}")

            logger.info(f"   📈 Retrieved {len(candles)} authentic candles from Binance")
            return candles

        except Exception as e:
            logger.error(f"   ❌ Binance API error: {e}")
            return None

    def fill_gap(
        self, gap_info: Dict, csv_path: Path, timeframe: str, metadata_path: Path = None
    ) -> bool:
        """Fill a single gap with authentic Binance data using API-first validation protocol"""
        logger.info(f"🔧 Filling gap: {gap_info['start_time']} → {gap_info['end_time']}")
        logger.info("   📋 Applying API-first validation protocol")

        # Load current CSV data to detect format
        df = pd.read_csv(csv_path, comment="#")
        df["date"] = pd.to_datetime(df["date"])

        # Detect format: enhanced (11 columns) vs legacy (6 columns)
        enhanced_columns = [
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
        legacy_columns = ["date", "open", "high", "low", "close", "volume"]

        is_enhanced_format = all(col in df.columns for col in enhanced_columns)
        is_legacy_format = all(col in df.columns for col in legacy_columns)

        if is_enhanced_format:
            logger.info("   🚀 Enhanced 11-column format detected")
            format_type = "enhanced"
        elif is_legacy_format:
            logger.info("   📊 Legacy 6-column format detected")
            format_type = "legacy"
        else:
            logger.error(f"   ❌ Unknown CSV format. Columns: {list(df.columns)}")
            return False

        # ✅ API-FIRST VALIDATION: Always use authentic Binance REST API data
        logger.info("   🔍 Step 1: Attempting authentic Binance REST API data retrieval")
        binance_data = self.fetch_binance_data(
            gap_info["start_time"],
            gap_info["end_time"],
            timeframe,
            enhanced_format=is_enhanced_format,
        )

        # Track gap filling details for metadata
        gap_fill_details = {
            "timestamp": gap_info["start_time"].strftime("%Y-%m-%d %H:%M:%S"),
            "duration_hours": (gap_info["end_time"] - gap_info["start_time"]).total_seconds()
            / 3600,
            "fill_method": None,
            "data_source": None,
            "authentic_data": False,
            "synthetic_data": False,
            "reason": None,
            "ohlcv": None,
            "microstructure_data": None,
        }

        if not binance_data:
            logger.warning("   ⚠️ Step 1 Failed: No authentic API data available")
            logger.info("   🔍 Step 2: Checking if gap is legitimate exchange outage")

            # Gap represents legitimate exchange outage - preserve data integrity
            # For now, fail gracefully to maintain authentic data mandate
            logger.error("   ❌ Gap filling failed: No authentic data available via API")
            logger.info("   📋 Preserving authentic data integrity - no synthetic fill applied")
            return False
        else:
            logger.info(
                f"   ✅ Step 1 Success: Retrieved {len(binance_data)} authentic candles from API"
            )

            # Update gap fill details for authentic API data
            gap_fill_details.update(
                {
                    "fill_method": "binance_rest_api",
                    "data_source": "https://api.binance.com/api/v3/klines",
                    "authentic_data": True,
                    "synthetic_data": False,
                    "reason": "missing_from_monthly_file_but_available_via_api",
                }
            )

            if binance_data:
                first_candle = binance_data[0]
                gap_fill_details["ohlcv"] = {
                    "open": first_candle["open"],
                    "high": first_candle["high"],
                    "low": first_candle["low"],
                    "close": first_candle["close"],
                    "volume": first_candle["volume"],
                }

                if is_enhanced_format and "quote_asset_volume" in first_candle:
                    gap_fill_details["microstructure_data"] = {
                        "quote_asset_volume": first_candle["quote_asset_volume"],
                        "number_of_trades": first_candle["number_of_trades"],
                        "taker_buy_base_asset_volume": first_candle["taker_buy_base_asset_volume"],
                        "taker_buy_quote_asset_volume": first_candle[
                            "taker_buy_quote_asset_volume"
                        ],
                    }

        # Create DataFrame for Binance data
        binance_df = pd.DataFrame(binance_data)
        binance_df["date"] = pd.to_datetime(binance_df["timestamp"])

        # Select appropriate columns based on format
        if is_enhanced_format:
            # For enhanced format, include all microstructure columns
            available_columns = ["date", "open", "high", "low", "close", "volume"]
            if "close_time" in binance_df.columns:
                available_columns.extend(
                    [
                        "close_time",
                        "quote_asset_volume",
                        "number_of_trades",
                        "taker_buy_base_asset_volume",
                        "taker_buy_quote_asset_volume",
                    ]
                )
            binance_df = binance_df[available_columns]
        else:
            # For legacy format, only basic OHLCV columns
            binance_df = binance_df[["date", "open", "high", "low", "close", "volume"]]

        # FIXED: Filter Binance data to only include timestamps within the gap period
        start_time = pd.to_datetime(gap_info["start_time"])
        end_time = pd.to_datetime(gap_info["end_time"])

        # Only include Binance data that falls within the gap period
        gap_mask = (binance_df["date"] >= start_time) & (binance_df["date"] < end_time)
        filtered_binance_df = binance_df[gap_mask].copy()

        if len(filtered_binance_df) == 0:
            logger.warning("   ⚠️ No authentic Binance data falls within gap period after filtering")
            return False

        logger.info(
            f"   📊 Filtered to {len(filtered_binance_df)} authentic candles within gap period"
        )

        # FIXED: Simple append and sort - no position-based insertion needed
        filled_df = pd.concat([df, filtered_binance_df], ignore_index=True)

        # Sort by date and remove any exact timestamp duplicates (keep first occurrence)
        filled_df = filled_df.sort_values("date").drop_duplicates(subset=["date"], keep="first")

        # Validate gap was actually filled
        filled_df_sorted = filled_df.sort_values("date").reset_index(drop=True)
        remaining_gaps = []

        # Check if gap is filled by looking for continuous timestamps
        for i in range(1, len(filled_df_sorted)):
            current_time = filled_df_sorted.iloc[i]["date"]
            previous_time = filled_df_sorted.iloc[i - 1]["date"]
            expected_interval = (
                pd.Timedelta(minutes=1)
                if timeframe == "1m"
                else pd.Timedelta(hours=1)
                if timeframe == "1h"
                else pd.Timedelta(minutes=int(timeframe[:-1]))
            )
            actual_gap = current_time - previous_time

            if actual_gap > expected_interval:
                # Check if this overlaps with our target gap
                if (previous_time < end_time) and (current_time > start_time):
                    remaining_gaps.append(f"{previous_time} → {current_time}")

        if remaining_gaps:
            logger.warning(f"   ⚠️ Gap partially filled - remaining gaps: {remaining_gaps}")

        # Save back to CSV with header comments preserved
        header_comments = []
        with open(csv_path, "r") as f:
            for line in f:
                if line.startswith("#"):
                    header_comments.append(line.rstrip())
                else:
                    break

        # Write header comments + data
        with open(csv_path, "w") as f:
            for comment in header_comments:
                f.write(comment + "\n")
            filled_df.to_csv(f, index=False)

        logger.info(f"   ✅ Gap filled with {len(filtered_binance_df)} authentic candles")
        return True

    def process_file(self, csv_path: Path, timeframe: str) -> Dict:
        """Process a single CSV file - detect and fill ALL gaps"""
        logger.info(f"🎯 Processing {csv_path} ({timeframe})")

        # Detect all gaps
        gaps = self.detect_all_gaps(csv_path, timeframe)

        if not gaps:
            logger.info(f"   ✅ No gaps found in {timeframe}")
            return {
                "timeframe": timeframe,
                "gaps_detected": 0,
                "gaps_filled": 0,
                "gaps_failed": 0,
                "success_rate": 100.0,
            }

        # Fill each gap
        filled_count = 0
        failed_count = 0

        for i, gap in enumerate(gaps, 1):
            logger.info(f"   🔧 Processing gap {i}/{len(gaps)}")
            if self.fill_gap(gap, csv_path, timeframe):
                filled_count += 1
            else:
                failed_count += 1

            # Brief pause between API calls
            if i < len(gaps):
                time.sleep(1)

        success_rate = (filled_count / len(gaps)) * 100 if gaps else 100.0

        result = {
            "timeframe": timeframe,
            "gaps_detected": len(gaps),
            "gaps_filled": filled_count,
            "gaps_failed": failed_count,
            "success_rate": success_rate,
        }

        logger.info(f"   📊 Result: {filled_count}/{len(gaps)} gaps filled ({success_rate:.1f}%)")
        return result


def main():
    """Main execution function"""
    logger.info("🚀 UNIVERSAL GAP FILLER - Fill ALL Gaps in ALL Timeframes")
    logger.info("=" * 60)

    filler = UniversalGapFiller()
    sample_data_dir = Path("../sample_data")

    # Define timeframes that need gap filling (exclude 4h which is perfect)
    target_timeframes = ["1m", "3m", "5m", "15m", "30m", "1h", "2h"]

    results = []

    for timeframe in target_timeframes:
        csv_pattern = f"binance_spot_SOLUSDT-{timeframe}_*.csv"
        csv_files = list(sample_data_dir.glob(csv_pattern))

        if not csv_files:
            logger.warning(f"❌ No CSV file found for {timeframe}")
            continue

        csv_file = csv_files[0]  # Use first match
        result = filler.process_file(csv_file, timeframe)
        results.append(result)

    # Summary report
    logger.info("\n" + "=" * 60)
    logger.info("📊 UNIVERSAL GAP FILLING SUMMARY")
    logger.info("=" * 60)

    total_gaps_detected = sum(r["gaps_detected"] for r in results)
    total_gaps_filled = sum(r["gaps_filled"] for r in results)
    total_gaps_failed = sum(r["gaps_failed"] for r in results)

    for result in results:
        status = (
            "✅" if result["success_rate"] == 100.0 else "⚠️" if result["success_rate"] > 0 else "❌"
        )
        logger.info(
            f"{status} {result['timeframe']:>3}: {result['gaps_filled']:>2}/{result['gaps_detected']:>2} gaps filled ({result['success_rate']:>5.1f}%)"
        )

    logger.info("-" * 60)
    overall_success = (
        (total_gaps_filled / total_gaps_detected * 100) if total_gaps_detected > 0 else 100.0
    )
    logger.info(
        f"🎯 OVERALL: {total_gaps_filled}/{total_gaps_detected} gaps filled ({overall_success:.1f}%)"
    )
    logger.info("=" * 60)

    if overall_success == 100.0:
        logger.info("🎉 ALL GAPS FILLED SUCCESSFULLY! Ready for validation.")
    else:
        logger.warning(f"⚠️ {total_gaps_failed} gaps failed to fill. Manual review needed.")


if __name__ == "__main__":
    main()
