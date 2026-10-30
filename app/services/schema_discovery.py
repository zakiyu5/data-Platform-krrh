import pandas as pd


def infer_column_type(series):
    s = series.dropna()
    if len(s) == 0:
        return "empty"

    sample = s.head(200).astype(str)

    # Time detection first (HH:MM or HH:MM:SS)
    time_like = sample.str.match(r"^\d{1,2}:\d{2}(:\d{2})?$")
    if time_like.mean() > 0.8:
        return "time"

    # Date / datetime
    date_success = 0
    for v in sample.head(50):
        try:
            pd.to_datetime(v, errors="raise")
            date_success += 1
        except Exception:
            pass
    if date_success / min(len(sample), 50) > 0.8:
        return "date"

    # Numeric
    try:
        pd.to_numeric(s)
        return "numeric"
    except Exception:
        pass

    # Identifier vs categorical vs text
    cardinality = s.nunique() / max(len(s), 1)
    if cardinality > 0.9 and len(s) > 20:
        return "identifier"
    if s.nunique() <= 30:
        return "categorical"
    return "text"


def profile_dataframe(df):
    profiles = []
    for i, col in enumerate(df.columns):
        s = df[col]
        profiles.append({
            "name": col,
            "position": i,
            "dtype": str(s.dtype),
            "inferred_type": infer_column_type(s),
            "non_null": int(s.notna().sum()),
            "null_count": int(s.isna().sum()),
            "null_pct": round(float(s.isna().mean() * 100), 2),
            "unique_count": int(s.nunique()),
            "sample_values": ", ".join(
                [str(x) for x in s.dropna().head(3).tolist()]
            ),
        })
    return profiles


def detect_context(df, profiles):
    """Very lightweight context detection by matching column names."""
    names = [p["name"].lower() for p in profiles]
    joined = " | ".join(names)

    rules = [
        ("WARD_ROUNDS", ["round no", "round date", "attending doctor", "admission no"], 0.90),
        ("OPD", ["visit date", "opd", "outpatient", "diagnosis"], 0.75),
        ("PHARMACY", ["medicine", "drug", "quantity", "dispens"], 0.80),
        ("LABORATORY", ["test", "result", "specimen", "lab"], 0.75),
        ("ADMISSIONS", ["admission date", "admission no", "ward"], 0.70),
        ("DISCHARGES", ["discharge date", "discharge"], 0.75),
        ("MATERNITY", ["delivery", "parity", "anc", "gestation"], 0.75),
        ("IMMUNISATION", ["vaccine", "immunis", "dose"], 0.75),
    ]
    best = ("UNKNOWN", 0.0)
    for ctx, keywords, base in rules:
        hits = sum(1 for k in keywords if k in joined)
        score = min(base + 0.03 * hits, 0.99) if hits > 0 else 0.0
        if score > best[1]:
            best = (ctx, round(score, 2))
    return best
