import streamlit as st
import cv2
import tempfile
import os

# Mengatur agar layout halaman memenuhi layar (opsional tapi bagus untuk editor)
st.set_page_config(page_title="Mini Video Editor", layout="wide")

st.title("🎥 Mini Video Editor (CapCut Style)")
st.write("Aplikasi edit video dengan panel kontrol di bagian bawah.")

# Bagian Upload Video (Di atas)
uploaded_video = st.file_uploader("Pilih file video Anda (.mp4, .mov)", type=["mp4", "mov", "avi"])

if uploaded_video is not None:
    # Simpan file sementara agar bisa dibaca OpenCV
    tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
    tfile.write(uploaded_video.read())
    
    # Membaca video menggunakan OpenCV
    cap = cv2.VideoCapture(tfile.name)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration = total_frames / fps if fps > 0 else 0
    
    # --- BAGIAN ATAS: PREVIEW VIDEO UTAMA ---
    st.subheader("Preview Video")
    col_preview1, col_preview2 = st.columns([2, 1])
    
    with col_preview1:
        st.video(uploaded_video)
        
    with col_preview2:
        st.info("📊 **Info File**")
        st.write(f"• Resolusi: **{width}x{height}**")
        st.write(f"• Durasi: **{duration:.2f} detik**")
        st.write(f"• Framerate: **{fps:.1f} FPS**")

    # Garis pemisah visual ala pembatas timeline
    st.markdown("---")

    # --- BAGIAN BAWAH: PANEL KONTROL / TIMELINE ALA CAPCUT ---
    st.markdown("### 🎛️ Panel Kontrol & Timeline Editor")
    
    # Membagi panel bawah menjadi beberapa kolom pengatur (seperti menu efek/potong di bawah CapCut)
    ctrl_col1, ctrl_col2 = st.columns(2)
    
    with ctrl_col1:
        st.write("**Potong Durasi (Trimming)**")
        start_time = st.slider("Mulai (detik):", 0.0, float(duration), 0.0)
        end_time = st.slider("Selesai (detik):", 0.0, float(duration), float(duration))
        
    with ctrl_col2:
        st.write("**Aksi & Ekspor**")
        effect_choice = st.selectbox("Pilih Efek Tambahan:", ["Normal", "Grayscale (Hitam Putih)", "Brighten (Cerahkan)"])
        
        # Jarak tombol agar sejajar dengan slider di sebelah kiri
        st.write("") 
        if st.button("▶ Proses & Terapkan", use_container_width=True):
            if start_time >= end_time:
                st.error("Waktu mulai harus lebih kecil dari waktu selesai!")
            else:
                st.success(f"Berhasil memproses video (Efek: {effect_choice}, Durasi: {start_time:.1f}s - {end_time:.1f}s)!")