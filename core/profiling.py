import re
import pandas as pd

# ─────────────────────────────────────────
# ANALYZE
# ─────────────────────────────────────────
def analyze_column(series):
    s = series.dropna().astype(str).str.strip()
    total = len(s)

    if total == 0:
        return {}

    return {
        'sample': s.head(10).tolist(),
        'total': total,
        'digit_only_ratio': s.str.match(r'^\d+$').mean(),
        'has_separator_ratio': s.str.contains(r'[.\-/ ]').mean(),
        'numeric_like_ratio': s.str.match(r'^[\d\.\-/ ]+$').mean(),
        'has_whitespace_ratio': s.str.contains(r'^\s|\s$').mean(),
        'mixed_case_ratio': (
            s.str.contains(r'[a-z]').mean() + s.str.contains(r'[A-Z]').mean()
        ) / 2,
        'unique_ratio': s.nunique() / total,
    }

# ─────────────────────────────────────────
# SUGGEST
# ─────────────────────────────────────────
def suggest_transformation(stats):
    if not stats:
        return []

    suggestions = []

    if stats['numeric_like_ratio'] > 0.8 and stats['has_separator_ratio'] > 0:
        suggestions.append('mixed_numeric_format')

    if stats['has_whitespace_ratio'] > 0:
        suggestions.append('whitespace_issue')

    if 0 < stats['mixed_case_ratio'] < 1:
        suggestions.append('case_inconsistent')

    return suggestions

# ─────────────────────────────────────────
# SAFE EVAL
# ─────────────────────────────────────────
def safe_eval_transform(df, col, expr):
    try:
        preview = eval(expr, {
            "df": df.copy(),
            "col": col,
            "pd": pd,
            "re": re,
            "s": df[col].astype(str),
            "apply": lambda func: df.apply(func, axis=1)
        })

        if not isinstance(preview, pd.Series):
            print("  ❌ Expression harus return pd.Series")
            return df[col]

        print("\n  Preview hasil (5 baris):")
        print(f"  Sebelum : {df[col].head(5).tolist()}")
        print(f"  Sesudah : {preview.head(5).tolist()}")

        konfirm = input("\n  Apply ke semua data? [y/n]: ").strip().lower()
        if konfirm == 'y':
            return preview
        return df[col]

    except SyntaxError as e:
        print(f"  ❌ Syntax error: {e}")
        return df[col]
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return df[col]

# ─────────────────────────────────────────
# APPLY
# ─────────────────────────────────────────
def apply_transformation(dfs, col, choice, expr=None):
    result = []

    for df in dfs:
        df = df.copy()

        if col not in df.columns:
            result.append(df)
            continue

        if choice == "remove_nondigit":
            df[col] = df[col].astype(str).str.replace(r'\D', '', regex=True)

        elif choice == "remove_separator":
            chars = expr or r'[.\-/ ]'
            df[col] = df[col].astype(str).str.replace(chars, '', regex=True)

        elif choice == "custom_regex":
            if expr and '|||' in expr:
                pattern, repl = expr.split('|||', 1)
                df[col] = df[col].astype(str).str.replace(pattern, repl, regex=True)

        elif choice == "strip_whitespace":
            df[col] = df[col].astype(str).str.strip()

        elif choice == "eval":
            if expr:
                df[col] = safe_eval_transform(df, col, expr)

        result.append(df)

    return result

def compare_and_suggest(stats_acuan, stats_target):
    suggestions = []

    # ── NUMERIK ──
    if stats_acuan['digit_only_ratio'] > 0.9 and stats_target['has_separator_ratio'] > 0.1:
        suggestions.append({
            'issue': 'Acuan digit only, target ada separator',
            'suggestion': 'mixed_numeric_format'
        })
    elif stats_acuan['has_separator_ratio'] > 0.1 and stats_target['digit_only_ratio'] > 0.9:
        suggestions.append({
            'issue': 'Acuan ada separator, target digit only',
            'suggestion': 'mixed_numeric_format'
        })

    # ── WHITESPACE ──
    if stats_target['has_whitespace_ratio'] > 0:
        suggestions.append({
            'issue': f"Target ada whitespace ({stats_target['has_whitespace_ratio']*100:.1f}%)",
            'suggestion': 'strip_whitespace'
        })

    # ── CASE ──
    if stats_target['mixed_case_ratio'] > 0 and stats_acuan['mixed_case_ratio'] == 0:
        suggestions.append({
            'issue': 'Case tidak konsisten di target',
            'suggestion': 'case_inconsistent'
        })

    # ── PANJANG KARAKTER ──
    acuan_len = sum(len(v) for v in stats_acuan['sample']) / max(len(stats_acuan['sample']), 1)
    target_len = sum(len(v) for v in stats_target['sample']) / max(len(stats_target['sample']), 1)
    if abs(acuan_len - target_len) > 1.5:
        suggestions.append({
            'issue': f"Panjang karakter beda — acuan ~{acuan_len:.1f}, target ~{target_len:.1f}",
            'suggestion': 'length_mismatch'
        })

    # ── TIPE DATA BEDA ──
    acuan_numeric = stats_acuan['numeric_like_ratio'] > 0.8
    target_numeric = stats_target['numeric_like_ratio'] > 0.8
    if acuan_numeric != target_numeric:
        suggestions.append({
            'issue': 'Tipe data berbeda — satu numerik, satu alfabet/campuran',
            'suggestion': 'type_mismatch'
        })

    # ── UNIQUE RATIO BEDA JAUH ──
    if abs(stats_acuan['unique_ratio'] - stats_target['unique_ratio']) > 0.3:
        suggestions.append({
            'issue': f"Keunikan nilai beda jauh — acuan {stats_acuan['unique_ratio']:.1%}, target {stats_target['unique_ratio']:.1%}",
            'suggestion': 'cardinality_mismatch'
        })

    return suggestions