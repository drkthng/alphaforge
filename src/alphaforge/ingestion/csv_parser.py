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


def parse_date_range(dates_str: str) -> Tuple[date, date]:
    """Parses 'M/D/YY - M/D/YY' or 'M/D/YY-M/D/YY' style strings."""
    if ' - ' in dates_str:
        parts = dates_str.split(' - ')
    elif '-' in dates_str:
        parts = dates_str.split('-')
    else:
        raise ValueError(f"Invalid date range format: {dates_str}")
    
    if len(parts) != 2:
        raise ValueError(f"Invalid date range format: {dates_str}")
    
    # helper for multiple date formats
    def _parse_d(s: str) -> date:
        s = s.strip()
        for fmt in ("%m/%d/%y", "%m/%d/%Y"):
            try:
                return datetime.strptime(s, fmt).date()
            except ValueError:
                continue
        raise ValueError(f"Could not parse date: {s}")

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
    """Parses RealTest stats CSV file."""
    results = []
    
    # Mapping from CSV header to internal metric name
    col_mapping = config.realtest.stats_csv_columns
    
    fixed_headers = [
        "Test", "Name", "Dates", "Periods", "NetProfit", "comp", "ROR", 
        "MaxDD", "MAR", "Trades", "PctWins", "Expectancy", "AvgWin", 
        "AvgLoss", "WinLen", "LossLen", "ProfitFactor", "Sharpe", 
        "AvgExp", "MaxExp"
    ]
    
    with open(csv_path, mode='r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Skip empty rows
            if not row or not any(str(v).strip() for v in row.values()):
                continue
                
            strategy_name = row.get("Name")
            if not strategy_name:
                continue
                
            test_number = row.get("Test", "")
            try:
                start_date, end_date = parse_date_range(row["Dates"])
            except (ValueError, KeyError):
                logger.warning(f"Skipping row with invalid dates: {row.get('Dates')}")
                continue
                
            periods = int(row["Periods"]) if row.get("Periods") else None
            
            metrics = {}
            # Map metrics using config
            for header in fixed_headers[4:]: # Skip Test, Name, Dates, Periods
                val = row.get(header)
                internal_name = col_mapping.get(header)
                if internal_name and val is not None:
                    metrics[internal_name] = parse_value(val)
            
            # Parameters are anything after MaxExp
            parameters = {}
            # We need to be careful with header matching here
            for header, val in row.items():
                if header is None: continue
                h_stripped = header.strip()
                if h_stripped not in fixed_headers:
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
        logger.warning(f"No valid data rows found in {csv_path}")
        
    return results
