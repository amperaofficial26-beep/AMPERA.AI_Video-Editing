import streamlit as st
import pandas as pd
import json
import pdfplumber
import zipfile
import os
import tempfile
import datetime
from PIL import Image
import plotly.express as expression_px

st.set_page_config(page_title="Enterprise Universal File Analyzer", layout="wide")

st.title("📂 Enterprise Universal File & Data Analyzer")
st.write("Aplikasi analisis file profesional dengan manajemen memori, router otomatis, visualisasi Plotly interaktif, dan pencarian kata kunci.")

# --- 1. FILE DIRECTORY & ENSIKLOPEDIA FORMAT ---
FILE_DIRECTORY = {
    "pdf": ("Dokumen PDF", "Dokumen portabel untuk laporan resmi dan e-book."),
    "docx": ("Dokumen Word", "Format dokumen pengolah kata berbasis XML."),
    "xlsx": ("Spreadsheet Excel", "Format lembar kerja dan tabel data modern."),
    "csv": ("Data Tabular CSV", "Format file teks untuk menyimpan data tabel."),
    "txt": ("Teks Polos", "Format file teks murni."),
    "json": ("JSON Data", "Format pertukaran data terstruktur."),
    "py": ("Python Source Code", "File skrip pemrograman Python."),
    "md": ("Markdown Documentation", "Format teks dengan markup ringan."),
    "png": ("Gambar PNG", "Format gambar raster berkualitas tinggi."),
    "jpg": ("Gambar JPEG", "Format gambar terkompresi umum."),
    "jpeg": ("Gambar JPEG", "Format gambar standar."),
    "webp": ("Gambar WebP", "Format gambar modern berukuran kecil."),
    "zip": ("Arsip ZIP", "Format file kompresi data.")
}

# --- 2. MANAJEMEN SESI & SAMPLE DATA ---
if "analysis_history" not in st.session_state:
    st.session_state.analysis_history = []

# Tombol Sampel Data Bawaan
with st.sidebar:
    st.header("⚙️ Kontrol & Data Contoh")
    use_sample = st.button("🧪 Coba dengan Data Contoh (CSV)")
    st.markdown("---")
    st.markdown("**Batasan Sistem:**")
    st.text("• Maksimal ukuran file: 200 MB\n• Pembersihan memori otomatis aktif")

# Mengatur sampel data jika tombol ditekan
uploaded_file = None
if use_sample:
    # Membuat sampel dataframe dummy secara instan
    sample_df = pd.DataFrame({
        "Kategori": ["Elektronik", "Pakaian", "Makanan", "Elektronik", "Pakaian"],
        "Penjualan": [1500000, 450000, 120000, 2300000, 600000],
        "Jumlah": [10, 25, 50, 15, 30],
        "Kepuasan": [4.5, 4.0, 3.8, 4.9, 4.2]
    })
    temp_sample = tempfile.NamedTemporaryFile(delete=False, suffix='.csv')
    sample_df.to_csv(temp_sample.name, index=False)
    # Bungkus sebagai objek file Streamlit-like
    with open(temp_sample.name, "rb") as f:
        class SampleFile:
            def __init__(self, file_obj, name):
                self.name = name
                self.size = os.path.getsize(file_obj)
                self._file = file_obj
            def read(self):
                return self._file.read()
            def getvalue(self):
                self._file.seek(0)
                return self._file.read()
        uploaded_file = SampleFile(f, "sample_penjualan.csv")

else:
    # Standar File Uploader dengan Drag and Drop
    uploaded_file = st.file_uploader(
        "Unggah file Anda (CSV, Excel, JSON, PDF, TXT, Gambar, atau ZIP):", 
        type=["csv", "xlsx", "xls", "json", "txt", "pdf", "docx", "png", "jpg", "jpeg", "webp", "zip", "py", "md"]
    )

# --- 3. PEMROSESAN UTAMA DENGAN TEMPFILE & CLEANUP ---
if uploaded_file is not None:
    file_name = uploaded_file.name
    file_extension = file_name.split('.')[-1].lower()
    file_size_bytes = uploaded_file.size if hasattr(uploaded_file, 'size') else len(uploaded_file.getvalue())
    file_size_kb = file_size_bytes / 1024

    # Validasi Ukuran File (Maksimal 200 MB)
    if file_size_kb > 204800:
        st.error("❌ Ukuran file terlalu besar! Batas maksimum adalah 200 MB.")
    else:
        # Indikator Loading Profesional
        with st.spinner("⏳ Memproses file secara aman di server..."):
            # Gunakan tempfile untuk manajemen memori yang bersih
            temp_dir = tempfile.TemporaryDirectory()
            temp_path = os.path.join(temp_dir.name, file_name)
            
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getvalue() if hasattr(uploaded_file, 'getvalue') else uploaded_file.read())

            file_timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cat_info, desc_info = FILE_DIRECTORY.get(
                file_extension, 
                ("File Universal / Biner", "Format file yang dianalisis strukturnya secara umum.")
            )

        st.success(f"✅ Berhasil memuat file: **{file_name}**")

        # --- 4. PANEL INFORMASI & METADATA ---
        st.markdown("---")
        st.subheader("📖 Ensiklopedia & Metadata File")
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        col_m1.metric("Kategori Sistem", cat_info)
        col_m2.metric("Ukuran File", f"{file_size_kb:.2f} KB")
        col_m3.metric("Waktu Pemrosesan", file_timestamp)
        col_m4.metric("Ekstensi", f".{file_extension.upper()}")

        st.markdown("---")
        st.subheader("🔍 Smart File Router & Hasil Analisis")

        # --- ROUTER 1: ARSIP & FILE TERKOMPRESI (.ZIP) ---
        if file_extension == "zip":
            st.info("📦 Terdeteksi arsip terkompresi. Mengekstrak isi file...")
            try:
                with zipfile.ZipFile(temp_path, 'r') as archive:
                    file_list = archive.namelist()
                    st.write(f"Ditemukan **{len(file_list)} item** di dalam arsip:")
                    st.dataframe(pd.DataFrame({"Daftar File Dalam Arsip": file_list}), use_container_width=True)
            except Exception as e:
                st.error(f"Gagal membaca arsip ZIP: {e}")

        # --- ROUTER 2: DATA TABULAR (CSV, Excel, JSON) ---
        elif file_extension in ["csv", "xlsx", "xls", "json"]:
            try:
                if file_extension == "csv":
                    df = pd.read_csv(temp_path)
                elif file_extension in ["xlsx", "xls"]:
                    df = pd.read_excel(temp_path)
                elif file_extension == "json":
                    df = pd.read_json(temp_path)

                # Ringkasan Statistik Otomatis (KPI)
                st.write("### 📊 Ringkasan Statistik Utama (KPI)")
                kpi1, kpi2, kpi3, kpi4 = st.columns(4)
                kpi1.metric("Total Baris", df.shape[0])
                kpi2.metric("Total Kolom", df.shape[1])
                kpi3.metric("Total Sel Kosong (Missing)", int(df.isnull().sum().sum()))
                kpi4.metric("Duplikat Data", int(df.duplicated().sum()))

                # Pratinjau Data Interaktif (st.dataframe dengan sorting & filter)
                st.write("### 📋 Pratinjau Data Interaktif")
                st.dataframe(df, use_container_width=True)

                # Visualisasi Dinamis Menggunakan Plotly
                st.write("### 📈 Visualisasi Grafik Dinamis")
                numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
                categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()

                if numeric_cols and categorical_cols:
                    v_col1, v_col2 = st.columns(2)
                    with v_col1:
                        x_axis = st.selectbox("Pilih Sumbu X (Kategori):", categorical_cols)
                    with v_col2:
                        y_axis = st.selectbox("Pilih Sumbu Y (Nilai Numerik):", numeric_cols)

                    fig = expression_px.bar(df, x=x_axis, y=y_axis, title=f"Grafik Batang {y_axis} berdasarkan {x_axis}")
                    st.plotly_chart(fig, use_container_width=True)
                elif numeric_cols:
                    fig = expression_px.box(df, y=numeric_cols[0], title=f"Distribusi Statistik {numeric_cols[0]}")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("Tidak ada kolom numerik yang cukup untuk membuat grafik otomatis.")

                # Ekspor Hasil Analisis
                st.write("### 💾 Ekspor Data Olahan")
                csv_export = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="⬇️ Unduh Data ke Format CSV",
                    data=csv_export,
                    file_name=f"processed_{file_name}",
                    mime="text/csv",
                    use_container_width=True
                )

            except Exception as e:
                st.error(f"Gagal memproses data tabular: {e}")

        # --- ROUTER 3: DOKUMEN TEKS & PDF (PDF, TXT, DOCX, PY, MD) ---
        elif file_extension in ["pdf", "txt", "docx", "py", "md"]:
            extracted_text = ""
            try:
                if file_extension == "pdf":
                    with pdfplumber.open(temp_path) as pdf:
                        extracted_text = "".join([page.extract_text() or "" for page in pdf.pages])
                else:
                    with open(temp_path, "r", encoding="utf-8", errors="ignore") as f:
                        extracted_text = f.read()

                # Metrik Teks
                words_list = extracted_text.split()
                t1, t2 = st.columns(2)
                t1.metric("Estimasi Jumlah Kata", len(words_list))
                t2.metric("Jumlah Karakter", len(extracted_text))

                # Fitur Pencarian Kata Kunci (Keyword Search)
                st.write("### 🔎 Pencarian Kata Kunci dalam Dokumen")
                keyword = st.text_input("Masukkan kata atau frasa yang ingin dicari:")
                if keyword:
                    count_kw = extracted_text.lower().count(keyword.lower())
                    st.info(f"Kata '**{keyword}**' ditemukan sebanyak **{count_kw}** kali dalam dokumen.")

                # Editor Teks & Ekstraksi / Ringkasan Poin Penting
                st.write("### 📝 Editor Teks & Pratinjau Dokumen")
                edited_content = st.text_area("Isi Dokumen (Dapat Diedit):", value=extracted_text, height=300)

                # Ekspor Teks
                st.download_button(
                    label="💾 Unduh Dokumen Hasil Suntingan",
                    data=edited_content,
                    file_name=f"edited_{file_name}",
                    mime="text/plain",
                    use_container_width=True
                )

            except Exception as e:
                st.error(f"Gagal mengekstrak teks dokumen: {e}")

        # --- ROUTER 4: MEDIA VISUAL (Gambar) ---
        elif file_extension in ["png", "jpg", "jpeg", "webp"]:
            try:
                img = Image.open(temp_path)
                w, h = img.size
                
                i1, i2, i3 = st.columns(3)
                i1.metric("Lebar Resolusi", f"{w} px")
                i2.metric("Tinggi Resolusi", f"{h} px")
                i3.metric("Mode Warna", img.mode)

                st.image(img, caption=f"Pratinjau Gambar: {file_name}", use_column_width=True)
            except Exception as e:
                st.error(f"Gagal memuat file gambar: {e}")

        else:
            st.warning("Format file dikenali sistem, namun tidak memerlukan parser khusus. Metadata dasar berhasil dicatat.")

        # --- 5. CLEANUP OTOMATIS MEMORI SERVER ---
        try:
            temp_dir.cleanup()
        except Exception:
            pass
