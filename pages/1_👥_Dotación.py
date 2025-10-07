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
# Importaciones necesarias para el comparador de mapas
from streamlit_image_comparison import image_comparison
from PIL import Image



# --- Configuración de la página y Estilos CSS ---
st.set_page_config(layout="wide")
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
st.markdown("""
<style>
/* --- GENERAL PAGE LAYOUT --- */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    scroll-behavior: smooth;
}

/* --- BOTONES --- */
div[data-testid="stSidebar"] div[data-testid="stButton"] button {
    border-radius: 0.5rem;
    font-weight: 600;
    width: 100%;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
div.stDownloadButton button {
    background-color: #28a745;
    color: white;
    font-weight: 600;
    padding: 0.75rem 1.25rem;
    border-radius: 0.5rem;
    border: none;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}
div.stDownloadButton button:hover {
    background-color: #218838;
}

/* --- FLEXBOX PARA TARJETAS KPI --- */
.summary-container {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 1rem;
    padding: 1rem;
    border-radius: 10px;
    background-color: white;
    box-shadow: 0 4px 10px rgba(0,0,0,0.05);
}
.summary-main-kpi, .summary-breakdown {
    flex: 1 1 300px;
    min-width: 280px;
    text-align: center;
}
.summary-main-kpi .value {
    font-size: 2.5rem;
}
.summary-sub-kpi .value {
    font-size: 1.2rem;
}

/* --- RESPONSIVE: COLUMNAS (Tablas + Gráficos) --- */
@media (max-width: 900px) {
    [data-testid="stHorizontalBlock"] {
        flex-direction: column !important;
    }
    .summary-main-kpi .value { font-size: 2rem; }
    .summary-sub-kpi .value { font-size: 1rem; }
}
@media (max-width: 600px) {
    .summary-container {
        padding: 0.5rem;
    }
    .summary-main-kpi .value { font-size: 1.8rem; }
    div.stDownloadButton button {
        width: 100%;
        padding: 0.5rem 1rem;
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
        # **LA CORRECCIÓN**: Asegurar que la columna exista antes de intentar filtrar
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
        # Verificación añadida: Asegurarse de que la columna exista en el DataFrame antes de filtrar
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
st.set_page_config(page_title="Dotacion: 2025", page_icon="👥")
st.title("👥 Dotación 2025")

st.write("Estructura y distribución geográfica y por gerencia de personal")

# --- Cuerpo Principal de la Aplicación ---
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

    # --- INICIO: LÓGICA DE FILTROS TIPO SLICER ---
    st.sidebar.header('Filtros del Dashboard')
    
    filter_cols_config = {
        'Periodo': 'Periodo', 'Gerencia': 'Gerencia', 'Relación': 'Relación', 'Función': 'Función',
        'Distrito': 'Distrito', 'Ministerio': 'Ministerio', 'Rango Antiguedad': 'Antigüedad',
        'Rango Edad': 'Edad', 'Sexo': 'Sexo', 'Nivel': 'Nivel', 'CECO': 'Centro de Costo'
    }
    filter_cols = list(filter_cols_config.keys())

    # 1. INICIALIZACIÓN DEL ESTADO: Si es la primera vez, llena todos los filtros.
    if 'selections' not in st.session_state:
        initial_selections = {col: get_sorted_unique_options(df, col) for col in filter_cols}
        st.session_state.selections = initial_selections
        st.rerun()

    # 2. BOTÓN DE RESETEO: Restablece el estado al inicial (todo seleccionado).
    if st.sidebar.button("🔄 Resetear Filtros", use_container_width=True, key="reset_filters"):
        initial_selections = {col: get_sorted_unique_options(df, col) for col in filter_cols}
        st.session_state.selections = initial_selections
        #AÑADIR ESTO para el checkbox
        # Forzar el reseteo del checkbox del mapa si existe en el estado de sesión
        if 'show_map_comp_check' in st.session_state:
            st.session_state['show_map_comp_check'] = False
        
        st.rerun()

    st.sidebar.markdown("---")

    # 3. LÓGICA DE RENDERIZADO Y ACTUALIZACIÓN (SLICER)
    # Guardamos una copia del estado ANTES de que el usuario interactúe.
    old_selections = {k: list(v) for k, v in st.session_state.selections.items()}

    # Iteramos para crear cada filtro.
    for col, title in filter_cols_config.items():
        # Las opciones disponibles se basan en el estado actual de los OTROS filtros.
        available_options = get_available_options(df, st.session_state.selections, col)
        
        # Las selecciones por defecto son las que ya están en el estado, si siguen siendo válidas.
        current_selection = [sel for sel in st.session_state.selections.get(col, []) if sel in available_options]
        
        # Creamos el widget multiselect.
        selected = st.sidebar.multiselect(
            title,
            options=available_options,
            default=current_selection,
            key=f"multiselect_{col}"
        )
        
        # Actualizamos el estado de la sesión con el valor que tiene el widget ahora.
        st.session_state.selections[col] = selected

    # 4. DETECCIÓN DE CAMBIOS: Si el estado cambió, recargamos la app para que todo se actualice.
    if old_selections != st.session_state.selections:
        # AÑADIR ESTO: Si los filtros cambian, forzamos la casilla del mapa a desmarcarse.
        # La clave es 'show_map_comp_check'
        if 'show_map_comp_check' in st.session_state:
            st.session_state['show_map_comp_check'] = False
        st.rerun()
    # --- FIN: LÓGICA DE FILTROS ---

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
                    if (obj.innerHTML.includes("👥")) {{ obj.innerHTML = `👥 ${{formattedVal}}`; }} else {{ obj.innerHTML = formattedVal; }}
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

    tab_names = ["📊 Resumen de Dotación", "⏳ Edad y Antigüedad", "📈 Desglose por Categoría", "📋 Datos Brutos"]
    if not df_coords.empty:
        tab_names.insert(1, "🗺️ Mapa Geográfico")
        tab_names.insert(1, "🗺️ Comparador de Mapas")
    
    tabs = st.tabs(tab_names)
    tab_map_comparador, tab_map_individual = (None, None)
    
    tab_resumen = tabs[0]
    tab_index = 1
    if not df_coords.empty:
        tab_map_comparador = tabs[tab_index]
        tab_index += 1
        tab_map_individual = tabs[tab_index]
        tab_index += 1
    tab_edad_antiguedad = tabs[tab_index]
    tab_desglose = tabs[tab_index + 1]
    tab_brutos = tabs[tab_index + 2]

    with tab_resumen:
        st.header('Resumen General de la Dotación')
        if filtered_df.empty:
            st.warning("No hay datos para mostrar con los filtros seleccionados.")
        else:
            st.metric(label="Total de Empleados (filtrado)", value=format_integer_es(len(filtered_df)))
            st.subheader('Dotación por Periodo (Total)')
            col_table_periodo, col_chart_periodo = st.columns([1, 2])
            periodo_counts = filtered_df.groupby('Periodo').size().reset_index(name='Cantidad')
            periodo_counts['Periodo'] = pd.Categorical(periodo_counts['Periodo'], categories=all_periodos, ordered=True)
            periodo_counts = periodo_counts.sort_values('Periodo').reset_index(drop=True)
            with col_chart_periodo:
                line_periodo = alt.Chart(periodo_counts).mark_line(point=True).encode(x=alt.X('Periodo', sort=all_periodos, title='Periodo'), y=alt.Y('Cantidad', title='Cantidad Total de Empleados', scale=alt.Scale(zero=False)), tooltip=['Periodo', alt.Tooltip('Cantidad', format=',.0f')])
                text_periodo = line_periodo.mark_text(align='center', baseline='bottom', dy=-10, color='black').encode(text='Cantidad:Q')
                st.altair_chart((line_periodo + text_periodo), use_container_width=True)
            with col_table_periodo:
                st.dataframe(periodo_counts.style.format({"Cantidad": format_integer_es}))
                generate_download_buttons(periodo_counts, 'dotacion_total_por_periodo', key_suffix="_resumen1")
            st.markdown('---')
            st.subheader('Distribución Comparativa por Sexo')
            col_table_sexo, col_chart_sexo = st.columns([1, 2])
            sexo_pivot = filtered_df.groupby(['Periodo', 'Sexo']).size().unstack(fill_value=0).reindex(all_periodos, fill_value=0).reset_index()
            with col_chart_sexo:
                if not sexo_pivot.empty:
                    fig_sexo = make_subplots(specs=[[{"secondary_y": True}]])
                    if 'Masculino' in sexo_pivot.columns:
                        fig_sexo.add_trace(go.Bar(x=sexo_pivot['Periodo'], y=sexo_pivot['Masculino'], name='Masculino', marker_color='#5b9bd5', text=sexo_pivot['Masculino'], textposition='outside'), secondary_y=False)
                        min_v, max_v = sexo_pivot['Masculino'].min(), sexo_pivot['Masculino'].max(); rng = max_v - min_v; pad = max(1, rng * 0.1) if rng > 0 else max(1, abs(min_v * 0.1))
                        fig_sexo.update_yaxes(title_text="Cantidad Masculino", range=[min_v - pad, max_v + pad * 1.5], secondary_y=False, showgrid=False)
                    if 'Femenino' in sexo_pivot.columns:
                        fig_sexo.add_trace(go.Scatter(x=sexo_pivot['Periodo'], y=sexo_pivot['Femenino'], name='Femenino', mode='lines+markers+text', text=sexo_pivot['Femenino'], textposition='top center', line=dict(color='#ed7d31')), secondary_y=True)
                        fig_sexo.update_yaxes(title_text="Cantidad Femenino", secondary_y=True, showgrid=True)
                    fig_sexo.update_layout(title_text="Distribución Comparativa por Sexo", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                    st.plotly_chart(fig_sexo, use_container_width=True, key="sexo_chart")
            with col_table_sexo:
                sexo_pivot['Total'] = sexo_pivot.get('Masculino', 0) + sexo_pivot.get('Femenino', 0)
                st.dataframe(sexo_pivot.style.format(formatter=format_integer_es, subset=[c for c in ['Masculino', 'Femenino', 'Total'] if c in sexo_pivot.columns]))
                generate_download_buttons(sexo_pivot, 'distribucion_sexo_por_periodo', key_suffix="_resumen2")
            st.markdown('---')
            st.subheader('Distribución Comparativa por Relación')
            col_table_rel, col_chart_rel = st.columns([1, 2])
            rel_pivot = filtered_df.groupby(['Periodo', 'Relación']).size().unstack(fill_value=0).reindex(all_periodos, fill_value=0).reset_index()
            with col_chart_rel:
                if not rel_pivot.empty:
                    fig_rel = make_subplots(specs=[[{"secondary_y": True}]])
                    if 'Convenio' in rel_pivot.columns:
                        fig_rel.add_trace(go.Bar(x=rel_pivot['Periodo'], y=rel_pivot['Convenio'], name='Convenio', marker_color='#4472c4', text=rel_pivot['Convenio'], textposition='outside'), secondary_y=False)
                        min_v, max_v = rel_pivot['Convenio'].min(), rel_pivot['Convenio'].max(); rng = max_v - min_v; pad = max(1, rng * 0.1) if rng > 0 else max(1, abs(min_v * 0.1))
                        fig_rel.update_yaxes(title_text="Cantidad Convenio", range=[min_v - pad, max_v + pad * 1.5], secondary_y=False, showgrid=False)
                    if 'FC' in rel_pivot.columns:
                        fig_rel.add_trace(go.Scatter(x=rel_pivot['Periodo'], y=rel_pivot['FC'], name='FC', mode='lines+markers+text', text=rel_pivot['FC'], textposition='top center', line=dict(color='#ffc000')), secondary_y=True)
                        fig_rel.update_yaxes(title_text="Cantidad FC", secondary_y=True, showgrid=True)
                    fig_rel.update_layout(title_text="Distribución Comparativa por Relación", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                    st.plotly_chart(fig_rel, use_container_width=True, key="rel_chart")
            with col_table_rel:
                rel_pivot['Total'] = rel_pivot.get('Convenio', 0) + rel_pivot.get('FC', 0)
                st.dataframe(rel_pivot.style.format(formatter=format_integer_es, subset=[c for c in ['Convenio', 'FC', 'Total'] if c in rel_pivot.columns]))
                generate_download_buttons(rel_pivot, 'distribucion_relacion_por_periodo', key_suffix="_resumen3")
            st.markdown('---')
            st.subheader('Variación Mensual de Dotación')
            col_table_var, col_chart_var = st.columns([1, 2])
            var_counts = filtered_df.groupby('Periodo').size().reindex(all_periodos, fill_value=0).reset_index(name='Cantidad_Actual')
            var_counts['Variacion_Cantidad'] = var_counts['Cantidad_Actual'].diff()
            var_counts['Variacion_%'] = (var_counts['Variacion_Cantidad'] / var_counts['Cantidad_Actual'].shift(1) * 100).replace([np.inf, -np.inf], 0)
            var_counts['label'] = var_counts.apply(lambda r: f"{format_integer_es(r['Variacion_Cantidad'])} ({format_percentage_es(r['Variacion_%'], 2)})" if pd.notna(r['Variacion_Cantidad']) and r.name > 0 else "", axis=1)
            with col_table_var:
                st.dataframe(var_counts.style.format({"Cantidad_Actual": format_integer_es, "Variacion_Cantidad": format_integer_es, "Variacion_%": lambda x: format_percentage_es(x, 2)}))
                generate_download_buttons(var_counts, 'variacion_mensual_total', key_suffix="_resumen4")
            with col_chart_var:
                chart_var = alt.Chart(var_counts.iloc[1:]).mark_bar().encode(x=alt.X('Periodo', sort=all_periodos), y=alt.Y('Variacion_Cantidad', title='Variación'), color=alt.condition(alt.datum.Variacion_Cantidad > 0, alt.value("green"), alt.value("red")), tooltip=['Periodo', 'Variacion_Cantidad', alt.Tooltip('Variacion_%', format='.2f')])
                text_var = chart_var.mark_text(align='center', baseline='middle', dy=alt.expr("datum.Variacion_Cantidad > 0 ? -10 : 15"), color='white').encode(text='label:N')
                st.altair_chart(chart_var + text_var, use_container_width=True)

    if tab_map_comparador and period_to_display:
        with tab_map_comparador:
            st.header(f"Comparador de Mapas para el Período: {period_to_display}")
            map_style_options = {
                "Satélite con Calles": "satellite-streets",
                "Mapa de Calles": "open-street-map",
                "Estilo Claro": "carto-positron",
            }
            c1, c2 = st.columns(2)
            with c1:
                style1_name = st.selectbox("Selecciona el estilo del mapa izquierdo:", options=list(map_style_options.keys()), index=0, key="map_style1")
            with c2:
                style2_name = st.selectbox("Selecciona el estilo del mapa derecho:", options=list(map_style_options.keys()), index=1, key="map_style2")

            st.markdown("---")
            
            # 2. BOTÓN DE ACTIVACIÓN/CARGA CONDICIONAL
            show_map_comparison = st.checkbox("✅ Mostrar Comparación de Mapas", value=False, key="show_map_comp_check")
            
            def generate_map_figure(df, mapbox_style):
                df_mapa_data = pd.merge(df, df_coords, on="Distrito", how="left")
                df_mapa_agg = df_mapa_data.groupby(['Distrito', 'Latitud', 'Longitud']).size().reset_index(name='Dotacion_Total')
                df_mapa_agg.dropna(subset=['Latitud', 'Longitud'], inplace=True)
                if df_mapa_agg.empty:
                    return None
                mapbox_access_token = "pk.eyJ1Ijoic2FuZHJhcXVldmVkbyIsImEiOiJjbWYzOGNkZ2QwYWg0MnFvbDJucWc5d3VwIn0.bz6E-qxAwk6ZFPYohBsdMw"
                px.set_mapbox_access_token(mapbox_access_token)
                fig = px.scatter_mapbox(
                    df_mapa_agg,
                    lat="Latitud", lon="Longitud",
                    size="Dotacion_Total", color="Dotacion_Total",
                    hover_name="Distrito",
                    hover_data={"Latitud": False, "Longitud": False, "Dotacion_Total": True},
                    color_continuous_scale=px.colors.sequential.Plasma, 
                    size_max=50,
                    mapbox_style=mapbox_style, 
                    zoom=6, center={"lat": -32.5, "lon": -61.5}
                )
                fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
                return fig

            # 3. LÓGICA CONDICIONAL: Solo si el usuario quiere ver el mapa.
            if show_map_comparison:
                df_mapa_display = filtered_df[filtered_df['Periodo'] == period_to_display]
                
                if 'Distrito' not in df_mapa_display.columns or 'Distrito' not in df_coords.columns:
                    st.warning("La columna 'Distrito' no se encuentra en los datos o en el archivo de coordenadas.")
                else:
                    # Uso la proporción [3, 2] que ya habías corregido para la tabla.
                    comp_col1, comp_col2 = st.columns([3, 2]) 
                    with comp_col1:
                        with st.spinner(f"Generando mapas ({style1_name} vs {style2_name})..."):
                            try:
                                fig1 = generate_map_figure(df_mapa_display, map_style_options[style1_name])
                                fig2 = generate_map_figure(df_mapa_display, map_style_options[style2_name])
                                if fig1 and fig2:
                                    # Las importaciones ya están al inicio del archivo
                                    # from streamlit_image_comparison import image_comparison 
                                    # from PIL import Image
                                    
                                    # MANTENEMOS EL AJUSTE PARA ESTABILIDAD
                                    img1_bytes = fig1.to_image(format="png", scale=2, engine="kaleido")
                                    img2_bytes = fig2.to_image(format="png", scale=2, engine="kaleido")
                                    img1_pil = Image.open(io.BytesIO(img1_bytes))
                                    img2_pil = Image.open(io.BytesIO(img2_bytes))
                                    
                                    # AGREGAMOS UN ANCHO ADECUADO PARA QUE SE VEA GRANDE
                                    image_comparison(
                                        img1=img1_pil,
                                        img2=img2_pil,
                                        label1=style1_name,
                                        label2=style2_name,
                                        width=850, # Ajuste el ancho a 850, puedes probar 800 o 900.
                                    )
                                else:
                                    st.warning("No hay datos de ubicación para mostrar en el mapa para el período seleccionado.")
                            except Exception as e:
                                st.error(f"Ocurrió un error al generar las imágenes del mapa: {e}")
                                st.info("Intente recargar la página o seleccionar un período con menos datos.")
                    
                    with comp_col2:
                            # Código de la tabla de pivot:
                            pivot_table = pd.pivot_table(data=df_mapa_display, index='Distrito', columns='Relación', aggfunc='size', fill_value=0)
                            if 'Convenio' not in pivot_table.columns: pivot_table['Convenio'] = 0
                            if 'FC' not in pivot_table.columns: pivot_table['FC'] = 0
                            pivot_table['Total'] = pivot_table['Convenio'] + pivot_table['FC']
                            pivot_table.sort_values(by='Total', ascending=False, inplace=True)
                            total_row = pd.DataFrame({'Distrito': ['**TOTAL GENERAL**'], 'Convenio': [pivot_table['Convenio'].sum()], 'FC': [pivot_table['FC'].sum()], 'Total': [pivot_table['Total'].sum()]})
                            df_final_table = pd.concat([pivot_table.reset_index(), total_row], ignore_index=True)
                            # NOTA: Asegúrate de que este `height` sea adecuado para tu pantalla
                            st.dataframe(df_final_table.style.format({'Convenio': '{:,}', 'FC': '{:,}', 'Total': '{:,}'}).set_properties(**{'text-align': 'right'}), use_container_width=True, height=500, hide_index=True)
            
            else:
                # 4. Mensaje que se muestra si el checkbox NO está marcado.
                st.info("Seleccione los estilos de mapa deseados y marque la casilla 'Mostrar Comparación de Mapas' para visualizar y generar la comparación.")
    # --- FIN CORRECCIÓN DEL BLOQUE tab_map_comparador ---

    if tab_map_individual and period_to_display:
        with tab_map_individual:
            st.header(f"Distribución Geográfica para el Período: {period_to_display}")
            map_style_options = {"Satélite con Calles": "satellite-streets", "Mapa de Calles": "open-street-map", "Estilo Claro": "carto-positron"}
            selected_style_name = st.selectbox("Selecciona el estilo del mapa:", list(map_style_options.keys()), key="map_style_individual")
            selected_mapbox_style = map_style_options[selected_style_name]
            df_mapa_display = filtered_df[filtered_df['Periodo'] == period_to_display]
            col_map, col_table = st.columns([3, 2])
            with col_map:
                if 'Distrito' not in df_mapa_display.columns or 'Distrito' not in df_coords.columns:
                    st.warning("La columna 'Distrito' es necesaria para la visualización del mapa.")
                else:
                    df_mapa_data = pd.merge(df_mapa_display, df_coords, on="Distrito", how="left").dropna(subset=['Latitud', 'Longitud'])
                    df_mapa_agg = df_mapa_data.groupby(['Distrito', 'Latitud', 'Longitud']).size().reset_index(name='Dotacion_Total')
                    if df_mapa_agg.empty: st.warning("No hay datos de ubicación para mostrar en el mapa para la selección actual.")
                    else:
                        mapbox_access_token = "pk.eyJ1Ijoic2FuZHJhcXVldmVkbyIsImEiOiJjbWYzOGNkZ2QwYWg0MnFvbDJucWc5d3VwIn0.bz6E-qxAwk6ZFPYohBsdMw"
                        px.set_mapbox_access_token(mapbox_access_token)
                        fig = px.scatter_mapbox(df_mapa_agg, lat="Latitud", lon="Longitud", size="Dotacion_Total", color="Dotacion_Total", hover_name="Distrito", color_continuous_scale=px.colors.sequential.Plasma, size_max=50, mapbox_style=selected_mapbox_style, zoom=6, center={"lat": -32.5, "lon": -61.5})
                        fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
                        st.plotly_chart(fig, use_container_width=True, key="map_individual_chart")
            with col_table:
                # st.markdown("##### Dotación por Distrito")
                pivot_table = pd.pivot_table(data=df_mapa_display, index='Distrito', columns='Relación', aggfunc='size', fill_value=0)
                if 'Convenio' not in pivot_table.columns: pivot_table['Convenio'] = 0
                if 'FC' not in pivot_table.columns: pivot_table['FC'] = 0
                pivot_table['Total'] = pivot_table['Convenio'] + pivot_table['FC']
                pivot_table.sort_values(by='Total', ascending=False, inplace=True)
                total_row = pd.DataFrame({'Distrito': ['**TOTAL GENERAL**'], 'Convenio': [pivot_table['Convenio'].sum()], 'FC': [pivot_table['FC'].sum()], 'Total': [pivot_table['Total'].sum()]})
                df_final_table = pd.concat([pivot_table.reset_index(), total_row], ignore_index=True)
                st.dataframe(df_final_table.style.format({'Convenio': '{:,}', 'FC': '{:,}', 'Total': '{:,}'}).set_properties(**{'text-align': 'right'}), use_container_width=True, height=460, hide_index=True)

    with tab_edad_antiguedad:
        st.header('Análisis de Edad y Antigüedad por Periodo')
        if filtered_df.empty or not selected_periodos: st.warning("No hay datos para mostrar con los filtros seleccionados.")
        else:
            periodo_a_mostrar_edad = st.selectbox('Selecciona un Periodo:', selected_periodos, index=len(selected_periodos) - 1 if selected_periodos else 0, key='periodo_selector_edad')
            df_periodo_edad = filtered_df[filtered_df['Periodo'] == periodo_a_mostrar_edad]
            st.subheader(f'Distribución por Edad para {periodo_a_mostrar_edad}'); col_table_edad, col_chart_edad = st.columns([1, 2])
            with col_chart_edad:
                all_rangos_edad = get_sorted_unique_options(df, 'Rango Edad')
                bars_edad = alt.Chart(df_periodo_edad).mark_bar().encode(x=alt.X('Rango Edad:N', sort=all_rangos_edad), y=alt.Y('count():Q', title='Cantidad'), color='Relación:N', tooltip=[alt.Tooltip('count()', format=',.0f'), 'Relación'])
                total_labels_edad = alt.Chart(df_periodo_edad).transform_aggregate(total_count='count()', groupby=['Rango Edad']).mark_text(dy=-8, align='center', color='black').encode(x=alt.X('Rango Edad:N', sort=all_rangos_edad), y=alt.Y('total_count:Q'), text=alt.Text('total_count:Q'))
                st.altair_chart(bars_edad + total_labels_edad, use_container_width=True)
            with col_table_edad:
                edad_table = df_periodo_edad.groupby(['Rango Edad', 'Relación']).size().unstack(fill_value=0)
                edad_table['Total'] = edad_table.sum(axis=1)
                st.dataframe(edad_table.style.format(format_integer_es))
                generate_download_buttons(edad_table.reset_index(), f'distribucion_edad_{periodo_a_mostrar_edad}', key_suffix="_edad")
            st.markdown('---')
            st.subheader(f'Distribución por Antigüedad para {periodo_a_mostrar_edad}'); col_table_ant, col_chart_ant = st.columns([1, 2])
            with col_chart_ant:
                all_rangos_antiguedad = get_sorted_unique_options(df, 'Rango Antiguedad')
                bars_antiguedad = alt.Chart(df_periodo_edad).mark_bar().encode(x=alt.X('Rango Antiguedad:N', sort=all_rangos_antiguedad), y=alt.Y('count():Q', title='Cantidad'), color='Relación:N', tooltip=[alt.Tooltip('count()', format=',.0f'), 'Relación'])
                total_labels_antiguedad = alt.Chart(df_periodo_edad).transform_aggregate(total_count='count()', groupby=['Rango Antiguedad']).mark_text(dy=-8, align='center', color='black').encode(x=alt.X('Rango Antiguedad:N', sort=all_rangos_antiguedad), y=alt.Y('total_count:Q'), text=alt.Text('total_count:Q'))
                st.altair_chart(bars_antiguedad + total_labels_antiguedad, use_container_width=True)
            with col_table_ant:
                antiguedad_table = df_periodo_edad.groupby(['Rango Antiguedad', 'Relación']).size().unstack(fill_value=0)
                antiguedad_table['Total'] = antiguedad_table.sum(axis=1)
                st.dataframe(antiguedad_table.style.format(format_integer_es))
                generate_download_buttons(antiguedad_table.reset_index(), f'distribucion_antiguedad_{periodo_a_mostrar_edad}', key_suffix="_antiguedad")

    with tab_desglose:
        st.header('Desglose Detallado por Categoría por Periodo')
        if filtered_df.empty or not selected_periodos: st.warning("No hay datos para mostrar.")
        else:
            periodo_a_mostrar_desglose = st.selectbox('Seleccionar Periodo:', selected_periodos, index=len(selected_periodos) - 1 if selected_periodos else 0, key='periodo_selector_desglose')
            cat_seleccionada = st.selectbox('Seleccionar Categoría:', ['Gerencia', 'Ministerio', 'Función', 'Distrito', 'Nivel'], key='cat_selector_desglose')
            df_periodo_desglose = filtered_df[filtered_df['Periodo'] == periodo_a_mostrar_desglose]
            st.subheader(f'Dotación por {cat_seleccionada} para {periodo_a_mostrar_desglose}')
            col_table_cat, col_chart_cat = st.columns([1, 2])
            with col_chart_cat:
                chart = alt.Chart(df_periodo_desglose).mark_bar().encode(x=alt.X(f'{cat_seleccionada}:N', sort='-y'), y=alt.Y('count():Q', title='Cantidad'), color=f'{cat_seleccionada}:N', tooltip=[alt.Tooltip('count()', format=',.0f'), cat_seleccionada])
                text_labels = chart.mark_text(align='center', baseline='middle', dy=-10).encode(text='count():Q')
                st.altair_chart(chart + text_labels, use_container_width=True)
            with col_table_cat:
                table_data = df_periodo_desglose.groupby(cat_seleccionada).size().reset_index(name='Cantidad').sort_values('Cantidad', ascending=False)
                st.dataframe(table_data.style.format({"Cantidad": format_integer_es}))
                generate_download_buttons(table_data, f'dotacion_{cat_seleccionada.lower()}_{periodo_a_mostrar_desglose}', key_suffix="_desglose")

    with tab_brutos:
        st.header('Tabla de Datos Filtrados')
        display_df = filtered_df.copy()
        if 'LEGAJO' in display_df.columns:
            display_df['LEGAJO'] = display_df['LEGAJO'].apply(lambda x: format_integer_es(x) if pd.notna(x) else '')
        st.dataframe(display_df)
        generate_download_buttons(filtered_df, 'datos_filtrados_dotacion', key_suffix="_brutos")

else:
    st.info("Por favor, cargue un archivo Excel para comenzar el análisis.")


