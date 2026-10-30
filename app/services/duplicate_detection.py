import pandas as pd


def _find(df, keywords):
    for c in df.columns:
        cl = c.lower()
        if any(k in cl for k in keywords):
            return c
    return None


def detect_duplicates(df):
    """Return dict describing exact + event-level duplicates."""
    result = {
        "exact_count": 0,
        "exact_sample": [],
        "event_count": 0,
        "event_groups": [],
        "repeated_patients": 0,
        "keys": {},
    }

    # --- Level 1: exact row duplicate ---
    exact_mask = df.duplicated(keep=False)
    exact_df = df[exact_mask]
    result["exact_count"] = int(exact_df.shape[0])
    result["exact_sample"] = exact_df.head(10).to_dict("records")

    # --- Key discovery ---
    pat = _find(df, ["patient no", "patient number", "patient id", "patientid"])
    adm = _find(df, ["admission no", "admission number", "adm no"])
    rdate = _find(df, ["round date"])
    rtime = _find(df, ["round time"])
    doc = _find(df, ["attending doctor", "doctor", "clinician"])

    result["keys"] = {
        "patient": pat, "admission": adm,
        "round_date": rdate, "round_time": rtime, "doctor": doc,
    }

    # --- Repeated patients (NOT duplicates) ---
    if pat:
        result["repeated_patients"] = int(df[pat].duplicated().sum())

    # --- Level 2: event duplicates ---
    if pat and adm and rdate:
        keys = [pat, adm, rdate]
        if rtime:
            keys.append(rtime)
        if doc:
            keys.append(doc)

        grouped = df.groupby(keys, dropna=False).size().reset_index(name="count")
        dupes = grouped[grouped["count"] > 1]
        result["event_count"] = int(dupes["count"].sum() - len(dupes))
        result["event_groups"] = dupes.sort_values("count", ascending=False).head(10).to_dict("records")

    return result
