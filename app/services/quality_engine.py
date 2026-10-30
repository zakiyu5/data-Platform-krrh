import pandas as pd


def scan_quality(df, profiles):
    """Return list of quality issues and a quality score."""
    issues = []

    # 1. Missing values per column
    for p in profiles:
        if p["null_pct"] > 0:
            severity = "critical" if p["null_pct"] > 50 else (
                "warning" if p["null_pct"] > 10 else "info"
            )
            issues.append({
                "column_name": p["name"],
                "issue_type": "missing_values",
                "severity": severity,
                "description": f"{p['null_pct']}% of values are missing ({p['null_count']} rows)",
                "affected_rows": p["null_count"],
                "recommended_action": "Review missing records",
            })

    # 2. Constant columns
    for p in profiles:
        if p["unique_count"] <= 1 and p["non_null"] > 0:
            issues.append({
                "column_name": p["name"],
                "issue_type": "constant_column",
                "severity": "info",
                "description": "Column has only one unique value",
                "affected_rows": p["non_null"],
                "recommended_action": "Consider removing from analysis",
            })

    # 3. Date consistency: Round Date < Admission Date
    def _find(cols):
        return next((c for c in cols if c.lower() in (
            "admission date", "round date", "admission time", "round time"
        )), None)

    adm_col = next((c for c in df.columns if c.lower() == "admission date"), None)
    rnd_col = next((c for c in df.columns if c.lower() == "round date"), None)
    if adm_col and rnd_col:
        try:
            a = pd.to_datetime(df[adm_col], errors="coerce")
            r = pd.to_datetime(df[rnd_col], errors="coerce")
            bad = (r < a).sum()
            if bad > 0:
                issues.append({
                    "column_name": f"{rnd_col} / {adm_col}",
                    "issue_type": "date_consistency",
                    "severity": "warning",
                    "description": f"Round Date is earlier than Admission Date in {int(bad)} rows",
                    "affected_rows": int(bad),
                    "recommended_action": "Review affected records",
                })
        except Exception:
            pass

    # 4. Age plausibility
    age_col = next((c for c in df.columns if c.lower() == "age"), None)
    if age_col:
        try:
            ages = pd.to_numeric(df[age_col], errors="coerce")
            bad = ((ages < 0) | (ages > 130)).sum()
            if bad > 0:
                issues.append({
                    "column_name": age_col,
                    "issue_type": "invalid_age",
                    "severity": "critical",
                    "description": f"{int(bad)} rows have age < 0 or > 130",
                    "affected_rows": int(bad),
                    "recommended_action": "Review invalid ages",
                })
        except Exception:
            pass

    # Quality score: simple, transparent
    weights = {"critical": 10, "warning": 5, "info": 1}
    penalty = 0
    total_rows = max(len(df), 1)
    for i in issues:
        ratio = min(i["affected_rows"] / total_rows, 1.0)
        penalty += weights.get(i["severity"], 1) * ratio
    score = max(0.0, round(100 - penalty, 2))

    return issues, score
