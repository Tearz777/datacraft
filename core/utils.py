def show_sample(dfs, col, show=True):
    if not show:
        return

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