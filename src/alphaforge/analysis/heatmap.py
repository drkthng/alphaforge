import pandas as pd
from typing import List, Dict, Any, Optional

def prepare_heatmap_data(
    runs: List[Dict[str, Any]], 
    x_param: str, 
    y_param: str, 
    metric: str, 
    fixed_params: Optional[Dict[str, Any]] = None
) -> pd.DataFrame:
    """
    Pivots run data into a 2D matrix for heatmap visualization.
    Filters the runs based on fixed_params if provided.
    """
    if not runs:
        return pd.DataFrame()
    
    filtered_data = []
    for r in runs:
        params = r.get("parameters_json", {})
        if not params:
            continue
            
        # Check if this run matches the fixed parameters
        match = True
        if fixed_params:
            for k, v in fixed_params.items():
                if params.get(k) != v:
                    match = False
                    break
        
        if match:
            # We need to extract the metric. It might be in core metrics or custom metrics.
            val = r.get(metric)
            if val is None:
                custom_metrics = r.get("custom_metrics_json", {}) or {}
                val = custom_metrics.get(metric)
            
            if x_param in params and y_param in params and val is not None:
                filtered_data.append({
                    x_param: params[x_param],
                    y_param: params[y_param],
                    metric: float(val)
                })
    
    if not filtered_data:
        return pd.DataFrame()
        
    df = pd.DataFrame(filtered_data)
    
    # Pivot. If multiple runs have the same X,Y (unlikely if fixed_params is complete), 
    # we take the mean.
    pivot_df = df.pivot_table(index=y_param, columns=x_param, values=metric, aggfunc="mean")
    
    # Ensure index and columns are sorted for a logical heatmap view
    pivot_df = pivot_df.sort_index(ascending=False).sort_index(axis=1)
    
    return pivot_df

def calculate_robustness(runs: List[Dict[str, Any]], metric: str = "sharpe", threshold: float = 0.0) -> float:
    """
    Calculates the percentage of runs where the metric exceeds the threshold.
    Higher percentage = more robust strategy across parameter space.
    """
    if not runs:
        return 0.0
        
    values = []
    for r in runs:
        val = r.get(metric)
        if val is None:
            custom_metrics = r.get("custom_metrics_json", {}) or {}
            val = custom_metrics.get(metric)
        if val is not None:
            values.append(float(val))
            
    if not values:
        return 0.0
        
    successes = sum(1 for v in values if v > threshold)
    return round((successes / len(values)) * 100, 1)
