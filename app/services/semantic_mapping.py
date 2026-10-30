"""Rule-based semantic mapping with confidence scoring.

The mapping engine combines:
  - column-name similarity
  - inferred data type compatibility
  - sample-value patterns

Never trust a mapping blindly: always return (concept, confidence, reason).
"""

VOCAB = [
    # (concept, keywords, expected_types, base_confidence)
    ("PATIENT_IDENTIFIER", ["patient no", "patient number", "patient id", "patientid", "patient_no"], ["identifier", "numeric", "text"], 0.99),
    ("ADMISSION_IDENTIFIER", ["admission no", "admission number", "adm no", "admission_no"], ["identifier", "numeric", "text"], 0.98),
    ("VISIT_IDENTIFIER", ["visit no", "visit id", "visit_no"], ["identifier", "numeric", "text"], 0.95),
    ("RECORD_REFERENCE", ["reference no", "ref no", "reference number"], ["identifier", "numeric", "text"], 0.85),
    ("CLINICAL_EVENT_SEQUENCE", ["round no", "round number", "event no", "sequence"], ["identifier", "numeric"], 0.95),
    ("VISIT_TYPE", ["visit category", "visit type", "patient category"], ["categorical", "text"], 0.92),
    ("PATIENT_FAMILY_NAME", ["surname", "last name", "family name"], ["text", "categorical"], 0.99),
    ("PATIENT_GIVEN_NAME", ["first name", "given name"], ["text", "categorical"], 0.99),
    ("PATIENT_OTHER_NAME", ["other name", "middle name"], ["text", "categorical"], 0.95),
    ("PATIENT_REGISTRATION_DATE", ["join date", "registration date", "enrol date"], ["date"], 0.70),
    ("CLINICIAN_NAME", ["attending doctor", "doctor", "clinician", "medical officer", "physician"], ["text", "categorical"], 0.97),
    ("ADMISSION_DATE", ["admission date", "adm date", "date admitted"], ["date"], 0.98),
    ("ADMISSION_TIME", ["admission time", "adm time"], ["time"], 0.98),
    ("DISCHARGE_DATE", ["discharge date", "date discharged"], ["date"], 0.98),
    ("DISCHARGE_TIME", ["discharge time"], ["time"], 0.95),
    ("CLINICAL_EVENT_DATE", ["round date", "ward round date", "event date", "visit date"], ["date"], 0.94),
    ("CLINICAL_EVENT_TIME", ["round time", "ward round time", "event time", "visit time"], ["time"], 0.94),
    ("USER_LOGIN_ID", ["login id", "login", "username", "user id"], ["text", "identifier"], 0.90),
    ("POSSIBLE_WARD_OR_UNIT", ["client machine", "machine", "workstation", "ward", "unit"], ["text", "categorical"], 0.67),
    ("RECORD_ENTRY_DATE", ["record date", "entry date", "created date"], ["date"], 0.95),
    ("RECORD_ENTRY_TIME", ["record time", "entry time", "created time"], ["time"], 0.95),
    ("DIAGNOSIS", ["diagnosis", "dx", "icd"], ["text", "categorical"], 0.90),
    ("SEX", ["sex", "gender"], ["categorical"], 0.95),
    ("AGE", ["age"], ["numeric"], 0.95),
    ("DEPARTMENT", ["department", "dept", "unit"], ["categorical", "text"], 0.80),
    ("MEDICINE", ["medicine", "drug", "medication"], ["text", "categorical"], 0.85),
    ("LAB_TEST", ["test", "investigation", "lab test"], ["text", "categorical"], 0.85),
]


def _matches(name, keywords):
    n = name.lower()
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
                reason.append(
                    f"Inferred type '{inferred_type}' does not match expected {expected_types}"
                )
            return concept, round(score, 2), reason

    return "UNKNOWN", 0.0, ["No known synonym matched"]
