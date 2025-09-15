# Gapless Crypto Data Examples

This directory contains comprehensive examples demonstrating how to use the gapless-crypto-data package for ultra-fast cryptocurrency data collection and gap filling.

## 🚀 Quick Start

### Prerequisites

Make sure you have the package installed:

```bash
# Using UV (recommended)
uv add gapless-crypto-data

# Or using pip
pip install gapless-crypto-data
```

## 📁 Example Files

### 1. [basic_data_collection.py](basic_data_collection.py)
**Demonstrates:** Basic data collection workflow

**Key Features:**
- Initialize BinancePublicDataCollector
- Collect data for multiple timeframes
- Analyze collected data

**Run it:**
```bash
uv run python examples/basic_data_collection.py
```

### 2. [gap_filling_example.py](gap_filling_example.py)
**Demonstrates:** Gap detection and filling

**Key Features:**
- Create sample data with gaps
- Detect gaps using UniversalGapFiller
- Fill gaps with authentic Binance API data
- Verify results

**Run it:**
```bash
uv run python examples/gap_filling_example.py
```

### 3. [complete_workflow.py](complete_workflow.py)
**Demonstrates:** End-to-end data pipeline

**Key Features:**
- Complete data collection workflow
- Data quality analysis
- Gap detection and filling
- Final data validation

**Run it:**
```bash
uv run python examples/complete_workflow.py
```

### 4. [cli_usage_examples.sh](cli_usage_examples.sh)
**Demonstrates:** CLI usage patterns

**Key Features:**
- Various CLI command examples
- Performance optimization tips
- Batch processing workflows
- Production use cases

**View it:**
```bash
bash examples/cli_usage_examples.sh
```

## 🎯 Example Workflows

### Quick Demo (2-3 minutes)
Perfect for testing and understanding the package:

```bash
# 1. Basic collection
uv run python examples/basic_data_collection.py

# 2. Gap filling demo
uv run python examples/gap_filling_example.py

# 3. CLI quick test
uv run gapless-crypto-data --symbol BTCUSDT --timeframes 1h --start 2024-01-01 --end 2024-01-02
```

### Production Workflow
For real-world data collection:

```bash
# 1. Large-scale collection with automatic gap filling
uv run gapless-crypto-data --symbol SOLUSDT --timeframes 1m,5m,1h,4h --start 2023-01-01 --end 2023-12-31

# 2. Complete workflow demo
uv run python examples/complete_workflow.py
```

### Batch Processing
For multiple symbols:

```bash
# Collect data for multiple assets with automatic gap filling
symbols=(BTCUSDT ETHUSDT SOLUSDT ADAUSDT)
for symbol in "${symbols[@]}"; do
  uv run gapless-crypto-data --symbol $symbol --timeframes 1h,4h --start 2024-01-01 --end 2024-01-31
done
```

## 📊 Expected Output

When you run the examples, you'll see:

1. **Ultra-fast collection** (22x faster than APIs)
2. **Progress indicators** showing download status
3. **File generation** with metadata
4. **Gap detection** and filling results
5. **Data validation** summaries

### Sample Output Structure
```
├── binance_spot_BTCUSDT-1h_20240101-20240131_1.0y.csv
├── binance_spot_BTCUSDT-1h_20240101-20240131_1.0y.metadata.json
├── binance_spot_ETHUSDT-4h_20240101-20240131_1.0y.csv
└── binance_spot_ETHUSDT-4h_20240101-20240131_1.0y.metadata.json
```

## 🔧 Customization

All examples can be customized by modifying:

- **Symbols:** Change `symbol` parameter (e.g., BTCUSDT, ETHUSDT, SOLUSDT)
- **Timeframes:** Modify timeframes list (1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h)
- **Date ranges:** Adjust start_date and end_date
- **Output locations:** Change file paths and directories

## 💡 Pro Tips

1. **Start small:** Use 1-2 day ranges for testing
2. **Scale gradually:** Increase to weeks/months for production
3. **Monitor performance:** Check file sizes and processing times
4. **Validate data:** Always run gap detection after collection
5. **Use multiple timeframes:** Different analyses need different granularity

## 🚨 Important Notes

- **Network dependency:** Examples require internet for data downloads
- **Storage space:** Large date ranges generate significant data
- **API limits:** Respect Binance public data fair usage
- **File cleanup:** Examples may create temporary files

## 📚 Further Reading

- [Main README](../README.md) - Package overview and installation
- [API Documentation](../docs/) - Detailed API reference
- [GitHub Issues](https://github.com/Eon-Labs/gapless-crypto-data/issues) - Report problems or request features

## 🤝 Contributing

Found an issue with examples or have ideas for new ones? Please:

1. Check existing issues
2. Create a new issue with details
3. Submit a pull request with improvements

---

**Happy data collecting! 🚀📊**