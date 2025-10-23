import streamlit as st
import pandas as pd
import altair as alt
from io import BytesIO
from fpdf import FPDF
import numpy as np
from datetime import datetime
import streamlit.components.v1 as components
import plotly.graph_objects as go
import re

# --- Configuración de la página ---
st.set_page_config(layout="wide", page_title="Indicadores de Eficiencia", page_icon="🎯")

# --- CSS Personalizado para un Estilo Profesional y RESPONSIVE ---
st.markdown("""
<style>
/* --- TEMA PERSONALIZADO PARA CONSISTENCIA VISUAL --- */
:root {
    --primary-color: #007BFF; /* Azul brillante */
    --secondary-color: #28A745; /* Verde para éxito */
    --warning-color: #FFC107; /* Amarillo para advertencia */
    --danger-color: #DC3545; /* Rojo para peligro */
    --info-color: #17A2B8; /* Azul claro para información */
    --background-color: #f0f2f6; /* Fondo gris claro */
    --secondary-background-color: #ffffff; /* Fondo blanco para tarjetas y sidebar */
    --text-color: #343A40; /* Gris oscuro para el texto principal */
    --light-text-color: #6C757D; /* Gris claro para texto secundario */
    --font: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

/* Forzar un fondo claro y color de texto oscuro para evitar el modo oscuro del sistema */
body, .stApp {
    background-color: var(--background-color) !important;
    color: var(--text-color) !important;
}

/* --- GENERAL Y TIPOGRAFÍA --- */
.stApp {
    font-size: 0.92rem;
    font-family: var(--font);
}

/* Forzar color de texto oscuro en elementos genéricos que Streamlit pueda cambiar */
p, div, span, label, li, h1, h2, h3, h4, h5, h6 {
    color: var(--text-color);
}

/* Estilo consistente para títulos y subtítulos */
h1 { font-size: 2.2rem; border-bottom: 2px solid var(--primary-color); padding-bottom: 10px; margin-bottom: 20px;}
h2 { font-size: 1.6rem; color: var(--text-color);}
h3 { font-size: 1.3rem; color: var(--light-text-color);}

/* --- Sidebar y Filtros --- */
[data-testid="stSidebar"] {
    background-color: var(--secondary-background-color);
    box-shadow: 2px 0 5px rgba(0,0,0,0.05);
}
div[data-testid="stSidebar"] .stSelectbox {
    margin-bottom: 1rem;
}
div[data-testid="stSidebar"] h2 {
    color: var(--primary-color);
}

/* Botones de control (Resetear) */
div[data-testid="stSidebar"] div[data-testid="stButton"] button {
    background-color: var(--primary-color);
    color: white;
    font-weight: bold;
    border-radius: 0.5rem;
    width: 100%;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    border: none;
    padding: 0.75rem 1.25rem;
    transition: background-color 0.2s ease;
}
div[data-testid="stSidebar"] div[data-testid="stButton"] button:hover {
    background-color: #0056b3; /* Un azul más oscuro */
}

/* --- Redondear esquinas de los gráficos --- */
[data-testid="stAltairChart"], [data-testid="stPlotlyChart"] {
    border-radius: 0.8rem;
    overflow: hidden;
    box-shadow: 0 4px 10px rgba(0,0,0,0.08); /* Sombra más pronunciada para gráficos */
    background-color: var(--secondary-background-color);
    padding: 1rem; /* Espaciado interno para el gráfico */
}

/* --- KPI Metrics Card --- */
[data-testid="stMetric"] {
    background-color: var(--secondary-background-color);
    border: 1px solid #E0E0E0;
    border-radius: 8px;
    padding: 1rem;
    text-align: center;
    box-shadow: 0 4px 8px rgba(0,0,0,0.05);
    transition: all 0.3s ease-in-out;
}
[data-testid="stMetric"]:hover {
    transform: translateY(-5px);
    box-shadow: 0 8px 16px rgba(0,0,0,0.1);
}

[data-testid="stMetricLabel"] {
    font-weight: 600;
    font-size: 0.95rem;
    color: var(--light-text-color);
}
[data-testid="stMetricValue"] {
    font-size: 2.2rem;
    font-weight: bold;
    color: var(--primary-color);
    margin-top: 0.5rem;
    margin-bottom: 0.2rem;
}
[data-testid="stMetricDelta"] {
    font-size: 1.0rem;
    font-weight: 500;
}
[data-testid="stMetricDelta"] svg {
    display: none; /* Oculta la flecha por defecto de Streamlit */
}
/* Estilo para los deltas personalizados */
.delta.green { color: #2ca02c; }
.delta.red { color: #d62728; }
.delta {
    font-size: 1.0rem;
    font-weight: 600;
    margin-top: 5px;
}
.delta-arrow {
    display: inline-block;
    width: 0;
    height: 0;
    margin-left: 5px;
    vertical-align: middle;
}
.delta-arrow.up {
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-bottom: 5px solid #2ca02c; /* Verde */
}
.delta-arrow.down {
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 5px solid #d62728; /* Rojo */
}


/* --- TABLAS STREAMLIT (DataFrame) --- */
.stDataFrame {
    width: 100%;
    border: none;
    border-radius: 8px;
    box-shadow: 0 4px 10px rgba(0,0,0,0.05);
    transition: background-color 0.3s ease-in-out, border-color 0.3s ease-in-out;
    background-color: var(--secondary-background-color);
}
.stDataFrame thead th {
    background-color: var(--primary-color);
    color: white;
    font-weight: bold;
    text-align: left;
    padding: 12px 15px;
    font-size: 0.95rem;
    border-bottom: 2px solid #0056b3;
}
.stDataFrame tbody tr:nth-of-type(even) {
    background-color: #f8f9fa; /* Ligeramente diferente para filas pares */
}
.stDataFrame tbody tr:hover {
    background-color: #e9f7ff; /* Fondo azul claro al pasar el ratón */
}
.stDataFrame tbody td {
    padding: 10px 15px;
    text-align: right;
    border-bottom: 1px solid #e9ecef;
    color: var(--text-color);
}
.stDataFrame tbody td:first-child {
    text-align: left;
    font-weight: 500;
}

/* --- Botones de Descarga --- */
div[data-testid="stDownloadButton"] button {
    background-color: var(--secondary-color);
    color: white;
    font-weight: bold;
    padding: 0.75rem 1.25rem;
    border-radius: 0.5rem;
    border: none;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    transition: all 0.2s ease-in-out;
}
div[data-testid="stDownloadButton"] button:hover {
    background-color: #218838; /* Verde más oscuro */
    transform: translateY(-2px);
    box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
}

/* --- Pestañas (Tabs) --- */
.stTabs [data-baseweb="tab"] {
    border-radius: 6px 6px 0 0;
    padding: 10px 20px;
    font-weight: 600;
    background-color: #e9ecef; /* Fondo de pestañas inactivas */
    color: var(--light-text-color);
    border: 1px solid #dee2e6;
    border-bottom: none;
    margin-right: 2px;
}
.stTabs [data-baseweb="tab"][aria-selected="true"] {
    background-color: var(--secondary-background-color);
    color: var(--primary-color);
    border-bottom: 3px solid var(--primary-color);
    border-top: 1px solid var(--primary-color);
    border-left: 1px solid var(--primary-color);
    border-right: 1px solid var(--primary-color);
    padding-bottom: 7px; /* Ajuste para el borde inferior */
}

/* --- Layout Responsive General --- */
@media (max-width: 768px) {
    h1 { font-size: 1.8rem; }
    h2 { font-size: 1.3rem; }
    h3 { font-size: 1rem; }

    div[data-testid="stHorizontalBlock"] {
        flex-wrap: wrap !important;
    }
    div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
        flex: 1 1 100% !important;
        min-width: 100% !important;
        margin-bottom: 1rem;
    }
    .stTabs {
        overflow-x: auto; /* Permite scroll horizontal en tabs en móviles */
    }
    [data-testid="stMetric"] {
        padding: 0.8rem;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.8rem;
    }
    [data-testid="stMetricLabel"], .delta {
        font-size: 0.85rem;
    }
}
</style>
""", unsafe_allow_html=True)


# --- Funciones de Formato de Números ---
custom_format_locale = {
    "decimal": ",", "thousands": ".", "grouping": [3], "currency": ["$", ""]
}
alt.renderers.set_embed_options(formatLocale=custom_format_locale)

def format_number_es(num):
    if pd.isna(num) or not isinstance(num, (int, float, np.number)): return ""
    s = f"{num:,.2f}"
    return s.replace(",", "TEMP").replace(".", ",").replace("TEMP", ".")

def format_integer_es(num):
    if pd.isna(num) or not isinstance(num, (int, float, np.number)): return ""
    s = f"{int(num):,}"
    return s.replace(",", ".")

def format_percentage_es(num, decimals=1):
    if pd.isna(num) or not isinstance(num, (int, float, np.number)): return ""
    return f"{num:,.{decimals}f}%".replace(",", "TEMP").replace(".", ",").replace("TEMP", ".")

# --- Funciones Auxiliares ---
def get_delta_string(current_val, prev_val):
    if prev_val == 0:
        if current_val > 0:
            return '<div class="delta green">▲ 100.0%</div>' # Aumento infinito, representamos como 100%
        else:
            return None # No hay cambio si ambos son 0
    
    delta_pct = ((current_val - prev_val) / prev_val) * 100
    color = 'green' if delta_pct >= 0 else 'red'
    arrow = 'up' if delta_pct >= 0 else 'down'
    return f'<div class="delta {color}"><span class="delta-arrow {arrow}"></span> {delta_pct:,.1f}%</div>'

def generate_download_buttons(df_to_download, filename_prefix, key_suffix=""):
    st.markdown("##### Opciones de Descarga:")
    col_dl1, col_dl2 = st.columns(2)
    csv_buffer = BytesIO()
    df_to_download.to_csv(csv_buffer, index=False)
    with col_dl1:
        st.download_button(label="⬇️ Descargar como CSV", data=csv_buffer.getvalue().decode('utf-8'), file_name=f"{filename_prefix}.csv", mime="text/csv", key=f"csv_download_{filename_prefix}{key_suffix}")
    excel_buffer = BytesIO()
    df_to_download.to_excel(excel_buffer, index=False, engine='openpyxl')
    excel_buffer.seek(0)
    with col_dl2:
        st.download_button(label="📊 Descargar como Excel", data=excel_buffer.getvalue(), file_name=f"{filename_prefix}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key=f"excel_download_{filename_prefix}{key_suffix}")

def apply_all_filters(df, selections):
    _df = df.copy()
    for col, values in selections.items():
        if values and col in _df.columns: 
            if col == 'Años': # Convertir los años a string para el filtro de lista
                _df = _df[_df['Año'].astype(str).isin([str(v) for v in values])]
            elif col == 'Meses': # Convertir los meses a string para el filtro de lista
                _df = _df[_df['Mes'].astype(str).isin([str(v) for v in values])]
            else:
                _df = _df[_df[col].isin(values)]
    return _df

def get_sorted_unique_options(dataframe, column_name):
    if column_name in dataframe.columns:
        unique_values = dataframe[column_name].dropna().unique().tolist()
        unique_values = [v for v in unique_values if v != 'no disponible']
        if column_name == 'Mes':
            month_order = {'Enero': 1, 'Febrero': 2, 'Marzo': 3, 'Abril': 4, 'Mayo': 5, 'Junio': 6, 'Julio': 7, 'Agosto': 8, 'Septiembre': 9, 'Octubre': 10, 'Noviembre': 11, 'Diciembre': 12}
            return sorted(unique_values, key=lambda x: month_order.get(x, 99))
        if column_name == 'Años':
            return sorted([int(x) for x in unique_values], reverse=True)
        return sorted(unique_values)
    return []
    
def get_available_options(df, selections, target_column):
    _df = df.copy()
    for col, values in selections.items():
        if col != target_column and values and col in _df.columns: 
            if col == 'Años':
                _df = _df[_df['Año'].astype(str).isin([str(v) for v in values])]
            elif col == 'Meses':
                _df = _df[_df['Mes'].astype(str).isin([str(v) for v in values])]
            else:
                _df = _df[_df[col].isin(values)]
    if target_column == 'Años':
        return get_sorted_unique_options(_df, 'Año')
    elif target_column == 'Meses':
        return get_sorted_unique_options(_df, 'Mes')
    return get_sorted_unique_options(_df, target_column)

@st.cache_data
def load_and_clean_data(uploaded_file):
    df_excel = pd.DataFrame()
    try:
        df_excel = pd.read_excel(uploaded_file, sheet_name='Eficiencia', engine='openpyxl')
    except Exception as e:
        st.error(f"ERROR CRÍTICO: No se pudo leer la hoja 'Eficiencia' del archivo cargado. Mensaje: {e}")
        return pd.DataFrame()
    if df_excel.empty: return pd.DataFrame()

    df_excel.columns = [re.sub(r'[^a-zA-Z0-9_]', '', col.replace(' ', '_')) for col in df_excel.columns]
    
    # Renombrar columnas clave de forma robusta
    df_excel.rename(columns={
        'Fecha': 'Periodo', 
        'Eficiencia_Total': 'Eficiencia_Total_raw',
        'Eficiencia_Operativa': 'Eficiencia_Operativa_raw',
        'Eficiencia_Gestion': 'Eficiencia_Gestion_raw',
        'Total_Inversiones': 'Total_Inversiones_raw'
    }, inplace=True)

    if 'Periodo' not in df_excel.columns:
        st.error("La columna 'Periodo' es obligatoria y no se encontró.")
        return pd.DataFrame()
    
    df_excel['Periodo'] = pd.to_datetime(df_excel['Periodo'], errors='coerce')
    df_excel.dropna(subset=['Periodo'], inplace=True)
    df_excel['Año'] = df_excel['Periodo'].dt.year
    df_excel['Mes_Num'] = df_excel['Periodo'].dt.month
    spanish_months_map = {1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'}
    df_excel['Mes'] = df_excel['Mes_Num'].map(spanish_months_map)

    # Convertir columnas a numéricas, llenando NaN con 0
    numeric_cols = [
        'Eficiencia_Total_raw', 'Eficiencia_Operativa_raw', 'Eficiencia_Gestion_raw',
        'Total_Inversiones_raw', 'Costos_Var_Interanual'
    ]
    for col in numeric_cols:
        if col in df_excel.columns:
            df_excel[col] = pd.to_numeric(df_excel[col], errors='coerce').fillna(0)
        else:
            df_excel[col] = 0 # Si la columna no existe, la creamos con 0

    return df_excel
    
# --- INICIO DE LA APLICACIÓN ---
st.title("🎯 Indicadores de Eficiencia")
st.write("Análisis de la variación de costos e indicadores clave.")

uploaded_file = st.file_uploader("📂 Cargue aquí su archivo Excel de Eficiencia", type=["xlsx"])
st.markdown("---")

if uploaded_file is not None:
    with st.spinner('Procesando archivo...'):
        df = load_and_clean_data(uploaded_file)
    if df.empty:
        st.error("El archivo cargado está vacío o no se pudo procesar correctamente.")
        st.stop()
    st.success(f"Se ha cargado un total de **{format_integer_es(len(df))}** registros de indicadores.")
    st.markdown("---")

    st.sidebar.header('Filtros Generales')
    
    filter_cols_config = {
        'Años': 'Años', 'Meses': 'Meses'
    }
    filter_cols = list(filter_cols_config.keys())

    if 'eff_selections' not in st.session_state:
        initial_selections = {'Años': get_sorted_unique_options(df, 'Año'), 'Meses': get_sorted_unique_options(df, 'Mes')}
        st.session_state.eff_selections = initial_selections
        st.rerun()

    if st.sidebar.button("🔄 Resetear Filtros", use_container_width=True, key="reset_filters"):
        initial_selections = {'Años': get_sorted_unique_options(df, 'Año'), 'Meses': get_sorted_unique_options(df, 'Mes')}
        st.session_state.eff_selections = initial_selections
        st.rerun()

    st.sidebar.markdown("---")

    old_selections = {k: list(v) for k, v in st.session_state.eff_selections.items()}

    for col_key, title in filter_cols_config.items():
        if col_key == 'Años':
            df_for_options = df.copy()
            for f_col, f_val in st.session_state.eff_selections.items():
                if f_col != col_key and f_val:
                    if f_col == 'Meses':
                         df_for_options = df_for_options[df_for_options['Mes'].isin(f_val)]
                    else:
                        df_for_options = df_for_options[df_for_options[f_col].isin(f_val)]

            available_options = get_sorted_unique_options(df_for_options, 'Año')
            current_selection = [sel for sel in st.session_state.eff_selections.get(col_key, []) if sel in available_options]
            selected = st.sidebar.multiselect(
                title,
                options=available_options,
                default=current_selection,
                key=f"multiselect_{col_key}"
            )
            st.session_state.eff_selections[col_key] = selected
        elif col_key == 'Meses':
            df_for_options = df.copy()
            for f_col, f_val in st.session_state.eff_selections.items():
                if f_col != col_key and f_val:
                    if f_col == 'Años':
                        df_for_options = df_for_options[df_for_options['Año'].isin(f_val)]
                    else:
                        df_for_options = df_for_options[df_for_options[f_col].isin(f_val)]
            
            available_options = get_sorted_unique_options(df_for_options, 'Mes')
            current_selection = [sel for sel in st.session_state.eff_selections.get(col_key, []) if sel in available_options]
            selected = st.sidebar.multiselect(
                title,
                options=available_options,
                default=current_selection,
                key=f"multiselect_{col_key}"
            )
            st.session_state.eff_selections[col_key] = selected
        else: # Para otras columnas, aunque en este dashboard solo hay Años y Meses
            available_options = get_available_options(df, st.session_state.eff_selections, col_key)
            current_selection = [sel for sel in st.session_state.eff_selections.get(col_key, []) if sel in available_options]
            selected = st.sidebar.multiselect(
                title,
                options=available_options,
                default=current_selection,
                key=f"multiselect_{col_key}"
            )
            st.session_state.eff_selections[col_key] = selected


    if old_selections != st.session_state.eff_selections:
        st.rerun()

    filtered_df = apply_all_filters(df, st.session_state.eff_selections)
    
    st.write(f"Después de aplicar los filtros, se muestran **{format_integer_es(len(filtered_df))}** registros.")
    st.markdown("---")

    # --- Lógica para KPIs y Deltas ---
    all_years_sorted = get_sorted_unique_options(df, 'Año')
    all_months_sorted = get_sorted_unique_options(df, 'Mes')

    selected_years = st.session_state.eff_selections.get('Años', [])
    selected_months = st.session_state.eff_selections.get('Meses', [])

    # Obtener el último período seleccionado y el anterior a ese
    df_for_kpis = filtered_df.sort_values(by=['Año', 'Mes_Num']).copy()
    
    latest_period_df = pd.DataFrame()
    previous_period_df = pd.DataFrame()

    if not df_for_kpis.empty:
        # Si se han seleccionado meses, el "último" periodo es el más reciente de esos meses
        # Si no, el "último" es el más reciente de todos los datos filtrados
        if not selected_months and not selected_years:
            latest_period_data = df_for_kpis.iloc[-1]
            latest_period_df = df_for_kpis[
                (df_for_kpis['Año'] == latest_period_data['Año']) & 
                (df_for_kpis['Mes_Num'] == latest_period_data['Mes_Num'])
            ]
            
            if len(df_for_kpis) > 1:
                previous_period_data = df_for_kpis.iloc[-2]
                previous_period_df = df_for_kpis[
                    (df_for_kpis['Año'] == previous_period_data['Año']) & 
                    (df_for_kpis['Mes_Num'] == previous_period_data['Mes_Num'])
                ]
        else: # Si hay selección de meses y/o años, buscamos en los datos filtrados
            unique_periods_filtered = df_for_kpis[['Año', 'Mes_Num', 'Mes']].drop_duplicates().sort_values(by=['Año', 'Mes_Num'])
            if not unique_periods_filtered.empty:
                latest_period_info = unique_periods_filtered.iloc[-1]
                latest_period_df = df_for_kpis[
                    (df_for_kpis['Año'] == latest_period_info['Año']) & 
                    (df_for_kpis['Mes_Num'] == latest_period_info['Mes_Num'])
                ]
                if len(unique_periods_filtered) > 1:
                    previous_period_info = unique_periods_filtered.iloc[-2]
                    previous_period_df = df_for_kpis[
                        (df_for_kpis['Año'] == previous_period_info['Año']) & 
                        (df_for_kpis['Mes_Num'] == previous_period_info['Mes_Num'])
                    ]

    # Calcular KPIs para el período actual
    eff_total_current = latest_period_df['Eficiencia_Total_raw'].sum() if not latest_period_df.empty else 0
    eff_operativa_current = latest_period_df['Eficiencia_Operativa_raw'].sum() if not latest_period_df.empty else 0
    eff_gestion_current = latest_period_df['Eficiencia_Gestion_raw'].sum() if not latest_period_df.empty else 0
    total_inversiones_current = latest_period_df['Total_Inversiones_raw'].sum() if not latest_period_df.empty else 0

    # Calcular KPIs para el período anterior
    eff_total_prev = previous_period_df['Eficiencia_Total_raw'].sum() if not previous_period_df.empty else 0
    eff_operativa_prev = previous_period_df['Eficiencia_Operativa_raw'].sum() if not previous_period_df.empty else 0
    eff_gestion_prev = previous_period_df['Eficiencia_Gestion_raw'].sum() if not previous_period_df.empty else 0
    total_inversiones_prev = previous_period_df['Total_Inversiones_raw'].sum() if not previous_period_df.empty else 0

    # Determinar el nombre del período actual para las etiquetas
    kpi_period_label = "Período Seleccionado"
    if not latest_period_df.empty:
        kpi_period_label = f"{latest_period_df['Mes'].iloc[0]} {latest_period_df['Año'].iloc[0]}"
    elif not filtered_df.empty:
        # Fallback a un rango si hay varios meses seleccionados y no un "último" único
        unique_months = filtered_df['Mes'].unique()
        unique_years = filtered_df['Año'].unique()
        if len(unique_months) == 1 and len(unique_years) == 1:
            kpi_period_label = f"{unique_months[0]} {unique_years[0]}"
        elif len(unique_years) == 1:
            kpi_period_label = f"Año {unique_years[0]}"
        elif len(unique_months) > 1 and len(unique_years) > 1:
            min_year, max_year = filtered_df['Año'].min(), filtered_df['Año'].max()
            kpi_period_label = f"Periodos {min_year}-{max_year}"

    # Mostrar las métricas en 4 columnas
    col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)

    with col_kpi1:
        st.markdown(f"""
            <div class="stMetric">
                <label class="stMetricLabel">Eficiencia Total<br>({kpi_period_label})</label>
                <div class="stMetricValue" data-target="{eff_total_current}">{format_number_es(eff_total_current)}</div>
                {get_delta_string(eff_total_current, eff_total_prev) if previous_period_df is not None else ''}
            </div>
            """, unsafe_allow_html=True)

    with col_kpi2:
        st.markdown(f"""
            <div class="stMetric">
                <label class="stMetricLabel">Eficiencia Operativa<br>({kpi_period_label})</label>
                <div class="stMetricValue" data-target="{eff_operativa_current}">{format_number_es(eff_operativa_current)}</div>
                {get_delta_string(eff_operativa_current, eff_operativa_prev) if previous_period_df is not None else ''}
            </div>
            """, unsafe_allow_html=True)
            
    with col_kpi3:
        st.markdown(f"""
            <div class="stMetric">
                <label class="stMetricLabel">Eficiencia de Gestión<br>({kpi_period_label})</label>
                <div class="stMetricValue" data-target="{eff_gestion_current}">{format_number_es(eff_gestion_current)}</div>
                {get_delta_string(eff_gestion_current, eff_gestion_prev) if previous_period_df is not None else ''}
            </div>
            """, unsafe_allow_html=True)

    with col_kpi4:
        st.markdown(f"""
            <div class="stMetric">
                <label class="stMetricLabel">Total Inversiones<br>({kpi_period_label})</label>
                <div class="stMetricValue" data-target="{total_inversiones_current}">{format_number_es(total_inversiones_current)}</div>
                {get_delta_string(total_inversiones_current, total_inversiones_prev) if previous_period_df is not None else ''}
            </div>
            """, unsafe_allow_html=True)
    
    # Script para animación de conteo
    st.markdown("""
        <script>
            function animateValue(obj, start, end, duration) {
                let startTimestamp = null;
                const step = (timestamp) => {
                    if (!startTimestamp) startTimestamp = timestamp;
                    const progress = Math.min((timestamp - startTimestamp) / duration, 1);
                    const currentVal = start + progress * (end - start);
                    obj.textContent = currentVal.toLocaleString('es-AR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
                    if (progress < 1) {
                        window.requestAnimationFrame(step);
                    }
                };
                window.requestAnimationFrame(step);
            }

            // Asegúrate de que el DOM esté completamente cargado
            document.addEventListener('DOMContentLoaded', function() {
                const kpiValues = document.querySelectorAll('.stMetricValue[data-target]');
                kpiValues.forEach(kpi => {
                    // Espera un poco para asegurar que los elementos estén visibles
                    setTimeout(() => {
                        const target = parseFloat(kpi.getAttribute('data-target').replace(',', '.')); // Soporte para decimales
                        animateValue(kpi, 0, target, 1500); // Animación de 1.5 segundos
                    }, 100);
                });
            });
        </script>
        """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # Tabs
    tab_variacion_interanual, tab_variacion_mensual, tab_detalle_indicadores = st.tabs(["Variación Interanual", "Variación Mensual", "Detalle de Indicadores"])

    with tab_variacion_interanual:
        st.subheader("Variación Interanual (Costos)")
        # --- Modificación: Filtrar Año 2024 ---
        df_interanual = filtered_df[filtered_df['Año'] != 2024].copy()
        
        if not df_interanual.empty:
            df_interanual['Periodo_Formatted'] = df_interanual['Periodo'].dt.strftime('%b-%y')
            # Asegurar el orden correcto de los periodos
            df_interanual = df_interanual.sort_values(by='Periodo')
            
            # --- Gráfico ---
            st.markdown("##### Gráfico de Variación Interanual")
            chart_interanual = alt.Chart(df_interanual).mark_bar(color='#5b9bd5').encode(
                x=alt.X('Periodo_Formatted:N', sort=alt.EncodingSortField(field="Periodo", op="min", order='ascending'), title='Período'),
                y=alt.Y('Costos_Var_Interanual:Q', title='Variación Interanual ($K)', axis=alt.Axis(format='$,.0s')),
                tooltip=[
                    alt.Tooltip('Periodo_Formatted', title='Período'),
                    alt.Tooltip('Costos_Var_Interanual', title='Variación ($K)', format='$,.2f')
                ]
            ).properties(
                title='Variación Interanual de Costos por Período'
            ).interactive()
            
            # Añadir etiquetas de valor
            text_labels = chart_interanual.mark_text(
                align='center',
                baseline='bottom',
                dy=-5, # Ajuste vertical para que no se solape con la barra
                color='black'
            ).encode(
                text=alt.Text('Costos_Var_Interanual:Q', format='$,.0f')
            )
            
            st.altair_chart((chart_interanual + text_labels), use_container_width=True)

            # --- Tabla ---
            st.markdown("##### Tabla de Variación Interanual")
            table_interanual = df_interanual[['Periodo_Formatted', 'Costos_Var_Interanual']].rename(columns={'Periodo_Formatted': 'Período', 'Costos_Var_Interanual': '$K_100%'})
            table_interanual['$K_100%'] = table_interanual['$K_100%'].apply(lambda x: format_number_es(x))
            st.dataframe(table_interanual.set_index('Período'), use_container_width=True)
            generate_download_buttons(table_interanual, 'Costos_Var_Interanual', '_interanual')
        else:
            st.info("No hay datos de variación interanual (excluyendo 2024) para mostrar con los filtros seleccionados.")
    
    with tab_variacion_mensual:
        st.subheader("Variación Mensual (Próximamente)")
        st.info("Esta sección aún no está implementada. Volveré pronto con nuevas características!")

    with tab_detalle_indicadores:
        st.subheader("Detalle de Indicadores")
        st.markdown("##### Valores por Período")
        # Mostrar los valores brutos de eficiencia y total_inversiones
        df_indicadores_display = filtered_df[['Periodo', 'Eficiencia_Total_raw', 'Eficiencia_Operativa_raw', 'Eficiencia_Gestion_raw', 'Total_Inversiones_raw']].copy()
        df_indicadores_display['Período'] = df_indicadores_display['Periodo'].dt.strftime('%b-%Y')
        df_indicadores_display.rename(columns={
            'Eficiencia_Total_raw': 'Eficiencia Total',
            'Eficiencia_Operativa_raw': 'Eficiencia Operativa',
            'Eficiencia_Gestion_raw': 'Eficiencia Gestión',
            'Total_Inversiones_raw': 'Total Inversiones'
        }, inplace=True)
        
        # Formatear columnas
        for col in ['Eficiencia Total', 'Eficiencia Operativa', 'Eficiencia Gestión', 'Total Inversiones']:
            if col in df_indicadores_display.columns:
                df_indicadores_display[col] = df_indicadores_display[col].apply(lambda x: format_number_es(x))
        
        st.dataframe(df_indicadores_display.set_index('Período'), use_container_width=True)
        generate_download_buttons(df_indicadores_display, 'Detalle_Indicadores', '_detalle')

else:
    st.info("Por favor, cargue un archivo Excel para comenzar el análisis.")
