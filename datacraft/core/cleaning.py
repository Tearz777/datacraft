import pandas as pd
import difflib

def apply_bulk_rules(dfs, col, rules):
    if not rules:
        return dfs

    result = []

    for i, df in enumerate(dfs, 1):
        df = df.copy()
        if col not in df.columns:
            print(f"  ⚠️ File {i}: kolom '{col}' tidak ditemukan")
            result.append(df)
            continue

        df[col] = df[col].astype(str)

        for rule in rules:
            mode = rule['mode']
            cari = rule['cari']
            ganti = rule['ganti']

            if mode == 'exact':
                mask = df[col].str.strip().str.upper() == cari.upper()
                df.loc[mask, col] = ganti

            elif mode == 'contains':
                mask = df[col].str.contains(cari, case=False, na=False)
                df.loc[mask, col] = ganti

            elif mode == 'replace':
                df[col] = df[col].str.replace(cari, ganti, regex=False)

            elif mode == 'pattern':
                df[col] = df[col].str.replace(cari, ganti, regex=True)

        df[col] = df[col].str.strip()
        result.append(df)

    return result

def find_inconsistencies(dfs, key):
    base_df = dfs[0]
    base_vals = set(base_df[key].dropna().unique())

    # Kolom pembanding — nama sama selain key
    common_cols = [col for col in base_df.columns
               if all(col in df.columns for df in dfs[1:]) and col != key]

    issues = []

    for i, df in enumerate(dfs[1:], 1):
        not_match = df[~df[key].isin(base_vals)].copy()

        if not_match.empty:
            continue

        for val in not_match[key].dropna().unique():
            target_row = not_match[not_match[key] == val].iloc[0]
            candidates = []

            if common_cols:
                # Buat filter berdasarkan kesamaan kolom pembanding
                mask = pd.Series([True] * len(base_df), index=base_df.index)
                for col in common_cols:
                    t_val = str(target_row[col]).strip().upper()
                    mask &= base_df[col].astype(str).str.strip().str.upper() == t_val

                matched = base_df[mask][key].tolist()
                candidates = matched[:3]

            # Fallback numerik
            if not candidates:
                try:
                    val_num = float(val)
                    base_nums = [(b, abs(float(b) - val_num)) for b in base_vals
                                if _is_float(b)]
                    base_nums.sort(key=lambda x: x[1])
                    candidates = [b[0] for b in base_nums[:3]]
                except ValueError:
                    candidates = difflib.get_close_matches(
                        val, base_vals, n=3, cutoff=0.6)

            issues.append({
                'val': val,
                'file_idx': i,
                'candidates': candidates,
                'context': target_row,
                'common_cols': common_cols
            })

    return issues

def _is_float(val):
    try:
        float(val)
        return True
    except:
        return False

def apply_title_case(dfs, key):
    return [df.assign(**{key: df[key].str.title()}) for df in dfs]