import pandas as pd
from datetime import datetime


def format_date(dt_string: str) -> str:
    """Convert ISO datetime string to readable format."""
    try:
        dt = datetime.fromisoformat(dt_string.replace("Z", "+00:00"))
        return dt.strftime("%d %b %Y, %I:%M %p")
    except Exception:
        return dt_string


def format_date_only(dt_string: str) -> str:
    try:
        dt = datetime.fromisoformat(dt_string.replace("Z", "+00:00"))
        return dt.strftime("%d %b %Y")
    except Exception:
        return dt_string


def compute_attendance_percentage(attended: int, total: int) -> float:
    if total == 0:
        return 0.0
    return round((attended / total) * 100, 2)


def build_attendance_dataframe(records: list, sessions: list) -> pd.DataFrame:
    """
    Build a student-vs-session attendance pivot table.
    records: list of attendance_record dicts
    sessions: list of attendance_session dicts
    Returns a DataFrame.
    """
    if not records or not sessions:
        return pd.DataFrame()

    session_dates = {s['id']: format_date_only(s.get('session_date', s.get('created_at', '')))
                     for s in sessions}

    rows = []
    for r in records:
        rows.append({
            "Student": r.get("profiles", {}).get("full_name", "Unknown"),
            "Email": r.get("profiles", {}).get("email", ""),
            "Session": session_dates.get(r.get("session_id"), "Unknown"),
            "Method": r.get("method", "").capitalize(),
            "Time": format_date(r.get("marked_at", ""))
        })

    return pd.DataFrame(rows)


def attendance_summary_df(records: list, total_sessions: int) -> pd.DataFrame:
    """
    Summarize attendance count per student.
    """
    if not records:
        return pd.DataFrame()

    from collections import Counter
    counter = Counter()
    name_map = {}

    for r in records:
        sid = r.get("student_id")
        counter[sid] += 1
        if sid not in name_map:
            profile = r.get("profiles", {})
            name_map[sid] = {
                "Name": profile.get("full_name", "Unknown"),
                "Email": profile.get("email", "")
            }

    rows = []
    for sid, count in counter.items():
        pct = compute_attendance_percentage(count, total_sessions)
        rows.append({
            "Name": name_map[sid]["Name"],
            "Email": name_map[sid]["Email"],
            "Classes Attended": count,
            "Total Classes": total_sessions,
            "Attendance %": pct
        })

    df = pd.DataFrame(rows).sort_values("Attendance %", ascending=False)
    return df


def status_badge(pct: float) -> str:
    if pct >= 75:
        return "🟢"
    elif pct >= 50:
        return "🟡"
    else:
        return "🔴"
