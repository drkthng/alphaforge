# AlphaForge: RealTest to Dashboard Workflow

This guide covers the standard daily workflow: starting from a backtest in RealTest, exporting the required data, and ingesting it into AlphaForge for tracking and analysis.

## Step 1: Run Your Backtest in RealTest
Develop your strategy and run your backtest or optimization in RealTest as you normally would. Ensure your strategy settings and parameters are finalized for the run you want to record.

## Step 2: Export Data from RealTest
AlphaForge requires up to three pieces of information to fully record a run. At an absolute minimum, it needs the **Stats CSV**. For the best experience, export all three:

1. **Stats CSV (Required):**
   - In RealTest, go to the results grid.
   - Right-click and export the results to a CSV file (e.g., `stats.csv`).
   - *Note:* AlphaForge will automatically read your performance metrics (Net Profit, Sharpe, MaxDD, etc.) and any custom parameters that appear after the `MaxExp` column.

2. **Equity Curve CSV (Highly Recommended):**
   - Open the equity chart for your backtest in RealTest.
   - Export the daily equity data to a CSV file (e.g., `equity.csv`).
   - This allows AlphaForge to generate interactive charts and calculate custom In-Sample/Out-of-Sample metrics.

3. **Strategy File (.rts) (Recommended):**
   - Save your RealTest strategy script (e.g., `my_strategy.rts`).
   - AlphaForge will archive a copy of this file and hash it, guaranteeing you always know the exact code that produced a specific backtest result.

*Tip: Save all these files in a dedicated temporary output folder (e.g., `C:\RealTest\Output\MyStrategy\`) to make ingestion easier.*

## Step 3: Ingest Data into AlphaForge
With your files exported, open your terminal (ensure your AlphaForge virtual environment is activated) and use the `ingest run` command.

```powershell
alphaforge ingest run "C:\RealTest\Output\MyStrategy\stats.csv" `
  --equity-csv "C:\RealTest\Output\MyStrategy\equity.csv" `
  --rts "C:\RealTest\Output\MyStrategy\my_strategy.rts" `
  --strategy "My Strategy Name" `
  --universe "SP500"
```

**What happens during ingestion?**
- AlphaForge parses the stats and records the run.
- It detects if this exact combination of parameters has been run before (preventing duplicate clutter).
- It versions and neatly archives the `.rts` file.
- It converts the equity CSV into a highly compressed Parquet file for blazing-fast dashboard rendering.

*Alternative: Bulk Scan*
If you've exported multiple CSVs to a single directory, you can ingest them all at once:
```powershell
alphaforge ingest scan "C:\RealTest\Output\MyStrategy\"
```

## Step 4: Analyze in the Dashboard
Once ingested, launch the dashboard to review your research:

```powershell
alphaforge launch
```

1. **Pipeline:** Move the newly ingested strategy from the *Inbox* to *Refining* or *Testing*.
2. **Leaderboard:** Compare this new run against all your historical tests. Sort by Sharpe, Net Profit, or Custom Metrics.
3. **Strategy Detail:** Click into the strategy to view the interactive equity curve, check parameter heatmaps, and analyze the In-Sample vs. Out-of-Sample performance split.
4. **Quick Capture:** Use the Research Inbox to jot down observations, paste relevant links, and capture ideas. Notes can later be linked to specific strategies for a complete research trail.
