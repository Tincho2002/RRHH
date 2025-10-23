# ===============================================================
# Visualizador de Eficiencia - V Corregida y Mejorada
# ===============================================================

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from io import BytesIO

# Configuración de la página para que ocupe todo el ancho
st.set_page_config(layout="wide", page_title="Visualizador de Eficiencia")

# ----------------- Funciones -----------------

@st.cache_data
def load_data(uploaded_file):
    """
    Carga los datos desde un archivo Excel, procesa las fechas,
    CALCULA TOTALES DE HORAS EXTRAS Y DÍAS DE GUARDIA, y extrae
    nombres de columnas, años y meses.
    """
    if uploaded_file is None:
        return pd.DataFrame(), [], [], [], {}

    df = pd.read_excel(uploaded_file)

    # ===============================================================
    # CÁLCULO DE TOTALES
    # ===============================================================

    # --- 1. Total Horas Extras (HE) ---
    he_costo_cols = ['$K_50%', '$K_100%']
    he_qty_cols = ['hs_50%', 'hs_100%']

    if all(col in df.columns for col in he_costo_cols):
        df['$K_Total_HE'] = df[he_costo_cols].fillna(0).sum(axis=1)

    if all(col in df.columns for col in he_qty_cols):
        df['hs_Total_HE'] = df[he_qty_cols].fillna(0).sum(axis=1)

    # ===============================================================
    # MODIFICACIÓN: Cálculo de Guardias corregido (5 componentes)
    # ===============================================================

    # --- 2. Total Guardias (GTO, GTI, 2T, 3T, TD) ---

    # Lista de columnas de COSTOS de guardia
    guardia_costo_cols = ['$K_Guardias_2T', '$K_Guardias_3T', '$K_GTO', '$K_GTI', '$K_TD']
    # Lista de columnas de CANTIDAD (días) de guardia
    guardia_qty_cols = ['ds_Guardias_2T', 'ds_Guardias_3T', 'ds_GTO', 'ds_GTI', 'ds_TD']

    # Se crea $K_Total_Guardias (para la Pestaña 1)
    if all(col in df.columns for col in guardia_costo_cols):
        df['$K_Total_Guardias'] = df[guardia_costo_cols].fillna(0).sum(axis=1)

    # Se crea ds_Total_Guardias (para la Pestaña 2)
    if all(col in df.columns for col in guardia_qty_cols):
        df['ds_Total_Guardias'] = df[guardia_qty_cols].fillna(0).sum(axis=1)
    # ===============================================================

    df['Período'] = pd.to_datetime(df['Período'])
    df['Año'] = df['Período'].dt.year
    df['Mes'] = df['Período'].dt.month
    df['Período_fmt'] = df['Período'].dt.strftime('%b-%y')  # Formato ej: Ene-25

    # --- NUEVO: Columnas de Agrupación Temporal ---
    df['Bimestre'] = (df['Mes'] - 1) // 2 + 1
    df['Trimestre'] = (df['Mes'] - 1) // 3 + 1
    df['Semestre'] = (df['Mes'] - 1) // 6 + 1
    # --- FIN NUEVO ---


    # Estas listas AHORA incluirán TODOS los totales nuevos
    k_cols = sorted([c for c in df.columns if c.startswith('$K_')])
    qty_cols = sorted([c for c in df.columns if c.startswith('hs_') or c.startswith('ds_')])

    years = sorted(df['Año'].unique(), reverse=True)
    months_map = {1:'Ene',2:'Feb',3:'Mar',4:'Abr',5:'May',6:'Jun',7:'Jul',8:'Ago',9:'Sep',10:'Oct',11:'Nov',12:'Dic'}

    return df, k_cols, qty_cols, years, months_map


def format_number(x):
    """
    Formatea los números para visualización (2 DECIMALES): separador de miles con punto,
    decimales con coma. Suprime los valores None o NaN.
    """
    if pd.isna(x):
        return ""  # Devuelve un string vacío para valores nulos
    try:
        if isinstance(x, (int, float)):
            return f"{float(x):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        pass
    return x

def format_number_int(x):
    """
    Formatea los números para visualización (0 DECIMALES): separador de miles con punto.
    Suprime los valores None o NaN.
    """
    if pd.isna(x):
        return ""  # Devuelve un string vacío para valores nulos
    try:
        if isinstance(x, (int, float)):
            # Se cambia :.2f por :.0f para formato entero
            return f"{float(x):,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        pass
    return x

def format_percentage(x):
    """
    Formatea los números como porcentaje (2 DECIMALES) con el signo %.
    """
    if pd.isna(x):
        return ""  # Devuelve un string vacío para valores nulos
    try:
        if isinstance(x, (int, float)):
            # Formato con 2 decimales, comas/puntos, y el signo %
            formatted_num = f"{float(x):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            return f"{formatted_num} %"
    except (ValueError, TypeError):
        pass
    return x


def to_excel(df):
    """
    Convierte un DataFrame a un objeto de bytes en formato Excel para su descarga.
    """
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Datos')
    output.seek(0)
    return output

def plot_line(df_plot, columns, yaxis_title):
    """
    Genera un gráfico de líneas con marcadores y etiquetas de datos.
    """
    fig = go.Figure()
    for col in columns:
        # Elige el formateador. Todas las 'ds_' (incluida 'ds_Total_Guardias') usarán int.
        formatter = format_number_int if col.startswith('ds_') else format_number

        fig.add_trace(go.Scatter(
            x=df_plot['Período_fmt'],
            y=df_plot[col],
            name=col,
            mode='lines+markers+text',
            text=[formatter(v) for v in df_plot[col]],
            textposition='top center'
        ))
    fig.update_layout(title=yaxis_title, template='plotly_white', xaxis_title='Período', yaxis_title=yaxis_title)
    return fig

def calc_variation(df, columns, tipo='mensual'):
    """
    Calcula la variación mensual o interanual de las columnas seleccionadas.
    """
    df_var = df[['Período', 'Período_fmt'] + columns].copy().sort_values('Período')
    df_val = pd.DataFrame()
    df_pct = pd.DataFrame()
    df_val['Período_fmt'] = df_var['Período_fmt']
    df_pct['Período_fmt'] = df_var['Período_fmt']

    for col in columns:
        shift_period = 12 if tipo == 'interanual' else 1
        df_val[col] = df_var[col].diff(periods=shift_period)
        df_pct[col] = (df_val[col] / df_var[col].shift(shift_period)) * 100

    df_val['Período'] = df_var['Período']
    df_pct['Período'] = df_var['Período']

    return df_val, df_pct

def plot_bar(df_plot, columns, yaxis_title):
    """
    Genera un gráfico de barras con etiquetas de datos fuera de las barras.
    """
    fig = go.Figure()
    for col in columns:
        # Elige el formateador. Todas las 'ds_' (incluida 'ds_Total_Guardias') usarán int.
        formatter = format_number_int if col.startswith('ds_') else format_number

        fig.add_trace(go.Bar(
            x=df_plot['Período_fmt'],
            y=df_plot[col],
            name=col,
            text=[formatter(v) for v in df_plot[col]],
            textposition='outside'
        ))
    fig.update_layout(title=yaxis_title, template='plotly_white', xaxis_title='Período', yaxis_title=yaxis_title)
    fig.update_traces(texttemplate='%{text}', textangle=0)
    return fig

def show_table(df_table, nombre, show_totals=False, is_percentage=False):
    """
    Muestra una tabla en Streamlit, ordenada, y agrega botones de descarga.
    Opcionalmente, añade una fila de totales.
    Acepta un flag 'is_percentage' para formatear con %.
    """
    df_sorted = df_table.sort_values(by='Período', ascending=False).reset_index(drop=True)
    df_display = df_sorted.drop(columns=['Período'])
    df_display.rename(columns={'Período_fmt': 'Período'}, inplace=True)

    if 'Período' in df_display.columns:
        cols = ['Período'] + [col for col in df_display.columns if col != 'Período']
        df_display = df_display[cols]

    if show_totals:
        totals_row = {col: df_display[col].sum() for col in df_display.select_dtypes(include='number').columns}
        totals_row['Período'] = 'Total'
        totals_df = pd.DataFrame([totals_row])
        df_display = pd.concat([df_display, totals_df], ignore_index=True)

    df_formatted = df_display.copy()

    for col in df_formatted.select_dtypes(include='number').columns:
        if is_percentage:
            df_formatted[col] = df_formatted[col].apply(format_percentage)
        # Todas las 'ds_' (incluida 'ds_Total_Guardias') usarán int.
        elif col.startswith('ds_'):
            df_formatted[col] = df_formatted[col].apply(format_number_int)
        else:
            df_formatted[col] = df_formatted[col].apply(format_number)

    st.dataframe(df_formatted, use_container_width=True)

    df_download = df_formatted.copy()

    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            label=f"📥 Descargar CSV ({nombre})",
            data=df_download.to_csv(index=False).encode('utf-8'),
            file_name=f"{nombre}.csv",
            mime='text/csv',
            use_container_width=True
        )
    with col2:
        st.download_button(
            label=f"📥 Descargar Excel ({nombre})",
            data=to_excel(df_download),
            file_name=f"{nombre}.xlsx",
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            use_container_width=True
        )

# --- FUNCIÓN PARA TARJETAS KPI (MODIFICADA) ---
def show_kpi_cards(df, var_list):
    """
    Calcula y muestra las tarjetas KPI para 2024 vs 2025 usando HTML/CSS.
    Usa el DataFrame *original* (df) para ignorar los filtros de mes/año.
    """
    # 1. Calcular totales
    df_2024 = df[df['Año'] == 2024][var_list].sum()
    df_2025 = df[df['Año'] == 2025][var_list].sum()

    # 2. Definir layout (5 columnas)
    cols = st.columns(5)
    
    # Mapeo de nombres amigables (label)
    label_map = {
        '$K_50%': 'Costo HE 50%',
        '$K_100%': 'Costo HE 100%',
        '$K_Total_HE': 'Costo Total HE',
        '$K_GTO': 'Costo GTO',
        '$K_GTI': 'Costo GTI',
        '$K_Guardias_2T': 'Costo Guardias 2T',
        '$K_Guardias_3T': 'Costo Guardias 3T',
        '$K_TD': 'Costo TD',
        '$K_Total_Guardias': 'Costo Total Guardias',
        'hs_50%': 'Horas HE 50%',
        'hs_100%': 'Horas HE 100%',
        'hs_Total_HE': 'Horas Total HE',
        'ds_GTO': 'Días GTO',
        'ds_GTI': 'Días GTI',
        'ds_Guardias_2T': 'Días Guardias 2T',
        'ds_Guardias_3T': 'Días Guardias 3T',
        'ds_TD': 'Días TD',
        'ds_Total_Guardias': 'Días Total Guardias',
    }

    # 3. Iterar y crear métricas
    col_index = 0
    for var in var_list:
        total_2024 = df_2024.get(var, 0)
        total_2025 = df_2025.get(var, 0)
        
        delta_abs = total_2025 - total_2024
        
        if total_2024 > 0 and not pd.isna(total_2024):
            delta_pct = (delta_abs / total_2024) * 100
        elif (total_2024 == 0 or pd.isna(total_2024)) and total_2025 > 0:
            delta_pct = 100.0 # Si 2024 es 0 y 2025 es > 0, es 100% (o N/A, pero 100% es indicativo)
        else:
            delta_pct = 0.0 # Cubre 0 a 0

        # --- Formato con prefijo/sufijo ---
        is_int = var.startswith('ds_') or var.startswith('hs_')
        formatter_val = format_number_int if is_int else format_number
        
        val_str = formatter_val(total_2025)
        delta_abs_str = formatter_val(abs(delta_abs)) # Usamos abs() para el color
        delta_pct_fmt = format_percentage(delta_pct) # format_percentage ya añade el " %"

        if var.startswith('$K_'):
            value_fmt = f"$K {val_str}"
            delta_abs_fmt = f"$K {delta_abs_str}"
        elif var.startswith('hs_'):
            value_fmt = f"{val_str} hs"
            delta_abs_fmt = f"{delta_abs_str} hs"
        elif var.startswith('ds_'):
            value_fmt = f"{val_str} ds"
            delta_abs_fmt = f"{delta_abs_str} ds"
        else:
            value_fmt = val_str
            delta_abs_fmt = delta_abs_str

        # --- Lógica de color y formato de delta ---
        delta_class = "delta-positive" if delta_abs >= 0 else "delta-negative"
        delta_icon = "↑" if delta_abs >= 0 else "↓"
        # Usamos <br> para el salto de línea en HTML
        delta_str_html = f"{delta_icon} {delta_abs_fmt}<br>({delta_pct_fmt})"

        # Asignar a la columna correcta
        current_col = cols[col_index % 5]
        label = label_map.get(var, var) # Usar nombre amigable
        
        # --- MODIFICACIÓN: Construir y renderizar tarjeta HTML ---
        html_card = f"""
        <div class="custom-metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value_fmt}</div>
            <div class="custom-delta {delta_class}">
                {delta_str_html}
            </div>
        </div>
        """
        current_col.markdown(html_card, unsafe_allow_html=True)
        # --- FIN MODIFICACIÓN ---
        
        col_index += 1

# ----------------- Inicio de la App -----------------

st.title("Visualizador de Eficiencia")

# --- CSS PARA ESTILOS DE TARJETAS (MODIFICADO PARA CENTRAR) ---
CSS_STYLE = """
<style>
/* --- MODIFICADO: Ahora aplica a nuestra clase personalizada --- */
.custom-metric-card {
    background-color: #f0f8ff; /* Color de fondo azul claro (AliceBlue) */
    border-radius: 10px;
    padding: 15px;
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    transition: transform 0.3s ease, box-shadow 0.3s ease;
    border: 1px solid #e0e0e0;
    /* Damos una altura mínima para alinear las tarjetas */
    min-height: 150px; 
    /* Asegurar que el padding se respete al 100% */
    box-sizing: border-box; 
    margin-bottom: 10px; /* Espacio por si se apilan en móvil */
    
    /* --- MODIFICACIÓN: Centrar contenido --- */
    text-align: center;
}

.custom-metric-card:hover {
    transform: scale(1.03); /* Transición de zoom */
    box-shadow: 0 8px 16px rgba(0,0,0,0.2);
}

/* --- NUEVO: Clases para el contenido interno --- */
.metric-label {
    font-size: 1rem; /* Tamaño de la etiqueta */
    color: #333; /* Color de etiqueta */
    margin-bottom: 5px;
}
.metric-value {
    font-size: 1.5rem; /* Tamaño del valor principal */
    font-weight: 600; /* Semi-bold */
    color: #000; /* Color de valor */
}
.custom-delta {
    font-size: 0.875rem; /* Tamaño del delta */
    line-height: 1.3;    /* Espacio entre líneas para el <br> */
    margin-top: 8px;   /* Ajuste para separarlo del valor */
}
/* --- FIN NUEVO --- */

.delta-positive {
    color: #28a745; /* Verde */
}
.delta-negative {
    color: #dc3545; /* Rojo */
}
</style>
"""
st.markdown(CSS_STYLE, unsafe_allow_html=True)
# --- FIN CSS ---


uploaded_file = st.file_uploader("Cargue el archivo 'eficiencia.xlsx'", type="xlsx")

if uploaded_file is None:
    st.info("Por favor, cargue un archivo Excel para comenzar.")
    st.stop()

# df, k_columns, y qty_columns ahora contendrán los nuevos totales
df, k_columns, qty_columns, all_years, month_map = load_data(uploaded_file)

if df.empty:
    st.error("El archivo cargado está vacío o no se pudo procesar.")
    st.stop()

# --- Definir listas de opciones "default" (todos seleccionados) ---
month_options = list(month_map.values())
all_bimestres = sorted(df['Bimestre'].unique())
all_trimestres = sorted(df['Trimestre'].unique())
all_semestres = sorted(df['Semestre'].unique())
# Ordenar los períodos específicos cronológicamente
all_periodos_especificos = list(df.sort_values('Período')['Período_fmt'].unique())
# --- FIN ---


# ----------------- Lógica de Filtros en Barra Lateral (MODIFICADA) -----------------
st.sidebar.header("Filtros Generales")

# --- NUEVO: Botón de Reseteo ---
def reset_filters():
    st.session_state.selected_years = all_years
    st.session_state.selected_months_names = month_options
    st.session_state.selected_bimestres = all_bimestres
    st.session_state.selected_trimestres = all_trimestres
    st.session_state.selected_semestres = all_semestres
    st.session_state.selected_periodos_especificos = all_periodos_especificos

st.sidebar.button("Resetear Filtros", on_click=reset_filters, use_container_width=True)
st.sidebar.markdown("---")
# --- FIN NUEVO ---

# --- MODIFICACIÓN: Inicializar Session State para evitar warning ---
if 'selected_years' not in st.session_state:
    reset_filters()
# --- FIN MODIFICACIÓN ---

# --- MODIFICADO: Filtros usan st.session_state (sin 'default') ---
selected_years = st.sidebar.multiselect(
    "Años:", 
    all_years, 
    key='selected_years'
)
selected_months_names = st.sidebar.multiselect(
    "Meses:", 
    month_options, 
    key='selected_months_names'
)
selected_months = [k for k,v in month_map.items() if v in selected_months_names]

selected_bimestres = st.sidebar.multiselect(
    "Bimestres:", 
    all_bimestres, 
    key='selected_bimestres'
)
selected_trimestres = st.sidebar.multiselect(
    "Trimestres:", 
    all_trimestres, 
    key='selected_trimestres'
)
selected_semestres = st.sidebar.multiselect(
    "Semestres:", 
    all_semestres, 
    key='selected_semestres'
)
st.sidebar.markdown("---")
selected_periodos_especificos = st.sidebar.multiselect(
    "Período Específico (Mes-Año):", 
    all_periodos_especificos, 
    key='selected_periodos_especificos'
)
# --- FIN MODIFICADO ---


# --- Lógica de filtro (usa valores de los widgets) ---
dff = df[
    df['Año'].isin(selected_years) &
    df['Mes'].isin(selected_months) &
    df['Bimestre'].isin(selected_bimestres) &
    df['Trimestre'].isin(selected_trimestres) &
    df['Semestre'].isin(selected_semestres) &
    df['Período_fmt'].isin(selected_periodos_especificos)
].copy()
# --- FIN ---

dff = dff.sort_values('Período')

# ----------------- Pestañas de la aplicación -----------------
tab1, tab2 = st.tabs(["$K (Costos)", "Cantidades (hs / ds)"])

# ----------------- Pestaña de Costos -----------------
with tab1:
    # --- SECCIÓN DE TARJETAS KPI (MODIFICADO) ---
    st.subheader("Totales Anuales (2025 vs 2024)")
    costo_vars_list = [
        '$K_50%', '$K_100%', '$K_Total_HE', '$K_TD', '$K_GTO', # Fila 1
        '$K_GTI', '$K_Guardias_2T', '$K_Guardias_3T', '$K_Total_Guardias' # Fila 2
    ]
    # Usamos 'df' (el original) para calcular totales sin afectar por filtros
    show_kpi_cards(df, costo_vars_list)
    st.markdown("---")
    # --- FIN SECCIÓN TARJETAS ---

    st.subheader("Análisis de Costos ($K)") 
    selected_k_vars = st.multiselect("Variables de Costos ($K):", k_columns, default=[k_columns[0]] if k_columns else [])

    if selected_k_vars:
        st.subheader("Evolución de Costos")
        fig = plot_line(dff, selected_k_vars, "$K (Costos)")
        st.plotly_chart(fig, use_container_width=True)
        table_k = dff[['Período', 'Período_fmt'] + selected_k_vars].copy()
        show_table(table_k, "Costos_Datos", show_totals=True)
        st.markdown("---")

        st.subheader("Variaciones Mensuales")
        tipo_var_mes = st.selectbox("Mostrar como:", ["Valores","Porcentaje"], key="mes_k")
        df_val_mes, df_pct_mes = calc_variation(dff, selected_k_vars,'mensual')
        is_pct_mes_k = (tipo_var_mes == 'Porcentaje')
        df_var_mes = df_pct_mes if is_pct_mes_k else df_val_mes
        fig_var_mes = plot_bar(df_var_mes, selected_k_vars, "Variación Mensual ($K)" if tipo_var_mes=='Valores' else "Variación Mensual (%)")
        st.plotly_chart(fig_var_mes, use_container_width=True)
        show_table(df_var_mes, "Costos_Var_Mensual", is_percentage=is_pct_mes_k)
        st.markdown("---")

        st.subheader("Variaciones Interanuales")
        tipo_var_anio = st.selectbox("Mostrar como:", ["Valores","Porcentaje"], key="inter_k")
        df_val_anio, df_pct_anio = calc_variation(dff, selected_k_vars,'interanual')
        is_pct_anio_k = (tipo_var_anio == 'Porcentaje')
        df_var_anio_raw = df_pct_anio if is_pct_anio_k else df_val_anio
        
        # --- MODIFICACIÓN: Excluir 2024 de Variaciones Interanuales ---
        if 'Período' in df_var_anio_raw.columns:
            df_var_anio = df_var_anio_raw[df_var_anio_raw['Período'].dt.year != 2024].copy()
        else:
            df_var_anio = df_var_anio_raw.copy()
        # --- FIN MODIFICACIÓN ---

        fig_var_anio = plot_bar(df_var_anio, selected_k_vars, "Variación Interanual ($K)" if tipo_var_anio=='Valores' else "Variación Interanual (%)")
        st.plotly_chart(fig_var_anio, use_container_width=True)
        show_table(df_var_anio, "Costos_Var_Interanual", is_percentage=is_pct_anio_k)

# ----------------- Pestaña de Cantidades -----------------
with tab2:
    # --- SECCIÓN DE TARJETAS KPI (MODIFICADO) ---
    st.subheader("Totales Anuales (2025 vs 2024)")
    qty_vars_list = [
        'hs_50%', 'hs_100%', 'hs_Total_HE', 'ds_TD', 'ds_GTO', # Fila 1
        'ds_GTI', 'ds_Guardias_2T', 'ds_Guardias_3T', 'ds_Total_Guardias' # Fila 2
    ]
    # Usamos 'df' (el original) para calcular totales sin afectar por filtros
    show_kpi_cards(df, qty_vars_list)
    st.markdown("---")
    # --- FIN SECCIÓN TARJETAS ---

    st.subheader("Análisis de Cantidades (hs / ds)") 
    selected_qty_vars = st.multiselect("Variables de Cantidad (hs / ds):", qty_columns, default=[qty_columns[0]] if qty_columns else [])

    if selected_qty_vars:
        st.subheader("Evolución de Cantidades")
        fig = plot_line(dff, selected_qty_vars, "Cantidades (hs/ds)")
        st.plotly_chart(fig, use_container_width=True)
        table_qty = dff[['Período', 'Período_fmt'] + selected_qty_vars].copy()
        show_table(table_qty, "Cantidades_Datos", show_totals=True)
        st.markdown("---")

        st.subheader("Variaciones Mensuales")
        tipo_var_mes_qty = st.selectbox("Mostrar como:", ["Valores","Porcentaje"], key="mes_qty")
        df_val_mes_qty, df_pct_mes_qty = calc_variation(dff, selected_qty_vars,'mensual')
        is_pct_mes_qty = (tipo_var_mes_qty == 'Porcentaje')
        df_var_mes_qty = df_pct_mes_qty if is_pct_mes_qty else df_val_mes_qty
        fig_var_mes_qty = plot_bar(df_var_mes_qty, selected_qty_vars, "Variación Mensual (Cantidad)" if tipo_var_mes_qty=='Valores' else "Variación Mensual (%)")
        st.plotly_chart(fig_var_mes_qty, use_container_width=True)
        show_table(df_var_mes_qty, "Cantidades_Var_Mensual", is_percentage=is_pct_mes_qty)
        st.markdown("---")

        st.subheader("Variaciones Interanuales")
        tipo_var_anio_qty = st.selectbox("Mostrar como:", ["Valores","Porcentaje"], key="inter_qty")
        df_val_anio_qty, df_pct_anio_qty = calc_variation(dff, selected_qty_vars,'interanual')
        is_pct_anio_qty = (tipo_var_anio_qty == 'Porcentaje')
        df_var_anio_qty_raw = df_pct_anio_qty if is_pct_anio_qty else df_val_anio_qty
        
        # --- MODIFICACIÓN: Excluir 2024 de Variaciones Interanuales ---
        if 'Período' in df_var_anio_qty_raw.columns:
            df_var_anio_qty = df_var_anio_qty_raw[df_var_anio_qty_raw['Período'].dt.year != 2024].copy()
        else:
            df_var_anio_qty = df_var_anio_qty_raw.copy()
        # --- FIN MODIFICACIÓN ---

        fig_var_anio_qty = plot_bar(df_var_anio_qty, selected_qty_vars, "Variación Interanual (Cantidad)" if tipo_var_anio_qty=='Valores' else "Variación Mensual (%)")
        st.plotly_chart(fig_var_anio_qty, use_container_width=True)
        show_table(df_var_anio_qty, "Cantidades_Var_Interanual", is_percentage=is_pct_anio_qty)

