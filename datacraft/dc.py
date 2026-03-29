import json
import sys
import os
from pathlib import Path
import pandas as pd
import difflib


SUPPORTED_FORMATS = {'.csv', '.json', '.geojson', '.xlsx', '.xls'}



# ─────────────────────────────────────────
# DATA CLEANING SESSION
# ─────────────────────────────────────────

def show_sample(dfs: list[pd.DataFrame], col: str):
    print("╔══════════════════════════════════════════════╗")
    print("║              SAMPLE DATA                     ║")
    print("╚══════════════════════════════════════════════╝")
    for i, df in enumerate(dfs, 1):
        print(f"\n  📄 File {i} — kolom '{col}':")
        print("  Head:")
        for val in df[col].dropna().head(5):
            print(f"    {val}")
        print("  Tail:")
        for val in df[col].dropna().tail(5):
            print(f"    {val}")


def input_rules() -> dict:
    print("\n  Format: CARI=GANTI (pisah koma)")
    print("  Contoh: KABUPATEN=KAB, KAB.=KAB")
    raw = input("  Rules: ").strip()

    if not raw:
        return {}

    rules = {}
    for pair in raw.split(','):
        if '=' in pair:
            k, v = pair.split('=', 1)
            rules[k.strip().upper()] = v.strip()
    return rules


def apply_bulk_rules(dfs, col, rules):
    if not rules:
        return dfs

    result = []
    for df in dfs:
        df = df.copy()
        df[col] = df[col].astype(str)
        for cari, ganti in rules.items():
            # Exact match — bukan contains
            mask = df[col].str.strip() == cari
            count = mask.sum()
            if count > 0:
                df.loc[mask, col] = ganti
                print(f"  🔄 '{cari}' → '{ganti}' ({count} replacement)")
            else:
                print(f"  ⚠️  '{cari}' tidak ditemukan di data")
        df[col] = df[col].str.strip()
        result.append(df)
    return result

def cleaning_session(dfs, col):
    while True:
        os.system('clear')
        show_sample(dfs, col)
        rules = input_rules()

        if rules:
            dfs = apply_bulk_rules(dfs, col, rules)
            os.system('clear')
            print("╔══════════════════════════════════════════════╗")
            print("║         PREVIEW SETELAH RULES DIAPPLY        ║")
            print("╚══════════════════════════════════════════════╝")
            show_sample(dfs, col)

        print("\n  [1] Tambah rules")
        print("  [2] Lanjut")

        if input("  Pilih: ").strip() == "2":
            return dfs

def rename_columns_session(dfs: list, metas: list) -> list:
    while True:
        os.system('clear')
        print("╔══════════════════════════════════════════════╗")
        print("║           RESOLVE KOLOM                      ║")
        print("╚══════════════════════════════════════════════╝")

        # Tampil kolom + sample tiap file
        for i, df in enumerate(dfs, 1):
            print(f"\n  📄 File {i} — {Path(metas[i-1]['path']).name}")
            for j, col in enumerate(df.columns, 1):
                sample = df[col].dropna().iloc[0] if len(df) > 0 else '-'
                print(f"    [{j}] {col} → {sample}")

        print("\n  [1] Rename kolom File 1 ikut File 2")
        print("  [2] Rename kolom File 2 ikut File 1")
        print("  [3] Bulk rename manual")
        print("  [4] Selesai")

        pilih = input("\n  Pilih: ").strip()

        if pilih == "1":
            dfs = _rename_by_reference(dfs, source_idx=0, target_idx=1)

        elif pilih == "2":
            dfs = _rename_by_reference(dfs, source_idx=1, target_idx=0)

        elif pilih == "3":
            dfs = _bulk_rename(dfs)

        elif pilih == "4":
            break

        # Cek apakah sudah ada kolom yang sama
        common = find_common_columns(dfs)
        if common:
            print(f"\n  ✅ Kolom yang sama ditemukan: {common}")
            print("  [1] Lanjut")
            print("  [2] Rename lagi")
            if input("  Pilih: ").strip() == "1":
                break

    return dfs


def _rename_by_reference(dfs: list, source_idx: int, target_idx: int) -> list:
    """Rename kolom source agar match dengan target — user pilih mapping."""
    os.system('clear')
    print("╔══════════════════════════════════════════════╗")
    print("║           RENAME BY REFERENCE                ║")
    print("╚══════════════════════════════════════════════╝")

    source_cols = list(dfs[source_idx].columns)
    target_cols = list(dfs[target_idx].columns)

    print(f"\n  Target (File {target_idx+1}): {target_cols}")
    print(f"\n  Pilih kolom File {source_idx+1} yang mau direname:\n")

    for i, col in enumerate(source_cols, 1):
        sample = dfs[source_idx][col].dropna().iloc[0] if len(dfs[source_idx]) > 0 else '-'
        print(f"  [{i}] {col} → {sample}")

    print(f"  [0] Batal")

    while True:
        try:
            p = int(input("\n  Pilih kolom: "))
            if p == 0:
                return dfs
            if 1 <= p <= len(source_cols):
                old = source_cols[p - 1]
                break
        except ValueError:
            pass
        print("  Input tidak valid.")

    print(f"\n  Rename '{old}' jadi kolom mana di File {target_idx+1}?")
    for i, col in enumerate(target_cols, 1):
        print(f"  [{i}] {col}")

    while True:
        try:
            p = int(input("\n  Pilih: "))
            if 1 <= p <= len(target_cols):
                new = target_cols[p - 1]
                break
        except ValueError:
            pass
        print("  Input tidak valid.")

    dfs = [df.copy() for df in dfs]
    dfs[source_idx].rename(columns={old: new}, inplace=True)
    print(f"\n  ✅ '{old}' → '{new}'")
    input("  Enter untuk lanjut...")
    return dfs


def _bulk_rename(dfs: list) -> list:
    """Bulk rename manual — format FILE:LAMA=BARU."""
    os.system('clear')
    print("╔══════════════════════════════════════════════╗")
    print("║           BULK RENAME MANUAL                 ║")
    print("╚══════════════════════════════════════════════╝")

    for i, df in enumerate(dfs, 1):
        print(f"\n  File {i}: {list(df.columns)}")

    print("\n  Format: FILE:LAMA=BARU (pisah koma)")
    print("  Contoh: 1:NAMA_KAB/KOTA=WILAYAH, 2:PROVINSI_KABUPATEN_KOTA=WILAYAH")

    raw = input("\n  Rename: ").strip()
    if not raw:
        return dfs

    dfs = [df.copy() for df in dfs]

    for pair in raw.split(','):
        pair = pair.strip()
        if ':' in pair and '=' in pair:
            file_part, col_part = pair.split(':', 1)
            old, new = col_part.split('=', 1)
            try:
                idx = int(file_part.strip()) - 1
                old = old.strip().upper()
                new = new.strip().upper()
                if old in dfs[idx].columns:
                    dfs[idx].rename(columns={old: new}, inplace=True)
                    print(f"  ✅ File {idx+1}: '{old}' → '{new}'")
                else:
                    print(f"  ⚠️  File {idx+1}: '{old}' tidak ditemukan")
            except (ValueError, IndexError):
                print(f"  ❌ Format salah: '{pair}'")

    input("\n  Enter untuk lanjut...")
    return dfs

# ─────────────────────────────────────────
# INCONSISTENCY RESOLVER
# ─────────────────────────────────────────

def find_inconsistencies(dfs, key):
    base = set(dfs[0][key].dropna().unique())
    issues = []

    for i, df in enumerate(dfs[1:], 1):
        values = set(df[key].dropna().unique())
        for val in values:
            if val not in base:
                issues.append({
                    'val': val,
                    'file_idx': i,
                    'candidates': difflib.get_close_matches(val, base, n=3, cutoff=0.6)
                })
    return issues


def resolve_inconsistencies(dfs, key):
    issues = find_inconsistencies(dfs, key)

    if not issues:
        print("✅ Tidak ada inkonsistensi.")
        return dfs

    dfs = [df.copy() for df in dfs]

    for i, item in enumerate(issues, 1):
        os.system('clear')
        print("╔══════════════════════════════════════════════╗")
        print(f"║  RESOLUSI [{i}/{len(issues)}] — '{item['val'][:20]}'║")
        print("╚══════════════════════════════════════════════╝")
        print(f"\n  ⚠️  '{item['val']}' (File {item['file_idx']+1})\n")

        for idx, c in enumerate(item['candidates'], 1):
            print(f"  [{idx}] {c}")

        print(f"  [{len(item['candidates'])+1}] Manual")
        print(f"  [{len(item['candidates'])+2}] Skip")

        try:
            choice = int(input("\n  Pilih: "))
        except ValueError:
            continue

        if 1 <= choice <= len(item['candidates']):
            new_val = item['candidates'][choice-1]
        elif choice == len(item['candidates']) + 1:
            new_val = input("  Manual: ").strip()
        else:
            continue

        dfs[item['file_idx']][key] = dfs[item['file_idx']][key].replace(item['val'], new_val)

    os.system('clear')
    print("╔══════════════════════════════════════════════╗")
    print("║           ✅ RESOLUSI SELESAI!               ║")
    print("╚══════════════════════════════════════════════╝\n")
    return dfs

def apply_title_case(dfs, key):
    return [df.assign(**{key: df[key].str.title()}) for df in dfs]


# ─────────────────────────────────────────
# FILE HANDLING
# ─────────────────────────────────────────

def detect_format(filepath):
    ext = Path(filepath).suffix.lower()
    if ext not in SUPPORTED_FORMATS:
        raise ValueError(f"Format tidak didukung: {ext}")
    return ext


def read_file(filepath):
    ext = detect_format(filepath)
    meta = {'ext': ext, 'path': filepath, 'is_geojson': False}

    if ext == '.csv':
        df = pd.read_csv(filepath, encoding='utf-8-sig')

    elif ext in {'.json', '.geojson'}:
        with open(filepath, encoding='utf-8') as f:
            raw = json.load(f)

        if raw.get('type') == 'FeatureCollection':
            meta['is_geojson'] = True
            meta['raw_geojson'] = raw
            df = pd.DataFrame([f.get('properties', {}) for f in raw.get('features', [])])
        else:
            df = pd.read_json(filepath)

    else:
        df = pd.read_excel(filepath, engine='openpyxl')

    df.columns = df.columns.str.strip().str.upper()
    return df, meta


# ─────────────────────────────────────────
# MERGE
# ─────────────────────────────────────────

def find_common_columns(dfs):
    common = set(dfs[0].columns)
    for df in dfs[1:]:
        common &= set(df.columns)
    return sorted(common)


def merge_two(left, right, key):
    merged = pd.merge(left, right, on=key, how='outer', suffixes=('_L', '_R'))

    for col in list(merged.columns):
        if col.endswith('_L'):
            base = col[:-2]
            r = base + '_R'
            if r in merged.columns and merged[col].equals(merged[r]):
                merged[base] = merged[col]
                merged.drop([col, r], axis=1, inplace=True)

    return merged


def merge_multiple(dfs, key):
    result = dfs[0]
    for df in dfs[1:]:
        result = merge_two(result, df, key)
    return result


# ─────────────────────────────────────────
# SAVE
# ─────────────────────────────────────────

def save_result(df, path, fmt, meta=None):
    if fmt == 'csv':
        df.to_csv(path, index=False, encoding='utf-8-sig')

    elif fmt == 'xlsx':
        df.to_excel(path, index=False)

    elif fmt == 'geojson' and meta and meta.get('is_geojson'):
        raw = meta['raw_geojson']
        records = df.to_dict('records')

        for i, f in enumerate(raw.get('features', [])):
            if i < len(records):
                f['properties'] = records[i]

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(raw, f, indent=2, ensure_ascii=False)

    else:
        df.to_json(path, orient='records', indent=2, force_ascii=False)

    print(f"\n✅ Saved: {path}")


# ─────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────

def main():
    os.system('clear')
    print("╔══════════════════════════════════════════════╗")
    print("║              DataCraft v1.0                  ║")
    print("╚══════════════════════════════════════════════╝")

    dfs, metas = [], []

    while True:
        fp = input(f"\n  Masukkan file {len(dfs)+1}: ").strip()

        if not fp:
            if not dfs:
                print("  ❌ Minimal 1 file.")
                continue
            break

        try:
            df, meta = read_file(fp)
            dfs.append(df)
            metas.append(meta)
            print(f"  ✅ {fp} → {len(df)} baris | kolom: {list(df.columns)}")
        except Exception as e:
            print(f"  ❌ {e}")
            continue

        if len(dfs) >= 2:
            lanjut = input("\n  Tambah file lagi? [Y=tambah / kosong=lanjut]: ").strip().lower()
            if lanjut != 'y':
                break

    # Mode inspect — hanya 1 file
    if len(dfs) == 1:
        os.system('clear')
        print("╔══════════════════════════════════════════════╗")
        print("║              MODE INSPECT                    ║")
        print("╚══════════════════════════════════════════════╝")

        cols = list(dfs[0].columns)
        print("\n  Pilih kolom:")
        for i, col in enumerate(cols, 1):
            print(f"  [{i}] {col}")

        if len(cols) > 3:
            print(f"\n  ⚠️  Banyak kolom ({len(cols)}), input maksimal [{len(cols)}]")

        while True:
            try:
                pilih = int(input("\n  Pilih: "))
                if 1 <= pilih <= len(cols):
                    col = cols[pilih - 1]
                    break
            except ValueError:
                pass
            print(f"  Input tidak valid. Pilih 1–{len(cols)}")

        show_sample(dfs, col)

        while True:
            print("\n  [1] Cleaning kolom ini")
            print("  [2] Pindah kolom")
            print("  [3] Selesai")

            pilih = input("  Pilih: ").strip()

            if pilih == "1":
                dfs = cleaning_session(dfs, col)

            elif pilih == "2":
                print("\n  Pilih kolom:")
                for i, c in enumerate(cols, 1):
                    print(f"  [{i}] {c}")

                while True:
                    try:
                        p = int(input("\n  Pilih: "))
                        if 1 <= p <= len(cols):
                            col = cols[p - 1]
                            break
                    except ValueError:
                        pass
                    print(f"  Input tidak valid. Pilih 1–{len(cols)}")

                os.system('clear')
                show_sample(dfs, col)

            elif pilih == "3":
                # Tanya simpan atau tidak
                print("\n  Simpan hasil? [1] Ya  [2] Tidak")
                if input("  Pilih: ").strip() == "1":
                    print("\n  Format output:")
                    for i, f in enumerate(['csv', 'json', 'xlsx', 'geojson'], 1):
                        print(f"  [{i}] {f}")

                    while True:
                        try:
                            p = int(input("  Pilih: "))
                            if 1 <= p <= 4:
                                fmt = ['csv', 'json', 'xlsx', 'geojson'][p - 1]
                                break
                        except ValueError:
                            pass
                        print("  Input tidak valid.")

                    name = input("  Nama output (tanpa ekstensi): ").strip()
                    save_result(dfs[0], f"{name}.{fmt}", fmt, metas[0])

                    print("\n╔══════════════════════════════════════════════╗")
                    print("║                  SELESAI! 🎉                 ║")
                    print("╚══════════════════════════════════════════════╝\n")
                break
      
    # Mode merge — 2 file atau lebih
    common = find_common_columns(dfs)

    if not common:
        print("\n⚠️  Tidak ada kolom yang sama.")
        dfs = rename_columns_session(dfs, metas)
        common = find_common_columns(dfs)

        if not common:
            print("\n❌ Masih tidak ada kolom yang sama. Keluar.")
            return

    print(f"\n🔍 Kolom yang sama: {common}")

    if len(common) == 1:
        key = common[0]
        print(f"  ✅ Otomatis pakai key: {key}")
    else:
        print("\n  Pilih kolom kunci:")
        for i, col in enumerate(common, 1):
            print(f"  [{i}] {col}")
        while True:
            try:
                pilih = int(input("  Pilih: "))
                if 1 <= pilih <= len(common):
                    key = common[pilih - 1]
                    break
            except ValueError:
                pass
            print("  Input tidak valid.")

    dfs = cleaning_session(dfs, key)
    dfs = resolve_inconsistencies(dfs, key)
    dfs = apply_title_case(dfs, key)

    os.system('clear')
    print("╔══════════════════════════════════════════════╗")
    print("║              HASIL MERGE                     ║")
    print("╚══════════════════════════════════════════════╝")

    result = merge_multiple(dfs, key)
    print(f"\n  ✅ {len(result)} baris | {len(result.columns)} kolom")
    print(f"  Kolom: {list(result.columns)}")

    print("\n╔══════════════════════════════════════════════╗")
    print("║              SIMPAN OUTPUT                   ║")
    print("╚══════════════════════════════════════════════╝")

    print("\n  Format output:")
    for i, f in enumerate(['csv', 'json', 'xlsx', 'geojson'], 1):
        print(f"  [{i}] {f}")

    while True:
        try:
            pilih = int(input("  Pilih: "))
            if 1 <= pilih <= 4:
                fmt = ['csv', 'json', 'xlsx', 'geojson'][pilih - 1]
                break
        except ValueError:
            pass
        print("  Input tidak valid.")

    name = input("  Nama output (tanpa ekstensi): ").strip()
    meta = next((m for m in metas if m.get('is_geojson')), None)

    save_result(result, f"{name}.{fmt}", fmt, meta)

    print("\n╔══════════════════════════════════════════════╗")
    print("║                  SELESAI! 🎉                 ║")
    print("╚══════════════════════════════════════════════╝\n")
    return


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  👋 Keluar. Sampai jumpa!\n")