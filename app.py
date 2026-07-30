import streamlit as st
import pandas as pd
import json
import pdfplumber
import zipfile
import os

st.set_page_config(page_title="Universal File Analyzer", layout="wide")

st.title("📁 Universal File Analyzer (Tanpa AI)")
st.write("Unggah file apa saja (CSV, Excel, PDF, JSON, TXT, ZIP) untuk melihat analisis struktur, statistik, dan isinya secara instan.")

# Bagian Upload File Universal
uploaded_file = st.file_uploader("Pilih file Anda", type=["csv", "xlsx", "xls", "json", "txt", "pdf", "zip"])

if uploaded_file is not None:
    file_name = uploaded_file.name
    file_extension = file_name.split('.')[-1].lower()
    file_size = uploaded_file.size / 1024 # dalam KB
    
    # Menampilkan Informasi Metadata Dasar File
    st.markdown("---")
    st.subheader("📊 Informasi Dasar File")
    m1, m2, m3 = st.columns(3)
    m1.metric("Nama File", file_name)
    m2.metric("Format / Ekstensi", file_extension.upper())
    m3.metric("Ukuran File", f"{file_size:.2f} KB")
    
    st.markdown("---")
    st.subheader("🔍 Hasil Analisis & Isi File")
    
    # 1. ANALISIS FILE TABULAR (CSV / Excel)
    if file_extension in ["csv", "xlsx", "xls"]:
        if file_extension == "csv":
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
            
        tab1, tab2, tab3 = st.tabs(["Pratinjau Data", "Statistik Ringkas", "Info Kolom"])
        
        with tab1:
            st.write(f"Menampilkan {min(50, len(df))} baris pertama dari total {len(df)} baris data:")
            st.dataframe(df.head(50), use_container_width=True)
            
        with tab2:
            st.write("Ringkasan Statistik Angka (Mean, Min, Max, dll):")
            st.dataframe(df.describe(), use_container_width=True)
            
        with tab3:
            st.write("Daftar Tipe Data Setiap Kolom:")
            buffer_info = pd.DataFrame({
                "Kolom": df.columns,
                "Tipe Data": df.dtypes.astype(str),
                "Data Kosong (Null)": df.isnull().sum()
            })
            st.dataframe(buffer_info, use_container_width=True)

    # 2. ANALISIS FILE PDF
    elif file_extension == "pdf":
        with pdfplumber.open(uploaded_file) as pdf:
            total_pages = len(pdf.pages)
            st.write(f"Total Halaman PDF: **{total_pages} halaman**")
            
            text_content = ""
            for i, page in enumerate(pdf.pages):
                text_content += f"\n--- Halaman {i+1} ---\n" + (page.extract_text() or "")
            
            # Statistik Teks Sederhana
            words = text_content.split()
            st.metric("Estimasi Jumlah Kata", len(words))
            
            with st.expander("Lihat Seluruh Isi Teks Ekstraksi"):
                st.text_area("Teks PDF:", text_content, height=300)

    # 3. ANALISIS FILE JSON
    elif file_extension == "json":
        try:
            data = json.load(uploaded_file)
            st.success("Format JSON valid!")
            st.json(data)
        except Exception as e:
            st.error(f"Gagal membaca JSON: {e}")

    # 4. ANALISIS FILE TEKS (TXT)
    elif file_extension == "txt":
        string_data = uploaded_file.getvalue().decode("utf-8")
        lines = string_data.splitlines()
        words = string_data.split()
        
        c1, c2 = st.columns(2)
        c1.metric("Jumlah Baris", len(lines))
        c2.metric("Jumlah Kata", len(words))
        
        st.subheader("Isi Teks:")
        st.text_area("Teks:", string_data, height=250)

    # 5. ANALISIS FILE ZIP (Arsip)
    elif file_extension == "zip":
        with zipfile.ZipFile(uploaded_file, 'r') as z:
            file_list = z.namelist()
            st.write(f"Arsip ZIP berisi **{len(file_list)} file/folder** di dalamnya:")
            
            df_zip = pd.DataFrame({"Daftar Isi File di Dalam ZIP": file_list})
            st.dataframe(df_zip, use_container_width=True)
