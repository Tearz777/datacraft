import os
import pandas as pd
from pathlib import Path
from collections import Counter

from core import (
    read_file, save_result,
    apply_bulk_rules, find_inconsistencies, apply_title_case,
    find_common_columns, merge_multiple,
    analyze_column, suggest_transformation, apply_transformation,
    show_sample
)
from core.ui import box, auto_map
from core.modes.power import _input_files, input_rules_basic


# ─────────────────────────────────────────
# AUTO DETECT + APPLY
# ─────────────────────────────────────────
def _auto_detect(dfs, col):
    stats = analyze_column(dfs[0][col])
    suggestions = suggest_transformation(stats)

    if not suggestions:
        print("\n  ℹ️ Tidak ada pola khusus terdeteksi")
        input("  Enter...")
        return dfs

    print(f"\n  ⚠️ Terdeteksi: {suggestions}")
    print("\n  Preview sebelum:")
    show_sample(dfs, col, show=True)

    print("\n  [Y] Apply otomatis")
    print("  [N] Skip")
    pilih = input("  Pilih: ").strip().lower()

    if pilih == "y":
        for s in suggestions:
            action = auto_map.get(s)
            if action and action != "eval":
                dfs = apply_transformation(dfs, col, action)

        print("\n  Preview sesudah:")
        show_sample(dfs, col, show=True)

    input("\n  Enter untuk lanjut...")
    return dfs


# ─────────────────────────────────────────
# CLEANING MANUAL (MENU)
# ─────────────────────────────────────────
def _cleaning_manual(dfs, col, snapshot=None):
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        box("CLEANING")
        show_sample(dfs, col, show=True)

        print("\n  [1] Tambah rules")
        if snapshot is not None:
            print("  [2] Undo semua")
        print("  [0] Selesai")

        pilih = input("\n  Pilih: ").strip()

        if pilih == "1":
            rules = input_rules_basic()
            if rules:
                dfs = apply_bulk_rules(dfs, col, rules)
                print("\n  Preview sesudah:")
                show_sample(dfs, col, show=True)
                input("  Enter...")

        elif pilih == "2" and snapshot is not None:
            dfs = [df.copy() for df in snapshot]
            print("  ✅ Data dikembalikan ke kondisi awal")
            input("  Enter...")

        elif pilih == "0":
            return dfs


# ─────────────────────────────────────────
# RESOLVE INKONSISTENSI (SIMPLE)
# ─────────────────────────────────────────
def _resolve_basic(dfs, key):
    issues = find_inconsistencies(dfs, key)

    if not issues:
        print("\n  ✅ Tidak ada inkonsistensi")
        input("  Enter...")
        return dfs

    total = len(issues)
    print(f"\n  ⚠️ {total} inkonsistensi ditemukan")

    for i, item in enumerate(issues, 1):
        os.system('cls' if os.name == 'nt' else 'clear')
        box(f"RESOLUSI [{i}/{total}]")
        print(f"\n  ⚠️ '{item['val']}' (File {item['file_idx']+1})\n")

        if item['context'] is not None:
            print("  Konteks:")
            for col in item['context'].index:
                print(f"    {col:<20} : {item['context'][col]}")
            print()

        for idx, c in enumerate(item['candidates'], 1):
            print(f"  [{idx}] {c}")

        print(f"  [{len(item['candidates'])+1}] Manual")
        print(f"  [{len(item['candidates'])+2}] Skip")
        print(f"  [0] Skip Semua")

        raw = input("\n  Pilih: ").strip().lower()

        if raw == "0":
            break

        try:
            choice = int(raw)
        except ValueError:
            continue

        if 1 <= choice <= len(item['candidates']):
            new_val = item['candidates'][choice - 1]
        elif choice == len(item['candidates']) + 1:
            new_val = input("  Manual: ").strip()
        elif choice == len(item['candidates']) + 2:
            continue
        else:
            continue

        dfs[item['file_idx']][key] = dfs[item['file_idx']][key].replace(item['val'], new_val)

    return dfs


# ─────────────────────────────────────────
# SAVE
# ─────────────────────────────────────────
def _save(dfs, metas):
    os.system('cls' if os.name == 'nt' else 'clear')
    box("SIMPAN OUTPUT")

    formats = ['csv', 'tsv', 'json', 'jsonl', 'xlsx', 'geojson']
    print("\n  Format output:")
    for i, f in enumerate(formats, 1):
        print(f"  [{i}] {f}")

    while True:
        try:
            pilih = int(input("  Pilih: "))
            if 1 <= pilih <= len(formats):
                fmt = formats[pilih - 1]
                break
            print("  ❌ Input tidak valid.")
        except ValueError:
            print("  ❌ Input tidak valid.")

    base_dir = Path(metas[0]['path']).parent
    name = input("  Nama file output: ").strip() or "output"
    path = str(base_dir / f"{name}.{fmt}")

    meta = next((m for m in metas if m.get('is_geojson')), None)

    if fmt == 'geojson' and not meta:
        print("\n  ⚠️ Tidak ada sumber GeoJSON.")
    else:
        save_result(dfs[0], path, fmt, meta)
        print(f"\n  📁 Disimpan di: {path}")

    box("SELESAI!")
    input("  Enter...")
    os.system('cls' if os.name == 'nt' else 'clear')


# ─────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────
def run_basic_mode():
    os.system('cls' if os.name == 'nt' else 'clear')
    box("BASIC MODE")

    dfs, metas = _input_files()
    if not dfs:
        return

    snapshot = [df.copy() for df in dfs]

    if len(dfs) == 1:
        # ===== SINGLE FILE =====
        cols = list(dfs[0].columns)
        print("\n  Pilih kolom:")
        for i, col in enumerate(cols, 1):
            print(f"  [{i}] {col}")

        while True:
            try:
                pilih = int(input("  Pilih: "))
                if 1 <= pilih <= len(cols):
                    col = cols[pilih - 1]
                    break
                print("  ❌ Input tidak valid.")
            except ValueError:
                print("  ❌ Input tidak valid.")

        dfs = _auto_detect(dfs, col)
        dfs = _cleaning_manual(dfs, col, snapshot=snapshot)

    else:
        # ===== MULTI FILE =====
        all_cols = []
        for df in dfs:
            all_cols.extend(df.columns)
        counts = Counter(all_cols)
        common = [col for col, count in counts.items() if count >= 2]

        if not common:
            print("\n  ❌ Tidak ada kolom sama — gunakan Power Mode untuk rename kolom")
            input("  Enter...")
            return

        print("\n  Pilih key:")
        for i, col in enumerate(common, 1):
            print(f"  [{i}] {col}")

        while True:
            try:
                pilih = int(input("  Pilih: "))
                if 1 <= pilih <= len(common):
                    key = common[pilih - 1]
                    break
                print("  ❌ Input tidak valid.")
            except ValueError:
                print("  ❌ Input tidak valid.")

        # Auto detect per file
        for i, df in enumerate(dfs):
            if key not in df.columns:
                continue
            print(f"\n  📄 File {i+1} — kolom '{key}'")
            dfs = _auto_detect([df] if i == 0 else dfs, key)

        # Cleaning manual
        dfs = _cleaning_manual(dfs, key, snapshot=snapshot)

        # Resolve
        dfs = _resolve_basic(dfs, key)

        # Merge
        if pd.api.types.is_string_dtype(dfs[0][key]):
            dfs = apply_title_case(dfs, key)
        result = merge_multiple(dfs, key)
        dfs = [result]

        box("HASIL MERGE")
        print(f"\n  ✅ {len(result)} baris | {len(result.columns)} kolom")
        input("  Enter...")

    _save(dfs, metas)
