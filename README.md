# AlphaForge

**Your personal quant research command center.**

AlphaForge is a desktop application for systematic traders and quant researchers who use [RealTest](https://realtest.trading) for backtesting. It replaces scattered spreadsheets, forgotten CSV exports, and half-remembered parameter tweaks with a structured, searchable, visual system — built to run locally on Windows with a single click.

> Stop losing track of what you tested, when you tested it, and why it mattered.

## Features

### Strategy Pipeline
Kanban board for tracking strategy statuses from inbox to deployment. Move strategies through refined, testing, paper trading, and deployed stages.

### Automated Ingestion
Parses RealTest CSV stats and equity curves. Archives and deduplicates `.rts` strategy files via SHA-256 hashing. Detects duplicate runs via parameter hashing to prevent redundant data.

### Global Leaderboard
Sortable metrics table comparing all ingested runs across universes. Quick-filter by strategy or status to find your best performers.

### Interactive Equity Curves & Advanced Analytics
Plotly-powered interactive charts with multi-run overlays and In-Sample / Out-of-Sample split lines. Visualize drawdowns and performance metrics dynamically. A custom metrics engine and multidimensional parameter heatmaps allow for robust analysis of what matters to your specific edge.

### Research Inbox & Quick Capture
Capture research notes with URL title fetching and link them to strategies. Never lose an idea or an observation from your research sessions. 

### Global Search
FTS5-indexed global search accessible directly from the sidebar helps you instantly locate strategies, notes, and metrics.

### Settings & Backup System
Ensure your data is secure with easily accessible configuration and database backup features cleanly integrated into the application settings.

## Screenshots

> Screenshots coming soon. See [Screenshot Guide](docs/SCREENSHOT_GUIDE.md) for instructions on capturing them.

![Pipeline View](docs/screenshots/pipeline.png)
![Leaderboard](docs/screenshots/leaderboard.png)
![Strategy Detail](docs/screenshots/detail.png)
![Equity Curves](docs/screenshots/equity_curves.png)

## Quick Start

> New to AlphaForge? Read the [RealTest Workflow Guide](docs/REALTEST_WORKFLOW.md) for a step-by-step walkthrough from running a backtest to viewing the results in the dashboard.

### Prerequisites
- Python 3.11+
- Windows 10/11 (for desktop app; the dashboard runs on any OS)
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

### Install

```bash
git clone https://github.com/drkthng/alphaforge.git
cd alphaforge
uv sync        # or: pip install -e "."
```

### Initialize
```bash
alphaforge init
```
Creates the database, data directories, and default configuration.

### Configure
Copy the example config and set your RealTest output path:
```bash
cp config.yaml.example config.yaml
```
Edit `config.yaml`:
```yaml
paths:
  realtest_output_dir: "C:/RealTest/Output"  # ← Your path here
```

### Ingest Backtest Data
```bash
# Single run with stats CSV, strategy code, and equity curve
alphaforge ingest run ./path/to/stats.csv \
  --rts ./path/to/strategy.rts \
  --equity-csv ./path/to/equity.csv \
  --strategy "My Strategy Name"

# Bulk-scan a directory for all CSVs
alphaforge ingest scan ./path/to/outputs/ --strategy "My Strategy"
```

### Launch Dashboard
```bash
alphaforge launch
```

### Build Desktop App (Windows)
```bash
alphaforge build
# Output: dist/AlphaForge/AlphaForge.exe
```

## Data Storage
All data stays on your machine:

```text
data/
├── alphaforge.db        # SQLite database (metadata)
├── archive/             # Versioned .rts strategy files  
│   └── {strategy_slug}/
├── equity_curves/       # Parquet files (one per backtest run)
│   └── run_{id}.parquet
└── attachments/         # Uploaded images, PDFs
    └── {strategy_id}/
```

## CLI Reference
| Command | Description |
| --- | --- |
| `alphaforge init` | Initialize database and directories |
| `alphaforge launch` | Start the dashboard |
| `alphaforge ingest run <csv>` | Ingest a single backtest run |
| `alphaforge ingest scan <dir>` | Scan and ingest all CSVs in a directory |
| `alphaforge ingest refresh` | Re-parse metrics for a run |
| `alphaforge build` | Build Windows desktop executable |

### Ingest Options
```text
--rts PATH          Path to .rts strategy file
--equity-csv PATH   Path to equity curve CSV
--reports-dir PATH  Path to HTML report directory
--strategy NAME     Strategy name (auto-detected from CSV if omitted)
--universe NAME     Universe name (e.g., "SP500")
--notes TEXT        Notes about this run
--non-interactive   Skip duplicate prompts
```

## RealTest Integration
AlphaForge expects two types of CSV output from RealTest:

### Stats/Optimization CSV
```text
Test,Name,Dates,Periods,NetProfit,comp,ROR,MaxDD,MAR,Trades,PctWins,Expectancy,AvgWin,AvgLoss,WinLen,LossLen,ProfitFactor,Sharpe,AvgExp,MaxExp,[parameters...]
```
Columns after `MaxExp` are treated as strategy parameters.

### Equity Curve CSV
```text
Date,Strategy,Equity,TWEQ,Drawdown,DDBars,Daily,Weekly,Monthly,Quarterly,Yearly,M2M,MAE,MFE,Setups,Orders,Entries,Exits,Positions,Invested,Exposure
```

## Configuration
See `config.yaml.example` for all options.

## Roadmap
- [ ] Folder watcher for automatic ingestion
- [ ] Remote access with authentication
- [ ] Automated cloud backup
- [ ] Walk-forward analysis UI enhancements
- [ ] Live deployment journal with broker integration

## Contributing
Issues, feature requests, and pull requests are welcome.

## License
MIT