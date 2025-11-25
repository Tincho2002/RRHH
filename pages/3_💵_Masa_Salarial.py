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

def format_integer_es(num):
    if pd.isna(num) or not isinstance(num, (int, float, np.number)): return ""
    s = f"{int(num):,}"
    return s.replace(",", ".")

# --- FUNCIONES DE EXPORTACIÓN ---
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
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

# --- LÓGICA DE FILTROS ---
def apply_filters(df, selections):
    _df = df.copy()
    for col, values in selections.items():
        if values:
            _df = _df[_df[col].isin(values)]
    return _df
    
# --- INICIO: FUNCIONES PARA FILTROS INTELIGENTES ---
def get_sorted_unique_options(dataframe, column_name):
    if column_name in dataframe.columns:
        unique_values = dataframe[column_name].dropna().unique().tolist()
        unique_values = [v for v in unique_values if v != 'no disponible']
        if column_name == 'Mes':
            all_months_order = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
            return sorted(unique_values, key=lambda m: all_months_order.index(m) if m in all_months_order else -1)
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
    if 'Unnamed: 0' in df.columns:
        df = df.drop(columns=['Unnamed: 0'])
    if 'Período' not in df.columns:
        st.error("Error Crítico: La columna 'Período' no se encuentra.")
        return pd.DataFrame()
    
    # --- MEJORA: Parseo robusto de fechas en español ---
    # Esto soluciona el problema si 'ene-25' viene como texto y no lo reconoce
    def parse_spanish_date(x):
        if isinstance(x, datetime):
            return x
        x_str = str(x).lower().strip()
        # Mapeo manual para asegurar que entienda meses en español
        replacements = {
            'ene': 'jan', 'abr': 'apr', 'ago': 'aug', 'dic': 'dec',
            'enero': 'january', 'feb': 'february', 'mar': 'march', 'abril': 'april',
            'may': 'may', 'jun': 'june', 'jul': 'july', 'agosto': 'august',
            'sept': 'sep', 'sep': 'sep', 'oct': 'october', 'nov': 'november', 'diciembre': 'december'
        }
        for es, en in replacements.items():
            if es in x_str:
                x_str = x_str.replace(es, en)
                break
        return pd.to_datetime(x_str, errors='coerce')

    # Intentar conversión directa, si falla usar el parser manual
    df['Período_Temp'] = pd.to_datetime(df['Período'], errors='coerce')
    mask_nat = df['Período_Temp'].isna()
    if mask_nat.any():
        df.loc[mask_nat, 'Período_Temp'] = df.loc[mask_nat, 'Período'].apply(parse_spanish_date)
    
    df['Período'] = df['Período_Temp']
    df.drop(columns=['Período_Temp'], inplace=True)
    
    df.dropna(subset=['Período'], inplace=True)
    df['Mes_Num'] = df['Período'].dt.month.astype(int)
    meses_es = {1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'}
    df['Mes'] = df['Mes_Num'].map(meses_es)
    
    df.rename(columns={'Clasificación Ministerio de Hacienda': 'Clasificacion_Ministerio', 'Nro. de Legajo': 'Legajo'}, inplace=True)
    key_filter_columns = ['Gerencia', 'Nivel', 'Clasificacion_Ministerio', 'Relación', 'Ceco', 'Legajo']
    for col in key_filter_columns:
        if col in df.columns:
            if col in ['Ceco', 'Legajo']:
                df[col] = pd.to_numeric(df[col], errors='coerce').astype('Int64').astype(str).replace('<NA>', 'no disponible')
            df[col] = df[col].astype(str).str.strip().replace(['', 'None', 'nan', 'nan.0', '0'], 'no disponible')
        else:
            df[col] = 'no disponible'

    if 'Dotación' in df.columns:
        df['Dotación'] = pd.to_numeric(df['Dotación'], errors='coerce').fillna(0).astype(int)

    df.dropna(subset=['Gerencia', 'Nivel', 'Clasificacion_Ministerio', 'Relación'], inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df

st.title('💵 Dashboard de Masa Salarial 2025')
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
    
# --- SIDEBAR: filtros ---
st.sidebar.header('Filtros del Dashboard')

filter_cols = ['Gerencia', 'Nivel', 'Clasificacion_Ministerio', 'Relación', 'Mes', 'Ceco', 'Legajo']

# Inicializar selección en session_state si no existe
if 'ms_selections' not in st.session_state:
    initial_selections = {col: get_sorted_unique_options(df, col) for col in filter_cols}
    st.session_state.ms_selections = initial_selections
    st.rerun()

# Botón de reset
if st.sidebar.button("🔄 Resetear Filtros", use_container_width=True, key="ms_clear"):
    initial_selections = {col: get_sorted_unique_options(df, col) for col in filter_cols}
    st.session_state.ms_selections = initial_selections
    st.rerun()

st.sidebar.markdown("---")

# Renderizado de filtros (slicer inteligente)
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

# Aplicar filtros
df_filtered = apply_filters(df, st.session_state.ms_selections)


# =============================================================================
# --- INICIO: LÓGICA DE MÉTRICAS CON DELTA Y DISEÑO DE TARJETAS ---
# =============================================================================

# 1. Identificar el mes actual y el mes anterior basado en la selección
all_months_sorted = get_sorted_unique_options(df, 'Mes')
selected_months = st.session_state.ms_selections.get('Mes', [])
sorted_selected_months = [m for m in all_months_sorted if m in selected_months]

latest_month_name = None
previous_month_name = None

if sorted_selected_months:
    # Si el usuario seleccionó meses, usamos el último y penúltimo de su selección
    latest_month_name = sorted_selected_months[-1]
    if len(sorted_selected_months) > 1:
        previous_month_name = sorted_selected_months[-2]
else:
    # Si no hay selección de mes, usamos el último mes de los datos filtrados
    if not df_filtered.empty:
        all_months_nums_sorted_in_df = sorted(df['Mes_Num'].unique())
        latest_month_num_fallback = df_filtered.sort_values('Mes_Num', ascending=False)['Mes_Num'].iloc[0]
        latest_month_name = df[df['Mes_Num'] == latest_month_num_fallback]['Mes'].iloc[0]
        
        # Intentamos encontrar el mes anterior en los datos generales
        if latest_month_num_fallback in all_months_nums_sorted_in_df:
            latest_index_fallback = all_months_nums_sorted_in_df.index(latest_month_num_fallback)
            if latest_index_fallback > 0:
                previous_month_num_fallback = all_months_nums_sorted_in_df[latest_index_fallback - 1]
                previous_month_name = df[df['Mes_Num'] == previous_month_num_fallback]['Mes'].iloc[0]

# 2. Crear DataFrames base para el mes actual y el anterior
# (filtramos por todo MENOS el mes)
selections_without_month = st.session_state.ms_selections.copy()
selections_without_month.pop('Mes', [])
df_metrics_base = apply_filters(df, selections_without_month)

df_current = pd.DataFrame()
df_previous = pd.DataFrame()

if latest_month_name:
    df_current = df_metrics_base[df_metrics_base['Mes'] == latest_month_name]
if previous_month_name:
    df_previous = df_metrics_base[df_metrics_base['Mes'] == previous_month_name]

# Si no se seleccionó ningún mes, df_current estará vacío.
# Lo poblamos con el último mes de df_metrics_base (que es todos los meses filtrados)
if df_current.empty and not df_metrics_base.empty and not sorted_selected_months:
     df_current = df_metrics_base[df_metrics_base['Mes'] == latest_month_name]


# 3. Función auxiliar para calcular las 4 métricas para un DataFrame de un mes
def calculate_monthly_metrics(df_month):
    if df_month.empty:
        return {'total_masa': 0, 'empleados': 0, 'costo_medio_conv': 0, 'costo_medio_fc': 0}
    
    total_masa = df_month['Total Mensual'].sum()
    empleados = df_month['Legajo'].nunique()
    
    # Usamos 'Nivel' == 'FC' para definir F. Convenio. Todo lo demás es Convenio.
    is_fc = df_month['Nivel'] == 'FC'
    df_fc = df_month[is_fc]
    df_convenio = df_month[~is_fc]

    total_masa_convenio = df_convenio['Total Mensual'].sum()
    total_masa_fc = df_fc['Total Mensual'].sum()
    
    dotacion_convenio = df_convenio['Legajo'].nunique()
    dotacion_fc = df_fc['Legajo'].nunique()
    
    # Calculamos el costo medio *de ese mes*
    costo_medio_conv = total_masa_convenio / dotacion_convenio if dotacion_convenio > 0 else 0
    costo_medio_fc = total_masa_fc / dotacion_fc if dotacion_fc > 0 else 0
    
    return {
        'total_masa': total_masa,
        'empleados': empleados,
        'costo_medio_conv': costo_medio_conv,
        'costo_medio_fc': costo_medio_fc
    }

# 4. Calcular métricas para ambos períodos
metrics_current = calculate_monthly_metrics(df_current)
metrics_previous = calculate_monthly_metrics(df_previous)

# === NUEVO: Calcular Total Anual (Acumulado según filtros) ===
total_anual_acumulado = df_filtered['Total Mensual'].sum()

# 5. Función auxiliar para calcular el string del delta
def get_delta_pct_str(current, previous):
    if previous > 0:
        delta = ((current - previous) / previous) * 100
    elif current > 0:
        delta = 100.0
    else:
        delta = 0.0
    
    # Retornar solo el porcentaje
    return delta

# 6. Calcular los 4 deltas
delta_total = get_delta_pct_str(metrics_current['total_masa'], metrics_previous['total_masa'])
delta_empleados = get_delta_pct_str(metrics_current['empleados'], metrics_previous['empleados'])
delta_costo_conv = get_delta_pct_str(metrics_current['costo_medio_conv'], metrics_previous['costo_medio_conv'])
delta_costo_fc = get_delta_pct_str(metrics_current['costo_medio_fc'], metrics_previous['costo_medio_fc'])

# 7. Definir etiquetas dinámicas para los KPIs
display_month_name = latest_month_name if latest_month_name else "N/A"

# ----------------------------------------------------------------------------
# --- TARJETAS DE MÉTRICAS (NUEVO DISEÑO HTML/CSS FLUIDO) ---
# ----------------------------------------------------------------------------
cards_html = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Source+Sans+Pro:wght@400;600;700&display=swap');

/* Contenedor Grid Responsivo */
.metrics-grid {{
    display: grid;
    /* CAMBIO: 5 Columnas para incluir el anual */
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

/* Tarjeta Base */
.metric-card {{
    background: white;
    border-radius: 12px;
    padding: 15px; /* Reducido de 20px para dar más aire */
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

/* Bordes de Color */
.border-orange {{ border-top: 4px solid #f97316; }} /* NUEVO Color */
.border-blue {{ border-top: 4px solid #3b82f6; }}
.border-cyan {{ border-top: 4px solid #06b6d4; }}
.border-violet {{ border-top: 4px solid #8b5cf6; }}
.border-pink {{ border-top: 4px solid #ec4899; }}

/* Texto */
.card-label {{
    font-size: 0.8rem; /* Reducido un poco */
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
    font-size: 1.2rem; /* Reducido de 1.6rem para que entren números grandes */
    font-weight: 700;
    color: #1e293b;
    margin-bottom: 8px;
    line-height: 1.2;
    word-wrap: break-word; /* Permitir que el número baje si es larguísimo */
}}

/* Delta (Pastillas) */
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

<!-- Tarjeta 0: Costo Anual (Acumulado) NUEVA -->
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

<!-- Tarjeta 2: Empleados -->
<div class="metric-card border-cyan">
    <div class="card-label" title="Empleados Únicos ({display_month_name})">Empleados Únicos ({display_month_name})</div>
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
# =============================================================================
# --- FIN: LÓGICA DE MÉTRICAS CON DELTA ---
# =============================================================================


st.markdown("---")

# --- TABS PRINCIPALES ---
tab_evolucion, tab_distribucion, tab_costos, tab_conceptos, tab_tabla = st.tabs(["Evolución Mensual y Anual", "Distribución por Gerencia y Clasificación", "Análisis de Costos Promedios", "Masa Salarial por Concepto / SIPAF", "Tabla de Datos Detallados"]) 

# ------------------------- TAB 1: EVOLUCIÓN -------------------------
with tab_evolucion:
    st.subheader("Evolución Mensual de la Masa Salarial")
    col_chart1, col_table1 = st.columns([2, 1])
    # Usamos df_filtered aquí para mostrar la evolución de los meses seleccionados
    masa_mensual = df_filtered.groupby('Mes').agg({'Total Mensual': 'sum', 'Mes_Num': 'first'}).reset_index().sort_values('Mes_Num')
    
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
        meses_ordenados = df.sort_values('Mes_Num')['Mes'].unique().tolist()
        base_chart1 = alt.Chart(masa_mensual).transform_window(
            total_sum='sum(Total Mensual)'
        ).transform_calculate(
            percentage="datum['Total Mensual'] / datum.total_sum",
            label_text="format(datum['Total Mensual'] / 1000000000, ',.2f') + 'G (' + format(datum.percentage, '.1%') + ')'"
        )
        line = base_chart1.mark_line(point=True, strokeWidth=3).encode(
            x=alt.X('Mes:N', sort=meses_ordenados, title='Mes'), 
            y=alt.Y('Total Mensual:Q', title='Masa Salarial ($)', axis=alt.Axis(format='$,.0s'), scale=y_scale), 
            tooltip=[alt.Tooltip('Mes:N'), alt.Tooltip('Total Mensual:Q', format='$,.2f')]
        )
        text = base_chart1.mark_text(align='center', baseline='bottom', dy=-10).encode(
            x=alt.X('Mes:N', sort=meses_ordenados), y=alt.Y('Total Mensual:Q', scale=y_scale), text='label_text:N'
        )
        line_chart = (line + text).properties(height=chart_height1, padding={'top': 35, 'left': 5, 'right': 5, 'bottom': 5}).configure(background='transparent').configure_view(fill='transparent')
        st.altair_chart(line_chart, use_container_width=True)
    with col_table1:
        masa_mensual_display = masa_mensual[['Mes', 'Total Mensual']].copy()
        if not masa_mensual_display.empty:
            total_row = pd.DataFrame([{'Mes': 'Total', 'Total Mensual': masa_mensual_display['Total Mensual'].sum()}])
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
        index=['Mes_Num', 'Mes'],
        columns='Clasificacion_Ministerio',
        aggfunc='sum',
        fill_value=0
    ).sort_index(level='Mes_Num').reset_index(level='Mes_Num', drop=True)

    summary_df_display = summary_df_filtered.reset_index().copy()
    
    if not summary_df_display.empty:
        col_chart_anual, col_table_anual = st.columns([2, 1])

        with col_table_anual:
            numeric_cols = summary_df_display.select_dtypes(include=np.number).columns
            if 'Total general' not in summary_df_display.columns and len(numeric_cols) > 0:
                summary_df_display['Total general'] = summary_df_display[numeric_cols].sum(axis=1)

            total_row = summary_df_display.select_dtypes(include=np.number).sum().rename('Total')
            summary_df_display = pd.concat([summary_df_display, total_row.to_frame().T], ignore_index=True)
            if 'Mes' in summary_df_display.columns:
                summary_df_display.iloc[-1, summary_df_display.columns.get_loc('Mes')] = 'Total'

            summary_currency_cols = [col for col in summary_df_display.columns if col != 'Mes' and pd.api.types.is_numeric_dtype(summary_df_display[col])]
            summary_format_mapper = {col: lambda x: f"${format_number_es(x)}" for col in summary_currency_cols}
            table_height_anual = 350 + 40
            st.dataframe(summary_df_display.style.format(summary_format_mapper, na_rep="").set_properties(subset=summary_currency_cols, **{'text-align': 'right'}), use_container_width=True, hide_index=True, height=table_height_anual)
        
        with col_chart_anual:
            summary_chart_data = summary_df_filtered.reset_index().melt(id_vars='Mes', var_name='Clasificacion', value_name='Masa Salarial')
            mes_sort_order = summary_chart_data['Mes'].dropna().unique().tolist()

            bar_chart = alt.Chart(summary_chart_data).mark_bar().encode(
                x=alt.X('Mes:N', sort=mes_sort_order, title='Mes'),
                y=alt.Y('sum(Masa Salarial):Q', title='Masa Salarial ($)', axis=alt.Axis(format='$,.0s')),
                color=alt.Color('Clasificacion:N', title='Clasificación'),
                tooltip=[alt.Tooltip('Mes:N'), alt.Tooltip('Clasificacion:N'), alt.Tooltip('sum(Masa Salarial):Q', format='$,.2f', title='Masa Salarial')]
            )
            text_labels = alt.Chart(summary_chart_data).transform_aggregate(
                total_masa_salarial='sum(Masa Salarial)',
                groupby=['Mes']
            ).mark_text(
                dy=-8,
                align='center',
                color='black'
            ).encode(
                x=alt.X('Mes:N', sort=mes_sort_order),
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
    
    # Selector para elegir vista: Acumulado vs Mensualizado
    vista_distribucion = st.radio(
        "Seleccione el tipo de visualización:",
        ["Vista Acumulada (Total del periodo)", "Vista Mensualizada (Evolución por Mes)"],
        horizontal=True,
        key="dist_mode_selector"
    )
    
    st.markdown("---")

    if vista_distribucion == "Vista Acumulada (Total del periodo)":
        # --- VISTA ORIGINAL (ACUMULADA) ---
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
        # --- VISTA NUEVA (MENSUALIZADA) ---
        
        # Obtener orden correcto de meses
        meses_ordenados_viz = df.sort_values('Mes_Num')['Mes'].unique().tolist()

        st.subheader("Evolución Mensual por Gerencia")
        
        # Agrupar por Gerencia Y Mes
        gerencia_mensual_data = df_filtered.groupby(['Gerencia', 'Mes', 'Mes_Num'])['Total Mensual'].sum().reset_index()
        
        # Calcular totales por Gerencia para las etiquetas
        gerencia_totales = gerencia_mensual_data.groupby('Gerencia')['Total Mensual'].sum().reset_index()
        
        col_chart_m_ger, col_table_m_ger = st.columns([3, 1])
        
        with col_chart_m_ger:
            # 1. Gráfico de barras apiladas (Stacked Bar)
            chart_ger_stacked = alt.Chart(gerencia_mensual_data).mark_bar().encode(
                y=alt.Y('Gerencia:N', sort='-x', title=None, axis=alt.Axis(labelLimit=150)),
                x=alt.X('Total Mensual:Q', title='Masa Salarial ($)', axis=alt.Axis(format='$,.0s')),
                color=alt.Color('Mes:N', sort=meses_ordenados_viz, title='Mes'),
                order=alt.Order('Mes_Num', sort='ascending'), 
                tooltip=[
                    alt.Tooltip('Gerencia:N'),
                    alt.Tooltip('Mes:N'),
                    alt.Tooltip('Total Mensual:Q', format='$,.2f')
                ]
            )
            
            # 2. Capa de texto para el TOTAL (Sum of Stack)
            text_totals_ger = alt.Chart(gerencia_totales).mark_text(
                align='left',
                baseline='middle',
                dx=5,  # Desplazamiento a la derecha de la barra
                color='black'
            ).encode(
                y=alt.Y('Gerencia:N', sort='-x'),
                x=alt.X('Total Mensual:Q'), # Posición al final de la barra apilada
                text=alt.Text('Total Mensual:Q', format='$,.2s') # Etiqueta con formato corto (e.g. $1M)
            )

            # Combinar gráficos
            final_chart_ger = (chart_ger_stacked + text_totals_ger).properties(
                height=(len(gerencia_mensual_data['Gerencia'].unique()) * 35) + 50
            ).configure_view(stroke=None).configure(background='transparent')
            
            st.altair_chart(final_chart_ger, use_container_width=True)

        with col_table_m_ger:
            pivot_ger_mensual = pd.pivot_table(
                gerencia_mensual_data, values='Total Mensual', index='Gerencia', columns='Mes', aggfunc='sum', fill_value=0
            )
            cols_presentes = [m for m in meses_ordenados_viz if m in pivot_ger_mensual.columns]
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
        
        # Agrupar por Clasificación Y Mes
        clasif_mensual_data = df_filtered.groupby(['Clasificacion_Ministerio', 'Mes', 'Mes_Num'])['Total Mensual'].sum().reset_index()
        
        # Totales para etiquetas
        clasif_totales = clasif_mensual_data.groupby('Clasificacion_Ministerio')['Total Mensual'].sum().reset_index()
        
        col_chart_m_clas, col_table_m_clas = st.columns([3, 1])

        with col_chart_m_clas:
            # Chart Vertical Apilado
            chart_clas_stacked = alt.Chart(clasif_mensual_data).mark_bar().encode(
                x=alt.X('Mes:N', sort=meses_ordenados_viz, title='Mes'),
                y=alt.Y('Total Mensual:Q', title='Masa Salarial ($)', axis=alt.Axis(format='$,.0s')),
                color=alt.Color('Clasificacion_Ministerio:N', title='Clasificación'),
                tooltip=[alt.Tooltip('Mes:N'), alt.Tooltip('Clasificacion_Ministerio:N'), alt.Tooltip('Total Mensual:Q', format='$,.2f')]
            )
            
            # Texto TOTAL para gráfico vertical (agrupado por Mes)
            # OJO: Aquí el stack es por Clasificación dentro de cada Mes.
            # Queremos el total por MES arriba de la barra.
            # Re-calculamos totales por Mes para este gráfico específico
            totales_por_mes = clasif_mensual_data.groupby(['Mes'])['Total Mensual'].sum().reset_index()
            
            text_totals_clas = alt.Chart(totales_por_mes).mark_text(
                align='center',
                baseline='bottom',
                dy=-5,
                color='black'
            ).encode(
                x=alt.X('Mes:N', sort=meses_ordenados_viz),
                y=alt.Y('Total Mensual:Q'),
                text=alt.Text('Total Mensual:Q', format='$,.2s')
            )

            final_chart_clas = (chart_clas_stacked + text_totals_clas).properties(
                height=400
            ).configure_view(stroke=None).configure(background='transparent')
            
            st.altair_chart(final_chart_clas, use_container_width=True)

        with col_table_m_clas:
            pivot_clas_mensual = pd.pivot_table(
                clasif_mensual_data, values='Total Mensual', index='Clasificacion_Ministerio', columns='Mes', aggfunc='sum', fill_value=0
            )
            cols_presentes_clas = [m for m in meses_ordenados_viz if m in pivot_clas_mensual.columns]
            pivot_clas_mensual = pivot_clas_mensual[cols_presentes_clas]
            pivot_clas_mensual['Total'] = pivot_clas_mensual.sum(axis=1)
            pivot_clas_mensual = pivot_clas_mensual.sort_values('Total', ascending=False)
            
            st.write("**Tabla Resumen ($)**")
            st.dataframe(
                pivot_clas_mensual.style.format(lambda x: f"${format_number_es(x)}"), 
                use_container_width=True,
                height=400
            )

# ------------------------- TAB 3: COSTOS PROMEDIOS (MODIFICADA) -------------------------
with tab_costos:
    st.subheader("Análisis de Costos Promedios Mensuales")
    st.markdown("Evolución del costo promedio (Total Masa / Dotación) por categorías clave.")
    
    # 1. Definición de opciones - Actualizado
    analysis_options_map = {
        "Relación": "Relación",
        "Nivel": "Nivel",
        "Clasificación Ministerial": "Clasificacion_Ministerio"
    }

    # 2. Columnas para selectores
    col_sel_dim, col_sel_view_mode = st.columns(2)
    
    with col_sel_dim:
        # Multiselect para elegir qué gráficos mostrar - Default solo Relación
        selected_analyses = st.multiselect(
            "Seleccione Dimensiones para Analizar:",
            options=list(analysis_options_map.keys()),
            default=["Relación"]
        )
        
    with col_sel_view_mode:
        # Checkbox para alternar vista de tabla
        show_detail_legajo = st.checkbox("Mostrar detalle por Legajo en tablas", value=False, help="Activa para ver el listado de empleados mes a mes.")

    st.markdown("---")
    
    meses_ordenados_costos = df.sort_values('Mes_Num')['Mes'].unique().tolist()

    if not selected_analyses:
        st.info("Por favor, seleccione al menos una dimensión para visualizar.")
    
    for label in selected_analyses:
        col_name = analysis_options_map[label]
        st.markdown(f"#### Análisis: {label}")
        
        # Calcular datos agrupados para el GRÁFICO (siempre es resumen mensual)
        grouped_stats = df_filtered.groupby([col_name, 'Mes', 'Mes_Num']).agg(
            Masa=('Total Mensual', 'sum'),
            Dotacion=('Legajo', 'nunique')
        ).reset_index()
        
        grouped_stats['Costo_Promedio'] = grouped_stats['Masa'] / grouped_stats['Dotacion']
        grouped_stats['Costo_Promedio'] = grouped_stats['Costo_Promedio'].fillna(0)
        
        # Renderizar Gráfico
        chart = alt.Chart(grouped_stats).mark_line(point=True).encode(
            x=alt.X('Mes:N', sort=meses_ordenados_costos, title='Mes'),
            y=alt.Y('Costo_Promedio:Q', title='Costo Promedio ($)', axis=alt.Axis(format='$,.0f')),
            color=alt.Color(f'{col_name}:N', title=col_name),
            tooltip=[
                alt.Tooltip('Mes:N'), 
                alt.Tooltip(f'{col_name}:N'), 
                alt.Tooltip('Costo_Promedio:Q', format='$,.2f'),
                alt.Tooltip('Dotacion:Q', title='Dotación')
            ]
        ).properties(height=350).configure_point(size=100)
        
        st.altair_chart(chart, use_container_width=True)
        
        # Renderizar Tabla según el Checkbox
        if show_detail_legajo:
            st.write(f"**Detalle por Mes y Legajo - {label}**")
            
            # 1. Seleccionar columnas base
            cols_base = ['Legajo', 'Apellido y Nombres', 'Gerencia', col_name]
            cols_pivot = ['Mes', 'Mes_Num', 'Total Mensual'] # Columnas para pivotear
            
            # Filtrar DF con columnas necesarias
            df_base = df_filtered[cols_base + cols_pivot].copy()
            
            # 2. Pivotear: Indices=Datos Legajo, Columnas=Mes, Valores=Total Mensual
            # Usamos pivot_table para manejar duplicados sumando (aunque por legajo/mes debería ser único)
            df_pivot = pd.pivot_table(
                df_base,
                values='Total Mensual',
                index=cols_base,
                columns='Mes',
                aggfunc='sum',
                fill_value=0
            ).reset_index()
            
            # 3. Ordenar columnas de meses cronológicamente
            meses_presentes = [m for m in meses_ordenados_costos if m in df_pivot.columns]
            
            # 4. Calcular Promedio Anual (o del periodo seleccionado) por Legajo
            # Sumamos los meses presentes y dividimos por la cantidad de meses con dato > 0 (o total meses)
            # Aquí calculamos promedio simple de los valores > 0
            # Ojo: "Promedio Anual" = Suma Total / Cantidad de Meses con dato
            valores_meses = df_pivot[meses_presentes]
            df_pivot['Promedio Mensual'] = valores_meses.replace(0, np.nan).mean(axis=1).fillna(0)
            
            # 5. Reordenar columnas finales
            cols_finales = cols_base + meses_presentes + ['Promedio Mensual']
            df_display_pivot = df_pivot[cols_finales].sort_values(['Gerencia', 'Apellido y Nombres'])
            
            # Formatear para mostrar
            format_dict = {m: lambda x: f"${format_number_es(x)}" if x > 0 else "-" for m in meses_presentes}
            format_dict['Promedio Mensual'] = lambda x: f"${format_number_es(x)}"
            
            st.dataframe(
                df_display_pivot.style.format(format_dict),
                use_container_width=True,
                height=400
            )

        else:
            st.write(f"**Resumen Mensual de Promedios - {label}**")
            # CORRECCIÓN DEL ERROR: Ordenar ANTES de filtrar columnas
            if 'Mes_Num' in grouped_stats.columns:
                grouped_stats = grouped_stats.sort_values('Mes_Num', ignore_index=True)
            
            cols_order = ['Mes', col_name, 'Masa', 'Dotacion', 'Costo_Promedio']
            grouped_display = grouped_stats[cols_order]
            
            st.dataframe(
                grouped_display.style.format({
                    "Masa": lambda x: f"${format_number_es(x)}",
                    "Costo_Promedio": lambda x: f"${format_number_es(x)}",
                    "Dotacion": "{:,.0f}"
                }),
                use_container_width=True
            )
        
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
    
    meses_ordenados_viz_conc = df.sort_values('Mes_Num')['Mes'].unique().tolist()

    if mode == "Masa por Concepto":
        if concept_cols_present:
            df_melted = df_filtered.melt(id_vars=['Mes', 'Mes_Num'], value_vars=concept_cols_present, var_name='Concepto', value_name='Monto')
            
            pivot_table = pd.pivot_table(df_melted, values='Monto', index='Concepto', columns='Mes', aggfunc='sum', fill_value=0)
            meses_en_datos = df_filtered[['Mes', 'Mes_Num']].drop_duplicates().sort_values('Mes_Num')['Mes'].tolist()
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
                    chart_data_mensual = chart_data_mensual.groupby(['Concepto', 'Mes', 'Mes_Num'])['Monto'].sum().reset_index()
                    total_por_concepto = chart_data_mensual.groupby('Concepto')['Monto'].sum().sort_values(ascending=False).index.tolist()

                    chart_height_mensual = (len(total_por_concepto) * 35) + 50

                    bar_chart_mensual = alt.Chart(chart_data_mensual).mark_bar().encode(
                        y=alt.Y('Concepto:N', sort=total_por_concepto, title=None, axis=alt.Axis(labelLimit=200)),
                        x=alt.X('Monto:Q', title='Masa Salarial ($)', axis=alt.Axis(format='$,.0s')),
                        color=alt.Color('Mes:N', sort=meses_ordenados_viz_conc, title='Mes'),
                        order=alt.Order('Mes_Num', sort='ascending'),
                        tooltip=[alt.Tooltip('Concepto:N'), alt.Tooltip('Mes:N'), alt.Tooltip('Monto:Q', format='$,.2f')]
                    ).properties(
                        height=chart_height_mensual
                    ).configure(background='transparent').configure_view(fill='transparent')
                    st.altair_chart(bar_chart_mensual, use_container_width=True)

            with col_table_concepto:
                height_table = chart_height_concepto + 35 if vista_conceptos == "Vista Acumulada" else chart_height_mensual
                st.dataframe(pivot_table.style.format(formatter=lambda x: f"${format_number_es(x)}").set_properties(**{'text-align': 'right'}), use_container_width=True, height=height_table)

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
            df_melted_sipaf = df_filtered.melt(id_vars=['Mes', 'Mes_Num'], value_vars=sipaf_cols_present, var_name='Concepto', value_name='Monto')
            
            pivot_table_sipaf = pd.pivot_table(df_melted_sipaf, values='Monto', index='Concepto', columns='Mes', aggfunc='sum', fill_value=0)
            meses_en_datos_sipaf = df_filtered[['Mes', 'Mes_Num']].drop_duplicates().sort_values('Mes_Num')['Mes'].tolist()
            if meses_en_datos_sipaf and all(mes in pivot_table_sipaf.columns for mes in meses_en_datos_sipaf):
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
                    chart_data_sipaf_mensual = df_melted_sipaf.groupby(['Concepto', 'Mes', 'Mes_Num'])['Monto'].sum().reset_index()
                    total_por_concepto_sipaf = chart_data_sipaf_mensual.groupby('Concepto')['Monto'].sum().sort_values(ascending=False).index.tolist()
                    chart_height_sipaf_mensual = (len(total_por_concepto_sipaf) * 35) + 50

                    bar_chart_sipaf_mensual = alt.Chart(chart_data_sipaf_mensual).mark_bar().encode(
                        y=alt.Y('Concepto:N', sort=total_por_concepto_sipaf, title=None, axis=alt.Axis(labelLimit=200)),
                        x=alt.X('Monto:Q', title='Masa Salarial ($)', axis=alt.Axis(format='$,.0s')),
                        color=alt.Color('Mes:N', sort=meses_ordenados_viz_conc, title='Mes'),
                        order=alt.Order('Mes_Num', sort='ascending'),
                        tooltip=[alt.Tooltip('Concepto:N'), alt.Tooltip('Mes:N'), alt.Tooltip('Monto:Q', format='$,.2f')]
                    ).properties(
                        height=chart_height_sipaf_mensual
                    ).configure(background='transparent').configure_view(fill='transparent')
                    st.altair_chart(bar_chart_sipaf_mensual, use_container_width=True)

            with col_table_sipaf:
                height_table_sipaf = chart_height_sipaf + 35 if vista_conceptos == "Vista Acumulada" else chart_height_sipaf_mensual
                st.dataframe(pivot_table_sipaf.style.format(formatter=lambda x: f"${format_number_es(x)}").set_properties(**{'text-align': 'right'}), use_container_width=True, height=height_table_sipaf)

            st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
            col_dl_9, col_dl_10 = st.columns(2)
            with col_dl_9:
                st.download_button(label="📥 Descargar CSV", data=pivot_table_sipaf.to_csv(index=True).encode('utf-8'), file_name='resumen_sipaf.csv', mime='text/csv', use_container_width=True)
            with col_dl_10:
                st.download_button(label="📥 Descargar Excel", data=to_excel(pivot_table_sipaf.reset_index()), file_name='resumen_sipaf.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', use_container_width=True)
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
        df_page = df_display.iloc[start_idx:end_idx]

        currency_columns = ['Total Sujeto a Retención', 'Vacaciones', 'Alquiler', 'Horas Extras', 'Nómina General con Aportes', 'Cs. Sociales s/Remunerativos', 'Cargas Sociales Ant.', 'IC Pagado', 'Vacaciones Pagadas', 'Cargas Sociales s/Vac. Pagadas', 'Retribución Cargo 1.1.1.', 'Antigüedad 1.1.3.', 'Retribuciones Extraordinarias 1.3.1.', 'Contribuciones Patronales', 'Gratificación por Antigüedad', 'Gratificación por Jubilación', 'Total No Remunerativo', 'SAC Horas Extras', 'Cargas Sociales SAC Hextras', 'SAC Pagado', 'Cargas Sociales s/SAC Pagado', 'Cargas Sociales Antigüedad', 'Nómina General sin Aportes', 'Gratificación Única y Extraordinaria', 'Gastos de Representación', 'Contribuciones Patronales 1.3.3.', 'S.A.C. 1.3.2.', 'S.A.C. 1.1.4.', 'Contribuciones Patronales 1.1.6.', 'Complementos 1.1.7.', 'Asignaciones Familiares 1.4.', 'Total Mensual']
        integer_columns = ['Nro. de Legajo', 'Dotación', 'Ceco']
        currency_formatter = lambda x: f"${format_number_es(x)}"
        format_mapper = {col: currency_formatter for col in currency_columns if col in df_page.columns}
        for col in integer_columns:
            if col in df_page.columns:
                format_mapper[col] = format_integer_es
        columns_to_align_right = [col for col in currency_columns + integer_columns if col in df_page.columns]
        st.dataframe(df_page.style.format(format_mapper, na_rep="").set_properties(subset=columns_to_align_right, **{'text-align': 'right'}), use_container_width=True, hide_index=True)
    else:
        st.info("No hay datos que coincidan con los filtros seleccionados.")

# --- FIN ---
