def render_status_badge(status: str) -> str:
    """Renders a colored HTML badge for a strategy status."""
    colors = {
        "inbox": "#6c757d",           # Gray
        "refined": "#007bff",         # Blue
        "testing": "#ffc107",         # Yellow
        "paper_trading": "#17a2b8",  # Cyan
        "deployed": "#28a745",        # Green
        "paused": "#fd7e14",         # Orange
        "rejected": "#dc3545",       # Red
        "retired": "#343a40"         # Dark Gray
    }
    color = colors.get(status, "#6c757d")
    return f'<span style="background-color: {color}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.8em; font-weight: bold;">{status.upper().replace("_", " ")}</span>'
