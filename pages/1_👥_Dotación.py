# ============================================================================================
# 👥 DOTACIÓN 2025 — Versión con Mapas y Comparador con Border Radius y Fondo Gris Claro
# ============================================================================================

import streamlit as st
import pandas as pd
import altair as alt
import io
from datetime import datetime
import numpy as np
import streamlit.components.v1 as components
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import re
from streamlit_image_comparison import image_comparison
from PIL import Image

# --- Configuración de la página ---
st.set_page_config(layout="wide", page_title="Dotación: 2025", page_icon="👥")

# --- CSS Global ---
st.markdown("""
<style>
div[data-testid="stSidebar"] div[data-testid="stButton"] button {
    border-radius: 0.5rem;
    font-weight: bold;
    width: 100%;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

div.stDownloadButton button {
    background-color: #28a745;
    color: white;
    font-weight: bold;
    padding: 0.75rem 1.25rem;
    border-radius: 0.5rem;
    border: none;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}
div.stDownloadButton button:hover { background-color: #218838; }

@media (max-width: 768px) {
    h1 { font-size: 1.9rem; }
    h2 { font-size: 1.5rem; }
    h3 { font-size: 1.2rem; }

    div[data-testid="stHorizontalBlock"] {
        flex-wrap: wrap !important;
    }
    div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
        flex: 1 1 100% !important;
        min-width: 100% !important;
        margin-bottom: 1rem;
    }
    .stTabs { overflow-x: auto; }
}

/* --- Borde redondeado y fondo gris claro para mapas --- */
.map-container {
    border-radius: 20px;
    overflow: hidden;
    background-color: #f8f9fa;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    padding: 5px;
}

/* --- Estilo para el comparador de imágenes --- */
div[data-testid="stImage"] img {
    border-radius: 20px !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}
div[data-testid="stImage"] canvas {
    border-radius: 20px !important;
    overflow: hidden;
}
</style>
""", unsafe_allow_html=True)

# --- Funciones auxiliares ---
custom_format_locale = {"decimal": ",", "thousands": ".", "grouping": [3], "currency": ["", ""]}
alt.renderers.set_embed_options(formatLocale=custom_format_locale)

def format_integer_es(num):
    if pd.isna(num) or not isinstance(num, (int, float, np.number)): return ""
    return f"{int(num):,}".replace(",", ".")

def format_percentage_es(num, decimals=1):
    if pd.isna(num) or not isinstance(num, (int, float, np.number)): return ""
    return f"{num:,.{decimals}f}%".replace(",", "TEMP").replace(".", ",").replace("TEMP", ".")

def generate_download_buttons(df_to_download, filename_prefix, key_suffix=""):
    st.markdown("##### Opciones de Descarga:")
    col_dl1, col_dl2 = st.columns(2)
    csv_buffer = io.StringIO()
    df_to_download.to_csv(csv_buffer, index=False)
    with col_dl1:
        st.download_button(label="⬇️ Descargar como CSV", data=csv_buffer.getvalue(),
                           file_name=f"{filename_prefix}.csv", mime="text/csv",
                           key=f"csv_download_{filename_prefix}{key_suffix}")
    excel_buffer = io.BytesIO()
    df_to_download.to_excel(excel_buffer, index=False, engine='openpyxl')
    excel_buffer.seek(0)
    with col_dl2:
        st.download_button(label="📊 Descargar como Excel", data=excel_buffer.getvalue(),
                           file_name=f"{filename_prefix}.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           key=f"excel_download_{filename_prefix}{key_suffix}")

def apply_all_filters(df, selections):
    _df = df.copy()
    for col, values in selections.items():
        if values and col in _df.columns:
            _df = _df[_df[col].isin(values)]
    return _df

@st.cache_data
def load_coords_from_url(url):
    try:
        df = pd.read_csv(url, encoding='latin-1')
        return df
    except Exception as e:
        st.error(f"Error al cargar coordenadas: {e}")
        return pd.DataFrame()

@st.cache_data
def load_and_clean_data(uploaded_file):
    try:
        df_excel = pd.read_excel(uploaded_file, sheet_name='Dotacion_25', engine='openpyxl')
    except Exception as e:
        st.error(f"No se pudo leer la hoja 'Dotacion_25': {e}")
        return pd.DataFrame()
    return df_excel

# --- Inicio App ---
st.title("👥 Dotación 2025")
st.write("Estructura y distribución geográfica y por gerencia de personal")

uploaded_file = st.file_uploader("📂 Cargue aquí su archivo Excel de dotación", type=["xlsx"])
st.markdown("---")

COORDS_URL = "https://raw.githubusercontent.com/Tincho2002/dotacion_assa_2025/main/coordenadas.csv"
df_coords = load_coords_from_url(COORDS_URL)

if uploaded_file is not None:
    df = load_and_clean_data(uploaded_file)
    if df.empty:
        st.error("Archivo vacío o con error de lectura.")
        st.stop()

    st.success(f"Se cargaron {format_integer_es(len(df))} registros.")
    st.markdown("---")

    # --- Tabs ---
    tab_names = ["🗺️ Comparador de Mapas", "🗺️ Mapa Geográfico"]
    tabs = st.tabs(tab_names)
    tab_map_comparador, tab_map_individual = tabs

    # ===================== COMPARADOR DE MAPAS =====================
    with tab_map_comparador:
        st.header("Comparador de Mapas con Border Radius")
        map_style_options = {
            "Satélite con Calles": "satellite-streets",
            "Mapa de Calles": "open-street-map",
            "Estilo Claro": "carto-positron",
        }
        c1, c2 = st.columns(2)
        with c1:
            style1_name = st.selectbox("Mapa izquierdo:", options=list(map_style_options.keys()), index=0)
        with c2:
            style2_name = st.selectbox("Mapa derecho:", options=list(map_style_options.keys()), index=1)
        st.markdown("---")

        if st.checkbox("✅ Mostrar Comparador", value=False):
            try:
                df_mapa_data = pd.merge(df, df_coords, on="Distrito", how="left")
                df_mapa_agg = df_mapa_data.groupby(['Distrito', 'Latitud', 'Longitud']).size().reset_index(name='Dotacion_Total')
                px.set_mapbox_access_token("pk.eyJ1Ijoic2FuZHJhcXVldmVkbyIsImEiOiJjbWYzOGNkZ2QwYWg0MnFvbDJucWc5d3VwIn0.bz6E-qxAwk6ZFPYohBsdMw")

                def gen_map(mapbox_style):
                    fig = px.scatter_mapbox(df_mapa_agg, lat="Latitud", lon="Longitud",
                                            size="Dotacion_Total", color="Dotacion_Total",
                                            hover_name="Distrito",
                                            color_continuous_scale=px.colors.sequential.Plasma,
                                            size_max=50, mapbox_style=mapbox_style,
                                            zoom=6, center={"lat": -32.5, "lon": -61.5})
                    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
                    return fig

                fig1 = gen_map(map_style_options[style1_name])
                fig2 = gen_map(map_style_options[style2_name])

                img1_bytes = fig1.to_image(format="png", scale=2, engine="kaleido")
                img2_bytes = fig2.to_image(format="png", scale=2, engine="kaleido")
                img1_pil = Image.open(io.BytesIO(img1_bytes))
                img2_pil = Image.open(io.BytesIO(img2_bytes))

                st.markdown('<div class="map-container">', unsafe_allow_html=True)
                image_comparison(
                    img1=img1_pil,
                    img2=img2_pil,
                    label1=style1_name,
                    label2=style2_name,
                    width=900,
                )
                st.markdown('</div>', unsafe_allow_html=True)

            except Exception as e:
                st.error(f"Ocurrió un error al generar el comparador: {e}")

    # ===================== MAPA INDIVIDUAL =====================
    with tab_map_individual:
        st.header("Mapa Individual con Estilo Visual Mejorado")
        map_style_options = {
            "Satélite con Calles": "satellite-streets",
            "Mapa de Calles": "open-street-map",
            "Estilo Claro": "carto-positron",
        }
        style_name = st.selectbox("Selecciona el estilo del mapa:", list(map_style_options.keys()), key="map_style_individual")
        df_mapa_data = pd.merge(df, df_coords, on="Distrito", how="left").dropna(subset=['Latitud', 'Longitud'])
        df_mapa_agg = df_mapa_data.groupby(['Distrito', 'Latitud', 'Longitud']).size().reset_index(name='Dotacion_Total')

        px.set_mapbox_access_token("pk.eyJ1Ijoic2FuZHJhcXVldmVkbyIsImEiOiJjbWYzOGNkZ2QwYWg0MnFvbDJucWc5d3VwIn0.bz6E-qxAwk6ZFPYohBsdMw")
        fig = px.scatter_mapbox(df_mapa_agg, lat="Latitud", lon="Longitud",
                                size="Dotacion_Total", color="Dotacion_Total",
                                hover_name="Distrito",
                                color_continuous_scale=px.colors.sequential.Plasma,
                                size_max=50, mapbox_style=map_style_options[style_name],
                                zoom=6, center={"lat": -32.5, "lon": -61.5})
        fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

        map_html = f"""
        <div class="map-container">
            {fig.to_html(include_plotlyjs='cdn', full_html=False)}
        </div>
        """
        components.html(map_html, height=600)

else:
    st.info("Por favor, cargue un archivo Excel para comenzar el análisis.")
