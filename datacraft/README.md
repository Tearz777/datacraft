# DataCraft

DataCraft adalah CLI tool berbasis Python untuk membantu proses **data cleaning dan merging secara interaktif** pada dataset kecil hingga menengah.

Dirancang untuk workflow praktis: membaca file, membersihkan data, menyamakan kolom, mengatasi inkonsistensi, lalu menggabungkan hasilnya.

---

## Instalasi

Pastikan Python 3.10+ sudah terinstall, lalu install dependencies:

pip install pandas openpyxl

Tidak perlu install package tambahan lain.

---

## Fitur

- Load multi-format:
  - CSV
  - JSON / GeoJSON
  - Excel (XLSX, XLS)

- Data cleaning:
  - Bulk replace (exact match)
  - Preview data (head & tail)

- Resolusi inkonsistensi:
  - Deteksi nilai yang tidak cocok antar file
  - Rekomendasi berdasarkan kemiripan (difflib)

- Rename kolom:
  - Referensi antar file
  - Bulk rename manual

- Merge data:
  - Outer join multi-file
  - Auto-merge kolom identik

- Output:
  - CSV
  - JSON
  - Excel
  - GeoJSON (preserve structure)

---

## Cara Pakai

Jalankan:

```
python dc.py
```

Lalu ikuti langkah interaktif:
1. Masukkan file (satu atau lebih)
2. Pilih kolom
3. Cleaning (opsional)
4. Resolve inkonsistensi
5. Merge
6. Simpan hasil

---

## Use Case

Tool ini cocok untuk:
- Menggabungkan data dari beberapa sumber
- Membersihkan data yang tidak konsisten
- Menyamakan format kolom sebelum merge
- Mengurangi pekerjaan manual di spreadsheet

---

## Batasan

- Dirancang untuk dataset kecil–menengah (± ratusan hingga ribuan baris)
- Masih berbasis input interaktif (belum fully automated)
- Cleaning masih berbasis rule manual (belum pattern engine)
- Tidak semua kasus transformasi kompleks bisa ditangani

---

## Status

> ⚠️ v1.0 — Work in Progress. Masih ada bug yang diketahui.
> Kontribusi dan feedback welcome.

---

## Roadmap

- [ ] Transform session (format kode, case conversion)
- [ ] Rename kolom interaktif
- [ ] Feature engineering (kalkulasi, gabung kolom)
- [ ] Statistik dasar & missing values detection
- [ ] Visualisasi CLI
- [ ] Config file per project

---

## Tujuan

DataCraft dibuat sebagai:
- Tool praktis untuk workflow pribadi
- Alternatif ringan dari cleaning manual di Excel
- Eksperimen dalam membangun CLI data tool

---

## Lisensi

MIT License — bebas dipakai dan dimodifikasi.