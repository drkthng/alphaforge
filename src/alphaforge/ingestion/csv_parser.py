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
    """Parses RealTest stats CSV file with robust header matching."""
    results = []
    
    # Mapping from CSV header to internal metric name
    col_mapping = config.realtest.stats_csv_columns
    
    fixed_headers = [
        "Test", "Name", "Dates", "Periods", "NetProfit", "comp", "ROR", 
        "MaxDD", "MAR", "Trades", "PctWins", "Expectancy", "AvgWin", 
        "AvgLoss", "WinLen", "LossLen", "ProfitFactor", "Sharpe", 
        "AvgExp", "MaxExp"
    ]

    name_aliases = {"name", "strategy", "strategy name"}
    date_aliases = {"dates", "date", "run dates", "backtest dates"}
    period_aliases = {"periods", "bars"}
    
    with open(csv_path, mode='r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
        
        # Find Aliases
        name_col = next((h for h in headers if h.lower() in name_aliases), "Name")
        date_col = next((h for h in headers if h.lower() in date_aliases), "Dates")
        period_col = next((h for h in headers if h.lower() in period_aliases), "Periods")

        # Periodic Report Detection: If the file contains columns unique to daily reports, reject it.
        periodic_detection_cols = {"equity", "tweq", "drawdown", "daily", "weekly", "monthly"}
        headers_lower = {h.lower() for h in headers}
        found_periodic = headers_lower.intersection(periodic_detection_cols)
        if found_periodic:
            raise ValueError(
                f"This file looks like a Periodic Report (found columns: {list(found_periodic)}). "
                "AlphaForge requires a Backtest Summary CSV as the primary ingestion file. "
                "Please use the periodic report file as the --equity-csv instead."
            )

        for row in reader:
            # Skip empty rows
            if not row or not any(str(v).strip() for v in row.values()):
                continue
                
            strategy_name = row.get(name_col)
            if not strategy_name:
                continue
                
            test_number = row.get("Test", "")
            
            dates_val = row.get(date_col)
            if not dates_val:
                logger.warning(f"Skipping row: missing date column '{date_col}'")
                continue

            try:
                start_date, end_date = parse_date_range(dates_val)
            except (ValueError, KeyError):
                logger.warning(f"Skipping row with invalid dates: {dates_val}")
                continue
                
            periods_val = row.get(period_col)
            periods = int(periods_val) if periods_val else None
            
            metrics = {}
            # Map metrics using config
            for header in fixed_headers[4:]: # Skip Test, Name, Dates, Periods
                val = row.get(header)
                internal_name = col_mapping.get(header)
                if internal_name and val is not None:
                    metrics[internal_name] = parse_value(val)
            
            # Parameters are anything not in fixed_headers and not an alias for core fields
            parameters = {}
            core_cols = {name_col, date_col, period_col, "Test"}
            for header, val in row.items():
                if header is None: continue
                h_stripped = header.strip()
                if h_stripped not in fixed_headers and h_stripped not in core_cols:
                    parameters[h_stripped] = parse_value(val)
            
            param_hash = compute_parameter_hash(parameters)
            
            results.append(ParsedRow(
                strategy_name=strategy_name,
                test_number=test_number,
                date_range_start=start_date,
                date_range_end=end_date,
                periods=periods,
                metrics=metrics,
                parameters=parameters,
                parameter_hash=param_hash
            ))
            
    if not results:
        logger.warning(f"No valid data rows found in {csv_path}. Headers found: {headers}")
        
    return results
