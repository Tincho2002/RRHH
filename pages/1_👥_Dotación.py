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

# --- Configuración de la página y Estilos CSS ---
st.set_page_config(layout="wide")

# --- CSS MEJORADO CON RESPONSIVIDAD ---
st.markdown("""
<style>
    /* Estilo para los botones de control (Resetear) */
    div[data-testid="stSidebar"] div[data-testid="stButton"] button {
        border-radius: 0.5rem;
        font-weight: bold;
        width: 100%;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    /* Estilo general para los botones de descarga */
    div.stDownloadButton button {
        background-color: #28a745;
        color: white;
        font-weight: bold;
        padding: 0.75rem 1.25rem;
        border-radius: 0.5rem;
        border: none;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    div.stDownloadButton button:hover {
        background-color: #218838;
    }

    /* --- CÓDIGO PARA DISEÑO RESPONSIVO (MÓVILES Y TABLETS) --- */
    @media (max-width: 768px) {
        
        .summary-container {
            flex-direction: column;
            align-items: stretch;
        }

        .summary-main-kpi {
            border-right: none;
            border-bottom: 2px solid #f0f2f6;
            padding-right: 0;
            padding-bottom: 20px;
            margin-bottom: 20px;
        }

        .summary-main-kpi .value {
            font-size: 2.8rem;
        }
        
        .summary-row {
            flex-direction: column;
            align-items: flex-start;
            gap: 15px;
        }

        div[data-testid="column"] {
            margin-bottom: 1.5rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# --- Funciones de Formato de Números ---
custom_format_locale = {
    "decimal": ",", "thousands": ".", "grouping": [3], "currency": ["", ""]
}
alt.renderers.set_embed_options(formatLocale=custom_format_locale)

def format_integer_es(num):
    if pd.isna(num) or not isinstance(num, (int, float, np.number)): return ""
    return f"{int(num):,}".replace(",", ".")

def format_percentage_es(num, decimals=1):
    if pd.isna(num) or not isinstance(num, (int, float, np.number)): return ""
    return f"{num:,.{decimals}f}%".replace(",", "TEMP").replace(".", ",").replace("TEMP", ".")

# --- Funciones Auxiliares ---
def generate_download_buttons(df_to_download, filename_prefix, key_suffix=""):
    st.markdown("##### Opciones de Descarga:")
    col_dl1, col_dl2 = st.columns(2)
    csv_buffer = io.StringIO()
    df_to_download.to_csv(csv_buffer, index=False)
    with col_dl1:
        st.download_button(label="⬇️ Descargar como CSV", data=csv_buffer.getvalue(), file_name=f"{filename_prefix}.csv", mime="text/csv", key=f"csv_download_{filename_prefix}{key_suffix}")
    excel_buffer = io.BytesIO()
    df_to_download.to_excel(excel_buffer, index=False, engine='openpyxl')
    excel_buffer.seek(0)
    with col_dl2:
        st.download_button(label="📊 Descargar como Excel", data=excel_buffer.getvalue(), file_name=f"{filename_prefix}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key=f"excel_download_{filename_prefix}{key_suffix}")

def apply_all_filters(df, selections):
    _df = df.copy()
    for col, values in selections.items():
        if values and col in _df.columns: 
            _df = _df[_df[col].isin(values)]
    return _df

def get_sorted_unique_options(dataframe, column_name):
    if column_name in dataframe.columns:
        unique_values = dataframe[column_name].dropna().unique().tolist()
        unique_values = [v for v in unique_values if v != 'no disponible']
        if column_name == 'Rango Antiguedad':
            order = ['de 0 a 5 años', 'de 5 a 10 años', 'de 11 a 15 años', 'de 16 a 20 años', 'de 21 a 25 años', 'de 26 a 30 años', 'de 31 a 35 años', 'más de 35 años']
            present_values = [val for val in order if val in unique_values]
            other_values = [val for val in unique_values if val not in order]
            return present_values + sorted(other_values)
        elif column_name == 'Rango Edad':
            order = ['de 0 a 19 años', 'de 19 a 25 años', 'de 26 a 30 años', 'de 31 a 35 años', 'de 36 a 40 años', 'de 41 a 45 años', 'de 46 a 50 años', 'de 51 a 55 años', 'de 56 a 60 años', 'de 61 a 65 años', 'más de 65 años']
            present_values = [val for val in order if val in unique_values]
            other_values = [val for val in unique_values if val not in order]
            return present_values + sorted(other_values)
        elif column_name == 'Periodo':
            month_order = {'Enero': 1, 'Febrero': 2, 'Marzo': 3, 'Abril': 4, 'Mayo': 5, 'Junio': 6, 'Julio': 7, 'Agosto': 8, 'Septiembre': 9, 'Octubre': 10, 'Noviembre': 11, 'Diciembre': 12}
            return sorted(unique_values, key=lambda x: month_order.get(x, 99))
        return sorted(unique_values)
    return []
    
def get_available_options(df, selections, target_column):
    _df = df.copy()
    for col, values in selections.items():
        if col != target_column and values and col in _df.columns: 
            _df = _df[_df[col].isin(values)]
    return get_sorted_unique_options(_df, target_column)

@st.cache_data
def load_coords_from_url(url):
    try:
        df = pd.read_csv(url, encoding='latin-1')
        return df
    except Exception as e:
        st.error(f"Error al cargar el archivo de coordenadas desde GitHub: {e}")
        return pd.DataFrame()

@st.cache_data
def load_and_clean_data(uploaded_file):
    df_excel = pd.DataFrame()
    try:
        df_excel = pd.read_excel(uploaded_file, sheet_name='Dotacion_25', engine='openpyxl')
    except Exception as e:
        st.error(f"ERROR CRÍTICO: No se pudo leer la hoja 'Dotacion_25' del archivo cargado. Mensaje: {e}")
        return pd.DataFrame()
    if df_excel.empty: return pd.DataFrame()
    if 'LEGAJO' in df_excel.columns: df_excel['LEGAJO'] = pd.to_numeric(df_excel['LEGAJO'], errors='coerce')
    
    excel_col_fecha_ingreso_raw = 'Fecha ing.'
    excel_col_fecha_nacimiento_raw = 'Fecha Nac.'
    excel_col_rango_antiguedad_raw = 'Rango (Antigüedad)'
    excel_col_rango_edad_raw = 'Rango (Edad)'
    
    if excel_col_rango_antiguedad_raw in df_excel.columns and df_excel[excel_col_rango_antiguedad_raw].notna().sum() > 0:
        df_excel['Rango Antiguedad'] = df_excel[excel_col_rango_antiguedad_raw].astype(str).str.strip().str.lower()
    else:
        if excel_col_fecha_ingreso_raw in df_excel.columns:
            temp_fecha_ingreso = pd.to_datetime(df_excel[excel_col_fecha_ingreso_raw], errors='coerce')
            if temp_fecha_ingreso.notna().sum() > 0:
                df_excel['Antiguedad (años)'] = (datetime.now() - temp_fecha_ingreso).dt.days / 365.25
                bins_antiguedad = [0, 5, 10, 15, 20, 25, 30, 35, float('inf')]
                labels_antiguedad = ['de 0 a 5 años', 'de 5 a 10 años', 'de 11 a 15 años', 'de 16 a 20 años', 'de 21 a 25 años', 'de 26 a 30 años', 'de 31 a 35 años', 'más de 35 años']
                df_excel['Rango Antiguedad'] = pd.cut(df_excel['Antiguedad (años)'], bins=bins_antiguedad, labels=labels_antiguedad, right=False, include_lowest=True).astype(str).str.strip().str.lower()
            else: df_excel['Rango Antiguedad'] = 'no disponible'
        else: df_excel['Rango Antiguedad'] = 'no disponible'
    
    if excel_col_rango_edad_raw in df_excel.columns and df_excel[excel_col_rango_edad_raw].notna().sum() > 0:
        df_excel['Rango Edad'] = df_excel[excel_col_rango_edad_raw].astype(str).str.strip().str.lower()
    else:
        if excel_col_fecha_nacimiento_raw in df_excel.columns:
            temp_fecha_nacimiento = pd.to_datetime(df_excel[excel_col_fecha_nacimiento_raw], errors='coerce')
            if temp_fecha_nacimiento.notna().sum() > 0:
                df_excel['Edad (años)'] = (datetime.now() - temp_fecha_nacimiento).dt.days / 365.25
                bins_edad = [0, 19, 25, 30, 35, 40, 45, 50, 55, 60, 65, float('inf')]
                labels_edad = ['de 0 a 19 años', 'de 19 a 25 años', 'de 26 a 30 años', 'de 31 a 35 años', 'de 36 a 40 años', 'de 41 a 45 años', 'de 46 a 50 años', 'de 51 a 55 años', 'de 56 a 60 años', 'de 61 a 65 años', 'más de 65 años']
                df_excel['Rango Edad'] = pd.cut(df_excel['Edad (años)'], bins=bins_edad, labels=labels_edad, right=False, include_lowest=True).astype(str).str.strip().str.lower()
            else: df_excel['Rango Edad'] = 'no disponible'
        else: df_excel['Rango Edad'] = 'no disponible'
    
    if 'Periodo' in df_excel.columns:
        try:
            temp_periodo = pd.to_datetime(df_excel['Periodo'], errors='coerce')
            if temp_periodo.notna().any():
                spanish_months_map = {1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'}
                df_excel['Periodo'] = temp_periodo.dt.month.map(spanish_months_map).astype(str)
            else: df_excel['Periodo'] = df_excel['Periodo'].astype(str).str.strip().str.capitalize()
        except Exception: df_excel['Periodo'] = df_excel['Periodo'].astype(str).str.strip().str.capitalize()

    if 'CECO' in df_excel.columns:
        df_excel['CECO'] = pd.to_numeric(df_excel['CECO'], errors='coerce')
        df_excel.dropna(subset=['CECO'], inplace=True)
        df_excel['CECO'] = df_excel['CECO'].astype(int).astype(str)

    text_cols_for_filters_charts = ['Gerencia', 'Relación', 'Sexo', 'Función', 'Distrito', 'Ministerio', 'Rango Antiguedad', 'Rango Edad', 'Periodo', 'Nivel', 'CECO']
    for col in text_cols_for_filters_charts:
        if col not in df_excel.columns: df_excel[col] = 'no disponible'
        df_excel[col] = df_excel[col].astype(str).replace(['None', 'nan', ''], 'no disponible').str.strip()
        if col in ['Rango Antiguedad', 'Rango Edad']: df_excel[col] = df_excel[col].str.lower()
        elif col == 'Periodo': df_excel[col] = df_excel[col].str.capitalize()
    
    return df_excel

# --- INICIO DE LA APLICACIÓN ---
st.title("👥 Dotación 2025")

st.write("Estructura y distribución geográfica y por gerencia de personal")

uploaded_file = st.file_uploader("📂 Cargue aquí su archivo Excel de dotación", type=["xlsx"])
st.markdown("---")

COORDS_URL = "https://raw.githubusercontent.com/Tincho2002/dotacion_assa_2025/main/coordenadas.csv"
df_coords = load_coords_from_url(COORDS_URL)

if uploaded_file is not None:
    with st.spinner('Procesando archivo...'):
        df = load_and_clean_data(uploaded_file)
    if df.empty:
        st.error("El archivo cargado está vacío o no se pudo procesar correctamente.")
        st.stop()
    st.success(f"Se ha cargado un total de **{format_integer_es(len(df))}** registros de empleados.")
    st.markdown("---")

    st.sidebar.header('Filtros del Dashboard')
    
    filter_cols_config = {
        'Periodo': 'Periodo', 'Gerencia': 'Gerencia', 'Relación': 'Relación', 'Función': 'Función',
        'Distrito': 'Distrito', 'Ministerio': 'Ministerio', 'Rango Antiguedad': 'Antigüedad',
        'Rango Edad': 'Edad', 'Sexo': 'Sexo', 'Nivel': 'Nivel', 'CECO': 'Centro de Costo'
    }
    filter_cols = list(filter_cols_config.keys())

    if 'selections' not in st.session_state:
        initial_selections = {col: get_sorted_unique_options(df, col) for col in filter_cols}
        st.session_state.selections = initial_selections
        st.rerun()

    if st.sidebar.button("🔄 Resetear Filtros", use_container_width=True, key="reset_filters"):
        initial_selections = {col: get_sorted_unique_options(df, col) for col in filter_cols}
        st.session_state.selections = initial_selections
        if 'show_map_comp_check' in st.session_state:
            st.session_state['show_map_comp_check'] = False
        st.rerun()

    st.sidebar.markdown("---")
    
    old_selections = {k: list(v) for k, v in st.session_state.selections.items()}

    for col, title in filter_cols_config.items():
        available_options = get_available_options(df, st.session_state.selections, col)
        current_selection = [sel for sel in st.session_state.selections.get(col, []) if sel in available_options]
        selected = st.sidebar.multiselect(
            title,
            options=available_options,
            default=current_selection,
            key=f"multiselect_{col}"
        )
        st.session_state.selections[col] = selected

    if old_selections != st.session_state.selections:
        if 'show_map_comp_check' in st.session_state:
            st.session_state['show_map_comp_check'] = False
        st.rerun()

    filtered_df = apply_all_filters(df, st.session_state.selections)
    
    st.write(f"Después de aplicar los filtros, se muestran **{format_integer_es(len(filtered_df))}** registros.")
    st.markdown("---")
    
    period_to_display = None
    all_periodos = get_sorted_unique_options(df, 'Periodo')
    selected_periodos = st.session_state.selections.get('Periodo', [])
    
    if selected_periodos:
        sorted_selected_periods = [p for p in all_periodos if p in selected_periodos]
        if sorted_selected_periods:
            period_to_display = sorted_selected_periods[-1]

    if not filtered_df.empty and period_to_display:
        df_display = filtered_df[filtered_df['Periodo'] == period_to_display].copy()
        total_dotacion = len(df_display)
        convenio_count = df_display[df_display['Relación'] == 'Convenio'].shape[0]
        fc_count = df_display[df_display['Relación'] == 'FC'].shape[0]
        masculino_count = df_display[df_display['Sexo'] == 'Masculino'].shape[0]
        femenino_count = df_display[df_display['Sexo'] == 'Femenino'].shape[0]
        convenio_pct = (convenio_count / total_dotacion * 100) if total_dotacion > 0 else 0
        fc_pct = (fc_count / total_dotacion * 100) if total_dotacion > 0 else 0
        masculino_pct = (masculino_count / total_dotacion * 100) if total_dotacion > 0 else 0
        femenino_pct = (femenino_count / total_dotacion * 100) if total_dotacion > 0 else 0
        card_html = f"""
        <style>
            .summary-container {{ display: flex; background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); align-items: center; gap: 20px; border: 1px solid #e0e0e0; }}
            .summary-main-kpi {{ text-align: center; border-right: 2px solid #f0f2f6; padding-right: 20px; flex-grow: 1; }}
            .summary-main-kpi .title {{ font-size: 1.1rem; font-weight: bold; color: #2C3E50; margin-bottom: 5px; }}
            .summary-main-kpi .value {{ font-size: 3.5rem; font-weight: bold; color: #2C3E50; }}
            .summary-breakdown {{ display: flex; flex-direction: column; gap: 15px; flex-grow: 2; }}
            .summary-row {{ display: flex; justify-content: space-around; align-items: center; }}
            .summary-sub-kpi {{ text-align: left; display: flex; align-items: center; gap: 10px; width: 200px; }}
            .summary-sub-kpi .icon {{ font-size: 2rem; }}
            .summary-sub-kpi .details {{ display: flex; flex-direction: column; }}
            .summary-sub-kpi .value {{ font-size: 1.5rem; font-weight: bold; color: #34495E; }}
            .summary-sub-kpi .label {{ font-size: 0.9rem; color: #7F8C8D; }}
        </style>
        <div class="summary-container">
            <div class="summary-main-kpi">
                <div class="title">DOTACIÓN {period_to_display.upper()}</div>
                <div class="value" data-target="{total_dotacion}">👥 0</div>
            </div>
            <div class="summary-breakdown">
                <div class="summary-row">
                    <div class="summary-sub-kpi"><div class="icon">📄</div><div class="details"><div class="value" data-target="{convenio_count}">0</div><div class="label">Convenio ({format_percentage_es(convenio_pct)})</div></div></div>
                    <div class="summary-sub-kpi"><div class="icon">💼</div><div class="details"><div class="value" data-target="{fc_count}">0</div><div class="label">Fuera de Convenio ({format_percentage_es(fc_pct)})</div></div></div>
                </div>
                <div class="summary-row">
                    <div class="summary-sub-kpi"><div class="icon">👨</div><div class="details"><div class="value" data-target="{masculino_count}">0</div><div class="label">Masculino ({format_percentage_es(masculino_pct)})</div></div></div>
                    <div class="summary-sub-kpi"><div class="icon">👩</div><div class="details"><div class="value" data-target="{femenino_count}">0</div><div class="label">Femenino ({format_percentage_es(femenino_pct)})</div></div></div>
                </div>
            </div>
        </div>
        <script>
            function animateValue(obj, start, end, duration) {{
                let startTimestamp = null;
                const step = (timestamp) => {{
                    if (!startTimestamp) startTimestamp = timestamp;
                    const progress = Math.min((timestamp - startTimestamp) / duration, 1);
                    const currentVal = Math.floor(progress * (end - start) + start);
                    let formattedVal = currentVal.toString().replace(/\\B(?=(\\d{{3}})+(?!\\d))/g, ".");
                    if (obj.innerHTML.includes("👥")) {{ obj.innerHTML = '👥 ' + formattedVal; }} else {{ obj.innerHTML = formattedVal; }}
                    if (progress < 1) {{ window.requestAnimationFrame(step); }}
                }};
                window.requestAnimationFrame(step);
            }}
            const counters = document.querySelectorAll('.value[data-target]');
            counters.forEach(counter => {{ const target = +counter.getAttribute('data-target'); setTimeout(() => animateValue(counter, 0, target, 1500), 100); }});
        </script>
        """
        components.html(card_html, height=220)
        st.markdown("<br>", unsafe_allow_html=True)
    
    # ... (El resto del código de las pestañas sigue aquí) ...
    
else:
    st.info("Por favor, cargue un archivo Excel para comenzar el análisis.")
