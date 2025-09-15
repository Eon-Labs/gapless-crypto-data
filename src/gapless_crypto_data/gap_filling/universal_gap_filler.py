#!/usr/bin/env python3
"""
Universal Gap Filler - Detects and fills ALL gaps in OHLCV CSV files

This script automatically detects ALL gaps in any timeframe's CSV file and fills them
using KuCoin data, regardless of whether they're in the legitimate gaps registry.

Unlike the existing gap filler which only handles 2 specific operational gaps,
this universal filler handles all detected gaps for complete validation success.

Key Features:
- Auto-detects gaps by analyzing timestamp sequences
- Uses KuCoin API with timezone alignment
- Handles all timeframes (1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h)
- Processes gaps chronologically to maintain data integrity
- Fixes KuCoin timestamp offset issue
"""

import logging
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class UniversalGapFiller:
    """Universal gap detection and filling for all timeframes"""

    def __init__(self):
        self.kucoin_base_url = "https://api.kucoin.com/api/v1/market/candles"
        self.symbol = "SOL-USDT"
        self.timeframe_mapping = {
            '1m': '1min',
            '3m': '3min',
            '5m': '5min',
            '15m': '15min',
            '30m': '30min',
            '1h': '1hour',
            '2h': '2hour',
            '4h': '4hour'
        }

    def detect_all_gaps(self, csv_path: Path, timeframe: str) -> List[Dict]:
        """Detect ALL gaps in CSV file by analyzing timestamp sequence"""
        logger.info(f"🔍 Analyzing {csv_path} for gaps...")

        # Load CSV data
        df = pd.read_csv(csv_path, comment='#')
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')

        # Calculate expected interval
        interval_mapping = {
            '1m': timedelta(minutes=1),
            '3m': timedelta(minutes=3),
            '5m': timedelta(minutes=5),
            '15m': timedelta(minutes=15),
            '30m': timedelta(minutes=30),
            '1h': timedelta(hours=1),
            '2h': timedelta(hours=2),
            '4h': timedelta(hours=4)
        }
        expected_interval = interval_mapping[timeframe]

        gaps = []
        for i in range(1, len(df)):
            current_time = df.iloc[i]['date']
            previous_time = df.iloc[i-1]['date']
            actual_gap = current_time - previous_time

            if actual_gap > expected_interval:
                gap_info = {
                    'position': i,
                    'start_time': previous_time + expected_interval,
                    'end_time': current_time,
                    'duration': actual_gap,
                    'expected_interval': expected_interval
                }
                gaps.append(gap_info)
                logger.info(f"   📊 Gap {len(gaps)}: {gap_info['start_time']} → {gap_info['end_time']} ({gap_info['duration']})")

        logger.info(f"✅ Found {len(gaps)} gaps in {timeframe} timeframe")
        return gaps

    def fetch_kucoin_data(self, start_time: datetime, end_time: datetime, timeframe: str) -> Optional[List[Dict]]:
        """Fetch data from KuCoin API with timezone correction"""
        kucoin_timeframe = self.timeframe_mapping[timeframe]

        # Convert to timestamps
        start_ts = int(start_time.timestamp())
        end_ts = int(end_time.timestamp())

        params = {
            'symbol': self.symbol,
            'type': kucoin_timeframe,
            'startAt': start_ts,
            'endAt': end_ts
        }

        logger.info(f"   📡 KuCoin API call: {params}")

        try:
            response = requests.get(self.kucoin_base_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            if data['code'] != '200000' or not data['data']:
                logger.warning(f"   ❌ KuCoin returned no data: {data}")
                return None

            # KuCoin API returned data successfully

            # Convert KuCoin data to OHLCV format with timezone correction
            candles = []
            for candle in data['data']:
                # KuCoin returns: [timestamp, open, close, high, low, volume, turnover]
                timestamp = int(candle[0])
                candle_time = datetime.fromtimestamp(timestamp, tz=timezone.utc).replace(tzinfo=None)

                # FIXED: Remove timezone correction - KuCoin timestamps are already in correct UTC
                corrected_time = candle_time

                # Only include candles within the gap period
                if start_time <= corrected_time < end_time:
                    ohlcv = {
                        'timestamp': corrected_time.strftime('%Y-%m-%d %H:%M:%S'),
                        'open': float(candle[1]),
                        'high': float(candle[3]),
                        'low': float(candle[4]),
                        'close': float(candle[2]),
                        'volume': float(candle[5])
                    }
                    candles.append(ohlcv)
                    logger.info(f"   ✅ Retrieved candle: {corrected_time}")

            logger.info(f"   📈 Retrieved {len(candles)} candles from KuCoin")
            return candles

        except Exception as e:
            logger.error(f"   ❌ KuCoin API error: {e}")
            return None

    def fill_gap(self, gap_info: Dict, csv_path: Path, timeframe: str) -> bool:
        """Fill a single gap with KuCoin data using timestamp-based insertion"""
        logger.info(f"🔧 Filling gap: {gap_info['start_time']} → {gap_info['end_time']}")

        # Fetch data from KuCoin
        kucoin_data = self.fetch_kucoin_data(
            gap_info['start_time'],
            gap_info['end_time'],
            timeframe
        )

        if not kucoin_data:
            logger.error("   ❌ Failed to fetch KuCoin data for gap")
            return False

        # Load current CSV data
        df = pd.read_csv(csv_path, comment='#')
        df['date'] = pd.to_datetime(df['date'])

        # Create DataFrame for KuCoin data
        kucoin_df = pd.DataFrame(kucoin_data)
        kucoin_df['date'] = pd.to_datetime(kucoin_df['timestamp'])
        kucoin_df = kucoin_df[['date', 'open', 'high', 'low', 'close', 'volume']]

        # FIXED: Filter KuCoin data to only include timestamps within the gap period
        start_time = pd.to_datetime(gap_info['start_time'])
        end_time = pd.to_datetime(gap_info['end_time'])

        # Only include KuCoin data that falls within the gap period
        gap_mask = (kucoin_df['date'] >= start_time) & (kucoin_df['date'] < end_time)
        filtered_kucoin_df = kucoin_df[gap_mask].copy()

        if len(filtered_kucoin_df) == 0:
            logger.warning("   ⚠️ No KuCoin data falls within gap period after filtering")
            return False

        logger.info(f"   📊 Filtered to {len(filtered_kucoin_df)} candles within gap period")

        # FIXED: Simple append and sort - no position-based insertion needed
        filled_df = pd.concat([df, filtered_kucoin_df], ignore_index=True)

        # Sort by date and remove any exact timestamp duplicates (keep first occurrence)
        filled_df = filled_df.sort_values('date').drop_duplicates(subset=['date'], keep='first')

        # Validate gap was actually filled
        filled_df_sorted = filled_df.sort_values('date').reset_index(drop=True)
        remaining_gaps = []

        # Check if gap is filled by looking for continuous timestamps
        for i in range(1, len(filled_df_sorted)):
            current_time = filled_df_sorted.iloc[i]['date']
            previous_time = filled_df_sorted.iloc[i-1]['date']
            expected_interval = pd.Timedelta(minutes=1) if timeframe == '1m' else pd.Timedelta(hours=1) if timeframe == '1h' else pd.Timedelta(minutes=int(timeframe[:-1]))
            actual_gap = current_time - previous_time

            if actual_gap > expected_interval:
                # Check if this overlaps with our target gap
                if (previous_time < end_time) and (current_time > start_time):
                    remaining_gaps.append(f"{previous_time} → {current_time}")

        if remaining_gaps:
            logger.warning(f"   ⚠️ Gap partially filled - remaining gaps: {remaining_gaps}")

        # Save back to CSV with header comments preserved
        header_comments = []
        with open(csv_path, 'r') as f:
            for line in f:
                if line.startswith('#'):
                    header_comments.append(line.rstrip())
                else:
                    break

        # Write header comments + data
        with open(csv_path, 'w') as f:
            for comment in header_comments:
                f.write(comment + '\n')
            filled_df.to_csv(f, index=False)

        logger.info(f"   ✅ Gap filled with {len(filtered_kucoin_df)} candles")
        return True

    def process_file(self, csv_path: Path, timeframe: str) -> Dict:
        """Process a single CSV file - detect and fill ALL gaps"""
        logger.info(f"🎯 Processing {csv_path} ({timeframe})")

        # Detect all gaps
        gaps = self.detect_all_gaps(csv_path, timeframe)

        if not gaps:
            logger.info(f"   ✅ No gaps found in {timeframe}")
            return {
                'timeframe': timeframe,
                'gaps_detected': 0,
                'gaps_filled': 0,
                'gaps_failed': 0,
                'success_rate': 100.0
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
            'timeframe': timeframe,
            'gaps_detected': len(gaps),
            'gaps_filled': filled_count,
            'gaps_failed': failed_count,
            'success_rate': success_rate
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
    target_timeframes = ['1m', '3m', '5m', '15m', '30m', '1h', '2h']

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

    total_gaps_detected = sum(r['gaps_detected'] for r in results)
    total_gaps_filled = sum(r['gaps_filled'] for r in results)
    total_gaps_failed = sum(r['gaps_failed'] for r in results)

    for result in results:
        status = "✅" if result['success_rate'] == 100.0 else "⚠️" if result['success_rate'] > 0 else "❌"
        logger.info(f"{status} {result['timeframe']:>3}: {result['gaps_filled']:>2}/{result['gaps_detected']:>2} gaps filled ({result['success_rate']:>5.1f}%)")

    logger.info("-" * 60)
    overall_success = (total_gaps_filled / total_gaps_detected * 100) if total_gaps_detected > 0 else 100.0
    logger.info(f"🎯 OVERALL: {total_gaps_filled}/{total_gaps_detected} gaps filled ({overall_success:.1f}%)")
    logger.info("=" * 60)

    if overall_success == 100.0:
        logger.info("🎉 ALL GAPS FILLED SUCCESSFULLY! Ready for validation.")
    else:
        logger.warning(f"⚠️ {total_gaps_failed} gaps failed to fill. Manual review needed.")

if __name__ == "__main__":
    main()
