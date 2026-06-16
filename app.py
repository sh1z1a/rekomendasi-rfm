import streamlit as st
import pandas as pd
import joblib
from datetime import timedelta
import dashboard
import recommendation

# Konfigurasi Halaman Streamlit
st.set_page_config(page_title="Sistem Rekomendasi Produk CV ABC", page_icon="🛒", layout="wide")

# Tambahkan caching untuk load model agar lebih cepat
@st.cache_resource
def load_models():
    try:
        scaler = joblib.load('models/scaler.pkl')
        kmeans = joblib.load('models/kmeans.pkl')
        segment_mapping = joblib.load('models/segment_mapping.pkl')
        top_products = joblib.load('models/top_products.pkl')
        periodic_recommendations = joblib.load('models/periodic_recommendations.pkl')
        return scaler, kmeans, segment_mapping, top_products, periodic_recommendations
    except FileNotFoundError:
        st.error("Model belum dilatih atau file .pkl tidak ditemukan di folder 'models'. Silakan jalankan kode Colab terlebih dahulu.")
        st.stop()

# Load semua model AI
scaler, kmeans, segment_mapping, top_products, periodic_recommendations = load_models()

# Sidebar Navigasi Modular
st.sidebar.title("Navigasi Sistem")
menu = st.sidebar.radio("Pilih Menu:", ["Data & Pemodelan AI", "Sistem Rekomendasi", "Insight Bisnis"])

if menu == "Data & Pemodelan AI":
    st.title("🧮 Pemrosesan Data & Prediksi Segmen")
    st.markdown("Fase ini digunakan untuk mengunggah data transaksi baru, menghitung RFM, dan melakukan prediksi segmen menggunakan K-Means tanpa melatih ulang model.")
    
    uploaded_file = st.file_uploader("Unggah Dataset Transaksi Pelanggan (CSV atau Excel)", type=['csv', 'xls', 'xlsx'])
    
    if uploaded_file is not None:
        try:
            fname = uploaded_file.name.lower()
            if fname.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            elif fname.endswith(('.xls', '.xlsx')):
                df = pd.read_excel(uploaded_file)
            else:
                st.error("Format file tidak didukung. Unggah file CSV atau Excel (xls/xlsx).")
                df = None

            if df is not None:
                st.success("Data berhasil dimuat!")

                with st.expander("🔍 Preview Dataset Awal"):
                    st.dataframe(df.head())
            
            # Data Cleaning (Asumsi kolom: tglPo, klienId, totalBayar, produk)
            if all(col in df.columns for col in ['tglPo', 'klienId', 'totalBayar']):
                df_clean = df.copy()
                df_clean['tglPo'] = pd.to_datetime(df_clean['tglPo'])
                df_clean = df_clean.dropna().drop_duplicates()

                # Normalisasi tipe `klienId` — ubah ke numeric, dan ke int jika semua nilai bilangan bulat
                df_clean['klienId'] = pd.to_numeric(df_clean['klienId'], errors='coerce')
                if not df_clean['klienId'].isna().any():
                    try:
                        if df_clean['klienId'].dropna().apply(float.is_integer).all():
                            df_clean['klienId'] = df_clean['klienId'].astype(int)
                    except Exception:
                        pass

                # Filter tahun minimal (mis. hanya gunakan data tahun 2022 ke atas)
                min_year = 2022
                before_count = len(df_clean)
                df_clean = df_clean[df_clean['tglPo'].dt.year >= min_year]
                after_count = len(df_clean)
                if df_clean.empty:
                    st.error(f"Tidak ada transaksi dari tahun {min_year} ke atas setelah filtering. Dataset asli memiliki {before_count} baris, semua dihapus oleh filter tahun.")
                    st.stop()

                # Perhitungan RFM
                st.subheader("⚡ Perhitungan RFM & Prediksi Segmen")
                tanggal_analisis = df_clean['tglPo'].max() + timedelta(days=1)
                
                rfm = df_clean.groupby('klienId').agg({
                    'tglPo': lambda x: (tanggal_analisis - x.max()).days,
                    'klienId': 'count',
                    'totalBayar': 'sum'
                }).rename(columns={'tglPo': 'Recency', 'klienId': 'Frequency', 'totalBayar': 'Monetary'})
                
                # Prediksi menggunakan Load Model (Bukan Training Ulang)
                rfm_scaled = scaler.transform(rfm)
                rfm['Cluster'] = kmeans.predict(rfm_scaled)
                rfm['Segment'] = rfm['Cluster'].map(segment_mapping)
                # Jika dataset sumber memiliki kolom market / mrkt id, simpan pada ringkasan RFM
                mrkt_col = None
                for c in df_clean.columns:
                    if 'mrkt' in c.lower() or 'market' in c.lower():
                        mrkt_col = c
                        break
                if mrkt_col:
                    try:
                        mapping = df_clean.dropna(subset=[mrkt_col]).drop_duplicates(subset=['klienId']).set_index('klienId')[mrkt_col].to_dict()
                        rfm['mrkt_id'] = rfm.index.map(mapping)
                    except Exception:
                        rfm['mrkt_id'] = None
                
                # Simpan ke session state agar bisa diakses di halaman lain
                st.session_state['rfm_data'] = rfm
                st.session_state['raw_data'] = df_clean
                
                st.dataframe(rfm.style.background_gradient(cmap='Blues'))
                st.success("Segmen pelanggan berhasil dikalkulasi!")
                
            else:
                st.error("Dataset harus memiliki kolom minimal: 'tglPo', 'klienId', 'totalBayar', 'produk'.")
                
        except Exception as e:
            st.error(f"Terjadi kesalahan saat membaca data: {e}")
    else:
        st.info("Silakan unggah dataset untuk memulai.")

elif menu == "Sistem Rekomendasi":
    # Pass segment mapping and raw customer history data to recommendation page
    raw_data = st.session_state.get('raw_data', None)
    recommendation.render_page(top_products, periodic_recommendations, segment_mapping, raw_data)
    
elif menu == "Insight Bisnis":
    dashboard.render_page()