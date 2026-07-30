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
    page_title="Dashboard Izin (Multi-Kategori) • Streamlit",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -------------------- Helpers --------------------
REQUIRED_COLS = ["SEKTOR", "JENIS IZIN", "KATEGORI", "BULAN", "JUMLAH"]
MONTH_ORDER_ID = [
    "JANUARI", "FEBRUARI", "MARET", "APRIL", "MEI", "JUNI",
    "JULI", "AGUSTUS", "SEPTEMBER", "OKTOBER", "NOVEMBER", "DESEMBER"
]

@st.cache_data(show_spinner=False)
def load_data(file) -> pd.DataFrame:
    if file is None:
        default_path = "Rekap Izin final.xlsx"
        if os.path.exists(default_path):
            df = pd.read_excel(default_path)
        else:
            st.error("Data tidak ditemukan. Unggah file Excel.")
            st.stop()
    else:
        if file.name.endswith(".csv"):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)

    df.columns = [c.strip().upper() for c in df.columns]
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        st.error(f"Kolom wajib belum lengkap: {missing}. Harus ada {REQUIRED_COLS}.")
        st.stop()

    df = df[df["BULAN"].str.upper() != "JUMLAH"].copy()
    df["BULAN"] = df["BULAN"].astype(str).str.upper().str.strip()
    df["BULAN"] = pd.Categorical(df["BULAN"], categories=MONTH_ORDER_ID, ordered=True)
    df = df.sort_values("BULAN")
    df["JUMLAH"] = pd.to_numeric(df["JUMLAH"], errors="coerce").fillna(0).astype(int)
    return df

def kpi_card(title, value, help_txt=None):
    st.metric(label=title, value=value, help=help_txt)

# -------------------- Sidebar --------------------
# -------------------- Load Data --------------------
@st.cache_data(show_spinner=False)
def load_data() -> pd.DataFrame:
    default_path = "Rekap Izin final.xlsx"

    if not os.path.exists(default_path):
        st.error(f"File '{default_path}' tidak ditemukan.")
        st.stop()

    df = pd.read_excel(default_path)

    # Normalisasi nama kolom
    df.columns = df.columns.astype(str).str.strip().str.upper()

    # Validasi kolom wajib
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        st.error(f"Kolom wajib belum lengkap: {missing}. Harus ada {REQUIRED_COLS}.")
        st.stop()

    # Bersihkan data
    df = df[df["BULAN"].astype(str).str.upper() != "JUMLAH"].copy()

    df["BULAN"] = (
        df["BULAN"]
        .astype(str)
        .str.upper()
        .str.strip()
    )

    df["BULAN"] = pd.Categorical(
        df["BULAN"],
        categories=MONTH_ORDER_ID,
        ordered=True
    )

    df = df.sort_values("BULAN")

    df["JUMLAH"] = (
        pd.to_numeric(df["JUMLAH"], errors="coerce")
        .fillna(0)
        .astype(int)
    )

    return df


# -------------------- Sidebar --------------------
with st.sidebar:
    st.header("⚙️ Pengaturan")

# Load data
df = load_data()

with st.sidebar:
    st.markdown("### 🔎 Filter")

    sektor_opts = sorted(df["SEKTOR"].dropna().unique().tolist())
    jenis_opts  = sorted(df["JENIS IZIN"].dropna().unique().tolist())
    bulan_opts  = [m for m in MONTH_ORDER_ID if m in df["BULAN"].unique().tolist()]

    with st.expander("Sektor", expanded=True):
        all_sektor = st.checkbox("Pilih Semua Sektor", value=True, key="all_sektor")
        sel_sektor = st.multiselect("Cari / pilih sektor", sektor_opts, default=(sektor_opts if all_sektor else []), key="ms_sektor")

    with st.expander("Jenis Izin", expanded=True):
        all_jenis = st.checkbox("Pilih Semua Jenis Izin", value=True, key="all_jenis")
        sel_jenis = st.multiselect("Cari / pilih jenis izin", jenis_opts, default=(jenis_opts if all_jenis else []), key="ms_jenis")

    with st.expander("Bulan", expanded=True):
        all_bulan = st.checkbox("Pilih Semua Bulan", value=True, key="all_bulan")
        sel_bulan = st.multiselect("Cari / pilih bulan", bulan_opts, default=(bulan_opts if all_bulan else []), key="ms_bulan")

    min_jml, max_jml = int(df["JUMLAH"].min()), int(df["JUMLAH"].max())
    rng = st.slider("Rentang Jumlah", min_value=min_jml, max_value=max_jml, value=(min_jml, max_jml), key="rng_jml")

    top_n = st.number_input("Top-N Jenis Izin untuk Tren", min_value=1, max_value=20, value=5, step=1, key="topn")
    st.caption("Tip: atur Top-N untuk fokus pada jenis izin terbanyak.")

# -------------------- Main Page --------------------
st.title("📊 Dashboard Izin Multi-Kategori")
# Urutan custom kategori
kategori_order = [
    "JUMLAH IZIN TERBIT",
    "JUMLAH BERKAS DICABUT",
    "JUMLAH PENOLAKAN",
    "JUMLAH IZIN SUKSES"
]

# Filter kategori agar hanya yang ada di data
kategori_opts = [k for k in kategori_order if k in df["KATEGORI"].unique()]

# Radio button dengan urutan custom
kategori_pilih = st.radio(
    "Pilih Kategori",
    kategori_opts,
    horizontal=True,
    key="kategori_pilih"
)

dff = df[
    (df["KATEGORI"] == kategori_pilih) &
    (df["SEKTOR"].isin(sel_sektor)) &
    (df["JENIS IZIN"].isin(sel_jenis)) &
    (df["BULAN"].isin(sel_bulan)) &
    (df["JUMLAH"].between(rng[0], rng[1]))
].copy()

st.caption(f"Kategori aktif: **{kategori_pilih}**")

# -------------------- KPI --------------------
c1, c2, c3, c4 = st.columns(4)
with c1:
    kpi_card("Total", f"{int(dff['JUMLAH'].sum()):,}".replace(",", "."))
with c2:
    kpi_card("Jumlah Sektor", dff["SEKTOR"].nunique())
with c3:
    kpi_card("Jenis Izin", dff["JENIS IZIN"].nunique())
with c4:
    bulan_peak = (dff.groupby("BULAN")["JUMLAH"].sum().idxmax() if not dff.empty else "-")
    kpi_card("Puncak Bulan", str(bulan_peak))

st.divider()

# -------------------- Charts --------------------
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Total per Bulan", "Sektor per Bulan", "Tren Top-N Jenis", "Komposisi Bulan", "Perbandingan Kategori", "Tabel & Unduh"
])

with tab1:
    st.subheader("Total per Bulan")
    g1 = dff.groupby("BULAN", as_index=False)["JUMLAH"].sum()

    # ---------------- Analisis Otomatis (pindah ke atas) ----------------
    if len(g1) >= 2:
        g1_nonzero = g1[g1["JUMLAH"] > 0]
        if len(g1_nonzero) >= 2:
            last_month = g1_nonzero.iloc[-1]
            prev_month = g1_nonzero.iloc[-2]

            perubahan = last_month["JUMLAH"] - prev_month["JUMLAH"]
            persen = (perubahan / prev_month["JUMLAH"] * 100) if prev_month["JUMLAH"] > 0 else None

            if perubahan > 0:
                st.success(
                    f"📊 Bulan **{last_month['BULAN']}** mengalami peningkatan jumlah izin sebesar "
                    f"**{perubahan:,}** ({persen:.1f}% dibanding bulan {prev_month['BULAN']})."
                )
            elif perubahan < 0:
                st.warning(
                    f"📉 Bulan **{last_month['BULAN']}** mengalami penurunan jumlah izin sebesar "
                    f"**{abs(perubahan):,}** ({abs(persen):.1f}% dibanding bulan {prev_month['BULAN']})."
                )
            else:
                st.info(
                    f"➡️ Jumlah izin di bulan **{last_month['BULAN']}** sama dengan bulan sebelumnya ({prev_month['BULAN']})."
                )

    # ---------------- Chart ----------------
    fig1 = px.bar(
        g1, x="BULAN", y="JUMLAH",
        text="JUMLAH",
        color_discrete_sequence=["#FF4B4B"]
    )
    fig1.update_traces(texttemplate='%{text}', textposition='outside')
    fig1.update_layout(yaxis_title="Jumlah", xaxis_title="Bulan")
    st.plotly_chart(fig1, use_container_width=True)

with tab2:
    st.subheader("Perbandingan Sektor per Bulan")
    barmode = st.radio("Mode batang", ["group", "stack"], horizontal=True, key="barmode")

    fig2 = px.bar(
        dff, x="BULAN", y="JUMLAH", color="SEKTOR", barmode=barmode,
        color_discrete_sequence=px.colors.qualitative.Set1  # 🎨 palet cerah & senada
    )
    fig2.update_layout(
        yaxis_title="Jumlah",
        xaxis_title="Bulan",
        legend_title="Sektor",
        hovermode="x unified",
        plot_bgcolor="white"
    )
    st.plotly_chart(fig2, use_container_width=True)


with tab3:
    st.subheader("Tren Top-N Jenis Izin")
    top_izin = dff.groupby("JENIS IZIN")["JUMLAH"].sum().nlargest(int(top_n)).index
    df_top = dff[dff["JENIS IZIN"].isin(top_izin)]

    fig3 = px.line(
        df_top, x="BULAN", y="JUMLAH", color="JENIS IZIN", markers=True,
        line_shape="spline",
        color_discrete_sequence=px.colors.qualitative.Set1  # 🎨 palet cerah & solid
    )
    fig3.update_traces(line_width=3, mode="lines+markers")
    fig3.update_layout(
        yaxis_title="Jumlah",
        xaxis_title="Bulan",
        legend_title="Jenis Izin",
        hovermode="x unified",
        plot_bgcolor="white"
    )
    st.plotly_chart(fig3, use_container_width=True)



with tab4:
    st.subheader("Komposisi Jenis Izin per Bulan (Bar Chart)")

    bulan_for_bar = st.selectbox("Pilih Bulan", options=bulan_opts, key="bar_month")

    dcomp = (
        dff[dff["BULAN"] == bulan_for_bar]
        .groupby("JENIS IZIN", as_index=False)["JUMLAH"]
        .sum()
        .sort_values("JUMLAH", ascending=False)
    )

    fig4 = px.bar(
        dcomp.head(15),   # tampilkan Top 15 biar jelas
        x="JUMLAH",
        y="JENIS IZIN",
        orientation="h",
        text="JUMLAH",
        color="JUMLAH",
        color_continuous_scale="Reds"   # 🔴 gradasi merah
    )
    fig4.update_traces(texttemplate='%{text}', textposition='outside')
    fig4.update_layout(
        yaxis=dict(categoryorder="total ascending"),
        xaxis_title="Jumlah",
        yaxis_title="Jenis Izin"
    )

    st.plotly_chart(fig4, use_container_width=True)

with tab5:
    st.subheader("Komposisi Kategori (Donut Chart)")

    g5 = df[
        (df["SEKTOR"].isin(sel_sektor)) &
        (df["JENIS IZIN"].isin(sel_jenis)) &
        (df["BULAN"].isin(sel_bulan))
    ].groupby("KATEGORI", as_index=False)["JUMLAH"].sum()

    # cari kategori dominan (nilai terbesar)
    max_kat = g5.loc[g5["JUMLAH"].idxmax(), "KATEGORI"]

    # custom warna: dominan merah, sisanya Set1
    base_colors = px.colors.qualitative.Set1
    color_map = {max_kat: "red"}
    i = 0
    for k in g5["KATEGORI"]:
        if k not in color_map:
            color_map[k] = base_colors[i % len(base_colors)]
            i += 1

    fig5 = px.pie(
        g5,
        names="KATEGORI",
        values="JUMLAH",
        hole=0.5,
        color="KATEGORI",
        color_discrete_map=color_map
    )

    # semua label di luar (dengan garis penghubung)
    fig5.update_traces(
        textinfo="label+percent+value",
        textfont_size=13,
        textposition="outside",     # label di luar
        marker=dict(line=dict(color="black", width=1)),
        showlegend=True
    )

    # supaya slice kecil (misalnya "JUMLAH BERKAS DICABUT") tetap ada label
    fig5.update_traces(
        automargin=True
    )

    # layout
    fig5.update_layout(
        legend_title="Kategori",
        legend=dict(font=dict(size=12)),
        plot_bgcolor="white",
        margin=dict(t=40, b=40, l=40, r=40)
    )

    st.plotly_chart(fig5, use_container_width=True)



with tab6:
    st.subheader("Data Terfilter")
    st.dataframe(dff, use_container_width=True, hide_index=True)
    csv = dff.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Unduh CSV (filter saat ini)", data=csv, file_name="data_filter.csv", mime="text/csv")

st.divider()
with st.expander("ℹ️ Cara Pakai"):
    st.markdown("""
- Unggah file **Excel/CSV** dengan kolom: `SEKTOR, JENIS IZIN, KATEGORI, BULAN, JUMLAH`.
- Pilih kategori di halaman utama, filter lain di sidebar.
- Tab **Komposisi Bulan** kini hanya menampilkan Top-5 Jenis Izin.
- Tab **Perbandingan Kategori** tetap menampilkan semua kategori.
""")
