import streamlit as st
import plotly.express as px
import pandas as pd

def render_page():
    st.title("📊 Dashboard Insight Bisnis CV ABC")
    
    if 'rfm_data' not in st.session_state or 'raw_data' not in st.session_state:
        st.warning("Data belum tersedia. Silakan upload dan proses data di menu pertama.")
        return
        
    rfm = st.session_state['rfm_data']
    raw_data = st.session_state['raw_data']
    
    # 1. KPI Cards
    st.subheader("Ringkasan Performa")
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Total Pelanggan Unik", f"{len(rfm)}")
    kpi2.metric("Total Transaksi", f"{rfm['Frequency'].sum()}")
    kpi3.metric("Total Pendapatan", f"Rp {rfm['Monetary'].sum():,.0f}")
    kpi4.metric("Rata-rata Pendapatan / Pelanggan", f"Rp {(rfm['Monetary'].sum()/len(rfm)):,.0f}")
    
    st.markdown("---")
    
    # 2. Visualisasi
    col1, col2 = st.columns(2)
    
    with col1:
        # Distribusi Segmentasi Pelanggan
        segmen_count = rfm['Segment'].value_counts().reset_index()
        segmen_count.columns = ['Segment', 'Jumlah']
        fig_pie = px.pie(segmen_count, values='Jumlah', names='Segment', 
                         title='Distribusi Segmen Pelanggan', hole=0.4)
        st.plotly_chart(fig_pie, use_container_width=True)
        
    with col2:
        # Segmen Pelanggan berdasarkan Pendapatan
        revenue_segment = rfm.groupby('Segment')['Monetary'].sum().reset_index()
        fig_bar = px.bar(revenue_segment, x='Segment', y='Monetary', 
                         title='Total Pendapatan per Segmen', color='Segment')
        st.plotly_chart(fig_bar, use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        # Tren Transaksi Perbulan
        raw_data['Bulan_Tahun'] = raw_data['tglPo'].dt.to_period('M').astype(str)
        trend_trx = raw_data.groupby('Bulan_Tahun').size().reset_index(name='Jumlah Transaksi')
        fig_line1 = px.line(trend_trx, x='Bulan_Tahun', y='Jumlah Transaksi', title='Tren Jumlah Transaksi Per Bulan')
        st.plotly_chart(fig_line1, use_container_width=True)
        
    with col4:
         # Tren Pendapatan Perbulan
         trend_rev = raw_data.groupby('Bulan_Tahun')['totalBayar'].sum().reset_index()
         fig_line2 = px.line(trend_rev, x='Bulan_Tahun', y='totalBayar', title='Tren Pendapatan Per Bulan')
         st.plotly_chart(fig_line2, use_container_width=True)

    # 3. Insight Otomatis
    st.subheader("💡 Insight Otomatis")
    segmen_terbesar = segmen_count.iloc[0]['Segment']
    segmen_terkecil = segmen_count.iloc[-1]['Segment']
    
    top_product = raw_data['produk'].value_counts().idxmax()
    
    st.write(f"- **Segmen Terbesar:** Mayoritas pelanggan Anda berada pada segmen **{segmen_terbesar}**.")
    st.write(f"- **Segmen Terkecil:** Segmen dengan jumlah pelanggan paling sedikit adalah **{segmen_terkecil}**.")
    st.write(f"- **Produk Paling Laris Global:** Secara keseluruhan, **{top_product}** adalah produk yang paling sering dibeli.")
    
    for index, row in revenue_segment.iterrows():
        st.write(f"- Segmen **{row['Segment']}** berkontribusi sebesar **Rp {row['Monetary']:,.0f}** terhadap total pendapatan.")
