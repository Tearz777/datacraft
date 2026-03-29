# DataCraft

DataCraft adalah CLI tool berbasis Python untuk **EDA (Exploratory Data Analysis)** — fokus pada data cleaning, normalisasi, dan merge multi-file secara interaktif.

---

## Instalasi

Pastikan Python 3.10+ sudah terinstall, lalu install dependencies:

```bash
pip install pandas openpyxl pyarrow
```

> `pyarrow` hanya diperlukan jika ingin menggunakan format output Parquet.

---

## Fitur

- **Load multi-format:** CSV, JSON, GeoJSON, Excel (XLSX, XLS), TSV, JSONL, Parquet
- **2 mode:** Power User (advanced) dan Basic (coming soon)
- **Auto detect pattern:** deteksi inkonsistensi format antar file secara otomatis
- **Data cleaning interaktif:**
  - Exact match, contains, replace sebagian, regex pattern
  - Preview head & tail sebelum dan sesudah cleaning
  - Undo semua perubahan ke kondisi awal
- **Rename kolom:** referensi antar file atau bulk rename manual
- **Resolusi inkonsistensi:**
  - Deteksi nilai tidak cocok antar file
  - Kandidat berdasarkan kesamaan kolom lain + kedekatan nilai numerik
  - Auto ganti, manual, skip, atau skip semua
- **Pre-merge & post-merge cleaning loop**
- **Merge data:** outer join multi-file, auto-merge kolom identik
- **Tab autocomplete path** di terminal (Linux/Termux)
- **Output:** CSV, TSV, JSON, JSONL, XLSX, GeoJSON, Parquet

---

## Cara Pakai

```bash
python dc_v2.py
```

Lalu ikuti langkah interaktif:
1. Pilih mode (Power User / Basic)
2. Masukkan file (1 atau lebih)
3. Rename kolom jika perlu
4. Auto detect pattern & transformasi
5. Pre-merge cleaning + resolve inkonsistensi
6. Merge
7. Post-merge cleaning
8. Simpan hasil

---

## Struktur Project

```
datacraft/
├── dc_v2.py        ← entry point + UI logic
└── core/
    ├── io.py       ← read/save file
    ├── cleaning.py ← bulk rules, find_inconsistencies
    ├── merge.py    ← find_common_columns, merge_multiple
    ├── profiling.py← analyze_column, compare_and_suggest
    └── utils.py    ← show_sample
```

---

## Use Case

- Menggabungkan data dari beberapa sumber berbeda format
- Membersihkan data yang inkonsisten sebelum analisis
- Normalisasi format kolom (kode wilayah, nama, dll)
- Alternatif ringan dari cleaning manual di Excel

---

## Batasan

- Dirancang untuk dataset kecil–menengah (ratusan hingga puluhan ribu baris)
- Basic mode belum diimplementasi
- Undo hanya tersedia untuk undo all (belum per-step)
- Tab autocomplete hanya works di Linux/Termux

---

## Status

> ⚠️ v2.0 — Work in Progress. Masih ada bug yang diketahui.
> Kontribusi dan feedback welcome.

---

## Roadmap

- [ ] Basic mode
- [ ] Feature engineering (kalkulasi, gabung kolom)
- [ ] Statistik dasar & missing values detection
- [ ] Visualisasi CLI
- [ ] Config file per project
- [ ] v2.5: Refactor — `dc.py` sebagai entry point murni, logic ke `core/modes/`
- [ ] v3.0: Web interface

---

## Tujuan

DataCraft dibuat sebagai:
- Tool praktis untuk workflow EDA pribadi
- Alternatif ringan dari cleaning manual di Excel
- Stepping stone menuju Web ERP

---

## Preview

**Main menu:**



![Main Menu](screenshot_main.jpg)



**Exit:**



![Exit](screenshot_exit.jpg)

## Lisensi

MIT License — bebas dipakai dan dimodifikasi.