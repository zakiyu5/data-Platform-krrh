VOCAB = [
    ("PATIENT_IDENTIFIER", ["patient id", "patient no", "patient number", "patientid", "patient_no", "id"], ["identifier", "numeric", "text"], 0.99),
    ("ADMISSION_IDENTIFIER", ["admission no", "admission number", "adm no", "admission_no"], ["identifier", "numeric", "text"], 0.98),
    ("CLINICIAN_NAME", ["attending doctor", "doctor", "clinician", "medical officer", "physician"], ["text", "categorical"], 0.97),
    ("SEX", ["sex", "gender"], ["categorical"], 0.95),
    ("AGE", ["age"], ["numeric"], 0.95),
    ("CONDITION", ["condition", "diagnosis", "dx", "disease", "illness"], ["text", "categorical"], 0.92),
    ("PROCEDURE", ["procedure", "surgery", "intervention", "operation"], ["text", "categorical"], 0.92),
    ("COST", ["cost", "price", "amount", "fee", "charge", "bill"], ["numeric"], 0.92),
    ("LENGTH_OF_STAY", ["length of stay", "los", "days admitted", "stay duration"], ["numeric"], 0.90),
    ("OUTCOME", ["outcome", "result", "disposition", "status"], ["text", "categorical"], 0.88),
    ("SATISFACTION", ["satisfaction", "rating", "score", "feedback"], ["numeric", "categorical"], 0.85),
    ("READMISSION", ["readmission", "readmit", "readmitted"], ["categorical", "text"], 0.85),
    ("VISIT_TYPE", ["visit category", "visit type", "patient category"], ["categorical", "text"], 0.92),
    ("ADMISSION_DATE", ["admission date", "adm date", "date admitted"], ["date"], 0.98),
    ("CLINICAL_EVENT_DATE", ["round date", "ward round date", "event date", "visit date"], ["date"], 0.94),
]

def _matches(name, keywords):
    n = name.lower().replace("_", " ").replace("-", " ")
    return any(k in n for k in keywords)

def map_column(column_name, inferred_type):
    """Return (concept, confidence, reason)."""
    for concept, keywords, expected_types, base in VOCAB:
        if _matches(column_name, keywords):
            score = base
            reason = [f"Name matches known synonym for {concept}"]
            if inferred_type in expected_types:
                score = min(score + 0.01, 0.99)
                reason.append(f"Inferred type '{inferred_type}' matches expected")
            else:
                score = max(score - 0.15, 0.30)
                reason.append(f"Inferred type '{inferred_type}' does not match expected")
            return concept, round(score, 2), reason

    return "UNKNOWN", 0.0, ["No known synonym matched"]
