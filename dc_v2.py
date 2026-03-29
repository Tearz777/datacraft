import pandas as pd
import os
import sys
import readline
import glob
import shutil
from pathlib import Path
from core.io import read_file, save_result
from core.cleaning import apply_bulk_rules, find_inconsistencies, apply_title_case
from core.merge import find_common_columns,merge_multiple
from core.profiling import analyze_column, suggest_transformation, apply_transformation, compare_and_suggest
from core.utils import show_sample

auto_map = {
        "mixed_numeric_format": "remove_separator",
        "whitespace_issue": "strip_whitespace",
        "case_inconsistent": "eval",
    }

lebar = shutil.get_terminal_size().columns

def box(title):
    import unicodedata
    vis = sum(2 if unicodedata.east_asian_width(c) in ('W','F') else 1 for c in title)
    pad_total = lebar - 2 - vis
    pad_left = pad_total // 2
    pad_right = pad_total - pad_left
    print("╔" + "═" * (lebar-2) + "╗")
    print("║" + " " * pad_left + title + " " * pad_right + "║")
    print("╚" + "═" * (lebar-2) + "╝")

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

        mode_map = {
            1: 'exact',
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
            print("  [3] Undo semua")
        print("  [2] Lanjut")

        pilih = input("  Pilih: ").strip()

        if pilih == "1":
            if mode == "power":
              rules = input_rules()
            else:
              rules = input_rules_basic()

            if rules:
                dfs = apply_bulk_rules(dfs, col, rules)
                input("Press Enter To Continue")

                os.system('cls' if os.name == 'nt' else 'clear')
                box("PREVIEW SETELAH RULES DIAPPLY")                
                show_sample(dfs, col, show=show)

        elif pilih == "3" and snapshot is not None:
            dfs = [df.copy() for df in snapshot]
            print("  ✅ Data dikembalikan ke kondisi awal")
            input("  Enter...")

        elif pilih == "2":
          
          return dfs

def rename_columns_session(dfs: list, metas: list) -> list:
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        box("RESOLVE KOLOM")
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
    os.system('cls' if os.name == 'nt' else 'clear')
    box("RENAME BY REFERENCE")
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
    os.system('cls' if os.name == 'nt' else 'clear')
    box("BULK RENAME MANUAL")
    
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

def resolve_inconsistencies(dfs, key):
    issues = find_inconsistencies(dfs, key)

    if not issues:
        print("✅ Tidak ada inkonsistensi.")
        return dfs

    dfs = [df.copy() for df in dfs]
    skip_all = False
    total=len(issues)

    for i, item in enumerate(issues, 1):
        if skip_all:
            break

        os.system('cls' if os.name == 'nt' else 'clear')
        box(f"RESOLUSI [{i}/{total}]")
        print(f"\n  ⚠️  Nilai tidak match: '{item['val']}' (File {item['file_idx']+1})\n")

        # Konteks vertikal
        if item['context'] is not None:
            print("  Konteks:")
            for col in item['context'].index:
                print(f"    {col:<20} : {item['context'][col]}")
            print()

        # Kandidat + info kolom pembanding
        for idx, c in enumerate(item['candidates'], 1):
            match = dfs[0][dfs[0][key] == c]
            print(f"  [{idx}] {c}")
            if not match.empty:
                for col in item['common_cols']:
                    if col in match.columns:
                        print(f"       {col} : {match.iloc[0][col]}")

        print(f"  [{len(item['candidates'])+1}] Manual")
        print(f"  [{len(item['candidates'])+2}] Skip")
        print(f"  [A] Ganti semua berdasarkan kolom pembanding")
        print(f"  [0] Skip Semua")

        raw = input("\n  Pilih: ").strip().lower()

        if raw == "0":
            skip_all = True
            break

        elif raw == "a" and item['common_cols']:
            # Auto ganti semua yang punya nilai kolom pembanding sama
            if item['candidates']:
                new_val = item['candidates'][0]
                target_row = item['context']
                mask = pd.Series([True] * len(dfs[item['file_idx']]),
                                index=dfs[item['file_idx']].index)
                for col in item['common_cols']:
                    t_val = str(target_row[col]).strip().upper()
                    mask &= dfs[item['file_idx']][col].astype(str).str.strip().str.upper() == t_val
                dfs[item['file_idx']].loc[mask, key] = new_val
                total -=1
                print(f"  ✅ Auto ganti → '{new_val}'")
                input("  Enter...")
            else:
                print("  ⚠️ Tidak ada kandidat.")
                input("  Enter...")
            continue

        try:
            choice = int(raw)
        except ValueError:
            continue

        if 1 <= choice <= len(item['candidates']):
            new_val = item['candidates'][choice-1]
        elif choice == len(item['candidates']) + 1:
            new_val = input("  Manual: ").strip()
        elif choice == len(item['candidates']) + 2:
            print("  ⏭️ Skip")
            continue
        else:
            continue

        dfs[item['file_idx']][key] = dfs[item['file_idx']][key].replace(item['val'], new_val)
        total -=1

    os.system('cls' if os.name == 'nt' else 'clear')
    box("✅ RESOLUSI SELESAI!")
    return dfs

def run_power_mode():
    os.system('cls' if os.name == 'nt' else 'clear')
    box("POWER MODE ⚡ ")
    dfs, metas = [], []

    # ───────── INPUT FILE ─────────
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
            if df.empty:
                print(f"  ⚠️ {fp} kosong (0 baris)")
            elif df.shape[1] == 0:
                print(f"  ⚠️ {fp} tidak punya kolom")
            dfs.append(df)
            metas.append(meta)
            print(f"  ✅ {fp} → {len(df)} baris | kolom: {list(df.columns)}")
        except Exception as e:
            print(f"  ❌ {e}")
            continue

        if len(dfs) >= 2:
            if input("\n  Tambah file lagi? [y/n]: ").strip().lower() != 'y':
                break

    # Simpan snapshot awal
    snapshot_original = [df.copy() for df in dfs]

    

    # ───────── SINGLE FILE MODE ─────────
    if len(dfs) == 1:
        is_merge=False
        box("SINGLE FILE MODE")
        cols = list(dfs[0].columns)
        print("\n  Pilih kolom kunci:")
        for i, col in enumerate(cols, 1):
            print(f"  [{i}] {col}")

        while True:
            try:
                pilih = int(input("  Pilih: "))
                if 1 <= pilih <= len(cols):
                    key = cols[pilih - 1]
                    break
            except ValueError:
                pass
            print("  ❌ Input tidak valid.")

        # Auto detect — single file
        while True:
            os.system('cls' if os.name == 'nt' else 'clear')
            box("AUTO DETECT PATTERN")
            
            cols = list(dfs[0].columns)
            print("\n  Pilih kolom:")
            for i, col in enumerate(cols, 1):
                print(f"  [{i}] {col}")
            print("  [0] Selesai")

            pilih_col = input("  Pilih: ").strip()
            if pilih_col in ("", "0"):
                break

            try:
                acuan_col = cols[int(pilih_col) - 1]
            except:
                print("  ❌ Input tidak valid.")
                input("  Enter...")
                continue

            stats = analyze_column(dfs[0][acuan_col])
            suggestions = suggest_transformation(stats)

            print("\n  Sample:")
            for val in stats.get('sample', [])[:5]:
                print(f"    {val}")

            if not suggestions:
                print("\n  ℹ️ Tidak ada pola khusus terdeteksi")
                input("  Enter...")
                continue

            print(f"\n  ⚠️ Terdeteksi: {suggestions}")
            print("\n  [A] Apply otomatis")
            print("  [M] Manual")
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
                    print("    s      → series kolom aktif (paling sering dipakai)")
                    print("    df     → DataFrame aktif")
                    print("    col    → nama kolom aktif")
                    print("    apply  → apply(lambda row: ...) per baris")
                    print("    pd, re → pandas, regex module")
                    expr = input("  Expr: ").strip()
                    dfs = apply_transformation(dfs, acuan_col, "eval", expr=expr)
                elif pilih2 == "5":
                    dfs = apply_transformation(dfs, acuan_col, "strip_whitespace")
                input("  Enter...")

        # Cleaning
        box("CLEANING")
        dfs = cleaning_session(dfs, key, mode="power", show=True, snapshot=snapshot_original)

    # ───────── MULTI FILE MODE ─────────
    else:
        is_merge=True
        # Rename kolom
        dfs = rename_columns_session(dfs, metas)

        # Pilih key dari common
        common = find_common_columns(dfs)
        if not common:
            print("\n  ❌ Tidak ada kolom yang sama.")
            return

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
            print("  ❌ Input tidak valid.")
        snapshot_premerge = [df.copy() for df in dfs]

        # Auto detect — multi file
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
            except ValueError:
                print("  ❌ Input tidak valid.")
                input("  Enter...")
                continue

            cols = list(dfs[acuan_idx].columns)
            print(f"\n  Pilih kolom dari File {acuan_idx+1}:")
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

            stats_acuan = analyze_column(dfs[acuan_idx][acuan_col])

            print("\n  Sample acuan:")
            for val in stats_acuan.get('sample', [])[:5]:
                print(f"    {val}")

            found_any = False

            for i, df in enumerate(dfs):
                if i == acuan_idx:
                    continue
                if acuan_col not in df.columns:
                    print(f"\n  ⚠️ File {i+1} tidak punya kolom '{acuan_col}' — skip")
                    continue

                stats_target = analyze_column(df[acuan_col])
                suggestions = compare_and_suggest(stats_acuan, stats_target)

                if not suggestions:
                    print(f"\n  ✅ File {i+1} — tidak ada perbedaan pola")
                    continue

                found_any = True
                print(f"\n  ⚠️ File {i+1} — ditemukan {len(suggestions)} issue:")
                for s in suggestions:
                    print(f"    - {s['issue']} → {s['suggestion']}")

                print("\n  [A] Apply otomatis")
                print("  [M] Manual")
                print("  [0] Skip")

                pilih = input("  Pilih: ").strip().lower()

                if pilih == "a":
                    for s in suggestions:
                        action = auto_map.get(s['suggestion'])
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
                      print("    s      → series kolom aktif (paling sering dipakai)")
                      print("    df     → DataFrame aktif")
                      print("    col    → nama kolom aktif")
                      print("    apply  → apply(lambda row: ...) per baris")
                      print("    pd, re → pandas, regex module")
                      expr = input("  Expr: ").strip()
                      dfs = apply_transformation(dfs, acuan_col, "eval", expr=expr)
                    elif pilih2 == "5":
                      dfs = apply_transformation(dfs, acuan_col, "strip_whitespace")
                    input("  Enter...")

            if not found_any:
                print("\n  ℹ️ Semua file konsisten dengan acuan")
                input("  Enter...")

        # Pre-merge cleaning + resolve loop
        while True:
            issues = find_inconsistencies(dfs, key)

            if not issues:
                print("\n  ✅ Tidak ada inkonsistensi!")
                input("  Enter untuk lanjut...")
                break

            os.system('cls' if os.name == 'nt' else 'clear')
            box("PRE-MERGE CLEANING")
            
            print(f"\n  ⚠️ Masih ada {len(issues)} inkonsistensi di kolom '{key}'")
            print("\n  Sample yang tidak match:")

            for item in issues[:5]:
                print(f"    '{item['val']}' (File {item['file_idx']+1})")

            if len(issues) > 5:
                print(f"    ... dan {len(issues)-5} lainnya")

            print("\n  [1] Cleaning")
            print("  [2] Resolve langsung")
            print("  [3] Undo semua")
            print("  [4] Lanjut merge anyway")
            print("  [5] Ganti key")

            pilih = input("\n  Pilih: ").strip()

            if pilih == "1":
                dfs = cleaning_session(dfs, key, mode="power", show=True, snapshot=snapshot_premerge)
            elif pilih == "2":
                dfs = resolve_inconsistencies(dfs, key)
            elif pilih == "3":
                dfs = [df.copy() for df in snapshot_premerge]
                print("  ✅ Data dikembalikan ke kondisi awal")
                input("  Enter...")
            elif pilih == "4":
                break
            elif pilih == "5":
                common = find_common_columns(dfs)
                print("\n  Pilih key baru:")
                for i, col in enumerate(common, 1):
                    print(f"  [{i}] {col}")
                while True:
                    try:
                        pilih_key = int(input("  Pilih: "))
                        if 1 <= pilih_key <= len(common):
                            key = common[pilih_key - 1]
                            snapshot_premerge = [df.copy() for df in dfs]
                            print(f"  ✅ Key diganti ke '{key}'")
                            input("  Enter...")
                            break
                    except ValueError:
                        pass
                    print("  ❌ Input tidak valid.")
                    
        # Normalisasi + merge
        dfs = apply_title_case(dfs, key)
        result = merge_multiple(dfs, key)
        os.system('cls' if os.name == 'nt' else 'clear')
        box("HASIL MERGE")
        print(f"\n  ✅ {len(result)} baris | {len(result.columns)} kolom")
        print(f"  Kolom: {list(result.columns)}")
        dfs = [result]

    # ───────── POST-MERGE CLEANING ─────────
    if is_merge:
        os.system('cls' if os.name == 'nt' else 'clear')
        box("POST-MERGE CLEANING")
        result_cols = list(dfs[0].columns)

        while True:
            print("\n  Pilih kolom:")
            for i, col in enumerate(result_cols, 1):
                print(f"  [{i}] {col}")
            print("  [0] Skip")

            try:
                pilih = int(input("  Pilih: "))
                if pilih == 0:
                    break
                elif 1 <= pilih <= len(result_cols):
                    col_target = result_cols[pilih - 1]
                    dfs[0] = cleaning_session([dfs[0]], col_target, mode="power", show=True, snapshot=[dfs[0].copy()])[0]
                    input("  Selesai cleaning. Enter untuk lanjut...")
                else:
                    print("  ❌ Input tidak valid.")
            except ValueError:
                print("  ❌ Input tidak valid.")

    # ───────── SAVE ─────────
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
        except ValueError:
            pass
        print("  ❌ Input tidak valid.")

    path = input("  Lokasi output (full path + nama file): ").strip()
    meta = next((m for m in metas if m.get('is_geojson')), None)

    if fmt == 'geojson' and not meta:
        print("\n  ⚠️ Tidak ada sumber GeoJSON.")
    else:
        save_result(dfs[0], path, fmt, meta)

    os.system('cls' if os.name == 'nt' else 'clear')
    box("SELESAI! 🎉")

def run_basic_mode():
    print("Fitur Masih Dikembangkan")
    input("Continue...")

def path_completer(text, state):
    expanded = os.path.expanduser(text)
    matches = glob.glob(expanded + '*')

    # Handle spasi di nama file — escape dengan backslash
    matches = [
        m.replace(os.path.expanduser('~'), '~').replace(' ', '\\ ')
        for m in matches
    ]

    return matches[state] if state < len(matches) else None

if __name__ == "__main__" :
    readline.set_completer(path_completer)
    readline.set_completer_delims('\t\n')
    readline.parse_and_bind('tab: complete')
    try:
        os.system('cls' if os.name == 'nt' else 'clear')
        box("DataCraft v2.0")


        while True:
            print("\nPilih mode:")
            print("[1] Power User")
            print("[2] Basic")
            print("[0] Keluar")

            mode = input("Pilih: ").strip()

            if mode == "1":
                run_power_mode()
            elif mode == "2":
                run_basic_mode()
            elif mode == "0":
                os.system("cls" if os.name== "nt" else "clear")
                box("👋 Sampai jumpa!")
                break
            else:
                print("❌ Pilihan tidak valid")
    except KeyboardInterrupt:
        os.system("cls" if os.name== "nt" else "clear")
        box("Aplikasi ditutup, semoga sukses 👋👋")
        box("Created By : Thery Vissabil Lillah")