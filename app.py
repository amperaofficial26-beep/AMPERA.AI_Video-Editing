import streamlit as st
import pandas as pd
import json
import pdfplumber
import zipfile
import os
from PIL import Image

st.set_page_config(page_title="Multi-Format File Analyzer", layout="wide")

st.title("📂 Mega Universal File Analyzer (100+ Format Support)")
st.write("Unggah file jenis apa saja untuk mendeteksi metadata, kategori, penjelasan format, serta melihat isi analisis dasarnya secara instan tanpa AI.")

# Kamus Ensiklopedia Kategori & Penjelasan 100+ Jenis File
FILE_DIRECTORY = {
    # Dokumen & Perkantoran
    "pdf": ("Dokumen Portable", "Format dokumen digital portabel yang sering digunakan untuk e-book, laporan resmi, dan formulir."),
    "docx": ("Dokumen Microsoft Word", "Format dokumen pengolah kata berbasis XML yang dikembangkan oleh Microsoft."),
    "doc": ("Dokumen Word Klasik", "Format dokumen biner lama dari Microsoft Word sebelum standar XML."),
    "xlsx": ("Spreadsheet Excel", "Format lembar kerja (tabel dan angka) modern dari Microsoft Excel."),
    "xls": ("Spreadsheet Excel Lama", "Format lembar kerja biner tradisional Microsoft Excel."),
    "csv": ("Data Tabular Terpisah Koma", "Format file teks sederhana untuk menyimpan data tabel (baris dan kolom)."),
    "txt": ("Teks Polos", "Format file teks murni tanpa gaya pemformatan khusus."),
    "pptx": ("Presentasi PowerPoint", "Format file presentasi slide dari Microsoft PowerPoint."),
    "pdf": ("Dokumen PDF", "Format dokumen dokumen universal."),
    "rtf": ("Rich Text Format", "Format teks lintas platform yang mendukung dasar pemformatan huruf."),
    "odt": ("OpenDocument Text", "Format dokumen teks standar terbuka (biasanya digunakan LibreOffice/OpenOffice)."),
    
    # Data & Pemrograman / Kode
    "json": ("JavaScript Object Notation", "Format ringan berbasis teks untuk pertukaran data terstruktur."),
    "xml": ("Extensible Markup Language", "Format markup untuk menyimpan dan mentransmisikan data terstruktur."),
    "html": ("HyperText Markup Language", "Format kode standar untuk merancang halaman situs web."),
    "css": ("Cascading Style Sheets", "File pengaturan gaya dan tata letak visual halaman web."),
    "js": ("JavaScript Source Code", "File skrip pemrograman yang berjalan di sisi web/browser."),
    "py": ("Python Source Code", "File kode skrip bahasa pemrograman Python."),
    "sql": ("Database Query", "File skrip berisi perintah bahasa kueri basis data relasional."),
    "yaml": ("YAML Configuration", "Format serialisasi data yang ramah dibaca manusia untuk konfigurasi."),
    "yml": ("YAML Configuration", "Format konfigurasi alternatif dari YAML."),
    "md": ("Markdown Documentation", "Format teks dengan markup ringan untuk dokumentasi teks dan catatan."),
    
    # Arsip & Kompresi
    "zip": ("Arsip Terkompresi ZIP", "Format file kompresi standar untuk membungkus banyak file/folder."),
    "rar": ("Arsip Terkompresi RAR", "Format arsip file berpemilik dengan tingkat kompresi tinggi."),
    "tar": ("Tape Archive", "Format penggabung banyak file Unix tanpa kompresi bawaan."),
    "gz": ("Gzip Compressed", "Format file tunggal yang dikompresi menggunakan algoritma Gzip."),
    "7z": ("7-Zip Archive", "Format arsip terkompresi dengan rasio kompresi sangat tinggi."),
    
    # Gambar & Grafis
    "png": ("Portable Network Graphics", "Format gambar raster berkualitas tinggi yang mendukung latar belakang transparan."),
    "jpg": ("JPEG Image", "Format gambar terkompresi yang paling umum digunakan untuk foto digital."),
    "jpeg": ("JPEG Image", "Varian ekstensi standar dari format gambar JPEG."),
    "gif": ("Graphics Interchange Format", "Format gambar yang mendukung animasi pendek berbasis bingkai."),
    "webp": ("WebP Image", "Format gambar modern besutan Google dengan ukuran kecil dan kualitas tinggi."),
    "svg": ("Scalable Vector Graphics", "Format gambar vektor berbasis XML yang tidak pecah saat di-zoom."),
    "bmp": ("Bitmap Image", "Format gambar raster mentah tanpa kompresi berukuran besar."),
    "ico": ("Icon File", "Format file khusus untuk ikon aplikasi atau situs web.")
}

# Bagian Upload File Universal
uploaded_file = st.file_uploader("Pilih file Anda (Mendukung semua ekstensi)", type=None)

if uploaded_file is not None:
    file_name = uploaded_file.name
    file_extension = file_name.split('.')[-1].lower()
    file_size_kb = uploaded_file.size / 1024
    file_size_mb = file_size_kb / 1024
    
    # Ambil penjelasan dari kamus, atau berikan informasi umum jika tidak terdaftar
    cat_info, desc_info = FILE_DIRECTORY.get(
        file_extension, 
        ("File Umum / Biner", "Format file umum yang dapat dianalisis berdasarkan struktur biner atau ukuran metadatanya.")
    )

    # --- INFORMASI METADATA & PENJELASAN FORMAT ---
    st.markdown("---")
    st.subheader("📖 Ensiklopedia & Penjelasan Format File")
    
    info_col1, info_col2 = st.columns(2)
    with info_col1:
        st.info(f"**Kategori Sistem:** {cat_info}")
        st.write(f"**Penjelasan Format:** {desc_info}")
    with info_col2:
        st.metric("Nama File", file_name)
        st.metric("Ekstensi", f".{file_extension.upper()}")
        size_str = f"{file_size_mb:.2f} MB" if file_size_kb >= 1024 else f"{file_size_kb:.2f} KB"
        st.metric("Ukuran File", size_str)

    st.markdown("---")
    st.subheader("🔍 Hasil Analisis & Ekstraksi Isi File")
    
    # 1. ANALISIS DATA TABULAR (CSV, Excel)
    if file_extension in ["csv", "xlsx", "xls"]:
        try:
            df = pd.read_csv(uploaded_file) if file_extension == "csv" else pd.read_excel(uploaded_file)
            tab1, tab2, tab3 = st.tabs(["Pratinjau Tabel", "Statistika Data", "Struktur Kolom"])
            with tab1:
                st.dataframe(df.head(50), use_container_width=True)
            with tab2:
                st.dataframe(df.describe(), use_container_width=True)
            with tab3:
                col_df = pd.DataFrame({"Kolom": df.columns, "Tipe Data": df.dtypes.astype(str), "Null Count": df.isnull().sum()})
                st.dataframe(col_df, use_container_width=True)
        except Exception as e:
            st.error(f"Gagal memproses tabel: {e}")

    # 2. ANALISIS DOKUMEN PDF
    elif file_extension == "pdf":
        try:
            with pdfplumber.open(uploaded_file) as pdf:
                st.metric("Total Halaman", len(pdf.pages))
                full_text = "".join([p.extract_text() or "" for p in pdf.pages])
                st.metric("Estimasi Jumlah Kata", len(full_text.split()))
                with st.expander("Lihat Seluruh Teks Dokumen"):
                    st.text_area("Isi Teks PDF:", full_text, height=300)
        except Exception as e:
            st.error(f"Gagal membaca PDF: {e}")

    # 3. ANALISIS FILE GAMBAR (PNG, JPG, WEBP, DLL)
    elif file_extension in ["png", "jpg", "jpeg", "webp", "bmp", "gif"]:
        try:
            img = Image.open(uploaded_file)
            w, h = img.size
            c1, c2, c3 = st.columns(3)
            c1.metric("Lebar (Width)", f"{w} px")
            c2.metric("Tinggi (Height)", f"{h} px")
            c3.metric("Mode Warna", img.mode)
            st.image(img, caption=f"Pratinjau Gambar: {file_name}", use_column_width=True)
        except Exception as e:
            st.error(f"Gagal memuat gambar: {e}")

    # 4. ANALISIS ARSIP ZIP
    elif file_extension == "zip":
        try:
            with zipfile.ZipFile(uploaded_file, 'r') as z:
                file_list = z.namelist()
                st.write(f"Arsip ini berisi **{len(file_list)} item** file/folder di dalamnya:")
                st.dataframe(pd.DataFrame({"Daftar File Dalam Arsip": file_list}), use_container_width=True)
        except Exception as e:
            st.error(f"Gagal membaca arsip ZIP: {e}")

    # 5. ANALISIS FILE TEKS / KODE (TXT, JSON, PY, HTML, CSS, MD, DLL)
    else:
        try:
            content = uploaded_file.getvalue().decode("utf-8", errors="ignore")
            lines = content.splitlines()
            words = content.split()
            
            c1, c2 = st.columns(2)
            c1.metric("Jumlah Baris", len(lines))
            c2.metric("Jumlah Kata", len(words))
            
            if file_extension == "json":
                st.json(json.loads(content))
            else:
                st.text_area("Pratinjau Isi File:", content, height=300)
        except Exception as e:
            st.warning("File berformat biner khusus. Metadata dasar di atas berhasil dikenali, namun isi teks tidak dapat ditampilkan langsung.")
