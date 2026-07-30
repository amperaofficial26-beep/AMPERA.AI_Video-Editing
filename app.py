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
import difflib
from moviepy.editor import VideoFileClip, AudioFileClip

st.set_page_config(page_title="Enterprise Universal File & Media Analyzer", layout="wide")

# --- CUSTOM THEME SETTINGS ---
with st.sidebar:
    st.header("⚙️ Kontrol & Pengaturan")
    theme_mode = st.selectbox("Tema Antarmuka", ["Standar Streamlit", "Minimalis Terang", "Mode Fokus"])
    st.markdown("---")
    st.markdown("**Batasan Sistem:**")
    st.text("• Maksimal ukuran file: 200 MB\n• Pembersihan memori otomatis aktif")

st.title("📂 Enterprise Universal File, Data & Media Analyzer")
st.write("Aplikasi analisis file profesional dengan dukungan multi-file, filter data, perbandingan file teks, serta analisis file video dan audio.")

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
    "zip": ("Arsip ZIP", "Format file kompresi data."),
    "mp4": ("Video MP4", "Format media video digital standar kompresi tinggi."),
    "avi": ("Video AVI", "Format kontainer multimedia Audio Video Interleave."),
    "mkv": ("Video MKV", "Format kontainer video terbuka yang mendukung banyak trek."),
    "mp3": ("Audio MP3", "Format file kompresi audio digital populer."),
    "wav": ("Audio WAV", "Format audio gelombang tanpa kompresi berkualitas tinggi.")
}

# --- 2. PILIHAN MODE UTAMA ---
app_mode = st.radio("Pilih Mode Kerja Aplikasi:", ["Analisis Tunggal / Batch (Banyak File)", "Perbandingan Dua File (Diff Tool)"], horizontal=True)
st.markdown("---")

if app_mode == "Analisis Tunggal / Batch (Banyak File)":
    use_sample = st.sidebar.button("🧪 Coba dengan Data Contoh (CSV)")
    
    uploaded_files = []
    if use_sample:
        sample_df = pd.DataFrame({
            "Kategori": ["Elektronik", "Pakaian", "Makanan", "Elektronik", "Pakaian"],
            "Penjualan": [1500000, 450000, 120000, 2300000, 600000],
            "Jumlah": [10, 25, 50, 15, 30],
            "Kepuasan": [4.5, 4.0, 3.8, 4.9, 4.2]
        })
        temp_sample = tempfile.NamedTemporaryFile(delete=False, suffix='.csv')
        sample_df.to_csv(temp_sample.name, index=False)
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
            uploaded_files = [SampleFile(f, "sample_penjualan.csv")]
    else:
        uploaded_files = st.file_uploader(
            "Unggah file (Dokumen, Tabular, Gambar, Arsip, atau Video/Audio):", 
            type=["csv", "xlsx", "xls", "json", "txt", "pdf", "docx", "png", "jpg", "jpeg", "webp", "zip", "py", "md", "mp4", "avi", "mkv", "mp3", "wav"],
            accept_multiple_files=True
        )

    if uploaded_files:
        for uploaded_file in uploaded_files:
            file_name = uploaded_file.name
            file_extension = file_name.split('.')[-1].lower()
            file_size_bytes = uploaded_file.size if hasattr(uploaded_file, 'size') else len(uploaded_file.getvalue())
            file_size_kb = file_size_bytes / 1024

            st.markdown(f"### 📦 Berkas Aktif: `{file_name}`")

            if file_size_kb > 204800:
                st.error(f"❌ Ukuran file {file_name} terlalu besar! Batas maksimum adalah 200 MB.")
                continue

            with st.spinner(f"⏳ Memproses {file_name}..."):
                temp_dir = tempfile.TemporaryDirectory()
                temp_path = os.path.join(temp_dir.name, file_name)
                
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getvalue() if hasattr(uploaded_file, 'getvalue') else uploaded_file.read())

                file_timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cat_info, desc_info = FILE_DIRECTORY.get(
                    file_extension, 
                    ("File Universal / Biner", "Format file yang dianalisis strukturnya secara umum.")
                )

            # Metadata Info
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            col_m1.metric("Kategori Sistem", cat_info)
            col_m2.metric("Ukuran File", f"{file_size_kb:.2f} KB")
            col_m3.metric("Waktu Diproses", file_timestamp)
            col_m4.metric("Ekstensi", f".{file_extension.upper()}")

            # --- ROUTER 1: ARSIP (ZIP) ---
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

                    st.write("#### 📊 Ringkasan Statistik Utama (KPI)")
                    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
                    kpi1.metric("Total Baris", df.shape[0])
                    kpi2.metric("Total Kolom", df.shape[1])
                    kpi3.metric("Sel Kosong (Missing)", int(df.isnull().sum().sum()))
                    kpi4.metric("Duplikat Data", int(df.duplicated().sum()))

                    st.write("#### 🔎 Advanced Data Filtering & Query Builder")
                    enable_filter = st.checkbox(f"Aktifkan Filter Data untuk {file_name}", value=False)
                    filtered_df = df
                    if enable_filter and not df.empty:
                        filter_col = st.selectbox(f"Pilih Kolom untuk Filter ({file_name}):", df.columns.tolist(), key=f"filter_{file_name}")
                        if pd.api.types.is_numeric_dtype(df[filter_col]):
                            min_val, max_val = float(df[filter_col].min()), float(df[filter_col].max())
                            val_range = st.slider(f"Rentang nilai untuk {filter_col}", min_val, max_val, (min_val, max_val), key=f"slider_{file_name}")
                            filtered_df = df[(df[filter_col] >= val_range[0]) & (df[filter_col] <= val_range[1])]
                        else:
                            unique_vals = df[filter_col].astype(str).unique().tolist()
                            selected_vals = st.multiselect(f"Pilih nilai {filter_col}", unique_vals, default=unique_vals[:min(5, len(unique_vals))], key=f"multi_{file_name}")
                            filtered_df = df[df[filter_col].astype(str).isin(selected_vals)]

                    st.write("#### 📋 Pratinjau Data Tabel")
                    st.dataframe(filtered_df, use_container_width=True)

                    st.write("#### 📈 Visualisasi Grafik Dinamis")
                    numeric_cols = filtered_df.select_dtypes(include=['number']).columns.tolist()
                    categorical_cols = filtered_df.select_dtypes(include=['object', 'category']).columns.tolist()

                    if numeric_cols and categorical_cols:
                        v_col1, v_col2 = st.columns(2)
                        with v_col1:
                            x_axis = st.selectbox("Pilih Sumbu X (Kategori):", categorical_cols, key=f"x_{file_name}")
                        with v_col2:
                            y_axis = st.selectbox("Pilih Sumbu Y (Nilai Numerik):", numeric_cols, key=f"y_{file_name}")

                        fig = expression_px.bar(filtered_df, x=x_axis, y=y_axis, title=f"Grafik {y_axis} berdasarkan {x_axis}")
                        st.plotly_chart(fig, use_container_width=True)
                    elif numeric_cols:
                        fig = expression_px.box(filtered_df, y=numeric_cols[0], title=f"Distribusi {numeric_cols[0]}")
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.warning("Kolom numerik tidak mencukupi untuk membuat grafik.")

                    csv_export = filtered_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label=f"⬇️ Unduh Data Olahan ({file_name})",
                        data=csv_export,
                        file_name=f"processed_{file_name}",
                        mime="text/csv",
                        use_container_width=True,
                        key=f"dl_{file_name}"
                    )
                except Exception as e:
                    st.error(f"Gagal memproses file tabular {file_name}: {e}")

            # --- ROUTER 3: DOKUMEN TEKS & PDF ---
            elif file_extension in ["pdf", "txt", "docx", "py", "md"]:
                extracted_text = ""
                try:
                    if file_extension == "pdf":
                        with pdfplumber.open(temp_path) as pdf:
                            extracted_text = "".join([page.extract_text() or "" for page in pdf.pages])
                    else:
                        with open(temp_path, "r", encoding="utf-8", errors="ignore") as f:
                            extracted_text = f.read()

                    t1, t2 = st.columns(2)
                    t1.metric("Estimasi Jumlah Kata", len(extracted_text.split()))
                    t2.metric("Jumlah Karakter", len(extracted_text))

                    keyword = st.text_input(f"Cari kata dalam {file_name}:", key=f"kw_{file_name}")
                    if keyword:
                        count_kw = extracted_text.lower().count(keyword.lower())
                        st.info(f"Kata '**{keyword}**' ditemukan sebanyak **{count_kw}** kali.")

                    edited_content = st.text_area(f"Editor Teks ({file_name}):", value=extracted_text, height=250, key=f"edit_{file_name}")
                    st.download_button(
                        label=f"💾 Unduh Dokumen Suntingan ({file_name})",
                        data=edited_content,
                        file_name=f"edited_{file_name}",
                        mime="text/plain",
                        use_container_width=True,
                        key=f"dl_txt_{file_name}"
                    )
                except Exception as e:
                    st.error(f"Gagal membaca teks {file_name}: {e}")

            # --- ROUTER 4: GAMBAR ---
            elif file_extension in ["png", "jpg", "jpeg", "webp"]:
                try:
                    img = Image.open(temp_path)
                    w, h = img.size
                    i1, i2, i3 = st.columns(3)
                    i1.metric("Lebar", f"{w} px")
                    i2.metric("Tinggi", f"{h} px")
                    i3.metric("Mode Warna", img.mode)
                    st.image(img, caption=file_name, use_column_width=True)
                except Exception as e:
                    st.error(f"Gagal memuat gambar: {e}")

            # --- ROUTER 5: VIDEO & AUDIO (MEDIA ANALYZER) ---
            elif file_extension in ["mp4", "avi", "mkv", "mp3", "wav"]:
                try:
                    if file_extension in ["mp4", "avi", "mkv"]:
                        clip = VideoFileClip(temp_path)
                        st.write("#### 🎬 Metadata & Pemutar Video")
                        v1, v2, v3 = st.columns(3)
                        v1.metric("Durasi", f"{int(clip.duration)} detik")
                        v2.metric("Resolusi", f"{clip.size[0]} x {clip.size[1]} px")
                        v3.metric("Frame Rate", f"{clip.fps:.2f} fps")
                        
                        st.video(uploaded_file)
                        clip.close()
                    else:
                        clip = AudioFileClip(temp_path)
                        st.write("#### 🎵 Metadata & Pemutar Audio")
                        a1, a2 = st.columns(2)
                        a1.metric("Durasi Audio", f"{int(clip.duration)} detik")
                        a2.metric("Jumlah Saluran (Channels)", clip.nchannels)
                        
                        st.audio(uploaded_file)
                        clip.close()
                except Exception as e:
                    st.error(f"Gagal memproses file media: {e}")

            st.markdown("---")
            try:
                temp_dir.cleanup()
            except Exception:
                pass

else:
    # --- FITUR PERBANDINGAN FILE (DIFF TOOL) ---
    st.subheader("⚖️ Perbandingan Dua File Teks / Kode (Diff Tool)")
    st.write("Unggah dua file teks, skrip, atau CSV untuk melihat perbedaan isi baris demi baris secara otomatis.")
    
    diff_file_1 = st.file_uploader("Unggah File Pertama (Versi Lama / Asli)", type=["txt", "py", "csv", "json", "md"], key="diff1")
    diff_file_2 = st.file_uploader("Unggah File Kedua (Versi Baru / Pembanding)", type=["txt", "py", "csv", "json", "md"], key="diff2")

    if diff_file_1 and diff_file_2:
        try:
            text1 = diff_file_1.getvalue().decode("utf-8", errors="ignore").splitlines()
            text2 = diff_file_2.getvalue().decode("utf-8", errors="ignore").splitlines()

            st.markdown("### 🔍 Hasil Analisis Perbedaan (Diff)")
            diff_result = list(difflib.unified_diff(
                text1, text2,
                fromfile=diff_file_1.name,
                tofile=diff_file_2.name,
                lineterm=''
            ))

            if diff_result:
                st.code("\n".join(diff_result), language="diff")
            else:
                st.success("✨ Kedua file memiliki isi yang **identik sama persis**! Tidak ditemukan perbedaan.")
        except Exception as e:
            st.error(f"Terjadi kesalahan saat membandingkan file: {e}")
