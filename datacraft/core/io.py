import json
from pathlib import Path
import pandas as pd

SUPPORTED_FORMATS = {
    '.csv', '.tsv',
    '.json', '.jsonl', '.geojson',
    '.xlsx', '.xls',
    '.parquet'
}


def detect_format(filepath):
    ext = Path(filepath).suffix.lower()
    if ext not in SUPPORTED_FORMATS:
        raise ValueError(f"Format tidak didukung: {ext}")
    return ext


def read_file(filepath):
    ext = detect_format(filepath)
    meta = {'ext': ext, 'path': filepath, 'is_geojson': False}

    # CSV / TSV
    if ext in {'.csv', '.tsv'}:
        sep = '\t' if ext == '.tsv' else ','
        df = pd.read_csv(filepath, encoding='utf-8-sig', sep=sep)

    # JSON / JSONL / GEOJSON
    elif ext in {'.json', '.jsonl', '.geojson'}:
        if ext == '.jsonl':
            df = pd.read_json(filepath, lines=True)
        else:
            with open(filepath, encoding='utf-8') as f:
                raw = json.load(f)

            if raw.get('type') == 'FeatureCollection':
                meta['is_geojson'] = True
                meta['raw_geojson'] = raw
                df = pd.DataFrame([
                    f.get('properties', {})
                    for f in raw.get('features', [])
                ])
            else:
                df = pd.read_json(filepath)

    # Excel
    elif ext in {'.xlsx', '.xls'}:
        df = pd.read_excel(filepath, engine='openpyxl')

    # Parquet (optional)
    elif ext == '.parquet':
        try:
            df = pd.read_parquet(filepath)
        except ImportError:
            raise ImportError(
                "Parquet butuh 'pyarrow', tidak tersedia di environment ini. "
                "Silahkan install pyarrow terlebih dahulu."
            )

    else:
        raise ValueError(f"Format tidak didukung: {ext}")

    # Normalisasi kolom
    df.columns = df.columns.str.strip().str.upper()

    return df, meta


def save_result(df, path, fmt, meta=None):
    # CSV / TSV
    if fmt in {'csv', 'tsv'}:
        sep = '\t' if fmt == 'tsv' else ','
        df.to_csv(path, index=False, encoding='utf-8-sig', sep=sep)

    # Excel
    elif fmt == 'xlsx':
        df.to_excel(path, index=False)

    # JSON
    elif fmt == 'json':
        df.to_json(path, orient='records', indent=2, force_ascii=False)

    # JSON Lines
    elif fmt == 'jsonl':
        df.to_json(path, orient='records', lines=True, force_ascii=False)

    # GeoJSON (preserve structure)
    elif fmt == 'geojson' and meta and meta.get('is_geojson'):
        raw = meta['raw_geojson']
        records = df.to_dict('records')

        for i, f in enumerate(raw.get('features', [])):
            if i < len(records):
                f['properties'] = records[i]

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(raw, f, indent=2, ensure_ascii=False)

    # Parquet (optional)
    elif fmt == 'parquet':
        try:
            df.to_parquet(path, index=False)
        except ImportError:
            raise ImportError(
                "Parquet butuh 'pyarrow', tidak tersedia di environment ini. "
                "Silahkan install pyarrow terlebih dahulu."
            )

    else:
        raise ValueError(f"Format output tidak didukung: {fmt}")