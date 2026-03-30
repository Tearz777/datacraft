import os
from pathlib import Path

from core import (
    read_file, save_result,
    apply_bulk_rules, find_inconsistencies, apply_title_case,
    find_common_columns, merge_multiple,
    analyze_column, suggest_transformation, apply_transformation, compare_and_suggest,
    show_sample
)
import pandas as pd
from core.ui import box, auto_map
from pathlib import Path

def _auto_clean_with_preview(dfs, col):
    stats = analyze_column(dfs[0][col])
    suggestions = suggest_transformation(stats)

    if not suggestions:
        return dfs

    print(f"\n  ⚠️ Terdeteksi: {suggestions}")
    print("\n  Preview sebelum:")
    show_sample(dfs, col, show=True)

    for s in suggestions:
        action = auto_map.get(s)
        if action and action != "eval":  # block eval
            dfs = apply_transformation(dfs, col, action)

    print("\n  Preview sesudah:")
    show_sample(dfs, col, show=True)

    input("\n  Enter untuk lanjut...")
    return dfs

def _auto_clean_multi(dfs, key):
    for i, df in enumerate(dfs):
        if key not in df.columns:
            continue

        stats = analyze_column(df[key])
        suggestions = suggest_transformation(stats)

        if not suggestions:
            continue

        print(f"\n  ⚠️ File {i+1} → {suggestions}")
        print("\n  Sebelum:")
        show_sample([df], key, show=True)

        for s in suggestions:
            action = auto_map.get(s)
            if action and action != "eval":
                dfs = apply_transformation(dfs, key, action)

        print("\n  Sesudah:")
        show_sample([dfs[i]], key, show=True)

        input("\n  Enter...")
    print("\n  ℹ️ Tidak ada perubahan (data sudah bersih)")
    input("Enter...")
    return dfs

def run_basic_mode():
    import os
    from pathlib import Path
    import pandas as pd

    os.system('cls' if os.name == 'nt' else 'clear')
    box("BASIC MODE")

    # INPUT FILE
    from core.modes.power import _input_files
    dfs, metas = _input_files()
    if not dfs:
        return

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

        dfs = _auto_clean_with_preview(dfs, col)

    else:
        # ===== MULTI FILE =====
        from collections import Counter

        all_cols = []
        for df in dfs:
            all_cols.extend(df.columns)

        counts = Counter(all_cols)
        common = [col for col, count in counts.items() if count >= 2]

        if not common:
            print("❌ Tidak ada kolom sama")
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

        dfs = _auto_clean_multi(dfs, key)

        # ===== RESOLVE =====
        issues = find_inconsistencies(dfs, key)

        if not issues:
            print("\n  ✅ Tidak ada inkonsistensi")
            input("Enter...")
        else:
            for item in issues:
                print(f"\n  ⚠️ '{item['val']}' tidak konsisten")

                if item['candidates']:
                    for i, c in enumerate(item['candidates'], 1):
                        print(f"  [{i}] {c}")

                print("  [M] Manual")
                print("  [S] Skip")

                pilih = input("  Pilih: ").strip().lower()

                if pilih == "m":
                    new_val = input("  Manual: ").strip()

                elif pilih.isdigit() and item['candidates']:
                    idx = int(pilih)
                    if 1 <= idx <= len(item['candidates']):
                        new_val = item['candidates'][idx - 1]
                    else:
                        continue
                else:
                    continue

                dfs[item['file_idx']][key] = (
                    dfs[item['file_idx']][key]
                    .replace(item['val'], new_val)
                )

        # ===== PRE-MERGE =====
        if pd.api.types.is_string_dtype(dfs[0][key]):
            dfs = apply_title_case(dfs, key)

        result = merge_multiple(dfs, key)
        dfs = [result]

    # ===== SAVE =====
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

    name = input("  Nama file output: ").strip()
    if not name:
        name = "output"

    path = str(base_dir / f"{name}.{fmt}")

    meta = next((m for m in metas if m.get('is_geojson')), None)

    if fmt == 'geojson' and not meta:
        print("\n  ⚠️ Tidak ada sumber GeoJSON.")
    else:
        save_result(dfs[0], path, fmt, meta)

    print(f"\n  📁 Disimpan di: {path}")
    box("PROGRAM SELESAI")
    input("Enter...")
    os.system('cls' if os.name == 'nt' else 'clear')