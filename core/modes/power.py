# core/modes/power.py

import os
import pandas as pd
from pathlib import Path

from core import (
    read_file, save_result,
    apply_bulk_rules, find_inconsistencies, apply_title_case,
    find_common_columns, merge_multiple,
    analyze_column, suggest_transformation, apply_transformation, compare_and_suggest,
    show_sample
)
from core.ui import box, auto_map

def input_rules():
    print("  Mode:")
    print("    exact     → sama persis")
    print("    contains  → mengandung teks")
    print("    replace   → replace sebagian")
    print("    pattern   → regex (transform berbasis pola)")
    raw = input("  Rules: ").strip()
    if not raw:
        return []

    rules = []
    for pair in raw.split(','):
        pair = pair.strip()
        if ':' in pair and '=' in pair:
            mode_part, rest = pair.split(':', 1)
            cari, ganti = rest.split('=', 1)
            rules.append({
                'mode': mode_part.strip().lower(),
                'cari': cari.strip(),
                'ganti': ganti.strip()
            })
    return rules

def input_rules_basic():
    rules = []
    while True:
        print("\n  Pilih mode:")
        print("  [1] Exact")
        print("  [2] Contains")
        print("  [3] Replace")
        print("  [4] Pattern")
        print("  [0] Selesai")

        try:
            pilih = int(input("  Pilih: "))
        except ValueError:
            print("  ❌ Input tidak valid")
            continue

        if pilih == 0:
            break

        mode_map = {1: 'exact', 
        2: 'contains', 
        3: 'replace', 
        4: 'pattern'
        }

        if pilih not in mode_map:
            print("  ❌ Pilihan tidak ada")
            continue

        cari = input("  Cari: ").strip()
        ganti = input("  Ganti: ").strip()

        rules.append({
            'mode': mode_map[pilih],
            'cari': cari,
            'ganti': ganti
        })

    return rules

def cleaning_session(dfs, col, mode="power", show=True, snapshot=None):
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        box("CLEANING SESSION")
        print()
        show_sample(dfs, col, show=show)

        print("\n  [1] Tambah rules (manual)")
        if snapshot is not None:
            print("  [2] Undo semua")
        print("  [0] Lanjut")

        pilih = input("  Pilih: ").strip()

        if pilih == "1":
            rules = input_rules() if mode == "power" else input_rules_basic()

            if rules:
                dfs = apply_bulk_rules(dfs, col, rules)
                input("Press Enter To Continue")

                os.system('cls' if os.name == 'nt' else 'clear')
                box("PREVIEW SETELAH RULES DIAPPLY")
                show_sample(dfs, col, show=show)

        elif pilih == "2" and snapshot is not None:
            dfs = [df.copy() for df in snapshot]
            print("  ✅ Data dikembalikan ke kondisi awal")
            input("  Enter...")

        elif pilih == "0":
            return dfs

def rename_columns_session(dfs: list, metas: list) -> list:
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        box("RESOLVE KOLOM")

        for i, df in enumerate(dfs, 1):
            print(f"\n  📄 File {i} — {Path(metas[i-1]['path']).name}")
            for j, col in enumerate(df.columns, 1):
                sample = df[col].dropna().iloc[0] if len(df) > 0 else '-'
                print(f"    [{j}] {col} → {sample}")
        print("\n  [1] Rename kolom berdasarkan file lain")
        print("  [2] Bulk rename manual")
        print("  [3] Selesai")

        pilih = input("\n  Pilih: ").strip()
        if pilih == "1":
          n = len(dfs)
          try:
            src = int(input("  File yang diubah: ")) - 1
            if not (0 <= src < n):
              raise ValueError
            if n == 2:
              # otomatis pilih file lain sebagai acuan
              ref = 1 - src
              print(f"  → File acuan otomatis: File {ref+1}")
            else:
              ref = int(input("  File acuan: ")) - 1
            if not (0 <= ref < n) or ref == src:
              raise ValueError
            dfs = _rename_by_reference(dfs, src, ref)
          except:
            print("  ❌ Input tidak valid")
            input("  Enter...")
        elif pilih == "2":
            dfs = _bulk_rename(dfs)
        elif pilih == "3":
            break
        from collections import Counter
        all_cols = []
        for df in dfs:
          all_cols.extend(df.columns)
        counts = Counter(all_cols)
        common = sorted([col for col, count in counts.items() if count >= 2])

        if common:
            print(f"\n  ✅ Kolom yang sama ditemukan: {common}")
            print("  [1] Lanjut")
            print("  [2] Rename lagi")
            if input("  Pilih: ").strip() == "1":
                break

    return dfs

def _rename_by_reference(dfs, source_idx, target_idx):
    os.system('cls' if os.name == 'nt' else 'clear')
    box("RENAME BY REFERENCE")

    source_cols = list(dfs[source_idx].columns)
    target_cols = list(dfs[target_idx].columns)

    print(f"\n  Target (File {target_idx+1}): {target_cols}")
    print(f"\n  Pilih kolom File {source_idx+1} yang mau direname:\n")

    for i, col in enumerate(source_cols, 1):
        sample = dfs[source_idx][col].dropna().iloc[0] if len(dfs[source_idx]) > 0 else '-'
        print(f"  [{i}] {col} → {sample}")

    print("  [0] Batal")

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

def _bulk_rename(dfs):
    os.system('cls' if os.name == 'nt' else 'clear')
    box("BULK RENAME MANUAL")

    for i, df in enumerate(dfs, 1):
        print(f"\n  File {i}: {list(df.columns)}")

    print("\n  Format: FILE:LAMA=BARU (pisah koma)")
    print("  Contoh: 1:NAMA_KAB/KOTA=WILAYAH")

    raw = input("\n  Rename: ").strip()
    if not raw:
        return dfs

    dfs = [df.copy() for df in dfs]

    for pair in raw.split(','):
        pair = pair.strip()

        if ':' not in pair or '=' not in pair:
            print(f"  ❌ Format salah: '{pair}'")
            continue

        try:
            file_part, col_part = pair.split(':', 1)
            old, new = col_part.split('=', 1)

            idx = int(file_part.strip()) - 1
            old = old.strip().upper()
            new = new.strip().upper()

            if old in dfs[idx].columns:
                dfs[idx].rename(columns={old: new}, inplace=True)
                print(f"  ✅ File {idx+1}: '{old}' → '{new}'")
            else:
                print(f"  ⚠️  File {idx+1}: '{old}' tidak ditemukan")

        except Exception:
            print(f"  ❌ Format salah: '{pair}'")

    input("\n  Enter untuk lanjut...")
    return dfs

def resolve_inconsistencies(dfs, key):
    issues = find_inconsistencies(dfs, key)

    if not issues:
        print("✅ Tidak ada inkonsistensi.")
        return dfs

    dfs = [df.copy() for df in dfs]
    total = len(issues)

    for i, item in enumerate(issues, 1):
        os.system('cls' if os.name == 'nt' else 'clear')
        box(f"RESOLUSI [{i}/{total}]")

        print(f"\n  ⚠️  Nilai tidak match: '{item['val']}' (File {item['file_idx']+1})\n")

        # Kandidat
        for idx, c in enumerate(item['candidates'], 1):
            print(f"  [{idx}] {c}")

        print(f"  [{len(item['candidates'])+1}] Manual")
        print(f"  [{len(item['candidates'])+2}] Skip")
        print(f"  [R] Kembali ke Auto Detect Pattern")

        raw = input("\n  Pilih: ").strip().lower()
        if raw == "r":
            return "back_to_detect"

        try:
            choice = int(raw)
        except:
            continue

        if 1 <= choice <= len(item['candidates']):
            new_val = item['candidates'][choice - 1]

        elif choice == len(item['candidates']) + 1:
            new_val = input("  Manual: ").strip()

        elif choice == len(item['candidates']) + 2:
            print("  ⏭️ Skip")
            continue

        else:
            continue

        dfs[item['file_idx']][key] = dfs[item['file_idx']][key].replace(item['val'], new_val)

    return dfs


# ===== NEW STRUCTURE (LEVEL 2 SPLIT) =====

def _input_files():
    dfs, metas = [], []

    while True:
        raw = input(f"\n  Masukkan file {len(dfs)+1}: ").strip()

        if not raw:
            if not dfs:
                print("  ❌ Minimal 1 file.")
                continue
            break

        fp = str(Path(raw.replace('\\ ', ' ')).expanduser())

        try:
            df, meta = read_file(fp)
            dfs.append(df)
            metas.append(meta)

            print(f"  ✅ {fp}")

            for col in df.columns:
                try:
                    sample = df[col].dropna().iloc[0]
                except:
                    sample = "-"
                print(f"     {col} → {sample}")

        except Exception as e:
            print(f"  ❌ {e}")
            continue

        if len(dfs) >= 2:
            if input("\n  Tambah file lagi? [y/n]: ").strip().lower() != 'y':
                break

    return dfs, metas

def _handle_single_file(dfs):
    key = dfs[0].columns[0]
    dfs = cleaning_session(dfs, key)
    return dfs

def _handle_multi_file(dfs, metas):
    dfs = rename_columns_session(dfs, metas)

    common = find_common_columns(dfs)

    if not common:
        print("\n  ❌ Tidak ada kolom yang sama.")
        return None

    # ===== PILIH KEY =====
    if len(common) == 1:
        key = common[0]
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
            except:
                pass
            print("  ❌ Input tidak valid.")

    # ===== AUTO DETECT =====
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        box("AUTO DETECT PATTERN")

        print("\n  Pilih file acuan:")
        for i, meta in enumerate(metas, 1):
            print(f"  [{i}] File {i} — {Path(meta['path']).name}")
        print("  [0] Selesai")

        pilih_file = input("  Pilih: ").strip()
        if pilih_file in ("", "0"):
            break

        try:
            acuan_idx = int(pilih_file) - 1
            if not (0 <= acuan_idx < len(dfs)):
                raise ValueError
        except:
            print("  ❌ Input tidak valid.")
            input("  Enter...")
            continue

        cols = list(dfs[acuan_idx].columns)

        print("\n  Pilih kolom:")
        for i, col in enumerate(cols, 1):
            print(f"  [{i}] {col}")
        print("  [0] Kembali")

        pilih_col = input("  Pilih: ").strip()
        if pilih_col in ("", "0"):
            continue

        try:
            acuan_col = cols[int(pilih_col) - 1]
        except:
            print("  ❌ Input tidak valid.")
            input("  Enter...")
            continue

        stats = analyze_column(dfs[acuan_idx][acuan_col])
        suggestions = suggest_transformation(stats)

        print("\n  Sample:")
        for val in stats.get('sample', [])[:5]:
            print(f"    {val}")

        if not suggestions:
            print("\n  ℹ️ Tidak ada pola")
            input("  Enter...")
            continue

        print(f"\n  ⚠️ Terdeteksi: {suggestions}")
        print("\n  [A] Apply otomatis")
        print("  [M] Apply Manual")
        print("  [0] Skip")

        pilih = input("  Pilih: ").strip().lower()

        if pilih == "a":
            for s in suggestions:
                action = auto_map.get(s)
                if action:
                    dfs = apply_transformation(dfs, acuan_col, action)

            print("  ✅ Done")
            input("  Enter...")

        elif pilih == "m":
            print("\n  [1] Hapus non-digit")
            print("  [2] Hapus separator")
            print("  [3] Regex replace")
            print("  [4] Eval")
            print("  [5] Strip whitespace")
            print("  [0] Skip")

            pilih2 = input("  Pilih: ").strip()

            if pilih2 == "1":
                dfs = apply_transformation(dfs, acuan_col, "remove_nondigit")

            elif pilih2 == "2":
                chars = input("  Karakter: ").strip()
                dfs = apply_transformation(dfs, acuan_col, "remove_separator", expr=chars)

            elif pilih2 == "3":
                p = input("  Pattern: ").strip()
                r = input("  Replace: ").strip()
                dfs = apply_transformation(dfs, acuan_col, "custom_regex", expr=f"{p}|||{r}")

            elif pilih2 == "4":
                print("  Variabel tersedia:")
                print("    s → series kolom aktif")
                print("    df → DataFrame aktif")
                print("    col → nama kolom")
                print("    apply → apply per baris")
                print("    pd, re → module")
                expr = input("  Expr: ").strip()
                dfs = apply_transformation(dfs, acuan_col, "eval", expr=expr)

            elif pilih2 == "5":
                dfs = apply_transformation(dfs, acuan_col, "strip_whitespace")

            input("  Enter...")

    # ===== RESOLVE =====
    result = resolve_inconsistencies(dfs, key)

    if result == "back_to_detect":
        return "back_to_detect"

    dfs = result

    # ===== MERGE =====
    import pandas as pd
    if pd.api.types.is_string_dtype(dfs[0][key]):
      dfs = apply_title_case(dfs, key)
    result = merge_multiple(dfs, key)

    return [result]

def run_power_mode():
    os.system('cls' if os.name == 'nt' else 'clear')
    box("POWER MODE ⚡ ")

    dfs, metas = _input_files()

    if not dfs:
        return

    snapshot_original = [df.copy() for df in dfs]

    if len(dfs) == 1:
        dfs = _handle_single_file(dfs)

    else:
        while True:
            result = _handle_multi_file(dfs, metas)

            if result == "back_to_detect":
                continue

            if result is None:
                return

            dfs = result
            break
          
    # ===== SAVE =====
    os.system('cls' if os.name == 'nt' else 'clear')
    box("SIMPAN OUTPUT")

    print("\n  Format output:")
    formats = ['csv', 'tsv', 'json', 'jsonl', 'xlsx', 'geojson', 'parquet']
    for i, f in enumerate(formats, 1):
      print(f"  [{i}] {f}")

    while True:
        try:
          pilih = int(input("  Pilih: "))
          if 1 <= pilih <= len(formats):
              fmt = formats[pilih - 1]
              break
        except :
              pass
        print("  ❌ Input tidak valid.")

    path = input("  Lokasi output (tanpa ekstensi): ").strip()
    if not path:
      path = f"output.{fmt}"
    else:
      path = path.rstrip('.')  # jaga-jaga
      path = f"{path}.{fmt}"
    meta = next((m for m in metas if m.get('is_geojson')), None)
    if fmt == 'geojson' and not meta:
      print("\n  ⚠️ Tidak ada sumber GeoJSON.")
    else:
      save_result(dfs[0], path, fmt, meta)
    box("Selesai")
    input("Enter...")
    os.system("cls"if os.name=="nt" else "clear")