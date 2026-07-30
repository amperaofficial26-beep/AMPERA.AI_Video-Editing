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
import base64

st.set_page_config(page_title="Ampera Enterprise Universal File & Media Analyzer", layout="wide")

# Fungsi untuk membaca file lokal menjadi base64 untuk latar belakang CSS
def get_base64_of_bin_file(bin_file):
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except Exception:
        return None

# Deteksi otomatis file background: "bg file analisa"
bg_file_options = ["bg file analisa.png", "bg file analisa.jpg", "bg file analisa.jpeg", "bg file analisa.webp"]
bg_path = None
for f in bg_file_options:
    if os.path.exists(f):
        bg_path = f
        break

# Deteksi otomatis file logo: "logo file analisa"
logo_file_options = ["logo file analisa.png", "logo file analisa.jpg", "logo file analisa.jpeg", "logo file analisa.webp"]
logo_path = None
for f in logo_file_options:
    if os.path.exists(f):
        logo_path = f
        break

# Konfigurasi CSS Background Kustom
if bg_path:
    bin_str = get_base64_of_bin_file(bg_path)
    page_bg_css = f"""
    <style>
    .stApp {{
        background-image: linear-gradient(rgba(15, 23, 42, 0.88), rgba(15, 23, 42, 0.88)), url("data:image/png;base64,{bin_str}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        color: #f8fafc;
    }}
    [data-testid="stSidebar"] {{
        background-color: rgba(30, 41, 59, 0.92);
        border-right: 1px solid #334155;
    }}
    h1, h2, h3, h4 {{
        color: #f1f5f9 !important;
    }}
    </style>
    """
else:
    page_bg_css = """
    <style>
    .stApp {
        background-color: #0f172a;
        color: #f8fafc;
    }
    [data-testid="stSidebar"] {
        background-color: #1e293b;
        border-right: 1px solid #334155;
    }
    h1, h2, h3, h4 {
        color: #f1f5f9 !important;
    }
    </style>
    """

st.markdown(page_bg_css, unsafe_allow_html=True)

with st.sidebar:
    # Menampilkan Logo dari file "logo file analisa"
    if logo_path:
        st.image(logo_path, width=100)
    else:
        st.info("💡 Tips: Letakkan file gambar bernama **'logo file analisa.png'** di folder ini.")
    
    st.header("⚙️ Kontrol & Pengaturan")
    st.markdown("---")
    st.markdown("**Batasan Sistem:**")
    st.text("• Maksimal ukuran file: 200 MB\n• Pembersihan memori otomatis aktif")

# --- HEADER UTAMA DENGAN LOGO ---
col_head1, col_head2 = st.columns([0.08, 0.92])
with col_head1:
    if logo_path:
        st.image(logo_path, width=60)
with col_head2:
    st.title("Ampera Enterprise Universal File, Data & Media Analyzer")

if not bg_path:
    st.warning("⚠️ File background **'bg file analisa'** (format .png/.jpg) belum ditemukan di folder aplikasi. Aplikasi saat ini menggunakan latar belakang gelap standar.")

st.write("Aplikasi analisis file profesional dengan antarmuka yang rapi, bersih, dan menggunakan aset kustom Anda.")

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

            with st.container():
                st.markdown(f"### 📦 Berkas: `{file_name}`")

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

                col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                with col_m1:
                    st.metric("📁 Kategori", cat_info)
                with col_m2:
                    st.metric("📊 Ukuran", f"{file_size_kb:.2f} KB")
                with col_m3:
                    st.metric("🕒 Waktu Proses", file_timestamp)
                with col_m4:
                    st.metric("🏷️ Ekstensi", f".{file_extension.upper()}")

                st.markdown("---")

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

                        st.subheader("📊 Ringkasan Statistik Utama (KPI)")
                        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
                        kpi1.metric("Total Baris", df.shape[0])
                        kpi2.metric("Total Kolom", df.shape[1])
                        kpi3.metric("Sel Kosong", int(df.isnull().sum().sum()))
                        kpi4.metric("Duplikat", int(df.duplicated().sum()))

                        with st.expander("🔎 Advanced Data Filtering & Query Builder", expanded=False):
                            enable_filter = st.checkbox(f"Aktifkan Filter Data", value=False, key=f"chk_{file_name}")
                            filtered_df = df
                            if enable_filter and not df.empty:
                                filter_col = st.selectbox("Pilih Kolom:", df.columns.tolist(), key=f"filter_{file_name}")
                                if pd.api.types.is_numeric_dtype(df[filter_col]):
                                    min_val, max_val = float(df[filter_col].min()), float(df[filter_col].max())
                                    val_range = st.slider("Rentang Nilai", min_val, max_val, (min_val, max_val), key=f"slider_{file_name}")
                                    filtered_df = df[(df[filter_col] >= val_range[0]) & (df[filter_col] <= val_range[1])]
                                else:
                                    unique_vals = df[filter_col].astype(str).unique().tolist()
                                    selected_vals = st.multiselect("Pilih Nilai", unique_vals, default=unique_vals[:min(5, len(unique_vals))], key=f"multi_{file_name}")
                                    filtered_df = df[df[filter_col].astype(str).isin(selected_vals)]

                        st.subheader("📋 Pratinjau Data Tabel")
                        st.dataframe(filtered_df, use_container_width=True)

                        st.subheader("📈 Visualisasi Grafik Dinamis")
                        numeric_cols = filtered_df.select_dtypes(include=['number']).columns.tolist()
                        categorical_cols = filtered_df.select_dtypes(include=['object', 'category']).columns.tolist()

                        if numeric_cols and categorical_cols:
                            v_col1, v_col2 = st.columns(2)
                            with v_col1:
                                x_axis = st.selectbox("Sumbu X (Kategori):", categorical_cols, key=f"x_{file_name}")
                            with v_col2:
                                y_axis = st.selectbox("Sumbu Y (Nilai):", numeric_cols, key=f"y_{file_name}")

                            fig = expression_px.bar(filtered_df, x=x_axis, y=y_axis, title=f"Grafik {y_axis} berdasarkan {x_axis}")
                            st.plotly_chart(fig, use_container_width=True)
                        elif numeric_cols:
                            fig = expression_px.box(filtered_df, y=numeric_cols[0], title=f"Distribusi {numeric_cols[0]}")
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.warning("Kolom numerik tidak mencukupi untuk membuat grafik.")

                        csv_export = filtered_df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label=f"⬇️ Unduh Data Olahan",
                            data=csv_export,
                            file_name=f"processed_{file_name}",
                            mime="text/csv",
                            use_container_width=True,
                            key=f"dl_{file_name}"
                        )
                    except Exception as e:
                        st.error(f"Gagal memproses file tabular: {e}")

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

                        st.subheader("📊 Statistik Dokumen")
                        t1, t2 = st.columns(2)
                        t1.metric("Jumlah Kata", len(extracted_text.split()))
                        t2.metric("Jumlah Karakter", len(extracted_text))

                        keyword = st.text_input(f"Cari kata dalam dokumen:", key=f"kw_{file_name}")
                        if keyword:
                            count_kw = extracted_text.lower().count(keyword.lower())
                            st.info(f"Kata '**{keyword}**' ditemukan sebanyak **{count_kw}** kali.")

                        st.subheader("📝 Editor Teks & Pratinjau")
                        edited_content = st.text_area("Isi Dokumen:", value=extracted_text, height=250, key=f"edit_{file_name}")
                        st.download_button(
                            label=f"💾 Unduh Dokumen Suntingan",
                            data=edited_content,
                            file_name=f"edited_{file_name}",
                            mime="text/plain",
                            use_container_width=True,
                            key=f"dl_txt_{file_name}"
                        )
                    except Exception as e:
                        st.error(f"Gagal membaca teks: {e}")

                # --- ROUTER 4: GAMBAR ---
                elif file_extension in ["png", "jpg", "jpeg", "webp"]:
                    try:
                        img = Image.open(temp_path)
                        w, h = img.size
                        st.subheader("🖼️ Informasi & Pratinjau Gambar")
                        i1, i2, i3 = st.columns(3)
                        i1.metric("Lebar", f"{w} px")
                        i2.metric("Tinggi", f"{h} px")
                        i3.metric("Mode Warna", img.mode)
                        st.image(img, caption=file_name, use_column_width=True)
                    except Exception as e:
                        st.error(f"Gagal memuat gambar: {e}")

                # --- ROUTER 5: VIDEO & AUDIO ---
                elif file_extension in ["mp4", "avi", "mkv", "mp3", "wav"]:
                    try:
                        if file_extension in ["mp4", "avi", "mkv"]:
                            clip = VideoFileClip(temp_path)
                            st.subheader("🎬 Metadata & Pemutar Video")
                            v1, v2, v3 = st.columns(3)
                            v1.metric("Durasi", f"{int(clip.duration)} detik")
                            v2.metric("Resolusi", f"{clip.size[0]} x {clip.size[1]} px")
                            v3.metric("Frame Rate", f"{clip.fps:.2f} fps")
                            
                            st.video(uploaded_file)
                            clip.close()
                        else:
                            clip = AudioFileClip(temp_path)
                            st.subheader("🎵 Metadata & Pemutar Audio")
                            a1, a2 = st.columns(2)
                            a1.metric("Durasi", f"{int(clip.duration)} detik")
                            a2.metric("Channels", clip.nchannels)
                            
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
    st.subheader("⚖️ Perbandingan Dua File Teks / Kode (Diff Tool)")
    st.write("Unggah dua file teks atau skrip untuk melihat perbedaan baris secara otomatis.")
    
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        diff_file_1 = st.file_uploader("File Pertama (Asli)", type=["txt", "py", "csv", "json", "md"], key="diff1")
    with col_d2:
        diff_file_2 = st.file_uploader("File Kedua (Pembanding)", type=["txt", "py", "csv", "json", "md"], key="diff2")

    if diff_file_1 and diff_file_2:
        try:
            text1 = diff_file_1.getvalue().decode("utf-8", errors="ignore").splitlines()
            text2 = diff_file_2.getvalue().decode("utf-8", errors="ignore").splitlines()

            st.markdown("### 🔍 Hasil Perbandingan (Diff)")
            diff_result = list(difflib.unified_diff(
                text1, text2,
                fromfile=diff_file_1.name,
                tofile=diff_file_2.name,
                lineterm=''
            ))

            if diff_result:
                st.code("\n".join(diff_result), language="diff")
            else:
                st.success("✨ Kedua file memiliki isi yang **identik sama persis**!")
        except Exception as e:
            st.error(f"Terjadi kesalahan saat membandingkan file: {e}")
