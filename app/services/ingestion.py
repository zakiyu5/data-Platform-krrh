import os
import hashlib
import pandas as pd
from werkzeug.utils import secure_filename


def compute_hash(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def save_upload(file, upload_folder):
    filename = secure_filename(file.filename)
    os.makedirs(upload_folder, exist_ok=True)
    path = os.path.join(upload_folder, filename)
    # Never overwrite; add numeric suffix if exists
    if os.path.exists(path):
        base, ext = os.path.splitext(filename)
        i = 1
        while os.path.exists(path):
            path = os.path.join(upload_folder, f"{base}_{i}{ext}")
            i += 1
    file.save(path)
    return path, os.path.basename(path)


def read_dataset(path):
    ext = path.rsplit(".", 1)[-1].lower()
    if ext == "csv":
        try:
            df = pd.read_csv(path)
        except UnicodeDecodeError:
            df = pd.read_csv(path, encoding="latin-1")
    elif ext in ("xlsx", "xls"):
        df = pd.read_excel(path, engine="openpyxl")
    else:
        raise ValueError(f"Unsupported file extension: {ext}")

    # Clean column names (strip whitespace)
    df.columns = [str(c).strip() for c in df.columns]
    # Drop fully empty rows
    df = df.dropna(how="all").reset_index(drop=True)
    return df
