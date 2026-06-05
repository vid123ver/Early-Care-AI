from database.mongo import fetch_user_reports_metrics

def analyze_trend(values):
    """
    values: list of (created_at, value)
    Returns: 'increasing risk', 'decreasing risk', or 'stable'
    """
    if len(values) < 2:
        return 'insufficient data'
    vals = [v for _, v in values]
    if vals[-1] > vals[0]:
        return 'increasing risk'
    elif vals[-1] < vals[0]:
        return 'decreasing risk'
    else:
        return 'stable'

def get_metric_trend(user_id, marker):
    values = fetch_user_reports_metrics(user_id, marker)
    trend = analyze_trend(values)
    return {
        'marker': marker,
        'history': [{"date": str(date), "value": val} for date, val in values],
        'trend': trend
    }

def get_all_trends(user_id, markers):
    return {m: get_metric_trend(user_id, m) for m in markers}
