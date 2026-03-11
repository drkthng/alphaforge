import csv
import hashlib
import json
import logging
import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, List, Optional, Tuple, Dict

from alphaforge.config import AppConfig

logger = logging.getLogger(__name__)

# --- Ingestion Constants ---

# Hardcoded mapping: CSV column (lowercase) → RunMetric field name
FIXED_COL_TO_METRIC = {
    "netprofit":    "net_profit",
    "comp":         "compound_return",
    "ror":          "cagr",
    "cagr":         "cagr",
    "maxdd":        "max_drawdown",
    "mar":          "mar",
    "trades":       "total_trades",
    "pctwins":      "pct_wins",
    "expectancy":   "expectancy",
    "avgwin":       "avg_win",
    "average_win":  "avg_win",
    "avgloss":      "avg_loss",
    "average_loss": "avg_loss",
    "winlen":       "win_length",
    "losslen":      "loss_length",
    "profitfactor": "profit_factor",
    "sharpe":       "sharpe",
    "avgexp":       "avg_exposure",
    "maxexp":       "max_exposure",
}

METADATA_COLS = {"test", "name", "dates", "periods"}
ALL_FIXED_COLS = METADATA_COLS | set(FIXED_COL_TO_METRIC.keys())


def parse_value(raw: Optional[str]) -> Any:
    """
    Strips whitespace and converts strings like '$1,234.56' or '12.5%' to floats.
    Unrecognized formats are returned as stripped strings.
    Handles 'n/a', 'ERR', '-' as None.
    Handles negative numbers in parentheses: ($1,234.56).
    """
    if raw is None:
        return None
    s = raw.strip()
    if not s or s.lower() in ('n/a', 'err', '-'):
        return None
    
    # Negative decimals in parentheses: ($1,234.56) or (1,234.56)
    paren_match = re.match(r'^\((.*)\)$', s)
    if paren_match:
        inner = paren_match.group(1).strip()
        val = parse_value(inner)
        if isinstance(val, (int, float)):
            return -abs(val)
        return s

    # Dollars: $1,234.56 or -$120.30
    dollar_match = re.match(r'^(-)?\$([\d,]+\.?\d*)$', s)
    if dollar_match:
        neg, val = dollar_match.groups()
        val = val.replace(',', '')
        return -float(val) if neg else float(val)

    # Percentages: 12.5% or -1.2%
    # Note: Spec says strip % and return float (e.g. 18.5% -> 18.5)
    percent_match = re.match(r'^(-)?([\d.]+)%$', s)
    if percent_match:
        neg, val = percent_match.groups()
        return -float(val) if neg else float(val)

    # Plain numbers (handle commas in non-dollar numbers too just in case)
    try:
        s_clean = s.replace(',', '')
        if '.' in s_clean:
            return float(s_clean)
        return int(s_clean)
    except ValueError:
        pass

    return s


def _parse_d(s: str) -> date:
    s = s.strip()
    for fmt in ("%m/%d/%y", "%m/%d/%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Could not parse date: {s}")


def parse_date_range(dates_str: str) -> Tuple[date, date]:
    """
    Parses 'M/D/YY - M/D/YY' or 'M/D/YY-M/D/YY' style strings.
    Also supports a single 'M/D/YY' date.
    """
    if ' - ' in dates_str:
        parts = dates_str.split(' - ')
    elif '-' in dates_str and len(dates_str.split('-')) == 2:
        parts = dates_str.split('-')
    else:
        # Try as single date
        try:
            d = _parse_d(dates_str)
            return d, d
        except ValueError:
            raise ValueError(f"Invalid date format: {dates_str}")
    
    if len(parts) != 2:
        raise ValueError(f"Invalid date range format: {dates_str}")
    
    return _parse_d(parts[0]), _parse_d(parts[1])


def compute_parameter_hash(params: Dict[str, Any]) -> str:
    """
    SHA-256 of sorted JSON of normalized parameter key-value pairs.
    Values are normalized to strings after rounding floats to 6 decimal places.
    This ensures {"p": 20} and {"p": "20"} produce the same hash.
    """
    normalized = {}
    for k, v in params.items():
        if isinstance(v, float):
            v_norm = format(round(v, 6), 'g')
        else:
            v_norm = str(v)
        normalized[str(k)] = v_norm
        
    json_str = json.dumps(normalized, sort_keys=True)
    return hashlib.sha256(json_str.encode()).hexdigest()


@dataclass
class ParsedRow:
    strategy_name: str
    test_number: str
    date_range_start: date
    date_range_end: date
    metrics: Dict[str, Any]
    parameters: Dict[str, Any]
    parameter_hash: str
    periods: Optional[int] = None


def parse_stats_csv(csv_path: Path, config: AppConfig) -> List[ParsedRow]:
    """Parses RealTest results-grid CSV export.

    Columns are identified case-insensitively. Everything after the last
    recognised fixed column (MaxExp) is treated as a strategy parameter.
    """
    results = []

    name_aliases = {"name", "strategy", "strategy name"}
    date_aliases = {"dates", "date", "run dates", "backtest dates"}
    period_aliases = {"periods", "bars"}

    with open(csv_path, mode='r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []

        # Build lowercase → original-header lookup
        lower_to_orig = {h.lower().strip(): h for h in headers}

        # --- Positive identification: require mandatory columns ---
        required = {"test", "name", "dates", "netprofit"}
        # Check aliases for name/dates
        has_name = any(h.lower().strip() in name_aliases for h in headers)
        has_dates = any(h.lower().strip() in date_aliases for h in headers)
        has_test = "test" in lower_to_orig
        has_netprofit = "netprofit" in lower_to_orig

        if not (has_test and has_name and has_dates and has_netprofit):
            missing = []
            if not has_test: missing.append("Test")
            if not has_name: missing.append("Name (or Strategy)")
            if not has_dates: missing.append("Dates")
            if not has_netprofit: missing.append("NetProfit")
            raise ValueError(
                f"This file is missing required columns: {missing}. "
                "AlphaForge expects a RealTest results-grid CSV export with "
                "columns: Test, Name, Dates, Periods, NetProfit, ..., MaxExp, "
                "followed by strategy-specific parameter columns."
            )

        # Resolve aliases to actual header strings
        name_col = next((h for h in headers if h.lower().strip() in name_aliases), "Name")
        date_col = next((h for h in headers if h.lower().strip() in date_aliases), "Dates")
        period_col = next((h for h in headers if h.lower().strip() in period_aliases), "Periods")

        # Identify which headers are fixed (metrics) vs parameters
        # by checking lowercase match against ALL_FIXED_COLS
        fixed_orig_set = set()   # original header strings that are fixed
        for h in headers:
            if h.lower().strip() in ALL_FIXED_COLS:
                fixed_orig_set.add(h)
        # Also add the resolved alias columns
        fixed_orig_set.update({name_col, date_col, period_col})

        for row in reader:
            if not row or not any(str(v).strip() for v in row.values()):
                continue

            strategy_name = row.get(name_col)
            if not strategy_name:
                continue

            test_number = row.get(lower_to_orig.get("test", "Test"), "")

            dates_val = row.get(date_col)
            if not dates_val:
                logger.warning(f"Skipping row: missing date column '{date_col}'")
                continue

            try:
                start_date, end_date = parse_date_range(dates_val)
            except (ValueError, KeyError):
                logger.warning(f"Skipping row with invalid dates: {dates_val}")
                continue

            period_raw = row.get(period_col)
            try:
                periods = int(str(period_raw).replace(",", "")) if period_raw else None
            except (ValueError, TypeError):
                periods = None

            # --- Extract metrics (case-insensitive) ---
            metrics = {}
            for csv_lower, metric_name in FIXED_COL_TO_METRIC.items():
                orig_header = lower_to_orig.get(csv_lower)
                if orig_header is None:
                    continue
                raw_val = row.get(orig_header)
                if raw_val is None:
                    continue
                # Handle Comp column: "True"/"False" → skip as metric
                if csv_lower == "comp" and str(raw_val).strip().lower() in ("true", "false"):
                    continue
                metrics[metric_name] = parse_value(raw_val)

            # --- Extract parameters (everything NOT in fixed cols) ---
            parameters = {}
            for header, val in row.items():
                if header is None:
                    continue
                if header in fixed_orig_set:
                    continue
                parameters[header.strip()] = parse_value(val)

            # Also store Comp as parameter if it was boolean
            comp_header = lower_to_orig.get("comp")
            if comp_header:
                comp_raw = row.get(comp_header, "").strip().lower()
                if comp_raw in ("true", "false"):
                    parameters["Comp"] = comp_raw == "true"

            param_hash = compute_parameter_hash(parameters)

            results.append(ParsedRow(
                strategy_name=strategy_name,
                test_number=test_number,
                date_range_start=start_date,
                date_range_end=end_date,
                periods=periods,
                metrics=metrics,
                parameters=parameters,
                parameter_hash=param_hash,
            ))

    if not results:
        logger.warning(f"No valid data rows found in {csv_path}. Headers: {headers}")

    return results
