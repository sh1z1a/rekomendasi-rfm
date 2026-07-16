import streamlit as st
import pandas as pd
import treatment

def get_segment_recommendation(segment, top_products):
    """
    Fungsi Rule-Based Filtering berdasarkan Segmentasi Pelanggan (K=3):
    - Loyal Customer -> Produk premium / lanjutan
    - Prospect Customer -> Produk dasar / populer
    - Pasif Customer -> Produk promo / reaktivasi
    """
    # Memetakan tipe produk berdasarkan kata kunci nama produk (Adaptif terhadap nama produk riil)
    premium_products = [p for p in top_products if any(keyword in p.lower() for keyword in ['premium', 'lanjutan', 'exclusive', 'mahal', 'level up'])]
    basic_products = [p for p in top_products if any(keyword in p.lower() for keyword in ['dasar', 'basic', 'starter', 'hemat'])]
    promo_products = [p for p in top_products if any(keyword in p.lower() for keyword in ['promo', 'diskon', 'sale', 'reaktivasi', 'bundling'])]
    
    # Fallback aman jika kata kunci tidak cocok dengan penamaan produk CV ABC
    if not premium_products:
        premium_products = top_products[:2]
    if not basic_products:
        basic_products = top_products[1:3]
    if not promo_products:
        promo_products = top_products[-2:]

    if segment == 'Loyal Customer':
        return premium_products[:3], "Pelanggan ini sangat aktif berbelanja dan memiliki nilai transaksi yang tinggi. Tawarkan produk eksklusif/premium untuk meningkatkan kepuasan mereka."
    elif segment == 'Prospect Customer':
        return basic_products[:3], "Pelanggan baru atau potensial yang masih dalam tahap awal berinteraksi. Tawarkan produk dasar dengan harga kompetitif agar mereka terbiasa berbelanja."
    elif segment == 'Pasif Customer':
        return promo_products[:3], "Pelanggan sudah lama tidak melakukan pemesanan. Tawarkan program promo atau paket bundling khusus sebagai strategi reaktivasi."
    else:
        # Fallback global jika segmen tidak terdefinisi
        return top_products[:3], "Tawarkan produk terlaris secara umum kepada pelanggan."


def render_page(top_products, periodic_recommendations, segment_mapping=None, customer_history_df=None):
    st.title("🎯 Sistem Rekomendasi Produk CV ABC")
    st.markdown("Halaman ini menyediakan dua skema rekomendasi: **Rekomendasi Personal** berbasis segmen RFM, dan **Rekomendasi Periodik** dinamis berbasis siklus waktu tren pasar.")
    
    # Validasi ketersediaan data transaksi di session state
    if 'rfm_data' not in st.session_state:
        st.warning("Data transaksi pelanggan belum tersedia. Silakan unggah berkas transaksi di menu 'Data & Pemodelan AI' terlebih dahulu.")
        return
        
    rfm = st.session_state['rfm_data']
    
    # Membuat Tab untuk memisahkan kedua model rekomendasi agar lebih rapi
    tab1, tab2 = st.tabs(["👤 Rekomendasi Personal Pelanggan", "📅 Rekomendasi Tren Periodik"])
    
    # --- TAB 1: REKOMENDASI PERSONAL PELANGGAN ---
    with tab1:
        st.subheader("🔍 Pencarian & Filter Pelanggan")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            seg_filter = st.selectbox(
                "Saring Berdasarkan Segmen:",
                ["Semua Segmen"] + list(rfm['Segment'].dropna().unique()),
                key="seg_filter"
            )
        with col2:
            segment_filtered_df = rfm.copy()
            if seg_filter != "Semua Segmen":
                segment_filtered_df = segment_filtered_df[segment_filtered_df['Segment'] == seg_filter]

            available_clusters = sorted(segment_filtered_df['Cluster'].dropna().astype(int).unique().tolist())
            cluster_options = ["Semua Klaster"] + [str(c) for c in available_clusters]

            if st.session_state.get('last_segment_filter') != seg_filter:
                if seg_filter == "Semua Segmen":
                    st.session_state['clus_filter'] = "Semua Klaster"
                else:
                    default_cluster = "Semua Klaster"
                    if available_clusters:
                        cluster_mode = segment_filtered_df['Cluster'].mode()
                        if not cluster_mode.empty:
                            default_cluster = str(int(cluster_mode.iloc[0]))
                    st.session_state['clus_filter'] = default_cluster
                st.session_state['last_segment_filter'] = seg_filter

            if st.session_state.get('clus_filter') not in cluster_options:
                st.session_state['clus_filter'] = cluster_options[1] if len(cluster_options) > 1 else cluster_options[0]

            clus_filter = st.selectbox(
                "Saring Berdasarkan Klaster:",
                cluster_options,
                key="clus_filter"
            )
        with col3:
            search_id = st.text_input("Cari ID Marketing:")
            
        # Menerapkan filter pencarian
        filtered_df = rfm.copy()
        if seg_filter != "Semua Segmen":
            filtered_df = filtered_df[filtered_df['Segment'] == seg_filter]
        if clus_filter != "Semua Klaster":
            filtered_df = filtered_df[filtered_df['Cluster'] == int(clus_filter)]
        if search_id:
            if 'mrkt_id' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['mrkt_id'].fillna('').astype(str).str.contains(search_id, case=False, na=False)]
            else:
                filtered_df = filtered_df[filtered_df.index.astype(str).str.contains(search_id)]
            
        # Tampilkan kolom mrkt_id jika tersedia dan reset index supaya klienId terlihat jelas
        display_df = filtered_df.copy().reset_index().rename(columns={'index': 'klienId'})
        if 'mrkt_id' in display_df.columns:
            display_df = display_df.rename(columns={'mrkt_id': 'mrkt id'})

        st.dataframe(display_df, use_container_width=True)
        
        st.markdown("---")
        
        if not filtered_df.empty:
            detail_segment_filter = st.selectbox(
                "Filter Segmen Pelanggan untuk Rekomendasi Detail:",
                ["Semua Segmen"] + list(rfm['Segment'].unique())
            )

            detail_df = filtered_df
            if detail_segment_filter != "Semua Segmen":
                detail_df = detail_df[detail_df['Segment'] == detail_segment_filter]

            if detail_df.empty:
                st.warning("Tidak ada pelanggan pada segmen yang dipilih sesuai filter saat ini.")
            else:
                selected_client_id = detail_df.index[0]
                customer_profile = detail_df.iloc[0]
                
                st.markdown(f"### 📋 Profil Pelanggan: `{selected_client_id}`")
                
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    st.metric("Recency (Hari Terakhir Transaksi)", f"{int(customer_profile['Recency'])} hari")
                with c2:
                    st.metric("Frequency (Jumlah Transaksi)", f"{int(customer_profile['Frequency'])} kali")
                with c3:
                    st.metric("Monetary (Total Belanja)", f"Rp {customer_profile['Monetary']:,.0f}")
                with c4:
                    # Memberikan warna segmen yang konsisten
                    seg_label = customer_profile['Segment']
                    if seg_label == 'Loyal Customer':
                        st.success(seg_label)
                    elif seg_label == 'Prospect Customer':
                        st.info(seg_label)
                    else:
                        st.warning(seg_label)

                mrkt_value = customer_profile['mrkt_id'] if 'mrkt_id' in customer_profile.index else None
                if pd.notna(mrkt_value) and str(mrkt_value) != 'nan':
                    st.caption(f"ID Marketing: {mrkt_value}")
                else:
                    st.caption("ID Marketing: Tidak tersedia")
                        
                # Menghitung rekomendasi personal berbasis aturan (rule-based)
                rekomen_personal, alasan_personal = get_segment_recommendation(customer_profile['Segment'], top_products)

                # Dapatkan rekomendasi treatment dan produk yang dipersonalisasi
                try:
                    personalized = treatment.get_personalized_treatment_and_recommendations(
                        selected_client_id,
                        rfm,
                        segment_mapping,
                        periodic_recommendations,
                        top_products,
                        customer_history_df
                    )
                except Exception:
                    personalized = None
                
                st.markdown("#### 💡 Rekomendasi Produk Personal Terpilih")
                st.info(f"**Alasan Rekomendasi:** {alasan_personal}")
                
                cols_prod = st.columns(len(rekomen_personal))
                for idx, prod in enumerate(rekomen_personal):
                    with cols_prod[idx]:
                        st.markdown(f"""
                        <div style="background-color: white; padding: 20px; border-radius: 8px; border-left: 5px solid #1e3a8a; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                            <span style="font-size: 24px;">📦</span>
                            <h4 style="margin: 10px 0 5px 0; color: #1e3a8a;">Rekomendasi #{idx+1}</h4>
                            <p style="font-weight: bold; font-size: 16px; margin: 0;">{prod}</p>
                        </div>
                        """, unsafe_allow_html=True)

                # Tampilkan rekomendasi treatment jika tersedia
                if personalized:
                    st.markdown("---")
                    st.markdown("#### 🩺 Rekomendasi Treatment & Strategi Personalisasi")
                    st.markdown(f"**Segmen:** {personalized.get('Segment', 'N/A')}")
                    st.markdown(f"**Tujuan Treatment:** {personalized.get('Treatment_Tujuan', '')}")
                    st.markdown("**Strategi yang Direkomendasikan:**")
                    for i, s in enumerate(personalized.get('Treatment_Strategi', [])):
                        st.write(f"{i+1}. {s}")
                    st.markdown(f"**Indikator Keberhasilan:** {personalized.get('Treatment_Indikator', '')}")

                    # Produk rekomendasi personal gabungan
                    st.markdown("**Rekomendasi Produk (Periodic & Global Top):**")
                    per = personalized.get('Rekomendasi_Produk', {}).get('Periodic', [])
                    gtop = personalized.get('Rekomendasi_Produk', {}).get('Global_Top', [])
                    st.write("- Periodik Terbaru: " + (", ".join(per) if per else "(tidak ada)"))
                    st.write("- Top Global: " + (", ".join(gtop) if gtop else "(tidak ada)"))
                    if personalized.get('Histori_Belanja'):
                        st.markdown("**Histori Belanja (singkat):**")
                        st.write(", ".join(personalized.get('Histori_Belanja')))
        else:
            st.warning("Tidak ditemukan data pelanggan yang cocok dengan parameter filter Anda.")
            
    # --- TAB 2: REKOMENDASI TREN PERIODIK (MODEL BARU) ---
    with tab2:
        st.subheader("📅 Model Rekomendasi Dinamis Berbasis Waktu")
        st.markdown("""
            Sistem ini membaca model dinamis `periodic_recommendations.pkl` untuk merumuskan tren produk terlaris di setiap kuartal/periode tertentu. 
            Hal ini membantu manajemen CV ABC mengantisipasi stok inventori musiman secara berkala.
        """)
        
        # Konversi dictionary periodic_recommendations ke bentuk list yang ramah dibaca pengguna
        periodic_periods = list(periodic_recommendations.keys())
        
        col_sel1, col_sel2 = st.columns([1, 2])
        with col_sel1:
            selected_period = st.selectbox("Pilih Periode Siklus Rekomendasi:", periodic_periods)
            
        period_data = periodic_recommendations[selected_period]
        
        with col_sel2:
            st.markdown(f"""
                <div style="background-color: #f1f5f9; padding: 15px; border-radius: 8px; margin-top: 10px;">
                    <p style="margin: 0; color: #475569; font-weight: bold;">Analisis Acuan Data:</p>
                    <p style="margin: 0; font-size: 18px; color: #0f172a;">Rekomendasi untuk siklus ini diambil berdasarkan performa transaksi terlaris pada bulan: <strong>{period_data['based_on_month']}</strong></p>
                </div>
            """, unsafe_allow_html=True)
            
        st.markdown("#### 🚀 Rekomendasi Produk Terpopuler untuk Siklus Ini:")
        
        recommended_products = period_data['recommended_products']
        
        if recommended_products:
            cols_period = st.columns(len(recommended_products))
            for idx, prod in enumerate(recommended_products):
                with cols_period[idx]:
                    st.markdown(f"""
                    <div style="background-color: #ecfdf5; padding: 20px; border-radius: 8px; border-top: 4px solid #10b981; box-shadow: 0 4px 6px rgba(0,0,0,0.05); text-align: center;">
                        <span style="font-size: 30px;">🌟</span>
                        <h4 style="margin: 10px 0 5px 0; color: #065f46;">Trending #{idx+1}</h4>
                        <p style="font-weight: bold; font-size: 16px; margin: 0; color: #0f172a;">{prod}</p>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("Tidak ada transaksi acuan pada bulan sebelumnya yang dapat dijadikan dasar rekomendasi produk untuk siklus ini.")
        
        st.markdown("  ")
        st.info(f""" **Penjelasan Detail Produk Terpopuler :** 
                Terkait produk terpopuler  diatas bisa berubah sewaktu-waktu menyesuaikan kondisi di lapangan. 
                Seperti pada trending #3 yang populer tidak hanya produk TAX UPDATE, tetapi mencakup produk PPh Pasal 21, EXCEL PPh 21 maupun Program Excel PPh 21.
                Perlu diingat, Sistem rekomendasi dapat dijadikan acuan bagi pihak manajemen CV ABC dalam menentukan tema jasa konsultasi pajak yang sedang trending ke depannya.
                Sistem rekomendasi TIDAK MENGGANTIKAN KEPUTUSAN FINAL dalam menentukan produk yang akan dibuka programnya pada periode tertentu.
                """)

        st.markdown("---")
        st.markdown("### 📊 Ringkasan Jadwal Siklus Rekomendasi")
        
        # Menyajikan data berkas .pkl ke dalam tabel interaktif di Streamlit
        periodic_table_data = []
        for period, data in periodic_recommendations.items():
            periodic_table_data.append({
                "Periode Mulai": period,
                "Bulan Analisis Acuan": data['based_on_month'],
                "Rekomendasi Produk Utama": ", ".join(data['recommended_products']) if data['recommended_products'] else "Data Kosong"
            })
            
        st.table(pd.DataFrame(periodic_table_data))