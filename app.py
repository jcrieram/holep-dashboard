"""
Dashboard HoLEP — Dr. Juan Carlos Riera M.
Acceso: http://100.84.66.88:8501  (via Tailscale)
"""

import warnings
warnings.filterwarnings("ignore")

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import io
import os
from datetime import datetime

import config as cfg

# ── Configuración de página ─────────────────────────────────────────────────
st.set_page_config(
    page_title="HoLEP Dashboard · Dr. Riera",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CSS ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  /* Fondo oscuro general */
  .stApp { background-color: #0d1117; color: #e6edf3; }
  section[data-testid="stSidebar"] { background-color: #161b22; }

  /* KPI cards */
  div[data-testid="metric-container"] {
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 12px;
    padding: 16px 20px;
  }
  div[data-testid="metric-container"] label { color: #8b949e !important; font-size:13px; }
  div[data-testid="metric-container"] [data-testid="metric-value"] { color: #58a6ff !important; font-size:28px; font-weight:700; }
  div[data-testid="metric-container"] [data-testid="metric-delta"] { font-size:12px; }

  /* Títulos */
  h1 { color: #e6edf3 !important; font-size:26px !important; }
  h2 { color: #c9d1d9 !important; font-size:20px !important; border-bottom:1px solid #21262d; padding-bottom:8px; }
  h3 { color: #8b949e !important; font-size:15px !important; }

  /* Tabs */
  .stTabs [data-baseweb="tab-list"] { background:#161b22; border-radius:8px; padding:4px; }
  .stTabs [data-baseweb="tab"] { color:#8b949e; border-radius:6px; }
  .stTabs [aria-selected="true"] { background:#21262d; color:#58a6ff !important; }

  /* Chat */
  .stChatMessage { background:#161b22; border:1px solid #21262d; border-radius:10px; }

  /* Botones */
  .stButton>button { background:#21262d; color:#e6edf3; border:1px solid #30363d; border-radius:8px; }
  .stButton>button:hover { background:#388bfd22; border-color:#58a6ff; }

  /* Dataframe */
  .stDataFrame { background:#161b22; }

  /* Alerta config */
  .config-warning {
    background:#2d1b00; border:1px solid #f0883e;
    border-radius:8px; padding:12px 16px; margin:8px 0;
    color:#f0883e; font-size:14px;
  }
</style>
""", unsafe_allow_html=True)

# ── Colores Plotly (tema oscuro) ────────────────────────────────────────────
PLOTLY_THEME = "plotly_dark"
COLOR_PRIMARY   = "#58a6ff"
COLOR_SUCCESS   = "#3fb950"
COLOR_WARNING   = "#f0883e"
COLOR_DANGER    = "#f85149"
COLOR_SECONDARY = "#8b949e"
PALETTE = [COLOR_PRIMARY, COLOR_SUCCESS, COLOR_WARNING, COLOR_DANGER,
           "#bc8cff", "#39d353", "#ffa657"]

# ── Carga de datos ──────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_data():
    try:
        resp = requests.get(cfg.SHEET_URL, timeout=15)
        resp.raise_for_status()
        df = pd.read_csv(io.StringIO(resp.text))
    except Exception as e:
        st.error(f"No se pudo leer el Google Sheet: {e}")
        return pd.DataFrame()

    # Filtrar filas vacías o separadores de año
    df = df[pd.to_numeric(df[cfg.COL_NUM], errors="coerce").notna()].copy()
    df[cfg.COL_NUM] = pd.to_numeric(df[cfg.COL_NUM], errors="coerce").astype(int)

    # Numerics
    for col in [cfg.COL_EDAD, cfg.COL_VOLUMEN, cfg.COL_TIEMPO, cfg.COL_PESO,
                cfg.COL_BIOPSIA, cfg.COL_PESO_ECO]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Fechas
    df[cfg.COL_FECHA] = pd.to_datetime(df[cfg.COL_FECHA], dayfirst=True, errors="coerce")

    # Normalizar booleanos
    for col in [cfg.COL_LITIASIS, cfg.COL_REINGRESO, cfg.COL_INCONT]:
        df[col] = df[col].astype(str).str.strip().str.upper().isin(["SI", "SÍ", "SI ", "SÍ "])

    # RPM — marcar RAO
    df["RPM_es_RAO"] = df[cfg.COL_RPM_PRE].astype(str).str.contains("RAO", case=False, na=False)
    df[cfg.COL_RPM_PRE] = pd.to_numeric(
        df[cfg.COL_RPM_PRE].astype(str).str.replace("RAO","",regex=False).str.strip(),
        errors="coerce"
    )

    # Mes y año para timeline
    df["Mes"] = df[cfg.COL_FECHA].dt.to_period("M").astype(str)
    df["Año"]  = df[cfg.COL_FECHA].dt.year
    df["N_cirugia"] = range(1, len(df)+1)

    # Coeficiente de enucleación
    mask = df[cfg.COL_VOLUMEN].notna() & df[cfg.COL_PESO].notna() & (df[cfg.COL_VOLUMEN] > 0)
    df.loc[mask, "Coef_enucleacion"] = (
        df.loc[mask, cfg.COL_PESO] / df.loc[mask, cfg.COL_VOLUMEN] * 100
    ).round(1)

    df[cfg.COL_CLINICA] = df[cfg.COL_CLINICA].astype(str).str.strip()
    df[cfg.COL_HALLAZGO] = df[cfg.COL_HALLAZGO].astype(str).str.strip()

    return df.reset_index(drop=True)

# ── Helpers de gráficos ─────────────────────────────────────────────────────
def fig_layout(fig, title="", h=380):
    fig.update_layout(
        template=PLOTLY_THEME,
        paper_bgcolor="#161b22",
        plot_bgcolor="#0d1117",
        font=dict(color="#c9d1d9", size=12),
        title=dict(text=title, font=dict(size=15, color="#e6edf3"), x=0.01),
        margin=dict(l=16, r=16, t=44 if title else 16, b=16),
        height=h,
        legend=dict(bgcolor="#161b22", bordercolor="#21262d", borderwidth=1),
        hoverlabel=dict(bgcolor="#21262d", font_size=13)
    )
    return fig

# ── Sidebar — Filtros ───────────────────────────────────────────────────────
def sidebar_filters(df):
    st.sidebar.markdown("## Filtros")

    clinicas = ["Todas"] + sorted(df[cfg.COL_CLINICA].dropna().unique().tolist())
    clinica_sel = st.sidebar.selectbox("Clínica", clinicas)

    if df[cfg.COL_FECHA].notna().any():
        fecha_min = df[cfg.COL_FECHA].min().date()
        fecha_max = df[cfg.COL_FECHA].max().date()
        rango_fecha = st.sidebar.date_input(
            "Período", value=(fecha_min, fecha_max),
            min_value=fecha_min, max_value=fecha_max
        )
    else:
        rango_fecha = None

    edad_min_d = int(df[cfg.COL_EDAD].min()) if df[cfg.COL_EDAD].notna().any() else 40
    edad_max_d = int(df[cfg.COL_EDAD].max()) if df[cfg.COL_EDAD].notna().any() else 90
    edad_rango = st.sidebar.slider("Rango de edad", edad_min_d, edad_max_d,
                                   (edad_min_d, edad_max_d))

    st.sidebar.markdown("---")
    st.sidebar.caption(f"Última carga: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    if st.sidebar.button("🔄 Actualizar datos"):
        st.cache_data.clear()
        st.rerun()

    # Aplicar filtros
    filtered = df.copy()
    if clinica_sel != "Todas":
        filtered = filtered[filtered[cfg.COL_CLINICA] == clinica_sel]
    if rango_fecha and len(rango_fecha) == 2:
        f0 = pd.Timestamp(rango_fecha[0])
        f1 = pd.Timestamp(rango_fecha[1])
        filtered = filtered[
            (filtered[cfg.COL_FECHA] >= f0) & (filtered[cfg.COL_FECHA] <= f1)
        ]
    filtered = filtered[
        (filtered[cfg.COL_EDAD] >= edad_rango[0]) &
        (filtered[cfg.COL_EDAD] <= edad_rango[1])
    ]
    return filtered

# ── Tab 1: Resumen ──────────────────────────────────────────────────────────
def tab_resumen(df):
    # KPIs
    total   = len(df)
    ed_prom = df[cfg.COL_EDAD].mean()
    vol_p   = df[cfg.COL_VOLUMEN].mean()
    t_prom  = df[cfg.COL_TIEMPO].mean()
    reing   = df[cfg.COL_REINGRESO].sum()
    incont  = df[cfg.COL_INCONT].sum()

    c1,c2,c3,c4,c5,c6 = st.columns(6)
    c1.metric("Total cirugías", total)
    c2.metric("Edad promedio", f"{ed_prom:.1f} años")
    c3.metric("Volumen promedio", f"{vol_p:.1f} gr")
    c4.metric("Tiempo promedio", f"{t_prom:.1f} min")
    c5.metric("Reingresos", f"{reing}  ({reing/total*100:.1f}%)" if total else "0")
    c6.metric("Incontinencia", f"{incont}  ({incont/total*100:.1f}%)" if total else "0")

    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        # Timeline mensual
        if df[cfg.COL_FECHA].notna().any():
            tl = df.groupby("Mes").size().reset_index(name="Cirugías")
            tl = tl[tl["Mes"].str.match(r"\d{4}-\d{2}")]
            tl = tl.sort_values("Mes")
            fig = px.bar(tl, x="Mes", y="Cirugías", color_discrete_sequence=[COLOR_PRIMARY])
            fig = fig_layout(fig, "Cirugías por mes")
            fig.update_xaxes(tickangle=-45, tickfont=dict(size=11))
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Pie clínicas
        clinica_cnt = df[cfg.COL_CLINICA].value_counts().reset_index()
        clinica_cnt.columns = ["Clínica","Cirugías"]
        fig = px.pie(clinica_cnt, names="Clínica", values="Cirugías",
                     color_discrete_sequence=PALETTE, hole=0.42)
        fig = fig_layout(fig, "Distribución por clínica")
        fig.update_traces(textinfo="percent+label", textfont_size=13)
        st.plotly_chart(fig, use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        # Hallazgos biopsia
        hall = df[cfg.COL_HALLAZGO]
        hall = hall[hall.notna() & (hall != "nan") & (hall != "")].value_counts().reset_index()
        hall.columns = ["Hallazgo","N"]
        if not hall.empty:
            fig = px.bar(hall, x="N", y="Hallazgo", orientation="h",
                         color_discrete_sequence=[COLOR_SUCCESS])
            fig = fig_layout(fig, "Hallazgos en biopsia", h=320)
            fig.update_yaxes(autorange="reversed")
            st.plotly_chart(fig, use_container_width=True)

    with col4:
        # Distribución de edad
        fig = px.histogram(df.dropna(subset=[cfg.COL_EDAD]),
                           x=cfg.COL_EDAD, nbins=12,
                           color_discrete_sequence=[COLOR_WARNING],
                           labels={cfg.COL_EDAD: "Edad (años)"})
        fig = fig_layout(fig, "Distribución de edad")
        fig.update_traces(marker_line_width=1, marker_line_color="#0d1117")
        st.plotly_chart(fig, use_container_width=True)

# ── Tab 2: Volúmenes y eficiencia ──────────────────────────────────────────
def tab_volumenes(df):
    col1, col2 = st.columns(2)

    with col1:
        # Scatter volumen vs tiempo
        d = df.dropna(subset=[cfg.COL_VOLUMEN, cfg.COL_TIEMPO])
        fig = px.scatter(
            d, x=cfg.COL_VOLUMEN, y=cfg.COL_TIEMPO,
            color=cfg.COL_CLINICA, color_discrete_sequence=PALETTE,
            trendline="ols",
            labels={cfg.COL_VOLUMEN:"Volumen próstata (gr)",
                    cfg.COL_TIEMPO:"Tiempo cirugía (min)"},
            hover_data={cfg.COL_NOMBRE: True, cfg.COL_EDAD: True, cfg.COL_RUT: False}
        )
        fig = fig_layout(fig, "Volumen próstata vs. Tiempo quirúrgico", h=420)
        fig.update_traces(marker=dict(size=9, opacity=0.85))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Scatter volumen vs peso obtenido (coeficiente de enucleación)
        d = df.dropna(subset=[cfg.COL_VOLUMEN, cfg.COL_PESO])
        fig = px.scatter(
            d, x=cfg.COL_VOLUMEN, y=cfg.COL_PESO,
            color=cfg.COL_CLINICA, color_discrete_sequence=PALETTE,
            trendline="ols",
            labels={cfg.COL_VOLUMEN:"Volumen próstata (gr)",
                    cfg.COL_PESO:"Peso obtenido (gr)"},
            hover_data={cfg.COL_NOMBRE: True, "Coef_enucleacion": True, cfg.COL_RUT: False}
        )
        fig = fig_layout(fig, "Volumen vs. Peso obtenido (coeficiente enucleación)", h=420)
        fig.update_traces(marker=dict(size=9, opacity=0.85))
        st.plotly_chart(fig, use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        # Histograma volúmenes con percentiles
        d = df[cfg.COL_VOLUMEN].dropna()
        fig = px.histogram(d, nbins=15, color_discrete_sequence=[COLOR_PRIMARY],
                           labels={cfg.COL_VOLUMEN:"Volumen próstata (gr)", "count":"N"})
        p25, p50, p75 = d.quantile([0.25,0.5,0.75])
        for val, label, color in [(p25,"p25","#8b949e"),(p50,"p50",COLOR_WARNING),(p75,"p75","#8b949e")]:
            fig.add_vline(x=val, line_dash="dash", line_color=color,
                          annotation_text=f"{label}: {val:.0f}gr",
                          annotation_position="top right",
                          annotation_font_size=11)
        fig = fig_layout(fig, "Distribución de volúmenes prostáticos")
        st.plotly_chart(fig, use_container_width=True)

    with col4:
        # Box plot tiempos por clínica
        d = df.dropna(subset=[cfg.COL_TIEMPO, cfg.COL_CLINICA])
        fig = px.box(d, x=cfg.COL_CLINICA, y=cfg.COL_TIEMPO,
                     color=cfg.COL_CLINICA, color_discrete_sequence=PALETTE,
                     labels={cfg.COL_CLINICA:"Clínica",
                             cfg.COL_TIEMPO:"Tiempo cirugía (min)"},
                     points="all")
        fig = fig_layout(fig, "Tiempo quirúrgico por clínica")
        fig.update_traces(marker=dict(size=5, opacity=0.7))
        st.plotly_chart(fig, use_container_width=True)

    # Tabla de grandes próstatas (>100 gr)
    grandes = df[df[cfg.COL_VOLUMEN] >= 100].dropna(subset=[cfg.COL_VOLUMEN])
    if not grandes.empty:
        st.markdown(f"#### Próstatas ≥ 100 gr — {len(grandes)} casos")
        cols_show = [cfg.COL_NUM, cfg.COL_FECHA, cfg.COL_EDAD,
                     cfg.COL_VOLUMEN, cfg.COL_TIEMPO, cfg.COL_PESO, cfg.COL_CLINICA]
        show = grandes[cols_show].copy()
        show[cfg.COL_FECHA] = show[cfg.COL_FECHA].dt.strftime("%d/%m/%Y")
        st.dataframe(show.reset_index(drop=True), use_container_width=True, height=220)

# ── Tab 3: Curva de aprendizaje ────────────────────────────────────────────
def tab_curva(df):
    d = df.dropna(subset=[cfg.COL_TIEMPO]).sort_values("N_cirugia")

    col1, col2 = st.columns(2)

    with col1:
        # Tiempo quirúrgico cronológico + media móvil
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=d["N_cirugia"], y=d[cfg.COL_TIEMPO],
            mode="markers", name="Caso",
            marker=dict(color=COLOR_SECONDARY, size=7, opacity=0.7)
        ))
        if len(d) >= 10:
            ma = d[cfg.COL_TIEMPO].rolling(10, min_periods=5).mean()
            fig.add_trace(go.Scatter(
                x=d["N_cirugia"], y=ma,
                mode="lines", name="Media móvil 10 casos",
                line=dict(color=COLOR_PRIMARY, width=3)
            ))
        fig = fig_layout(fig, "Tiempo quirúrgico — curva de aprendizaje", h=400)
        fig.update_xaxes(title="N° cirugía")
        fig.update_yaxes(title="Tiempo (min)")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Volumen vs N° cirugía — ¿opera próstatas más grandes con el tiempo?
        d2 = df.dropna(subset=[cfg.COL_VOLUMEN]).sort_values("N_cirugia")
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=d2["N_cirugia"], y=d2[cfg.COL_VOLUMEN],
            mode="markers", name="Volumen",
            marker=dict(color=COLOR_WARNING, size=8, opacity=0.75)
        ))
        if len(d2) >= 10:
            ma2 = d2[cfg.COL_VOLUMEN].rolling(10, min_periods=5).mean()
            fig.add_trace(go.Scatter(
                x=d2["N_cirugia"], y=ma2,
                mode="lines", name="Media móvil",
                line=dict(color=COLOR_SUCCESS, width=3)
            ))
        fig = fig_layout(fig, "Complejidad con el tiempo (volumen prostático)", h=400)
        fig.update_xaxes(title="N° cirugía")
        fig.update_yaxes(title="Volumen (gr)")
        st.plotly_chart(fig, use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        # Tiempo promedio por trimestre
        d3 = df.dropna(subset=[cfg.COL_TIEMPO, cfg.COL_FECHA]).copy()
        d3["Trimestre"] = d3[cfg.COL_FECHA].dt.to_period("Q").astype(str)
        trim = d3.groupby("Trimestre")[cfg.COL_TIEMPO].agg(["mean","count"]).reset_index()
        trim.columns = ["Trimestre","Tiempo medio","N"]
        trim = trim[trim["N"] >= 3]
        if not trim.empty:
            fig = px.bar(trim, x="Trimestre", y="Tiempo medio",
                         text="N", color_discrete_sequence=[COLOR_PRIMARY],
                         labels={"Tiempo medio":"Tiempo medio (min)"})
            fig = fig_layout(fig, "Tiempo medio por trimestre")
            fig.update_traces(texttemplate="%{text} casos", textposition="outside")
            st.plotly_chart(fig, use_container_width=True)

    with col4:
        # Coeficiente de enucleación a lo largo del tiempo
        d4 = df.dropna(subset=["Coef_enucleacion"]).sort_values("N_cirugia")
        if not d4.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=d4["N_cirugia"], y=d4["Coef_enucleacion"],
                mode="markers", name="Coef. enucleación",
                marker=dict(color=COLOR_DANGER, size=8, opacity=0.75)
            ))
            if len(d4) >= 8:
                ma4 = d4["Coef_enucleacion"].rolling(8, min_periods=4).mean()
                fig.add_trace(go.Scatter(
                    x=d4["N_cirugia"], y=ma4, mode="lines",
                    name="Media móvil",
                    line=dict(color="#bc8cff", width=3)
                ))
            fig.add_hline(y=80, line_dash="dot", line_color=COLOR_SUCCESS,
                          annotation_text="Meta 80%", annotation_font_size=11)
            fig = fig_layout(fig, "Coeficiente de enucleación (peso/volumen × 100)", h=400)
            fig.update_yaxes(title="%")
            st.plotly_chart(fig, use_container_width=True)

# ── Tab 4: Complicaciones ──────────────────────────────────────────────────
def tab_complicaciones(df):
    total = len(df)

    # KPIs complicaciones
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Reingresos", f"{df[cfg.COL_REINGRESO].sum()}",
              f"{df[cfg.COL_REINGRESO].mean()*100:.1f}%")
    c2.metric("Incontinencia", f"{df[cfg.COL_INCONT].sum()}",
              f"{df[cfg.COL_INCONT].mean()*100:.1f}%")
    c3.metric("Litiasis vesical", f"{df[cfg.COL_LITIASIS].sum()}",
              f"{df[cfg.COL_LITIASIS].mean()*100:.1f}%")
    c4.metric("RAO preop", f"{df['RPM_es_RAO'].sum()}",
              f"{df['RPM_es_RAO'].mean()*100:.1f}%")

    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        # Motivos de reingreso
        mot = df[df[cfg.COL_REINGRESO]][cfg.COL_MOT_REING]
        mot = mot[mot.notna() & (mot.astype(str).str.strip() != "") & (mot.astype(str) != "nan")]
        if not mot.empty:
            mot_cnt = mot.astype(str).str.strip().value_counts().reset_index()
            mot_cnt.columns = ["Motivo","N"]
            fig = px.bar(mot_cnt, x="N", y="Motivo", orientation="h",
                         color_discrete_sequence=[COLOR_DANGER])
            fig = fig_layout(fig, "Motivos de reingreso", h=320)
            fig.update_yaxes(autorange="reversed")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sin reingresos en el período seleccionado.")

    with col2:
        # Complicaciones e incidentes
        comp = df[cfg.COL_COMPLIC]
        comp = comp[comp.notna() & (comp.astype(str).str.strip() != "") & (comp.astype(str) != "nan")]
        if not comp.empty:
            comp_cnt = comp.astype(str).str.strip().str.lower()
            comp_cnt = comp_cnt.value_counts().reset_index()
            comp_cnt.columns = ["Complicación","N"]
            fig = px.bar(comp_cnt, x="N", y="Complicación", orientation="h",
                         color_discrete_sequence=[COLOR_WARNING])
            fig = fig_layout(fig, "Complicaciones e incidentes", h=320)
            fig.update_yaxes(autorange="reversed")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sin complicaciones registradas en el período.")

    # Tabla de casos con eventos
    st.markdown("#### Casos con reingreso, incontinencia o litiasis")
    mask_ev = df[cfg.COL_REINGRESO] | df[cfg.COL_INCONT] | df[cfg.COL_LITIASIS]
    if mask_ev.any():
        cols_ev = [cfg.COL_NUM, cfg.COL_FECHA, cfg.COL_NOMBRE, cfg.COL_EDAD,
                   cfg.COL_VOLUMEN, cfg.COL_TIEMPO,
                   cfg.COL_REINGRESO, cfg.COL_MOT_REING,
                   cfg.COL_INCONT, cfg.COL_LITIASIS,
                   cfg.COL_COMPLIC, cfg.COL_CLINICA]
        show_ev = df[mask_ev][cols_ev].copy()
        show_ev[cfg.COL_FECHA] = show_ev[cfg.COL_FECHA].dt.strftime("%d/%m/%Y")
        st.dataframe(show_ev.reset_index(drop=True), use_container_width=True)
    else:
        st.success("Sin eventos adversos en el período seleccionado.")

# ── Tab 5: Datos completos ─────────────────────────────────────────────────
def tab_datos(df):
    st.markdown(f"**{len(df)} registros** — ordenados por fecha de cirugía")
    cols_tabla = [cfg.COL_NUM, cfg.COL_FECHA, cfg.COL_CLINICA,
                  cfg.COL_EDAD, cfg.COL_VOLUMEN, cfg.COL_TIEMPO,
                  cfg.COL_PESO, cfg.COL_RPM_PRE,
                  cfg.COL_BIOPSIA, cfg.COL_HALLAZGO,
                  cfg.COL_REINGRESO, cfg.COL_INCONT,
                  cfg.COL_LITIASIS, cfg.COL_COMPLIC]
    show = df.sort_values(cfg.COL_FECHA, ascending=False)[cols_tabla].copy()
    show[cfg.COL_FECHA] = show[cfg.COL_FECHA].dt.strftime("%d/%m/%Y")
    st.dataframe(show.reset_index(drop=True), use_container_width=True, height=500)

    col1, col2 = st.columns(2)
    with col1:
        csv = show.to_csv(index=False).encode("utf-8")
        st.download_button("⬇ Descargar CSV", csv,
                           f"holep_{datetime.now().strftime('%Y%m%d')}.csv",
                           "text/csv")

# ── Tab 6: Chat IA ─────────────────────────────────────────────────────────
def tab_chat(df):
    api_key = cfg.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY","")

    if not api_key:
        st.markdown("""
        <div class="config-warning">
        ⚠️  Para activar el chat, agrega tu API Key de Google Gemini (gratis) en
        <code>holep_dashboard/config.py</code> → variable <code>GEMINI_API_KEY</code><br><br>
        Obtén tu key gratis en <strong>aistudio.google.com</strong> → "Get API key"
        </div>
        """, unsafe_allow_html=True)
        return

    def build_context(df):
        total = len(df)
        return f"""Eres asistente médico-estadístico del Dr. Juan Carlos Riera M., urólogo especialista en HoLEP, radicado en Viña del Mar, Chile.

DATOS AGREGADOS DE SU SERIE ({total} pacientes, período {df[cfg.COL_FECHA].min().strftime('%b %Y') if df[cfg.COL_FECHA].notna().any() else 'N/D'} – {df[cfg.COL_FECHA].max().strftime('%b %Y') if df[cfg.COL_FECHA].notna().any() else 'N/D'}):

- Edad: media {df[cfg.COL_EDAD].mean():.1f} años (rango {df[cfg.COL_EDAD].min():.0f}–{df[cfg.COL_EDAD].max():.0f})
- Volumen prostático: media {df[cfg.COL_VOLUMEN].mean():.1f} gr (min {df[cfg.COL_VOLUMEN].min():.0f}, max {df[cfg.COL_VOLUMEN].max():.0f})
- Tiempo cirugía: media {df[cfg.COL_TIEMPO].mean():.1f} min (min {df[cfg.COL_TIEMPO].min():.0f}, max {df[cfg.COL_TIEMPO].max():.0f})
- Peso obtenido: media {df[cfg.COL_PESO].mean():.1f} gr
- Coef. enucleación medio: {df['Coef_enucleacion'].mean():.1f}%
- Tasa reingreso: {df[cfg.COL_REINGRESO].mean()*100:.1f}% ({df[cfg.COL_REINGRESO].sum()} casos)
- Tasa incontinencia: {df[cfg.COL_INCONT].mean()*100:.1f}% ({df[cfg.COL_INCONT].sum()} casos)
- Tasa litiasis vesical: {df[cfg.COL_LITIASIS].mean()*100:.1f}% ({df[cfg.COL_LITIASIS].sum()} casos)
- Pacientes con RAO preoperatorio: {df['RPM_es_RAO'].sum()} ({df['RPM_es_RAO'].mean()*100:.1f}%)
- Distribución por clínica: {df[cfg.COL_CLINICA].value_counts().to_dict()}
- Hallazgos biopsia: {df[cfg.COL_HALLAZGO][df[cfg.COL_HALLAZGO].notna() & (df[cfg.COL_HALLAZGO]!='nan')].value_counts().to_dict()}

Contexto clínico HoLEP: enucleación prostática con láser de holmio, estándar de oro para HPB. Coeficiente de enucleación >80% indica técnica óptima. Tiempo quirúrgico disminuye con la curva de aprendizaje.

Responde en español, con criterio clínico riguroso, conciso y útil para el médico."""

    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []

    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Pregunta sobre tus datos HoLEP..."):
        st.session_state.chat_messages.append({"role":"user","content":prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Analizando..."):
                try:
                    import google.generativeai as genai
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel(
                        model_name="gemini-2.5-flash",
                        system_instruction=build_context(df)
                    )
                    # Construir historial en formato Gemini
                    history = []
                    for m in st.session_state.chat_messages[:-1]:
                        role = "user" if m["role"] == "user" else "model"
                        history.append({"role": role, "parts": [m["content"]]})
                    chat = model.start_chat(history=history)
                    resp = chat.send_message(prompt)
                    reply = resp.text
                except Exception as e:
                    reply = f"Error al conectar con Gemini: {e}"

                st.markdown(reply)
                st.session_state.chat_messages.append({"role":"assistant","content":reply})

    if st.session_state.chat_messages:
        if st.button("🗑 Limpiar chat"):
            st.session_state.chat_messages = []
            st.rerun()

    st.markdown("##### Preguntas de ejemplo")
    for ej in [
        "¿Mi curva de aprendizaje muestra mejoría en los últimos 3 meses?",
        "¿Cómo se compara mi tasa de reingresos con la literatura HoLEP publicada?",
        "¿Cuál es mi coeficiente de enucleación promedio y qué significa?",
        "¿Hay diferencias en resultados entre mis clínicas?",
        "¿Qué casos de próstata grande tuve y cómo resultaron?",
    ]:
        st.caption(f"→ _{ej}_")

# ── Main ────────────────────────────────────────────────────────────────────
def main():
    # Header
    st.markdown("""
    <div style="display:flex;align-items:center;gap:14px;margin-bottom:8px">
      <span style="font-size:36px">🔬</span>
      <div>
        <h1 style="margin:0">Dashboard HoLEP</h1>
        <p style="color:#8b949e;margin:0;font-size:14px">Dr. Juan Carlos Riera M. — Serie quirúrgica personal</p>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Cargar datos
    with st.spinner("Cargando datos desde Google Sheet..."):
        df_raw = load_data()

    if df_raw.empty:
        st.error("No se pudieron cargar los datos. Verifica que el Google Sheet esté compartido como 'Cualquiera con el enlace puede ver'.")
        return

    # Filtros sidebar
    df = sidebar_filters(df_raw)

    if len(df) == 0:
        st.warning("No hay datos para los filtros seleccionados.")
        return

    # Tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Resumen",
        "🔵 Volúmenes",
        "📈 Curva aprendizaje",
        "⚠️ Complicaciones",
        "📋 Datos",
        "🤖 Chat IA"
    ])

    with tab1: tab_resumen(df)
    with tab2: tab_volumenes(df)
    with tab3: tab_curva(df)
    with tab4: tab_complicaciones(df)
    with tab5: tab_datos(df)
    with tab6: tab_chat(df)

if __name__ == "__main__":
    main()
