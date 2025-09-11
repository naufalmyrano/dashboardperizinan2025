import os
import pandas as pd
import numpy as np
import streamlit as st

try:
    import plotly.express as px
except ModuleNotFoundError:
    st.set_page_config(page_title="Dependency Missing")
    st.error(
        "Module `plotly` tidak ditemukan.\n\n"
        "Jalankan: `python -m pip install plotly`\n"
        "Lalu jalankan ulang Streamlit."
    )
    st.stop()

# -------------------- Page Config --------------------
st.set_page_config(
    page_title="Dashboard Izin (Jan–Apr) • Streamlit",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -------------------- Helpers --------------------
REQUIRED_COLS = ["BULAN", "JUMLAH", "SEKTOR", "JENIS_IZIN"]
MONTH_ORDER_ID = [
    "JANUARI", "FEBRUARI", "MARET", "APRIL", "MEI", "JUNI",
    "JULI", "AGUSTUS", "SEPTEMBER", "OKTOBER", "NOVEMBER", "DESEMBER"
]
MONTH_ABBR_MAP = {
    "JAN": "JANUARI", "FEB": "FEBRUARI", "MAR": "MARET", "APR": "APRIL",
    "MEI": "MEI", "JUN": "JUNI", "JUL": "JULI",
    "AGU": "AGUSTUS", "AGS": "AGUSTUS", "AGT": "AGUSTUS", "AUG": "AGUSTUS",
    "SEP": "SEPTEMBER",
    "OKT": "OKTOBER",
    "NOV": "NOVEMBER",
    "DES": "DESEMBER", "DEC": "DESEMBER",
}

@st.cache_data(show_spinner=False)
def load_csv(file) -> pd.DataFrame:
    if file is None:
        default_path = "data_izin_jan_apr.csv"
        if os.path.exists(default_path):
            df = pd.read_csv(default_path)
        else:
            # fallback contoh data
            df = pd.DataFrame({
                "BULAN": ["JANUARI", "FEBRUARI", "MARET", "APRIL"] * 2,
                "JUMLAH": [120, 150, 200, 220, 80, 60, 90, 110],
                "SEKTOR": ["Industri"] * 4 + ["Perdagangan"] * 4,
                "JENIS_IZIN": ["Izin A"] * 4 + ["Izin B"] * 4,
            })
    else:
        df = pd.read_csv(file)

    # normalisasi nama kolom
    df.columns = [c.strip().upper() for c in df.columns]

    # validasi kolom wajib
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        st.error(f"Kolom wajib belum lengkap: {missing}. Harus ada {REQUIRED_COLS}.")
        st.stop()

    # tipe numerik
    df["JUMLAH"] = pd.to_numeric(df["JUMLAH"], errors="coerce").fillna(0).astype(int)

    # normalisasi bulan -> kapital, trim, map singkatan ke nama Indonesia penuh
    df["BULAN"] = df["BULAN"].astype(str).str.upper().str.strip()
    df["BULAN"] = df["BULAN"].replace(MONTH_ABBR_MAP)

    # set kategori berurutan
    df["BULAN"] = pd.Categorical(df["BULAN"], categories=MONTH_ORDER_ID, ordered=True)
    df = df.sort_values("BULAN")

    return df

def kpi_card(title, value, help_txt=None):
    st.metric(label=title, value=value, help=help_txt)

# -------------------- Sidebar --------------------
with st.sidebar:
    st.header("⚙️ Pengaturan")
    uploaded = st.file_uploader("Unggah data CSV (opsional)", type=["csv"], key="csv_uploader")

df = load_csv(uploaded)

with st.sidebar:
    st.markdown("### 🔎 Filter")

    sektor_opts = sorted(df["SEKTOR"].dropna().unique().tolist())
    jenis_opts  = sorted(df["JENIS_IZIN"].dropna().unique().tolist())
    # tampilkan bulan sesuai urutan kategori
    bulan_opts  = [m for m in MONTH_ORDER_ID if m in df["BULAN"].unique().tolist()]

    # --- SEKTOR ---
    with st.expander("Sektor", expanded=True):
        all_sektor = st.checkbox("Pilih Semua Sektor", value=True, key="all_sektor")
        sel_sektor = st.multiselect(
            "Cari / pilih sektor", sektor_opts,
            default=(sektor_opts if all_sektor else []),
            key="ms_sektor"
        )

    # --- JENIS IZIN ---
    with st.expander("Jenis Izin", expanded=True):
        all_jenis = st.checkbox("Pilih Semua Jenis Izin", value=True, key="all_jenis")
        sel_jenis = st.multiselect(
            "Cari / pilih jenis izin", jenis_opts,
            default=(jenis_opts if all_jenis else []),
            key="ms_jenis"
        )

    # --- BULAN ---
    with st.expander("Bulan", expanded=True):
        all_bulan = st.checkbox("Pilih Semua Bulan", value=True, key="all_bulan")
        sel_bulan = st.multiselect(
            "Cari / pilih bulan", bulan_opts,
            default=(bulan_opts if all_bulan else []),
            key="ms_bulan"
        )

    # --- RENTANG JUMLAH ---
    min_jml, max_jml = int(df["JUMLAH"].min()), int(df["JUMLAH"].max())
    rng = st.slider(
        "Rentang Jumlah",
        min_value=min_jml, max_value=max_jml,
        value=(min_jml, max_jml), key="rng_jml"
    )

    # --- TOP-N JENIS IZIN ---
    top_n = st.number_input(
        "Top-N Jenis Izin untuk Tren",
        min_value=1, max_value=20, value=5, step=1, key="topn"
    )
    st.caption("Tip: atur Top-N untuk fokus pada jenis izin terbanyak.")

# Terapkan filter
dff = df[
    df["SEKTOR"].isin(sel_sektor) &
    df["JENIS_IZIN"].isin(sel_jenis) &
    df["BULAN"].isin(sel_bulan) &
    df["JUMLAH"].between(rng[0], rng[1])
].copy()

# -------------------- Header --------------------
st.title("📊 Dashboard Izin Jan–Apr")

# -------------------- KPI --------------------
c1, c2, c3, c4 = st.columns(4)
with c1:
    kpi_card("Total Izin", f"{int(dff['JUMLAH'].sum()):,}".replace(",", "."))
with c2:
    kpi_card("Jumlah Sektor", dff["SEKTOR"].nunique())
with c3:
    kpi_card("Jenis Izin", dff["JENIS_IZIN"].nunique())
with c4:
    bulan_peak = (dff.groupby("BULAN")["JUMLAH"].sum().idxmax() if not dff.empty else "-")
    kpi_card("Puncak Bulan", str(bulan_peak))

st.divider()

# -------------------- Charts --------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Total per Bulan", "Sektor per Bulan", "Tren Top-N Jenis", "Komposisi Bulan", "Tabel & Unduh"
])

with tab1:
    st.subheader("Total Izin Terbit per Bulan")
    g1 = dff.groupby("BULAN", as_index=False)["JUMLAH"].sum()
    fig1 = px.bar(
        g1, x="BULAN", y="JUMLAH",
        text="JUMLAH",
        labels={"JUMLAH": "Jumlah Izin", "BULAN": "Bulan"},
    )
    fig1.update_traces(textposition="outside")
    fig1.update_layout(margin=dict(t=10, r=10, b=10, l=10))
    st.plotly_chart(fig1, use_container_width=True)

with tab2:
    st.subheader("Perbandingan Sektor per Bulan")
    barmode = st.radio("Mode batang", ["group", "stack"], horizontal=True, key="barmode")
    fig2 = px.bar(
        dff, x="BULAN", y="JUMLAH", color="SEKTOR",
        barmode=barmode,
        labels={"JUMLAH": "Jumlah Izin", "BULAN": "Bulan", "SEKTOR": "Sektor"},
    )
    st.plotly_chart(fig2, use_container_width=True)

with tab3:
    st.subheader("Tren Top-N Jenis Izin")
    top_izin = dff.groupby("JENIS_IZIN")["JUMLAH"].sum().nlargest(int(top_n)).index
    df_top = dff[dff["JENIS_IZIN"].isin(top_izin)]
    fig3 = px.line(
        df_top, x="BULAN", y="JUMLAH", color="JENIS_IZIN", markers=True,
        labels={"JUMLAH": "Jumlah Izin", "BULAN": "Bulan", "JENIS_IZIN": "Jenis Izin"},
    )
    st.plotly_chart(fig3, use_container_width=True)

with tab4:
    st.subheader("Komposisi Jenis Izin per Bulan (Pie)")
    bulan_for_pie = st.selectbox(
        "Pilih Bulan", options=[m for m in MONTH_ORDER_ID if m in dff["BULAN"].unique()],
        key="pie_month"
    )
    dpie = dff[dff["BULAN"] == bulan_for_pie].groupby("JENIS_IZIN", as_index=False)["JUMLAH"].sum()
    fig4 = px.pie(dpie, names="JENIS_IZIN", values="JUMLAH", hole=0.35)
    st.plotly_chart(fig4, use_container_width=True)

with tab5:
    st.subheader("Data Terfilter")
    st.dataframe(dff, use_container_width=True, hide_index=True)
    csv = dff.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Unduh CSV (filter saat ini)", data=csv,
                       file_name="data_filter.csv", mime="text/csv")

st.divider()
with st.expander("ℹ️ Cara Pakai"):
    st.markdown("""
- Unggah file **CSV** dengan kolom: `BULAN, JUMLAH, SEKTOR, JENIS_IZIN`.  
- Gunakan filter di sidebar.  
- Tab **Tren Top-N** otomatis memilih N jenis izin teratas.  
- Jika tidak unggah CSV, aplikasi pakai contoh data.
""")

