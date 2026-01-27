import streamlit as st
import pandas as pd
import altair as alt
from io import BytesIO
from fpdf import FPDF
import numpy as np
from datetime import datetime
import streamlit.components.v1 as components

# --- Configuración de la página ---
st.set_page_config(layout="wide", page_title="Masa Salarial", page_icon="💸")

# --- CSS Personalizado para un Estilo Profesional y RESPONSIVE ---
st.markdown("""
<style>
/* --- TEMA PERSONALIZADO --- */
:root {
    --primary-color: #6C5CE7;
    --background-color: #f0f2f6;
    --secondary-background-color: #f8f7fc;
    --text-color: #1a1a2e;
    --font: 'Source Sans Pro', sans-serif;
}

/* Importar fuente */
@import url('https://fonts.googleapis.com/css2?family=Source+Sans+Pro:wght@400;600;700&display=swap');

.stApp {
    font-family: var(--font);
}

/* Estilos generales de tablas y botones para mantener coherencia */
div[data-testid="stDownloadButton"] button {
    background-color: var(--primary-color);
    color: white;
    border: none;
    transition: all 0.3s ease;
}
div[data-testid="stDownloadButton"] button:hover {
    background-color: #5A4ADF;
    transform: translateY(-2px);
    box-shadow: 0 4px 10px rgba(0,0,0,0.1);
}

/* Redondear bordes de gráficos */
[data-testid="stAltairChart"], [data-testid="stPlotlyChart"] {
    border-radius: 12px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    background: white;
    padding: 10px;
}

/* Ajuste Responsive */
@media (max-width: 768px) {
    div[data-testid="stHorizontalBlock"] { flex-wrap: wrap !important; }
    div[data-testid="stHorizontalBlock"] > div[data-testid="column"] { flex: 1 1 100% !important; min-width: 100% !important; }
}
</style>
""", unsafe_allow_html=True)


# --- Formato de Números ---
custom_format_locale = {
    "decimal": ",", "thousands": ".", "grouping": [3], "currency": ["$", ""]
}
alt.renderers.set_embed_options(formatLocale=custom_format_locale)

def format_number_es(num):
    if pd.isna(num) or not isinstance(num, (int, float, np.number)): return ""
    s = f"{num:,.2f}"
    return s.replace(",", "TEMP").replace(".", ",").replace("TEMP", ".")

def format_integer_es(val):
    """
    Formatea enteros con punto de miles. 
    Si el valor NO es numérico (ej: un ID alfanumérico de Ceco o Legajo), lo devuelve como string tal cual.
    Esto soluciona el problema de columnas vacías.
    """
    if pd.isna(val): return ""
    if isinstance(val, (int, float, np.number)):
        s = f"{int(val):,}"
        return s.replace(",", ".")
    return str(val)

# --- FUNCIONES DE EXPORTACIÓN ---
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=True, sheet_name='Sheet1') # Index True para capturar indices en pivots
    return output.getvalue()

def to_pdf(df, periodo):
    periodo_str = ", ".join(periodo) if isinstance(periodo, list) else str(periodo)
    html_table = df.to_html(index=False, border=0)
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8">
    <style>
        body {{ font-family: "Arial", sans-serif; }} h2 {{ text-align: center; }}
        h3 {{ text-align: center; font-weight: normal; font-size: 12px; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 6px 5px; text-align: left; border: 1px solid #dddddd; font-size: 9px; }}
        thead th {{ background-color: #f2f2f2; font-size: 10px; font-weight: bold; }}
    </style>
    </head>
    <body>
        <h2>Reporte Resumido de Datos</h2><h3>Período: {periodo_str}</h3>{html_table}
    </body>
    </html>
    """
    pdf = FPDF(orientation='L', unit='mm', format='A3')
    pdf.add_page()
    pdf.write_html(html_content)
    return bytes(pdf.output())

# --- LÓGICA DE FILTROS (MEJORADA CON BUSCADOR) ---
def apply_filters(df, selections):
    # 1. Verificar si hay búsqueda por Legajo (Prioridad Alta)
    search_leg = st.session_state.get("search_legajo_global", "").strip()
    
    if search_leg:
        mask = df['Legajo'].astype(str).str.contains(search_leg, case=False, na=False)
        _df_search = df[mask].copy()
        if not _df_search.empty:
            return _df_search
    
    # 2. Filtrado Normal por Multiselects
    _df = df.copy()
    for col, values in selections.items():
        if values:
            _df = _df[_df[col].isin(values)]
    return _df
    
# --- INICIO: FUNCIONES PARA FILTROS INTELIGENTES ---
def get_sorted_unique_options(dataframe, column_name):
    if column_name in dataframe.columns:
        unique_values = dataframe[column_name].dropna().unique().tolist()
        # Eliminamos valores nulos explícitos
        unique_values = [v for v in unique_values if v not in ['nan', 'None', '']]
        
        if column_name == 'Mes':
            all_months_order = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
            return sorted(unique_values, key=lambda m: all_months_order.index(m) if m in all_months_order else -1)
        
        elif column_name == 'Año':
            # Ordenar años descendente (el más reciente primero)
            try:
                return sorted(unique_values, reverse=True)
            except:
                return sorted(unique_values)

        return sorted(unique_values)
    return []

def get_available_options(df, selections, target_column):
    _df = df.copy()
    for col, values in selections.items():
        if col != target_column and values:
            _df = _df[_df[col].isin(values)]
    return get_sorted_unique_options(_df, target_column)
# --- FIN: FUNCIONES PARA FILTROS INTELIGENTES ---

# --- CARGA DE DATOS ---
@st.cache_data
def load_data(uploaded_file):
    try:
        df = pd.read_excel(uploaded_file, sheet_name='masa_salarial', header=0, engine='openpyxl')
    except Exception as e:
        st.error(f"Error al leer el archivo Excel. Asegúrate de que tenga una hoja llamada 'masa_salarial'. Error: {e}")
        return pd.DataFrame()
        
    df.columns = [str(col).strip() for col in df.columns]
    
    # --- LIMPIEZA PREVENTIVA ---
    # Eliminar columnas duplicadas si las hubiera para evitar errores
    df = df.loc[:, ~df.columns.duplicated()]
    # Eliminar columnas Unnamed
    df = df.loc[:, ~df.columns.astype(str).str.startswith('Unnamed:')]

    if 'Período' not in df.columns:
        st.error("Error Crítico: La columna 'Período' no se encuentra.")
        return pd.DataFrame()
    
    def parse_spanish_date(x):
        if isinstance(x, datetime): return x
        x_str = str(x).lower().strip()
        replacements = {
            'ene': 'jan', 'abr': 'apr', 'ago': 'aug', 'dic': 'dec',
            'enero': 'january', 'feb': 'february', 'mar': 'march', 'abril': 'april',
            'may': 'may', 'jun': 'june', 'jul': 'july', 'agosto': 'august',
            'sept': 'sep', 'set': 'sep', 'sep': 'sep', 'oct': 'october', 'nov': 'november', 'diciembre': 'december'
        }
        for es, en in replacements.items():
            if es in x_str:
                x_str = x_str.replace(es, en)
                break
        try:
            return pd.to_datetime(x_str, dayfirst=True)
        except:
            return pd.to_datetime(x_str, errors='coerce')

    df['Período_Temp'] = pd.to_datetime(df['Período'], errors='coerce')
    mask_nat = df['Período_Temp'].isna()
    if mask_nat.any():
        df.loc[mask_nat, 'Período_Temp'] = df.loc[mask_nat, 'Período'].apply(parse_spanish_date)
    
    df['Período'] = df['Período_Temp']
    df.drop(columns=['Período_Temp'], inplace=True)
    df.dropna(subset=['Período'], inplace=True)
    
    # --- EXTRACCIÓN DE FECHAS (MES Y AÑO) ---
    df['Mes_Num'] = df['Período'].dt.month.astype(int)
    meses_es = {1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'}
    df['Mes'] = df['Mes_Num'].map(meses_es)
    
    # NUEVO: Crear columna Año
    df['Año'] = df['Período'].dt.year.astype(int).astype(str)
    
    df.rename(columns={'Clasificación Ministerio de Hacienda': 'Clasificacion_Ministerio', 'Nro. de Legajo': 'Legajo'}, inplace=True)
    
    if 'Total Mensual' in df.columns:
        df['Total Mensual'] = pd.to_numeric(df['Total Mensual'], errors='coerce').fillna(0)

    # --- CORRECCIÓN CRÍTICA DE LEGAJOS (USANDO VECTORIZACIÓN) ---
    if 'Legajo' in df.columns:
        # 1. Intentar convertir a numérico
        s_numeric = pd.to_numeric(df['Legajo'], errors='coerce')
        
        # 2. Crear serie de Legajos Numéricos Limpios (Strings sin .0)
        # fillna(0) es temporal, luego np.where lo sobreescribe si era NaN original
        numeric_legajos = s_numeric.fillna(0).astype(int).astype(str)
        
        # 3. Crear serie de Legajos Virtuales para TODOS (por si acaso)
        virtual_legajos = 'S/L-' + df.index.astype(str)
        
        # 4. Combinar usando np.where: 
        # Si el valor numérico NO es NA, usa el número limpio.
        # Si ES NA (era texto sucio o vacío), usa el virtual.
        df['Legajo'] = np.where(s_numeric.notna(), numeric_legajos, virtual_legajos)
    else:
        # Si no existe la columna, creamos virtuales para todos
        df['Legajo'] = 'S/L-' + df.index.astype(str)

    # LIMPIEZA AGRESIVA DE CATEGORÍAS PARA ARREGLAR FILTROS VACÍOS, CASCADA Y CECO VACÍO
    cols_to_clean = ['Gerencia', 'Nivel', 'Clasificacion_Ministerio', 'Relación', 'Ceco']
    for col in cols_to_clean:
        if col in df.columns:
            # 1. Convertir a string
            s = df[col].astype(str)
            # 2. Quitar decimal .0 si existe al final
            s = s.str.replace(r'\.0$', '', regex=True)
            # 3. Estandarizar nulos
            s = s.replace(['nan', 'None', '', '<NA>'], 'No Informado')
            df[col] = s
        else:
            df[col] = 'No Informado'

    # Asegurar que Dotación es numérica entera
    if 'Dotación' in df.columns:
        df['Dotación'] = pd.to_numeric(df['Dotación'], errors='coerce').fillna(0).astype(int)
    else:
        df['Dotación'] = 1

    df.reset_index(drop=True, inplace=True)
    return df

# MODIFICADO: Título genérico (sin año fijo)
st.title('💵 Dashboard de Masa Salarial')
st.markdown("Análisis interactivo de los costos de la mano de obra de la compañía.")

uploaded_file = st.file_uploader("📂 Cargue aquí su archivo Excel de Masa Salarial", type=["xlsx"]) 

if uploaded_file is None:
    st.info("Por favor, cargue un archivo para comenzar el análisis.")
    st.stop()

# Cargamos datos
df = load_data(uploaded_file)

if df.empty:
    st.error("El archivo cargado está vacío o no se pudo procesar. El dashboard no puede continuar.")
    st.stop()

if 'last_uploaded_file' not in st.session_state:
    st.session_state.last_uploaded_file = None

if st.session_state.last_uploaded_file != uploaded_file.name:
    if 'ms_selections' in st.session_state:
        del st.session_state.ms_selections
    st.session_state.last_uploaded_file = uploaded_file.name

# --- SIDEBAR: filtros ---
st.sidebar.header('Filtros del Dashboard')

search_query = st.sidebar.text_input("🔍 Buscar por Legajo (Omite otros filtros)", key="search_legajo_global", help="Escriba un número de legajo para ver su historia completa ignorando los filtros de abajo.")

if search_query:
    st.sidebar.info(f"Filtros desactivados. Mostrando solo legajo: {search_query}")

# MODIFICADO: Agregado 'Año' al inicio de los filtros
filter_cols = ['Año', 'Mes', 'Gerencia', 'Nivel', 'Clasificacion_Ministerio', 'Relación', 'Ceco', 'Legajo']

if 'ms_selections' not in st.session_state:
    initial_selections = {col: get_sorted_unique_options(df, col) for col in filter_cols}
    st.session_state.ms_selections = initial_selections
    st.rerun()

def reset_filters_callback():
    st.session_state.ms_selections = {col: get_sorted_unique_options(df, col) for col in filter_cols}
    st.session_state.search_legajo_global = "" 

st.sidebar.button("🔄 Resetear Filtros", use_container_width=True, on_click=reset_filters_callback)

st.sidebar.markdown("---")

if not search_query:
    old_selections = {k: list(v) for k, v in st.session_state.ms_selections.items()}
    for col in filter_cols:
        label = col.replace('_', ' ').replace('Clasificacion Ministerio', 'Clasificación Ministerio')
        available_options = get_available_options(df, st.session_state.ms_selections, col)
        current_selection = [sel for sel in st.session_state.ms_selections.get(col, []) if sel in available_options]
        selected = st.sidebar.multiselect(
            label,
            options=available_options,
            default=current_selection,
            key=f"ms_multiselect_{col}"
        )
        st.session_state.ms_selections[col] = selected

    if old_selections != st.session_state.ms_selections:
        st.rerun()

df_filtered = apply_filters(df, st.session_state.ms_selections)


# =============================================================================
# --- INICIO: LÓGICA DE MÉTRICAS (CORREGIDA PARA AÑOS NUEVOS) ---
# =============================================================================

# 1. Determinar el contexto de filtros "Estructurales" (sin tiempo)
# Esto nos sirve para buscar el mes anterior histórico real, aunque no esté seleccionado en el filtro de mes/año
selections_structural = st.session_state.ms_selections.copy()
if 'Mes' in selections_structural: del selections_structural['Mes']
if 'Año' in selections_structural: del selections_structural['Año']

df_structural = apply_filters(df, selections_structural)

# 2. Determinar el "Último Período" basado en lo que el usuario está viendo (df_filtered)
if not df_filtered.empty:
    # Usamos la columna de fecha real (datetime) para encontrar el máximo, ignorando nombres de meses
    latest_period_dt = df_filtered['Período'].max()
    
    # df_current: Datos del último período disponible dentro de la selección
    df_current = df_filtered[df_filtered['Período'] == latest_period_dt]
    
    # 3. Determinar el "Período Anterior" histórico (mirando fuera de los filtros de tiempo si es necesario)
    # Buscamos en df_structural todos los períodos disponibles
    available_periods = sorted(df_structural['Período'].unique())
    
    # Encontramos el índice del current
    if latest_period_dt in available_periods:
        current_idx = available_periods.index(latest_period_dt)
        if current_idx > 0:
            previous_period_dt = available_periods[current_idx - 1]
            df_previous = df_structural[df_structural['Período'] == previous_period_dt]
        else:
            df_previous = pd.DataFrame()
            previous_period_dt = None
    else:
        df_previous = pd.DataFrame()
        previous_period_dt = None
        
    # Nombre para mostrar
    meses_espanol = {1: "ENERO", 2: "FEBRERO", 3: "MARZO", 4: "ABRIL", 5: "MAYO", 6: "JUNIO", 7: "JULIO", 8: "AGOSTO", 9: "SEPTIEMBRE", 10: "OCTUBRE", 11: "NOVIEMBRE", 12: "DICIEMBRE"}
    display_month_name = f"{meses_espanol.get(latest_period_dt.month, '')} {latest_period_dt.year}"

else:
    # Caso fallback si no hay datos
    df_current = pd.DataFrame()
    df_previous = pd.DataFrame()
    display_month_name = "N/A"


def calculate_monthly_metrics(df_month):
    if df_month.empty:
        return {'total_masa': 0, 'empleados': 0, 'costo_medio_conv': 0, 'costo_medio_fc': 0}
    
    total_masa = df_month['Total Mensual'].sum()
    empleados = df_month['Dotación'].sum()
    
    is_fc = df_month['Nivel'] == 'FC'
    df_fc = df_month[is_fc]
    df_convenio = df_month[~is_fc]

    total_masa_convenio = df_convenio['Total Mensual'].sum()
    total_masa_fc = df_fc['Total Mensual'].sum()
    
    dotacion_convenio = df_convenio['Dotación'].sum()
    dotacion_fc = df_fc['Dotación'].sum()
    
    costo_medio_conv = total_masa_convenio / dotacion_convenio if dotacion_convenio > 0 else 0
    costo_medio_fc = total_masa_fc / dotacion_fc if dotacion_fc > 0 else 0
    
    return {
        'total_masa': total_masa,
        'empleados': empleados,
        'costo_medio_conv': costo_medio_conv,
        'costo_medio_fc': costo_medio_fc
    }

metrics_current = calculate_monthly_metrics(df_current)
metrics_previous = calculate_monthly_metrics(df_previous)

total_anual_acumulado = df_filtered['Total Mensual'].sum()

def get_delta_pct_str(current, previous):
    if previous > 0:
        delta = ((current - previous) / previous) * 100
    elif current > 0:
        delta = 100.0
    else:
        delta = 0.0
    return delta

delta_total = get_delta_pct_str(metrics_current['total_masa'], metrics_previous['total_masa'])
delta_empleados = get_delta_pct_str(metrics_current['empleados'], metrics_previous['empleados'])
delta_costo_conv = get_delta_pct_str(metrics_current['costo_medio_conv'], metrics_previous['costo_medio_conv'])
delta_costo_fc = get_delta_pct_str(metrics_current['costo_medio_fc'], metrics_previous['costo_medio_fc'])

# --- TARJETAS DE MÉTRICAS ---
cards_html = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Source+Sans+Pro:wght@400;600;700&display=swap');

.metrics-grid {{
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 15px;
    margin-bottom: 30px;
    font-family: 'Source Sans Pro', sans-serif;
}}

@media (max-width: 768px) {{
    .metrics-grid {{
        grid-template-columns: repeat(2, 1fr); 
    }}
}}

.metric-card {{
    background: white;
    border-radius: 12px;
    padding: 15px; 
    box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    border: 1px solid #f0f2f6;
    transition: transform 0.3s ease, box-shadow 0.3s ease;
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    min-width: 0; 
    overflow-wrap: break-word;
}}

.metric-card:hover {{
    transform: translateY(-5px);
    box-shadow: 0 10px 15px rgba(0,0,0,0.1);
}}

.border-orange {{ border-top: 4px solid #f97316; }} 
.border-blue {{ border-top: 4px solid #3b82f6; }}
.border-cyan {{ border-top: 4px solid #06b6d4; }}
.border-violet {{ border-top: 4px solid #8b5cf6; }}
.border-pink {{ border-top: 4px solid #ec4899; }}

.card-label {{
    font-size: 0.8rem; 
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: #64748b;
    margin-bottom: 10px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    width: 100%;
}}

.card-value {{
    font-size: 1.2rem; 
    font-weight: 700;
    color: #1e293b;
    margin-bottom: 8px;
    line-height: 1.2;
    word-wrap: break-word; 
}}

.card-delta {{
    font-size: 0.75rem;
    font-weight: 600;
    padding: 4px 10px;
    border-radius: 20px;
    display: inline-flex;
    align-items: center;
    gap: 4px;
}}

.delta-green {{ background-color: #dcfce7; color: #166534; }}
.delta-red {{ background-color: #fee2e2; color: #991b1b; }}
.delta-neutral {{ background-color: #f1f5f9; color: #64748b; }}
</style>

<div class="metrics-grid">

<!-- Tarjeta 0: Costo Anual -->
<div class="metric-card border-orange">
    <div class="card-label" title="Costo Acumulado (Año)">Costo Acumulado (Año)</div>
    <div class="card-value">${format_integer_es(total_anual_acumulado)}</div>
    <div class="card-delta delta-neutral">
        Total Filtrado
    </div>
</div>

<!-- Tarjeta 1: Masa Salarial -->
<div class="metric-card border-blue">
    <div class="card-label" title="Masa Salarial ({display_month_name})">Masa Salarial ({display_month_name})</div>
    <div class="card-value">${format_integer_es(metrics_current['total_masa'])}</div>
    <div class="card-delta {'delta-green' if delta_total <= 0 else 'delta-red' if delta_total > 0 else 'delta-neutral'}">
        {'▼' if delta_total <= 0 else '▲'} {abs(delta_total):.1f}%
    </div>
</div>

<!-- Tarjeta 2: Dotación Liquidada -->
<div class="metric-card border-cyan">
    <div class="card-label" title="Dotación Liquidada ({display_month_name})">Dotación Liquidada ({display_month_name})</div>
    <div class="card-value">{format_integer_es(metrics_current['empleados'])}</div>
    <div class="card-delta {'delta-green' if delta_empleados >= 0 else 'delta-red'}">
        {'▲' if delta_empleados >= 0 else '▼'} {abs(delta_empleados):.1f}%
    </div>
</div>

<!-- Tarjeta 3: Costo Medio Convenio -->
<div class="metric-card border-violet">
    <div class="card-label" title="Costo Medio Conv. ({display_month_name})">Costo Medio Conv. ({display_month_name})</div>
    <div class="card-value">${format_number_es(metrics_current['costo_medio_conv'])}</div>
    <div class="card-delta {'delta-green' if delta_costo_conv <= 0 else 'delta-red' if delta_costo_conv > 0 else 'delta-neutral'}">
        {'▼' if delta_costo_conv <= 0 else '▲'} {abs(delta_costo_conv):.1f}%
    </div>
</div>

<!-- Tarjeta 4: Costo Medio FC -->
<div class="metric-card border-pink">
    <div class="card-label" title="Costo Medio F.C. ({display_month_name})">Costo Medio F.C. ({display_month_name})</div>
    <div class="card-value">${format_number_es(metrics_current['costo_medio_fc'])}</div>
    <div class="card-delta {'delta-green' if delta_costo_fc <= 0 else 'delta-red' if delta_costo_fc > 0 else 'delta-neutral'}">
        {'▼' if delta_costo_fc <= 0 else '▲'} {abs(delta_costo_fc):.1f}%
    </div>
</div>
</div>
"""

st.markdown(cards_html, unsafe_allow_html=True)

st.markdown("---")

# --- TABS PRINCIPALES ---
tab_evolucion, tab_distribucion, tab_costos, tab_conceptos, tab_tabla = st.tabs(["Evolución Mensual y Anual", "Distribución por Gerencia y Clasificación", "Análisis de Costos Promedios", "Masa Salarial por Concepto / SIPAF", "Tabla de Datos Detallados"]) 

# ------------------------- TAB 1: EVOLUCIÓN -------------------------
with tab_evolucion:
    st.subheader("Evolución Mensual de la Masa Salarial")
    col_chart1, col_table1 = st.columns([2, 1])
    # Agrupamos por Año-Mes para que el gráfico sea cronológico si hay varios años
    # Pero para simplificar en el gráfico, usaremos 'Mes' y asumimos filtro de año activo o agregación
    masa_mensual = df_filtered.groupby(['Mes', 'Mes_Num', 'Año']).agg({'Total Mensual': 'sum'}).reset_index().sort_values(['Año', 'Mes_Num'])
    
    # Creamos etiqueta Mes-Año para el gráfico si hay más de un año seleccionado
    unique_years = df_filtered['Año'].unique()
    if len(unique_years) > 1:
        masa_mensual['Periodo_Label'] = masa_mensual['Mes'] + "-" + masa_mensual['Año']
    else:
        masa_mensual['Periodo_Label'] = masa_mensual['Mes']

    y_domain = [0, 1]
    if not masa_mensual.empty:
        min_val = masa_mensual['Total Mensual'].min()
        max_val = masa_mensual['Total Mensual'].max()
        padding = (max_val - min_val) * 0.2 if max_val != min_val else max_val * 0.2
        y_domain = [min_val - padding, max_val + padding]
        if y_domain[0] < 0 and min_val >= 0: y_domain[0] = 0
    y_scale = alt.Scale(domain=y_domain)

    chart_height1 = (len(masa_mensual) + 1) * 35 + 3
    with col_chart1:
        # Orden personalizado para el eje X
        sort_order = masa_mensual['Periodo_Label'].tolist()
        
        base_chart1 = alt.Chart(masa_mensual).transform_window(
            total_sum='sum(Total Mensual)'
        ).transform_calculate(
            percentage="datum['Total Mensual'] / datum.total_sum",
            label_text="format(datum['Total Mensual'] / 1000000000, ',.2f') + 'G (' + format(datum.percentage, '.1%') + ')'"
        )
        line = base_chart1.mark_line(point=True, strokeWidth=3).encode(
            x=alt.X('Periodo_Label:N', sort=sort_order, title='Período'), 
            y=alt.Y('Total Mensual:Q', title='Masa Salarial ($)', axis=alt.Axis(format='$,.0s'), scale=y_scale), 
            tooltip=[alt.Tooltip('Periodo_Label:N', title='Período'), alt.Tooltip('Total Mensual:Q', format='$,.2f')]
        )
        text = base_chart1.mark_text(align='center', baseline='bottom', dy=-10).encode(
            x=alt.X('Periodo_Label:N', sort=sort_order), y=alt.Y('Total Mensual:Q', scale=y_scale), text='label_text:N'
        )
        line_chart = (line + text).properties(height=chart_height1, padding={'top': 35, 'left': 5, 'right': 5, 'bottom': 5}).configure(background='transparent').configure_view(fill='transparent')
        st.altair_chart(line_chart, use_container_width=True)
    with col_table1:
        masa_mensual_display = masa_mensual[['Periodo_Label', 'Total Mensual']].rename(columns={'Periodo_Label': 'Mes/Año'}).copy()
        if not masa_mensual_display.empty:
            total_row = pd.DataFrame([{'Mes/Año': 'Total', 'Total Mensual': masa_mensual_display['Total Mensual'].sum()}])
            masa_mensual_display = pd.concat([masa_mensual_display, total_row], ignore_index=True)
        st.dataframe(masa_mensual_display.style.format({"Total Mensual": lambda x: f"${format_number_es(x)}"}).set_properties(subset=["Total Mensual"], **{'text-align': 'right'}), hide_index=True, use_container_width=True, height=chart_height1)
    
    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
    dl1_col, dl2_col = st.columns(2)
    with dl1_col:
        st.download_button(label="📥 Descargar CSV", data=masa_mensual_display.to_csv(index=False).encode('utf-8'), file_name='evolucion_mensual.csv', mime='text/csv', use_container_width=True)
    with dl2_col:
        st.download_button(label="📥 Descargar Excel", data=to_excel(masa_mensual_display), file_name='evolucion_mensual.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', use_container_width=True)

    st.markdown("---")
    st.subheader("Resumen de Evolución Anual (Datos Filtrados)")
    summary_df_filtered = pd.pivot_table(
        df_filtered,
        values='Total Mensual',
        index=['Año', 'Mes_Num', 'Mes'], # Incluir año en el index
        columns='Clasificacion_Ministerio',
        aggfunc='sum',
        fill_value=0
    ).sort_index(level=['Año', 'Mes_Num']) # Ordenar por Año y MesNum

    # Aplanar para visualización
    summary_df_display = summary_df_filtered.reset_index().drop(columns=['Mes_Num'])
    
    if not summary_df_display.empty:
        col_chart_anual, col_table_anual = st.columns([2, 1])

        with col_table_anual:
            numeric_cols = summary_df_display.select_dtypes(include=np.number).columns
            # Excluir 'Año' si se detectó como numérico
            numeric_cols = [c for c in numeric_cols if c != 'Año']
            
            if 'Total general' not in summary_df_display.columns and len(numeric_cols) > 0:
                summary_df_display['Total general'] = summary_df_display[numeric_cols].sum(axis=1)

            total_row = summary_df_display[numeric_cols].sum().rename('Total')
            # Reconstruir dataframe con fila total
            summary_df_display_final = pd.concat([summary_df_display, total_row.to_frame().T], ignore_index=True)
            
            # Llenar labels en fila total
            if 'Mes' in summary_df_display_final.columns:
                summary_df_display_final.iloc[-1, summary_df_display_final.columns.get_loc('Mes')] = 'Total'
            if 'Año' in summary_df_display_final.columns:
                summary_df_display_final.iloc[-1, summary_df_display_final.columns.get_loc('Año')] = ''

            summary_currency_cols = [col for col in summary_df_display_final.columns if col not in ['Mes', 'Año'] and pd.api.types.is_numeric_dtype(summary_df_display_final[col])]
            summary_format_mapper = {col: lambda x: f"${format_number_es(x)}" for col in summary_currency_cols}
            table_height_anual = 350 + 40
            st.dataframe(summary_df_display_final.style.format(summary_format_mapper, na_rep="").set_properties(subset=summary_currency_cols, **{'text-align': 'right'}), use_container_width=True, hide_index=True, height=table_height_anual)
        
        with col_chart_anual:
            summary_chart_data = summary_df_filtered.reset_index()
            # Crear etiqueta compuesta para el eje X
            summary_chart_data['Eje_X'] = summary_chart_data['Mes'] + " " + summary_chart_data['Año'].astype(str)
            summary_chart_data = summary_chart_data.melt(id_vars=['Eje_X', 'Mes_Num', 'Año'], var_name='Clasificacion', value_name='Masa Salarial')
            
            # Ordenar por Año y MesNum
            sort_order_anual = summary_chart_data.sort_values(['Año', 'Mes_Num'])['Eje_X'].unique().tolist()

            bar_chart = alt.Chart(summary_chart_data).mark_bar().encode(
                x=alt.X('Eje_X:N', sort=sort_order_anual, title='Mes/Año'),
                y=alt.Y('sum(Masa Salarial):Q', title='Masa Salarial ($)', axis=alt.Axis(format='$,.0s')),
                color=alt.Color('Clasificacion:N', title='Clasificación'),
                tooltip=[alt.Tooltip('Eje_X:N', title='Período'), alt.Tooltip('Clasificacion:N'), alt.Tooltip('sum(Masa Salarial):Q', format='$,.2f', title='Masa Salarial')]
            )
            text_labels = alt.Chart(summary_chart_data).transform_aggregate(
                total_masa_salarial='sum(Masa Salarial)',
                groupby=['Eje_X']
            ).mark_text(
                dy=-8,
                align='center',
                color='black'
            ).encode(
                x=alt.X('Eje_X:N', sort=sort_order_anual),
                y=alt.Y('total_masa_salarial:Q'),
                text=alt.Text('total_masa_salarial:Q', format='$,.2s')
            )
            summary_chart = (bar_chart + text_labels).properties(
                height=350, padding={'top': 25, 'left': 5, 'right': 5, 'bottom': 5}
            ).configure(
                background='transparent'
            ).configure_view(
                fill='transparent'
            )
            st.altair_chart(summary_chart, use_container_width=True)

        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
        dl_a_col, dl_b_col = st.columns(2)
        with dl_a_col:
            st.download_button(label="📥 Descargar CSV", data=summary_df_display.to_csv(index=False).encode('utf-8'), file_name='resumen_anual_filtrado.csv', mime='text/csv', use_container_width=True)
        with dl_b_col:
            st.download_button(label="📥 Descargar Excel", data=to_excel(summary_df_display), file_name='resumen_anual_filtrado.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', use_container_width=True)

# ------------------------- TAB 2: DISTRIBUCIÓN -------------------------
with tab_distribucion:
    st.subheader("Análisis de Distribución")
    
    vista_distribucion = st.radio(
        "Seleccione el tipo de visualización:",
        ["Vista Acumulada (Total del periodo)", "Vista Mensualizada (Evolución por Mes)"],
        horizontal=True,
        key="dist_mode_selector"
    )
    
    st.markdown("---")

    if vista_distribucion == "Vista Acumulada (Total del periodo)":
        st.subheader("Masa Salarial Acumulada por Gerencia")
        col_chart2, col_table2 = st.columns([3, 2])
        gerencia_data = df_filtered.groupby('Gerencia')['Total Mensual'].sum().sort_values(ascending=False).reset_index()
        chart_height2 = (len(gerencia_data) + 1) * 35 + 3
        with col_chart2:
            base_chart2 = alt.Chart(gerencia_data).mark_bar().encode(
                x=alt.X('Total Mensual:Q', title='Masa Salarial ($)', axis=alt.Axis(format='$,.0s')),
                y=alt.Y('Gerencia:N', sort='-x', title=None, axis=alt.Axis(labelLimit=120)),
                tooltip=[alt.Tooltip('Gerencia:N', title='Gerencia'), alt.Tooltip('Total Mensual:Q', format='$,.2f')]
            )
            text = base_chart2.mark_text(align='left', baseline='middle', dx=5).encode(
                x='Total Mensual:Q', y=alt.Y('Gerencia:N', sort='-x'), text=alt.Text('Total Mensual:Q', format='$,.0s'), color=alt.value('black')
            )
            bar_chart = (base_chart2 + text).properties(height=chart_height2, padding={'top': 25, 'left': 5, 'right': 5, 'bottom': 5}).configure(background='transparent').configure_view(fill='transparent')
            st.altair_chart(bar_chart, use_container_width=True)
        with col_table2:
            gerencia_data_display = gerencia_data.copy()
            if not gerencia_data_display.empty:
                total_row = pd.DataFrame([{'Gerencia': 'Total', 'Total Mensual': gerencia_data_display['Total Mensual'].sum()}])
                gerencia_data_display = pd.concat([gerencia_data_display, total_row], ignore_index=True)
            st.dataframe(gerencia_data_display.style.format({"Total Mensual": lambda x: f"${format_number_es(x)}"}).set_properties(subset=["Total Mensual"], **{'text-align': 'right'}), hide_index=True, use_container_width=True, height=chart_height2)
        
        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
        dl3_col, dl4_col = st.columns(2)
        with dl3_col:
            st.download_button(label="📥 Descargar CSV (Gerencia)", data=gerencia_data_display.to_csv(index=False).encode('utf-8'), file_name='masa_por_gerencia.csv', mime='text/csv', use_container_width=True)
        with dl4_col:
            st.download_button(label="📥 Descargar Excel (Gerencia)", data=to_excel(gerencia_data_display), file_name='masa_por_gerencia.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', use_container_width=True)

        st.markdown("---")
        st.subheader("Distribución Acumulada por Clasificación")
        col_chart3, col_table3 = st.columns([2, 1])
        clasificacion_data = df_filtered.groupby('Clasificacion_Ministerio')['Total Mensual'].sum().reset_index()
        
        with col_chart3:
            clasificacion_data = clasificacion_data.sort_values('Total Mensual', ascending=False)
            total = clasificacion_data['Total Mensual'].sum()
            if total > 0:
                clasificacion_data['Porcentaje'] = (clasificacion_data['Total Mensual'] / total)
            else:
                clasificacion_data['Porcentaje'] = 0

            base_chart = alt.Chart(clasificacion_data).encode(
                theta=alt.Theta(field="Total Mensual", type="quantitative", stack=True),
                color=alt.Color(field="Clasificacion_Ministerio", type="nominal", title="Clasificación",
                                sort=alt.EncodingSortField(field="Total Mensual", order="descending")),
                tooltip=[
                    alt.Tooltip('Clasificacion_Ministerio', title='Clasificación'),
                    alt.Tooltip('Total Mensual', format='$,.2f'),
                    alt.Tooltip('Porcentaje', format='.2%')
                ]
            )
            pie = base_chart.mark_arc(innerRadius=70, outerRadius=110)
            text = base_chart.mark_text(radius=140, size=12, fill='black').encode(
                text=alt.condition(
                    alt.datum.Porcentaje > 0.03,
                    alt.Text('Porcentaje:Q', format='.1%'),
                    alt.value('')
                )
            )
            final_chart = (pie + text).properties(height=400).configure_view(stroke=None).configure(background='transparent')
            st.altair_chart(final_chart, use_container_width=True)

        with col_table3:
            table_data = clasificacion_data.rename(columns={'Clasificacion_Ministerio': 'Clasificación'})
            table_display_data = table_data[['Clasificación', 'Total Mensual']]
            if not table_display_data.empty:
                total_row = pd.DataFrame([{'Clasificación': 'Total', 'Total Mensual': table_display_data['Total Mensual'].sum()}])
                table_display_data = pd.concat([table_display_data, total_row], ignore_index=True)
            table_height = (len(table_display_data) + 1) * 35 + 3
            st.dataframe(table_display_data.copy().style.format({"Total Mensual": lambda x: f"${format_number_es(x)}"}).set_properties(subset=["Total Mensual"], **{'text-align': 'right'}), hide_index=True, use_container_width=True, height=table_height)

        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
        dl5_col, dl6_col = st.columns(2)
        with dl5_col:
            st.download_button(label="📥 Descargar CSV (Clasif.)", data=table_display_data.to_csv(index=False).encode('utf-8'), file_name='distribucion_clasificacion.csv', mime='text/csv', use_container_width=True)
        with dl6_col:
            st.download_button(label="📥 Descargar Excel (Clasif.)", data=to_excel(table_display_data), file_name='distribucion_clasificacion.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', use_container_width=True)

    else:
        # Preparamos etiqueta compuesta para visualización mensual
        df_filtered['Eje_X'] = df_filtered['Mes'] + " " + df_filtered['Año'].astype(str)
        orden_eje_x = df_filtered.sort_values(['Año', 'Mes_Num'])['Eje_X'].unique().tolist()

        st.subheader("Evolución Mensual por Gerencia")
        
        gerencia_mensual_data = df_filtered.groupby(['Gerencia', 'Eje_X'])['Total Mensual'].sum().reset_index()
        gerencia_totales = gerencia_mensual_data.groupby('Gerencia')['Total Mensual'].sum().reset_index()
        
        col_chart_m_ger, col_table_m_ger = st.columns([3, 1])
        
        with col_chart_m_ger:
            chart_ger_stacked = alt.Chart(gerencia_mensual_data).mark_bar().encode(
                y=alt.Y('Gerencia:N', sort='-x', title=None, axis=alt.Axis(labelLimit=150)),
                x=alt.X('Total Mensual:Q', title='Masa Salarial ($)', axis=alt.Axis(format='$,.0s')),
                color=alt.Color('Eje_X:N', sort=orden_eje_x, title='Período'),
                tooltip=[
                    alt.Tooltip('Gerencia:N'),
                    alt.Tooltip('Eje_X:N', title='Período'),
                    alt.Tooltip('Total Mensual:Q', format='$,.2f')
                ]
            )
            text_totals_ger = alt.Chart(gerencia_totales).mark_text(
                align='left',
                baseline='middle',
                dx=5,
                color='black'
            ).encode(
                y=alt.Y('Gerencia:N', sort='-x'),
                x=alt.X('Total Mensual:Q'),
                text=alt.Text('Total Mensual:Q', format='$,.2s')
            )
            final_chart_ger = (chart_ger_stacked + text_totals_ger).properties(
                height=(len(gerencia_mensual_data['Gerencia'].unique()) * 35) + 50
            ).configure_view(stroke=None).configure(background='transparent')
            
            st.altair_chart(final_chart_ger, use_container_width=True)

        with col_table_m_ger:
            pivot_ger_mensual = pd.pivot_table(
                gerencia_mensual_data, values='Total Mensual', index='Gerencia', columns='Eje_X', aggfunc='sum', fill_value=0
            )
            cols_presentes = [m for m in orden_eje_x if m in pivot_ger_mensual.columns]
            pivot_ger_mensual = pivot_ger_mensual[cols_presentes]
            pivot_ger_mensual['Total'] = pivot_ger_mensual.sum(axis=1)
            pivot_ger_mensual = pivot_ger_mensual.sort_values('Total', ascending=False)
            
            st.write("**Tabla Resumen ($)**")
            st.dataframe(
                pivot_ger_mensual.style.format(lambda x: f"${format_number_es(x)}"), 
                use_container_width=True,
                height=(len(pivot_ger_mensual) * 35) + 50
            )

        st.markdown("---")
        st.subheader("Evolución Mensual por Clasificación")
        
        clasif_mensual_data = df_filtered.groupby(['Clasificacion_Ministerio', 'Eje_X'])['Total Mensual'].sum().reset_index()
        
        col_chart_m_clas, col_table_m_clas = st.columns([3, 1])

        with col_chart_m_clas:
            chart_clas_stacked = alt.Chart(clasif_mensual_data).mark_bar().encode(
                x=alt.X('Eje_X:N', sort=orden_eje_x, title='Período'),
                y=alt.Y('Total Mensual:Q', title='Masa Salarial ($)', axis=alt.Axis(format='$,.0s')),
                color=alt.Color('Clasificacion_Ministerio:N', title='Clasificación'),
                tooltip=[alt.Tooltip('Eje_X:N', title='Período'), alt.Tooltip('Clasificacion_Ministerio:N'), alt.Tooltip('Total Mensual:Q', format='$,.2f')]
            )
            totales_por_mes = clasif_mensual_data.groupby(['Eje_X'])['Total Mensual'].sum().reset_index()
            
            text_totals_clas = alt.Chart(totales_por_mes).mark_text(
                align='center',
                baseline='bottom',
                dy=-5,
                color='black'
            ).encode(
                x=alt.X('Eje_X:N', sort=orden_eje_x),
                y=alt.Y('Total Mensual:Q'),
                text=alt.Text('Total Mensual:Q', format='$,.2s')
            )

            final_chart_clas = (chart_clas_stacked + text_totals_clas).properties(
                height=400
            ).configure_view(stroke=None).configure(background='transparent')
            
            st.altair_chart(final_chart_clas, use_container_width=True)

        with col_table_m_clas:
            pivot_clas_mensual = pd.pivot_table(
                clasif_mensual_data, values='Total Mensual', index='Clasificacion_Ministerio', columns='Eje_X', aggfunc='sum', fill_value=0
            )
            cols_presentes_clas = [m for m in orden_eje_x if m in pivot_clas_mensual.columns]
            pivot_clas_mensual = pivot_clas_mensual[cols_presentes_clas]
            pivot_clas_mensual['Total'] = pivot_clas_mensual.sum(axis=1)
            pivot_clas_mensual = pivot_clas_mensual.sort_values('Total', ascending=False)
            
            st.write("**Tabla Resumen ($)**")
            st.dataframe(
                pivot_clas_mensual.style.format(lambda x: f"${format_number_es(x)}"), 
                use_container_width=True,
                height=400
            )

# --- TAB 3 (COSTOS PROMEDIOS) ---
with tab_costos:
    st.subheader("Análisis de Costos Promedios")
    st.markdown("Haga clic en cualquier punto de los gráficos para filtrar o ver detalles.")
    
    opts = {
        "Relación": "Relación", 
        "Nivel": "Nivel", 
        "Clasificación Ministerial": "Clasificacion_Ministerio"
    }
    
    c_sel, c_chk = st.columns(2)
    with c_sel: 
        sels = st.multiselect(
            "Dimensiones para Analizar:", 
            list(opts.keys()), 
            default=["Relación"]
        )
    with c_chk: 
        det = st.checkbox(
            "Ver detalle por Legajo en tablas", 
            help="Activa para ver el listado de empleados mes a mes."
        )
    
    st.markdown("---")
    
    # Preparar eje X compuesto
    df_filtered['Eje_X'] = df_filtered['Mes'] + " " + df_filtered['Año'].astype(str)
    meses_ordenados_costos = df_filtered.sort_values(['Año', 'Mes_Num'])['Eje_X'].unique().tolist()
    
    # Detectar si hay un solo mes visible
    is_single_month = len(meses_ordenados_costos) == 1
    
    if is_single_month:
        st.info(f"Visualización de mes único detectada: {meses_ordenados_costos[0]}. Los gráficos se muestran como distribución (Torta).")

    if not sels:
        st.info("Por favor, seleccione al menos una dimensión para visualizar.")
    
    for l in sels:
        col_cat = opts[l] 
        st.markdown(f"#### Análisis: {l}")
        
        g = df_filtered.groupby([col_cat, 'Eje_X']).agg(
            M=('Total Mensual', 'sum'), 
            D=('Dotación', 'sum')
        ).reset_index()
        
        g['CP'] = g['M'] / g['D']
        g['CP'] = g['CP'].fillna(0)
        
        if is_single_month:
            base_pie = alt.Chart(g).encode(
                theta=alt.Theta(field="M", type="quantitative", stack=True),
                color=alt.Color(field=col_cat, type="nominal", title=col_cat),
                tooltip=[
                    alt.Tooltip('Eje_X:N', title='Período'),
                    alt.Tooltip(f'{col_cat}:N'),
                    alt.Tooltip('M:Q', format='$,.2f', title='Masa Salarial (Total)'),
                    alt.Tooltip('D:Q', title='Dotación'),
                    alt.Tooltip('CP:Q', format='$,.2f', title='Costo Promedio')
                ]
            )
            pie_mark = base_pie.mark_arc(innerRadius=60, outerRadius=100)
            pie_text = base_pie.mark_text(radius=120).encode(
                text=alt.Text("M:Q", format="$,.2s")
            )
            final_chart_costos = (pie_mark + pie_text).properties(height=350)
            st.altair_chart(final_chart_costos, use_container_width=True)
            
        else:
            if l == "Relación":
                # --- GRÁFICO DE DOBLE EJE (DUAL AXIS) ---
                base_rel = alt.Chart(g).encode(
                    x=alt.X('Eje_X:N', sort=meses_ordenados_costos, title='Período')
                )
                
                # Capa 1: Barras Convenio (Eje Y Principal - Izquierda)
                bars_convenio = base_rel.transform_filter(
                    alt.datum.Relación == 'Convenio'
                ).mark_bar(opacity=0.7, width=20).encode(
                    y=alt.Y('CP:Q', title='Costo Promedio ($) - Convenio', axis=alt.Axis(format='$,.0f', titleColor='#1f77b4')),
                    color=alt.value('#1f77b4'),
                    tooltip=[
                        alt.Tooltip('Eje_X:N', title='Período'), 
                        alt.Tooltip('Relación:N'), 
                        alt.Tooltip('M:Q', format='$,.2f', title='Masa'), 
                        alt.Tooltip('D:Q', title='Dotación'), 
                        alt.Tooltip('CP:Q', format='$,.2f', title='Costo Promedio')
                    ]
                )
                
                # Capa 2: Línea Fuera de Convenio (Eje Y Secundario - Derecha)
                lines_fc = base_rel.transform_filter(
                    alt.datum.Relación != 'Convenio'
                ).mark_line(point=True, strokeWidth=3).encode(
                    y=alt.Y('CP:Q', title='Costo Promedio ($) - Fuera Convenio', axis=alt.Axis(format='$,.0f', titleColor='#ff7f0e')),
                    color=alt.value('#ff7f0e'), 
                    tooltip=[
                        alt.Tooltip('Eje_X:N', title='Período'), 
                        alt.Tooltip('Relación:N'), 
                        alt.Tooltip('M:Q', format='$,.2f', title='Masa'), 
                        alt.Tooltip('D:Q', title='Dotación'), 
                        alt.Tooltip('CP:Q', format='$,.2f', title='Costo Promedio')
                    ]
                )
                
                # Resolver escalas independientes para crear el efecto de doble eje
                final_chart_costos = alt.layer(bars_convenio, lines_fc).resolve_scale(
                    y='independent'
                ).properties(height=350)
                
                st.altair_chart(final_chart_costos, use_container_width=True)
            else:
                final_chart_costos = alt.Chart(g).mark_line(point=True).encode(
                    x=alt.X('Eje_X:N', sort=meses_ordenados_costos, title='Período'), 
                    y=alt.Y('CP:Q', title='Costo Promedio ($)', axis=alt.Axis(format='$,.0f')), 
                    color=alt.Color(f'{col_cat}:N', title=col_cat),
                    tooltip=[
                        alt.Tooltip('Eje_X:N', title='Período'), 
                        alt.Tooltip(f'{col_cat}:N'), 
                        alt.Tooltip('M:Q', format='$,.2f', title='Masa Salarial (Num)'), 
                        alt.Tooltip('D:Q', title='Dotación (Den)'),
                        alt.Tooltip('CP:Q', format='$,.2f', title='Costo Promedio')
                    ]
                ).properties(height=350).configure_point(size=100)
                st.altair_chart(final_chart_costos, use_container_width=True)
        
        if det:
            st.write(f"**Detalle por Mes y Legajo - {l}**")
            cols_base = ['Legajo', 'Apellido y Nombres', 'Gerencia', col_cat]
            # Usar Eje_X como columna de columnas para la pivot
            df_b = df_filtered[cols_base + ['Eje_X', 'Total Mensual']].copy()
            p = pd.pivot_table(df_b, values='Total Mensual', index=cols_base, columns='Eje_X', aggfunc='sum', fill_value=0).reset_index()
            mp = [m for m in meses_ordenados_costos if m in p.columns]
            vals = p[mp]
            p['Promedio Mensual'] = vals.replace(0, np.nan).mean(axis=1).fillna(0)
            p = p.sort_values(['Gerencia', 'Apellido y Nombres'])
            
            # 1. Definir columnas a mostrar
            cols_finales = cols_base + mp + ['Promedio Mensual']
            df_detailed_display = p[cols_finales].copy()
            
            # 2. FIJAR COLUMNAS USANDO TODAS LAS COLUMNAS DE TEXTO COMO ÍNDICE
            index_cols_safe = ['Legajo', 'Apellido y Nombres', 'Gerencia', col_cat]
            df_show = df_detailed_display.set_index(index_cols_safe)
            
            # 3. Identificar columnas numéricas para formatear
            cols_numericas = mp + ['Promedio Mensual']
            format_dict = {col: lambda x: f"${format_number_es(x)}" if pd.notnull(x) and x != 0 else ("-" if x == 0 else "") for col in cols_numericas if col in df_show.columns}

            # 4. Configurar anchos fijos
            col_config = {
                "Promedio Mensual": st.column_config.Column("Promedio Mensual", width=110),
            }
            for m in mp:
                col_config[m] = st.column_config.Column(m, width=110)

            # 5. Aplicar formato y estilos con TRY/EXCEPT para robustez
            try:
                styler = df_show.style.format(format_dict)
                # ALINEACIÓN DERECHA EXPLÍCITA
                cols_subset = [c for c in cols_numericas if c in df_show.columns]
                styler.set_properties(subset=cols_subset, **{'text-align': 'right !important'})
                
                if 'Promedio Mensual' in df_show.columns:
                    styler.set_properties(subset=['Promedio Mensual'], **{'background-color': '#FFE0B2', 'color': '#000000', 'font-weight': 'bold', 'text-align': 'right !important'})

                st.dataframe(styler, use_container_width=False, height=400, column_config=col_config)
            except Exception:
                st.dataframe(df_show, use_container_width=False, height=400)
            
            col_d1, col_d2 = st.columns(2)
            with col_d1: st.download_button(f"📥 Descargar Detalle CSV ({l})", data=df_detailed_display.to_csv(index=False).encode('utf-8'), file_name=f'detalle_costos_{l}.csv', mime='text/csv', use_container_width=True)
            with col_d2: st.download_button(f"📥 Descargar Detalle Excel ({l})", data=to_excel(df_detailed_display), file_name=f'detalle_costos_{l}.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', use_container_width=True)
            
        else:
            st.write(f"**Resumen Mensual Desglosado (Masa y Dotación) - {l}**")
            
            pivot_multi = pd.pivot_table(
                df_filtered,
                values=['Total Mensual', 'Dotación'],
                index=col_cat,
                columns='Eje_X', # Usar mes/año
                aggfunc={'Total Mensual': 'sum', 'Dotación': 'sum'},
                fill_value=0
            )
            
            available_months = [m for m in meses_ordenados_costos if m in pivot_multi.columns.levels[1]]
            
            for mes in available_months:
                 masa = pivot_multi[('Total Mensual', mes)]
                 dot = pivot_multi[('Dotación', mes)]
                 avg = masa.div(dot.replace(0, np.nan)).fillna(0)
                 pivot_multi[('Promedio', mes)] = avg

            new_columns = []
            for mes in available_months:
                new_columns.append(('Total Mensual', mes))
                new_columns.append(('Dotación', mes))
                new_columns.append(('Promedio', mes))
            
            pivot_multi = pivot_multi.reindex(columns=new_columns)
            
            masa_anual = df_filtered.groupby(col_cat)['Total Mensual'].sum()
            dot_acum_anual = df_filtered.groupby([col_cat, 'Eje_X'])['Dotación'].sum().groupby(col_cat).sum()
            costo_prom_anual = masa_anual.div(dot_acum_anual.replace(0, np.nan)).fillna(0)
            
            prom_cols_tuples = [('Promedio', m) for m in available_months]
            prom_de_promedios = pivot_multi[prom_cols_tuples].mean(axis=1).fillna(0)

            pivot_multi[('Total Anual', 'Masa Total ($)')] = masa_anual
            pivot_multi[('Total Anual', 'Dotación Acum. (#)')] = dot_acum_anual
            pivot_multi[('Total Anual', 'Costo Promedio Ponderado ($)')] = costo_prom_anual
            pivot_multi[('Total Anual', 'Promedio de Promedios ($)')] = prom_de_promedios

            total_row_sums = pivot_multi[[c for c in pivot_multi.columns if c[0] in ['Total Mensual', 'Dotación']]].sum()
            
            total_row_vals = {}
            for col in total_row_sums.index:
                total_row_vals[col] = total_row_sums[col]
            
            for mes in available_months:
                m_t = total_row_vals.get(('Total Mensual', mes), 0)
                d_t = total_row_vals.get(('Dotación', mes), 0)
                p_t = m_t / d_t if d_t > 0 else 0
                total_row_vals[('Promedio', mes)] = p_t
            
            t_masa_anual = sum([total_row_vals.get(('Total Mensual', m), 0) for m in available_months])
            t_dot_anual = sum([total_row_vals.get(('Dotación', m), 0) for m in available_months])
            t_prom_pond = t_masa_anual / t_dot_anual if t_dot_anual > 0 else 0
            
            all_monthly_avgs = [total_row_vals.get(('Promedio', m), 0) for m in available_months]
            t_prom_de_prom = sum(all_monthly_avgs) / len(all_monthly_avgs) if all_monthly_avgs else 0

            total_row_vals[('Total Anual', 'Masa Total ($)')] = t_masa_anual
            total_row_vals[('Total Anual', 'Dotación Acum. (#)')] = t_dot_anual
            total_row_vals[('Total Anual', 'Costo Promedio Ponderado ($)')] = t_prom_pond
            total_row_vals[('Total Anual', 'Promedio de Promedios ($)')] = t_prom_de_prom
            
            total_series = pd.Series(total_row_vals, name='PROMEDIO GENERAL')
            pivot_multi.loc['PROMEDIO GENERAL'] = total_series
            
            flat_cols = []
            for metric, mes in pivot_multi.columns:
                if metric == 'Total Mensual':
                    flat_cols.append(f"{mes} - Masa ($)")
                elif metric == 'Dotación':
                    flat_cols.append(f"{mes} - Dot. (#)")
                elif metric == 'Promedio':
                    flat_cols.append(f"Prom. {mes} ($)")
                elif metric == 'Total Anual':
                    flat_cols.append(f"ANUAL - {mes}")
                else:
                    flat_cols.append(f"{mes} {metric}")
            
            pivot_multi.columns = flat_cols
            
            # Reset index
            pivot_multi = pivot_multi.reset_index()
            
            cols_masa = [c for c in flat_cols if "($)" in c]
            cols_dot = [c for c in flat_cols if "(#)" in c]
            
            # Identificar columnas a colorear
            cols_promedio = [c for c in pivot_multi.columns if "Prom." in c or "PROMEDIO" in c.upper() or "Anual" in c]

            # Configuración de columnas
            pivot_to_show = pivot_multi.set_index(col_cat)

            config_resumen = {}
            for c in pivot_to_show.columns:
                if "Masa" in c:
                    config_resumen[c] = st.column_config.Column(c, width=160)
                elif "Promedio" in c or "Prom." in c:
                     config_resumen[c] = st.column_config.Column(c, width=120)
                elif "Dot." in c or "Dotación" in c:
                     config_resumen[c] = st.column_config.Column(c, width=90)
            
            # Formateo visual via Styler
            try:
                format_dict_multi = {}
                for c in cols_masa + [col for col in cols_promedio if col in pivot_to_show.columns]:
                    if c in pivot_to_show.columns:
                        format_dict_multi[c] = lambda x: f"${format_number_es(x)}" if pd.notnull(x) else ""
                
                for c in cols_dot:
                    if c in pivot_to_show.columns:
                        format_dict_multi[c] = lambda x: f"{int(x)}" if pd.notnull(x) else ""

                styler_multi = pivot_to_show.style.format(format_dict_multi)
                
                # Alineación y Colores
                cols_subset_multi = list(pivot_to_show.columns)
                styler_multi.set_properties(subset=cols_subset_multi, **{'text-align': 'right !important'})

                styler_multi.set_properties(
                    subset=[c for c in cols_promedio if c in pivot_to_show.columns], 
                    **{'background-color': '#FFE0B2', 'color': '#000000', 'text-align': 'right !important'}
                )

                st.dataframe(
                    styler_multi,
                    use_container_width=False,
                    hide_index=False, 
                    column_config=config_resumen
                )
            except Exception:
                st.dataframe(pivot_to_show, use_container_width=False)
            
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                st.download_button(f"📥 Descargar Resumen CSV ({l})", data=pivot_multi.to_csv(index=True).encode('utf-8'), file_name=f'resumen_costos_{l}.csv', mime='text/csv', use_container_width=True)
            with col_d2:
                st.download_button(f"📥 Descargar Resumen Excel ({l})", data=to_excel(pivot_multi.reset_index()), file_name=f'resumen_costos_{l}.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', use_container_width=True)
            
        st.markdown("---")


# ------------------------- TAB 4: CONCEPTOS / SIPAF -------------------------
with tab_conceptos:
    st.subheader("Masa Salarial por Concepto / SIPAF")
    
    col_sel_1, col_sel_2 = st.columns(2)
    with col_sel_1:
        mode = st.radio("Seleccionar grupo de conceptos:", options=["Masa por Concepto", "Resumen SIPAF"], index=0, horizontal=True)
    with col_sel_2:
        vista_conceptos = st.radio("Seleccionar visualización:", options=["Vista Acumulada", "Vista Mensualizada"], index=0, horizontal=True, key="concept_view_mode")
    
    st.markdown("---")

    concept_columns_to_pivot = [
        'Nómina General con Aportes', 'Antigüedad', 'Horas Extras', 'Cs. Sociales s/Remunerativos',
        'Cargas Sociales Antigüedad', 'Cargas Sociales Horas Extras', 'Nómina General sin Aportes',
        'Gratificación Única y Extraordinaria', 'Gastos de Representación', 'Gratificación por Antigüedad',
        'Gratificación por Jubilación', 'SAC Horas Extras', 'Cargas Sociales SAC Hextras', 'SAC Pagado',
        'Cargas Sociales s/SAC Pagado', 'Vacaciones Pagadas', 'Cargas Sociales s/Vac. Pagadas',
        'Asignaciones Familiares 1.4.', 'Total Mensual'
    ]
    concept_cols_present = [col for col in concept_columns_to_pivot if col in df_filtered.columns]

    concept_columns_sipaf = [
        'Retribución Cargo 1.1.1', 'Antigüedad 1.1.3', 'Retribuciones Extraordinarias 1.3.1',
        'Contribuciones Patronales 1.3.3', 'SAC 1.3.2', 'SAC 1.1.4',
        'Contribuciones Patronales 1.1.6', 'Complementos 1.1.7', 'Asignaciones Familiares 1.4'
    ]
    
    # Preparar eje X compuesto
    df_filtered['Eje_X'] = df_filtered['Mes'] + " " + df_filtered['Año'].astype(str)
    meses_ordenados_viz_conc = df_filtered.sort_values(['Año', 'Mes_Num'])['Eje_X'].unique().tolist()

    if mode == "Masa por Concepto":
        if concept_cols_present:
            df_melted = df_filtered.melt(id_vars=['Eje_X', 'Mes', 'Mes_Num', 'Año'], value_vars=concept_cols_present, var_name='Concepto', value_name='Monto')
            
            pivot_table = pd.pivot_table(df_melted, values='Monto', index='Concepto', columns='Eje_X', aggfunc='sum', fill_value=0)
            
            meses_en_datos = meses_ordenados_viz_conc
            
            if all(mes in pivot_table.columns for mes in meses_en_datos):
                pivot_table = pivot_table[meses_en_datos]
            pivot_table['Total general'] = pivot_table.sum(axis=1)
            pivot_table = pivot_table.reindex(concept_cols_present).dropna(how='all')

            col_chart_concepto, col_table_concepto = st.columns([2, 1])
            
            with col_chart_concepto:
                if vista_conceptos == "Vista Acumulada":
                    chart_data_concepto = pivot_table.reset_index()
                    chart_data_concepto = chart_data_concepto[chart_data_concepto['Concepto'] != 'Total Mensual']
                    chart_data_concepto = chart_data_concepto.sort_values('Total general', ascending=False)
                    chart_height_concepto = (len(chart_data_concepto) + 1) * 35 + 3
                    
                    base_chart_concepto = alt.Chart(chart_data_concepto).mark_bar().encode(
                        x=alt.X('Total general:Q', title='Masa Salarial ($)', axis=alt.Axis(format='$,.0s')),
                        y=alt.Y('Concepto:N', sort='-x', title=None, axis=alt.Axis(labelLimit=200)),
                        tooltip=[alt.Tooltip('Concepto:N'), alt.Tooltip('Total general:Q', format='$,.2f', title='Total')]
                    )
                    text_labels_concepto = base_chart_concepto.mark_text(align='left', baseline='middle', dx=3).encode(text=alt.Text('Total general:Q', format='$,.0s'))
                    bar_chart_concepto = (base_chart_concepto + text_labels_concepto).properties(height=chart_height_concepto, padding={'top': 25, 'left': 5, 'right': 5, 'bottom': 5}).configure(background='transparent').configure_view(fill='transparent')
                    st.altair_chart(bar_chart_concepto, use_container_width=True)
                else:
                    chart_data_mensual = df_melted[df_melted['Concepto'] != 'Total Mensual']
                    chart_data_mensual = chart_data_mensual.groupby(['Concepto', 'Eje_X', 'Mes_Num', 'Año'])['Monto'].sum().reset_index()
                    
                    totals_concept = chart_data_mensual.groupby('Concepto')['Monto'].sum().reset_index()

                    total_por_concepto = chart_data_mensual.groupby('Concepto')['Monto'].sum().sort_values(ascending=False).index.tolist()
                    chart_height_mensual = (len(total_por_concepto) * 35) + 50

                    bar_chart_mensual = alt.Chart(chart_data_mensual).mark_bar().encode(
                        y=alt.Y('Concepto:N', sort=total_por_concepto, title=None, axis=alt.Axis(labelLimit=200)),
                        x=alt.X('Monto:Q', title='Masa Salarial ($)', axis=alt.Axis(format='$,.0s')),
                        color=alt.Color('Eje_X:N', sort=meses_ordenados_viz_conc, title='Período'),
                        order=alt.Order(['Año', 'Mes_Num'], sort='ascending'),
                        tooltip=[alt.Tooltip('Concepto:N'), alt.Tooltip('Eje_X:N', title='Período'), alt.Tooltip('Monto:Q', format='$,.2f')]
                    )

                    text_totals_mensual = alt.Chart(totals_concept).mark_text(
                        align='left',
                        baseline='middle',
                        dx=3,
                        color='black'
                    ).encode(
                        y=alt.Y('Concepto:N', sort=total_por_concepto),
                        x=alt.X('Monto:Q'),
                        text=alt.Text('Monto:Q', format='$,.2s')
                    )

                    final_chart_mensual = (bar_chart_mensual + text_totals_mensual).properties(
                        height=chart_height_mensual
                    ).configure(background='transparent').configure_view(fill='transparent')
                    
                    st.altair_chart(final_chart_mensual, use_container_width=True)

            with col_table_concepto:
                height_table = chart_height_concepto + 35 if vista_conceptos == "Vista Acumulada" else chart_height_mensual
                
                # Formato directo en datos para evitar KeyError con set_index/styles
                df_concepto_show = pivot_table.copy()
                for col in df_concepto_show.columns:
                    if pd.api.types.is_numeric_dtype(df_concepto_show[col]):
                        df_concepto_show[col] = df_concepto_show[col].apply(lambda x: f"${format_number_es(x)}")

                config_concepto = {
                    c: st.column_config.Column(c, width=110) for c in df_concepto_show.columns
                }
                
                try:
                    styler_conceptos = df_concepto_show.style
                    styler_conceptos.set_properties(**{'text-align': 'right'})
                    st.dataframe(styler_conceptos, use_container_width=False, height=height_table, column_config=config_concepto)
                except Exception:
                    st.dataframe(df_concepto_show, use_container_width=False, height=height_table)

            st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
            col_dl_7, col_dl_8 = st.columns(2)
            with col_dl_7:
                st.download_button(label="📥 Descargar CSV", data=pivot_table.to_csv(index=True).encode('utf-8'), file_name='masa_por_concepto.csv', mime='text/csv', use_container_width=True)
            with col_dl_8:
                st.download_button(label="📥 Descargar Excel", data=to_excel(pivot_table.reset_index()), file_name='masa_por_concepto.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', use_container_width=True)
        else:
            st.info("No hay datos de conceptos para mostrar con los filtros seleccionados.")

    else:
        df_filtered.columns = df_filtered.columns.str.strip().str.replace(r"\s+", " ", regex=True)
        sipaf_cols_present = []
        for col in df_filtered.columns:
            for expected in concept_columns_sipaf:
                if expected.lower().replace(".", "") in col.lower().replace(".", ""):
                    sipaf_cols_present.append(col)
        sipaf_cols_present = list(dict.fromkeys(sipaf_cols_present))

        if sipaf_cols_present:
            df_melted_sipaf = df_filtered.melt(id_vars=['Eje_X', 'Mes', 'Mes_Num', 'Año'], value_vars=sipaf_cols_present, var_name='Concepto', value_name='Monto')
            
            pivot_table_sipaf = pd.pivot_table(df_melted_sipaf, values='Monto', index='Concepto', columns='Eje_X', aggfunc='sum', fill_value=0)
            
            meses_en_datos_sipaf = meses_ordenados_viz_conc
            
            if all(mes in pivot_table_sipaf.columns for mes in meses_en_datos_sipaf):
                pivot_table_sipaf = pivot_table_sipaf[meses_en_datos_sipaf]
            pivot_table_sipaf['Total general'] = pivot_table_sipaf.sum(axis=1)
            pivot_table_sipaf = pivot_table_sipaf.dropna(how='all')
            if not pivot_table_sipaf.empty:
                total_row = pivot_table_sipaf.sum().rename('Total general')
                pivot_table_sipaf = pd.concat([pivot_table_sipaf, total_row.to_frame().T])

            col_chart_sipaf, col_table_sipaf = st.columns([2, 1])
            
            with col_chart_sipaf:
                if vista_conceptos == "Vista Acumulada":
                    chart_data_sipaf = pivot_table_sipaf.drop('Total general').reset_index()
                    chart_data_sipaf = chart_data_sipaf.rename(columns={'index': 'Concepto'})
                    chart_data_sipaf = chart_data_sipaf.sort_values('Total general', ascending=False)
                    chart_height_sipaf = (len(chart_data_sipaf) + 1) * 35 + 3
                    
                    base_chart_sipaf = alt.Chart(chart_data_sipaf).mark_bar().encode(
                        x=alt.X('Total general:Q', title='Masa Salarial ($)', axis=alt.Axis(format='$,.0s')),
                        y=alt.Y('Concepto:N', sort='-x', title=None, axis=alt.Axis(labelLimit=200)),
                        tooltip=[alt.Tooltip('Concepto:N'), alt.Tooltip('Total general:Q', format='$,.2f', title='Total')]
                    )
                    text_labels_sipaf = base_chart_sipaf.mark_text(align='left', baseline='middle', dx=3).encode(text=alt.Text('Total general:Q', format='$,.0s'))
                    bar_chart_sipaf = (base_chart_sipaf + text_labels_sipaf).properties(height=chart_height_sipaf, padding={'top': 25, 'left': 5, 'right': 5, 'bottom': 5}).configure(background='transparent').configure_view(fill='transparent')
                    st.altair_chart(bar_chart_sipaf, use_container_width=True)
                else:
                    chart_data_sipaf_mensual = df_melted_sipaf.groupby(['Concepto', 'Eje_X', 'Mes_Num', 'Año'])['Monto'].sum().reset_index()

                    totals_sipaf = chart_data_sipaf_mensual.groupby('Concepto')['Monto'].sum().reset_index()

                    total_por_concepto_sipaf = chart_data_sipaf_mensual.groupby('Concepto')['Monto'].sum().sort_values(ascending=False).index.tolist()
                    chart_height_sipaf_mensual = (len(total_por_concepto_sipaf) * 35) + 50

                    bar_chart_sipaf_mensual = alt.Chart(chart_data_sipaf_mensual).mark_bar().encode(
                        y=alt.Y('Concepto:N', sort=total_por_concepto_sipaf, title=None, axis=alt.Axis(labelLimit=200)),
                        x=alt.X('Monto:Q', title='Masa Salarial ($)', axis=alt.Axis(format='$,.0s')),
                        color=alt.Color('Eje_X:N', sort=meses_ordenados_viz_conc, title='Período'),
                        order=alt.Order(['Año', 'Mes_Num'], sort='ascending'),
                        tooltip=[alt.Tooltip('Concepto:N'), alt.Tooltip('Eje_X:N', title='Período'), alt.Tooltip('Monto:Q', format='$,.2f')]
                    )

                    text_totals_sipaf = alt.Chart(totals_sipaf).mark_text(
                        align='left',
                        baseline='middle',
                        dx=3,
                        color='black'
                    ).encode(
                        y=alt.Y('Concepto:N', sort=total_por_concepto_sipaf),
                        x=alt.X('Monto:Q'),
                        text=alt.Text('Monto:Q', format='$,.2s')
                    )

                    final_chart_sipaf = (bar_chart_sipaf_mensual + text_totals_sipaf).properties(
                        height=chart_height_sipaf_mensual
                    ).configure(background='transparent').configure_view(fill='transparent')

                    st.altair_chart(final_chart_sipaf, use_container_width=True)

            with col_table_sipaf:
                height_table_sipaf = chart_height_sipaf + 35 if vista_conceptos == "Vista Acumulada" else chart_height_sipaf_mensual
                
                # Formato directo
                df_sipaf_show = pivot_table_sipaf.copy()
                for col in df_sipaf_show.columns:
                    if pd.api.types.is_numeric_dtype(df_sipaf_show[col]):
                        df_sipaf_show[col] = df_sipaf_show[col].apply(lambda x: f"${format_number_es(x)}")

                config_sipaf = {
                    c: st.column_config.Column(c, width=110) for c in df_sipaf_show.columns
                }
                
                try:
                    styler_sipaf = df_sipaf_show.style
                    styler_sipaf.set_properties(**{'text-align': 'right'})
                    st.dataframe(styler_sipaf, use_container_width=False, height=height_table_sipaf, column_config=config_sipaf)
                except Exception:
                    st.dataframe(df_sipaf_show, use_container_width=False, height=height_table_sipaf)

            st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
            col_dl_9, col_dl_10 = st.columns(2)
            with col_dl_9:
                st.download_button(label="📥 Descargar CSV", data=pivot_table_sipaf.to_csv(index=True).encode('utf-8'), file_name='resumen_sipaf.csv', mime='text/csv', use_container_width=True)
            with col_dl_10:
                st.download_button(label="📥 Descargar Excel", data=to_excel(pivot_table.reset_index()), file_name='resumen_sipaf.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', use_container_width=True)
        else:
            st.info("No hay datos de conceptos SIPAF para mostrar con los filtros seleccionados.")

# ------------------------- TAB 5: TABLA DETALLADA -------------------------
with tab_tabla:
    st.subheader("Tabla de Datos Detallados")
    df_display = df_filtered.copy().reset_index(drop=True)
    if not df_display.empty:
        st.markdown("##### Descargar datos")
        col_btn1, col_btn2, col_btn3 = st.columns([1,1,1])
        with col_btn1:
            st.download_button(label="📥 CSV (Tabla Completa)", data=df_display.to_csv(index=False).encode('utf-8'), file_name='datos_detallados.csv', mime='text/csv', use_container_width=True)
        with col_btn2:
            st.download_button(label="📥 Excel (Tabla Completa)", data=to_excel(df_display), file_name='datos_detallados.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', use_container_width=True)
        with col_btn3:
            pdf_summary_cols = ['Período', 'Nro. de Legajo', 'Apellido y Nombres', 'Gerencia', 'Clasificacion_Ministerio', 'Total Mensual']
            existing_pdf_cols = [col for col in pdf_summary_cols if col in df_display.columns]
            df_pdf_raw = df_display[existing_pdf_cols]
            df_pdf_formatted = df_pdf_raw.copy()
            df_pdf_formatted['Período'] = df_pdf_formatted['Período'].dt.strftime('%Y-%m')
            df_pdf_formatted['Total Mensual'] = df_pdf_formatted['Total Mensual'].apply(lambda x: f"${format_number_es(x)}")
            st.download_button(label="📥 PDF (Resumen)", data=to_pdf(df_pdf_formatted, st.session_state.ms_selections.get('Mes', [])), file_name='resumen_detallado.pdf', mime='application/pdf', use_container_width=True)

        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
        if 'page_number' not in st.session_state: st.session_state.page_number = 0
        PAGE_SIZE = 50
        total_rows = len(df_display)
        num_pages = (total_rows // PAGE_SIZE) + (1 if total_rows % PAGE_SIZE > 0 else 0)
        st.write(f"Mostrando **{PAGE_SIZE}** filas por página. Total de filas: **{total_rows}**.")
        prev_col, page_col, next_col = st.columns([2, 8, 2])
        if prev_col.button("⬅️ Anterior", use_container_width=True):
            if st.session_state.page_number > 0: st.session_state.page_number -= 1
        if next_col.button("Siguiente ➡️", use_container_width=True):
            if st.session_state.page_number < num_pages - 1: st.session_state.page_number += 1
        page_col.write(f"Página **{st.session_state.page_number + 1}** de **{num_pages}**")
        start_idx = st.session_state.page_number * PAGE_SIZE
        end_idx = min(start_idx + PAGE_SIZE, total_rows)
        
        # Copia para visualización
        df_page = df_display.iloc[start_idx:end_idx].copy()

        currency_columns = ['Total Sujeto a Retención', 'Vacaciones', 'Alquiler', 'Horas Extras', 'Nómina General con Aportes', 'Cs. Sociales s/Remunerativos', 'Cargas Sociales Ant.', 'IC Pagado', 'Vacaciones Pagadas', 'Cargas Sociales s/Vac. Pagadas', 'Retribución Cargo 1.1.1.', 'Antigüedad 1.1.3.', 'Retribuciones Extraordinarias 1.3.1.', 'Contribuciones Patronales', 'Gratificación por Antigüedad', 'Gratificación por Jubilación', 'Total No Remunerativo', 'SAC Horas Extras', 'Cargas Sociales SAC Hextras', 'SAC Pagado', 'Cargas Sociales s/SAC Pagado', 'Cargas Sociales Antigüedad', 'Nómina General sin Aportes', 'Gratificación Única y Extraordinaria', 'Gastos de Representación', 'Contribuciones Patronales 1.3.3.', 'S.A.C. 1.3.2.', 'S.A.C. 1.1.4.', 'Contribuciones Patronales 1.1.6.', 'Complementos 1.1.7.', 'Asignaciones Familiares 1.4.', 'Total Mensual']
        integer_columns = ['Dotación'] 
        
        currency_formatter = lambda x: f"${format_number_es(x)}"
        format_mapper = {col: currency_formatter for col in currency_columns if col in df_page.columns}
        for col in integer_columns:
            if col in df_page.columns:
                format_mapper[col] = format_integer_es
        
        # Columnas que queremos alinear a la derecha (incluyendo IDs aunque sean texto)
        columns_to_align_right = [col for col in currency_columns + integer_columns + ['Ceco', 'Nro. de Legajo'] if col in df_page.columns]
        
        # Aplicar fijación de columnas también a esta tabla
        cols_fix_tabla = ['Período', 'Legajo', 'Apellido y Nombres']
        existing_fix_cols = [c for c in cols_fix_tabla if c in df_page.columns]
        
        # --- BLINDAJE ANTI-ERROR EN VISUALIZACIÓN ---
        try:
            if existing_fix_cols:
                # Para la tabla de datos detallados, usamos set_index para fijar columnas.
                df_page_show = df_page.set_index(existing_fix_cols)
                
                # Ajustar formateo para no incluir índice
                format_mapper_no_index = {k: v for k, v in format_mapper.items() if k not in existing_fix_cols}
                cols_align_no_index = [c for c in columns_to_align_right if c not in existing_fix_cols]
                
                st.dataframe(
                    df_page_show.style.format(format_mapper_no_index, na_rep="")
                    .set_properties(subset=cols_align_no_index, **{'text-align': 'right !important'}), 
                    use_container_width=False, 
                    hide_index=False # Mostrar índice para que se fije
                )
            else:
                st.dataframe(
                    df_page.style.format(format_mapper, na_rep="")
                    .set_properties(subset=columns_to_align_right, **{'text-align': 'right !important'}), 
                    use_container_width=False, 
                    hide_index=True
                )
        except Exception:
            # Si el estilo falla (por tipos de datos raros o duplicados), mostramos modo compatibilidad
            st.warning("⚠️ Nota: Se detectó un problema con el formato visual avanzado. Se muestra la tabla en modo de compatibilidad.")
            
            # Aplicar formato directamente a los datos (convirtiéndolos a string)
            df_fallback = df_page.copy()
            for col, func in format_mapper.items():
                if col in df_fallback.columns:
                    try:
                        df_fallback[col] = df_fallback[col].apply(func)
                    except:
                        pass
            
            st.dataframe(df_fallback, use_container_width=False, hide_index=True)

    else:
        st.info("No hay datos que coincidan con los filtros seleccionados.")

# --- FIN ---