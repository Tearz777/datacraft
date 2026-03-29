import pandas as pd


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