import pandas as pd


treatment_strategies = {
    'Loyal Customer': {
        'strategi': [
            "Program Apresiasi/Reward: Berikan poin loyalitas, diskon eksklusif untuk layanan premium (misal: 'Strategic Tax Planning', 'Financial Advisory').",
            "Akses VIP: Tawarkan akses awal ke workshop/seminar baru atau konsultasi khusus.",
            "Survei Kepuasan & Testimonial: Libatkan mereka untuk feedback dan testimonial positif.",
            "Rekomendasi Produk (Upselling/Cross-selling): Tawarkan produk dengan nilai tinggi atau baru dari daftar rekomendasi periodik/global yang sesuai dengan histori belanja mereka."
        ],
        'tujuan': "Mempertahankan loyalitas, mendorong upselling dan cross-selling produk/jasa konsultasi premium.",
        'indikator_keberhasilan': "Tingkat churn rendah, peningkatan nilai transaksi rata-rata (ARPU), partisipasi dalam program loyalitas, referral. Jumlah pembelian jasa premium meningkat."
    },
    'Prospect Customer': {
        'strategi': [
            "Penawaran Paket Bundling: Tawarkan paket jasa yang relevan (misal: PPh Badan + Jasa Laporan Keuangan) dengan harga menarik.",
            "Diskon Terbatas: Berikan diskon khusus untuk transaksi berikutnya atau layanan tertentu dalam periode waktu terbatas.",
            "Edukasi Berbasis Kebutuhan: Kirimkan newsletter informatif tentang pentingnya kepatuhan pajak atau manajemen keuangan yang relevan dengan bisnis mereka.",
            "Reminder Layanan: Ingatkan tentang layanan yang mungkin relevan berdasarkan musim (misal: 'Tax Update' menjelang SPT Tahunan) atau histori serupa.",
            "Rekomendasi Produk: Tawarkan produk yang populer secara global atau sedang tren di periode ini untuk menarik minat mereka."
        ],
        'tujuan': "Mendorong peningkatan frekuensi dan nilai transaksi, mengaktifkan kembali minat.",
        'indikator_keberhasilan': "Peningkatan jumlah transaksi, peningkatan nilai AOV (Average Order Value), konversi ke segmen Loyal. Peningkatan engagement dengan email atau promosi."
    },
    'Pasif Customer': {
        'strategi': [
            "Diskon Re-aktivasi: Tawarkan diskon atau voucher khusus (misal: diskon 10% untuk jasa pertama setelah 6 bulan tidak aktif).",
            "Survei Ketidakaktifan: Kirim survei singkat via email untuk memahami alasan mereka tidak aktif lagi.",
            "Informasi Update Regulasi: Kirimkan informasi penting terkait update regulasi pajak atau berita bisnis relevan (tanpa hard-selling).",
            "Konsultasi Gratis Singkat: Tawarkan sesi konsultasi gratis singkat untuk mengidentifikasi kebutuhan mereka dan menarik kembali minat.",
            "Rekomendasi Produk: Tawarkan produk yang paling basic atau sering dicari untuk memancing mereka kembali bertransaksi."
        ],
        'tujuan': "Mengaktifkan kembali pelanggan yang sudah lama tidak aktif, mendorong transaksi pertama setelah vakum.",
        'indikator_keberhasilan': "Tingkat re-aktivasi, transaksi pertama setelah periode pasif, peningkatan engagement (membuka email, klik tautan)."
    }
}


def get_personalized_treatment_and_recommendations(
    klien_id,
    rfm_df,
    segment_mapping,
    periodic_recs_dict,
    top_products_global_list,
    customer_history_df=None
):
    result = {
        'klienId': klien_id,
        'mrktId': 'Tidak Ditemukan',
        'Segment': 'Tidak Ditemukan',
        'RFM_Metrics': None,
        'Treatment_Tujuan': 'Tidak Ditemukan',
        'Treatment_Strategi': [],
        'Treatment_Indikator': 'Tidak Ditemukan',
        'Rekomendasi_Produk': {'Periodic': [], 'Global_Top': []},
        'Histori_Belanja': []
    }

    # Cari data klien di rfm_df (index asumsi = klienId)
    if klien_id in rfm_df.index:
        client_data = rfm_df.loc[klien_id]
        # jika ada banyak baris, ambil first
        if isinstance(client_data, pd.DataFrame):
            client_data = client_data.iloc[0]

        # mrkt id bisa bernama 'mrkt_id' atau 'mrktid' atau 'mrkt'
        mrkt_cols = [c for c in rfm_df.columns if 'mrkt' in c.lower()]
        mrkt_val = None
        if mrkt_cols:
            try:
                mrkt_val = client_data[mrkt_cols[0]]
            except Exception:
                mrkt_val = None

        result['mrktId'] = mrkt_val if mrkt_val is not None else 'Tidak Ditemukan'
        result['Segment'] = client_data.get('Segment', 'Tidak Ditemukan')
        result['RFM_Metrics'] = {
            'Recency': client_data.get('Recency'),
            'Frequency': client_data.get('Frequency'),
            'Monetary': client_data.get('Monetary')
        }

        # Ambil strategi treatment dari dictionary
        if result['Segment'] in treatment_strategies:
            seg_info = treatment_strategies[result['Segment']]
            result['Treatment_Tujuan'] = seg_info['tujuan']
            result['Treatment_Strategi'] = seg_info['strategi']
            result['Treatment_Indikator'] = seg_info['indikator_keberhasilan']

    # Rekomendasi produk periodik (ambil periode terbaru jika ada)
    latest_period = None
    try:
        if periodic_recs_dict:
            latest_period = sorted(periodic_recs_dict.keys(), reverse=True)[0]
    except Exception:
        latest_period = None

    if latest_period and periodic_recs_dict.get(latest_period):
        recs = periodic_recs_dict[latest_period].get('recommended_products', [])
        result['Rekomendasi_Produk']['Periodic'] = recs

    # Global top-N
    try:
        result['Rekomendasi_Produk']['Global_Top'] = list(top_products_global_list)[:3]
    except Exception:
        result['Rekomendasi_Produk']['Global_Top'] = []

    # Histori belanja jika tersedia
    if customer_history_df is not None:
        try:
            hist = customer_history_df[customer_history_df['klienId'] == klien_id]
            if not hist.empty:
                # jika ada kolom 'produk' ambil daftar produk dari semua transaksi terakhir
                if 'produk' in hist.columns:
                    # gabungkan unique produk
                    products = hist['produk'].explode() if hist['produk'].apply(lambda x: isinstance(x, (list, tuple))).any() else hist['produk']
                    result['Histori_Belanja'] = list(pd.Series(products.tolist()).dropna().astype(str).unique())
                else:
                    result['Histori_Belanja'] = []
        except Exception:
            result['Histori_Belanja'] = []

    return result
