import streamlit as st
import pandas as pd
import altair as alt
from io import BytesIO
# from fpdf import FPDF # Comentado si no se usa to_pdf
import numpy as np
from datetime import datetime
import streamlit.components.v1 as components
import plotly.graph_objects as go
import re

# --- Configuración de la página ---
st.set_page_config(layout="wide", page_title="Indicadores de Eficiencia", page_icon="🎯")

# --- CSS Personalizado para un Estilo Profesional y RESPONSIVE ---
# (CSS Omitido por brevedad - es el mismo que la versión anterior)
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
/* Estilos base de la tarjeta KPI (ya los tenías) */
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
    height: 3em; /* Asegura espacio para 2 líneas */
    line-height: 1.5em;
    display: flex;
    align-items: center;
    justify-content: center;
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
/* Oculta la flecha por defecto de Streamlit que viene con st.metric delta */
[data-testid="stMetricDelta"] svg {
    display: none;
}
/* Estilos para el contenedor del delta personalizado */
.delta-container {
    height: 1.5em; /* Reserva espacio para el delta */
    margin-top: 5px;
}
/* Estilo para los deltas personalizados (texto y flecha) */
.delta.green { color: #2ca02c; }
.delta.red { color: #d62728; }
.delta {
    font-size: 1.0rem;
    font-weight: 600;
}
.delta-arrow {
    display: inline-block; /* Permite que esté en línea con el texto */
    margin-right: 3px; /* Espacio entre flecha y número */
    font-size: 0.9em; /* Tamaño relativo de la flecha */
    line-height: 1; /* Asegura alineación vertical */
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
    """Genera el HTML para mostrar el delta porcentual con flecha y color."""
    if prev_val is None or pd.isna(prev_val):
        return '<div class="delta-container"></div>' # Espacio vacío si no hay dato previo
    if prev_val == 0:
        if current_val > 0:
            delta_pct = 100.0
        elif current_val < 0:
             delta_pct = -100.0
        else:
             delta_pct = 0.0
    else:
        delta_pct = ((current_val - prev_val) / prev_val) * 100
    
    if abs(delta_pct) < 0.01: # Si el cambio es muy pequeño, no mostrar delta
         return '<div class="delta-container"></div>'
         
    color = 'green' if delta_pct >= 0 else 'red'
    arrow = '▲' if delta_pct >= 0 else '▼' # Usar caracteres unicode para flechas
    return f'<div class="delta-container"><div class="delta {color}"><span class="delta-arrow">{arrow}</span> {delta_pct:,.1f}%</div></div>'

def generate_download_buttons(df_to_download, filename_prefix, key_suffix=""):
    st.markdown("##### Opciones de Descarga:")
    col_dl1, col_dl2 = st.columns(2)
    csv_buffer = BytesIO()
    # Asegurar codificación utf-8 para CSV
    df_to_download.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
    csv_data = csv_buffer.getvalue()
    with col_dl1:
        st.download_button(
            label="⬇️ Descargar como CSV",
            data=csv_data,
            file_name=f"{filename_prefix}.csv",
            mime="text/csv",
            key=f"csv_download_{filename_prefix}{key_suffix}"
        )
    excel_buffer = BytesIO()
    df_to_download.to_excel(excel_buffer, index=False, engine='openpyxl')
    excel_buffer.seek(0)
    with col_dl2:
        st.download_button(
            label="📊 Descargar como Excel",
            data=excel_buffer.getvalue(),
            file_name=f"{filename_prefix}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key=f"excel_download_{filename_prefix}{key_suffix}"
        )


def apply_all_filters(df, selections):
    _df = df.copy()
    for col, values in selections.items():
        # Asegurar que 'values' no esté vacío y la columna exista
        if values and col in _df.columns:
            # Filtrado específico para Años (columna 'Año' es numérica)
            if col == 'Años':
                # Convertir selección a números enteros para comparar
                numeric_values = [int(v) for v in values if str(v).isdigit()]
                if numeric_values:
                    _df = _df[_df['Año'].isin(numeric_values)]
            # Filtrado específico para Meses (columna 'Mes' es string)
            elif col == 'Meses':
                # Comparar como strings
                _df = _df[_df['Mes'].astype(str).isin([str(v) for v in values])]
            # Filtrado general para otras columnas si se añadieran
            else:
                _df = _df[_df[col].isin(values)]
    return _df

def get_sorted_unique_options(dataframe, column_name):
    if column_name in dataframe.columns:
        unique_values = dataframe[column_name].dropna().unique().tolist()
        unique_values = [v for v in unique_values if v != 'no disponible']
        if column_name == 'Mes':
            month_order = {'Enero': 1, 'Febrero': 2, 'Marzo': 3, 'Abril': 4, 'Mayo': 5, 'Junio': 6, 'Julio': 7, 'Agosto': 8, 'Septiembre': 9, 'Octubre': 10, 'Noviembre': 11, 'Diciembre': 12}
            # Filtrar solo meses presentes en los datos antes de ordenar
            present_months = [m for m in unique_values if m in month_order]
            return sorted(present_months, key=lambda x: month_order.get(x, 99))
        if column_name == 'Años' or column_name == 'Año': # Añadido 'Año'
             # Convertir a int para ordenar, luego devolver como string si es necesario, o mantener int
             try:
                  int_values = [int(x) for x in unique_values]
                  return sorted(int_values, reverse=True) # Devolver como enteros
             except ValueError: # Si algún valor no es numérico, ordenar como string
                  return sorted(map(str, unique_values), reverse=True)
        return sorted(unique_values)
    return []

def get_available_options(df, selections, target_column):
    _df = df.copy()
    for col, values in selections.items():
        # Asegurar que los valores del filtro sean del tipo correcto para la comparación
        if col != target_column and values and col in _df.columns:
            if col == 'Años':
                 # Comparar con la columna 'Año' (numérica) usando valores numéricos
                 numeric_values = [int(v) for v in values if str(v).isdigit()]
                 if numeric_values:
                      _df = _df[_df['Año'].isin(numeric_values)]
            elif col == 'Meses':
                 # Comparar con la columna 'Mes' (string) usando valores string
                 _df = _df[_df['Mes'].astype(str).isin([str(v) for v in values])]
            else:
                _df = _df[_df[col].isin(values)]

    # Determinar qué columna usar para obtener opciones únicas
    source_col = 'Año' if target_column == 'Años' else 'Mes' if target_column == 'Meses' else target_column
    return get_sorted_unique_options(_df, source_col)


@st.cache_data
def load_and_clean_data(uploaded_file):
    df_read = pd.DataFrame()
    file_type = uploaded_file.type
    
    try:
        # Intentar leer como Excel primero
        st.info("Intentando leer como archivo Excel...")
        # Intentar leer desde la primera fila
        try:
            df_read = pd.read_excel(uploaded_file, sheet_name='Eficiencia', header=0, engine='openpyxl')
        except Exception:
            # Si falla, intentar leer desde la segunda fila
            st.warning("No se pudo leer desde la fila 1, intentando desde la fila 2...")
            uploaded_file.seek(0) # Reiniciar el puntero del archivo
            df_read = pd.read_excel(uploaded_file, sheet_name='Eficiencia', header=1, engine='openpyxl')
        st.success("Archivo leído como Excel.")
        
    except Exception as e_excel:
        st.warning(f"No se pudo leer como Excel ({e_excel}). Intentando leer como CSV...")
        try:
            # Si falla Excel, intentar leer como CSV
            uploaded_file.seek(0) # Reiniciar puntero
            # Intentar detectar separador automáticamente
            df_read = pd.read_csv(uploaded_file, header=0, sep=None, engine='python', encoding='utf-8-sig')
            # Verificar si leyó correctamente o necesita saltar fila
            if df_read.shape[1] <= 1 or df_read.iloc[0].isnull().all():
                 st.warning("Leyendo CSV desde la segunda fila...")
                 uploaded_file.seek(0)
                 df_read = pd.read_csv(uploaded_file, header=1, sep=None, engine='python', encoding='utf-8-sig')
            st.success("Archivo leído como CSV.")
        except Exception as e_csv:
            st.error(f"ERROR CRÍTICO: No se pudo leer el archivo ni como Excel ni como CSV.")
            st.error(f"Detalle Excel: {e_excel}")
            st.error(f"Detalle CSV: {e_csv}")
            return pd.DataFrame()

    if df_read.empty:
        st.error("El archivo parece estar vacío después de la lectura.")
        return pd.DataFrame()

    df = df_read.copy() # Trabajar con una copia

    # --- Limpieza robusta de nombres de columna ---
    original_columns = df.columns.tolist()
    cleaned_columns = []
    for col in original_columns:
        new_col = str(col).strip() # Quitar espacios al inicio/final
        new_col = new_col.replace('$', 'K_') # Reemplazar $ con K_
        new_col = new_col.replace('%', '_pct') # Reemplazar % con _pct
        new_col = re.sub(r'\s+', '_', new_col) # Reemplazar espacios intermedios con _
        new_col = re.sub(r'[^a-zA-Z0-9_]+', '', new_col) # Eliminar otros caracteres no válidos
        new_col = new_col.strip('_') # Quitar _ al inicio/final
        cleaned_columns.append(new_col)
    
    df.columns = cleaned_columns
    st.write("Columnas después de la limpieza:", df.columns.tolist()) # Debug: Mostrar columnas limpias

    # --- Identificar columna de Período ---
    periodo_col_name = None
    possible_period_names = ['periodo', 'fecha']
    for name in possible_period_names:
         found_col = next((col for col in df.columns if name in col.lower()), None)
         if found_col:
              periodo_col_name = found_col
              break

    if not periodo_col_name:
         st.error("No se pudo identificar la columna de fecha/período. Buscando 'Periodo' o 'Fecha'.")
         return pd.DataFrame()
    else:
         st.info(f"Columna de período identificada como: '{periodo_col_name}'")
         if periodo_col_name != 'Periodo':
              df.rename(columns={periodo_col_name: 'Periodo'}, inplace=True) # Renombrar a estándar

    # Procesar Período
    df['Periodo'] = pd.to_datetime(df['Periodo'], errors='coerce')
    df.dropna(subset=['Periodo'], inplace=True)
    df['Año'] = df['Periodo'].dt.year
    df['Mes_Num'] = df['Periodo'].dt.month
    spanish_months_map = {1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'}
    df['Mes'] = df['Mes_Num'].map(spanish_months_map)

    # --- Convertir todas las columnas numéricas posibles ---
    numeric_cols_found = []
    for col in df.columns:
        # Intentar convertir columnas que no sean de fecha/texto conocido
        if col not in ['Periodo', 'Año', 'Mes_Num', 'Mes']:
            try:
                # Intentar convertir a numérico, forzando errores a NaN
                df[col] = pd.to_numeric(df[col], errors='coerce')
                # Si la conversión fue exitosa (no todos NaN), llenar NaN con 0
                if not df[col].isnull().all():
                     df[col] = df[col].fillna(0)
                     numeric_cols_found.append(col)
                # else: # Si todos son NaN, quizás no era numérica, dejarla como estaba o eliminarla?
                #     st.warning(f"Columna '{col}' parecía numérica pero contenía solo valores no convertibles.")
            except Exception:
                # Si falla la conversión inicial, no es numérica
                st.info(f"Columna '{col}' no se convirtió a numérica.")
                pass # Dejar la columna como está si no se puede convertir

    st.write("Columnas numéricas identificadas y limpiadas:", numeric_cols_found) # Debug

    # --- Calcular Indicadores Faltantes (BASADO EN SUPOSICIONES) ---
    # !! REVISAR ESTOS CÁLCULOS !!
    
    # Sumar costos ($K_)
    k_cols = [col for col in df.columns if col.startswith('K_')]
    if k_cols:
        df['Total_Costos_Calculados'] = df[k_cols].sum(axis=1)
    else:
        df['Total_Costos_Calculados'] = 0
        st.warning("No se encontraron columnas de costo (empezando con 'K_') para calcular costos totales.")

    # Sumar cantidades (hs_ y ds_)
    qty_cols = [col for col in df.columns if col.startswith('hs_') or col.startswith('ds_')]
    if qty_cols:
        df['Total_Cantidades_Calculadas'] = df[qty_cols].sum(axis=1)
    else:
        df['Total_Cantidades_Calculadas'] = 0
        st.warning("No se encontraron columnas de cantidad (empezando con 'hs_' o 'ds_') para calcular cantidades totales.")

    # Calcular Eficiencia Total (si es posible)
    df['Eficiencia_Total_raw'] = df.apply(lambda row: row['Total_Costos_Calculados'] / row['Total_Cantidades_Calculadas'] if row['Total_Cantidades_Calculadas'] != 0 else 0, axis=1)

    # Calcular Inversiones (si es posible) - Suposición: GTO y GTI son inversiones
    inv_cols = [col for col in df.columns if 'GTO' in col or 'GTI' in col]
    k_inv_cols = [col for col in inv_cols if col.startswith('K_')] # Solo sumar las de costos
    if k_inv_cols:
         df['Total_Inversiones_raw'] = df[k_inv_cols].sum(axis=1)
    else:
         df['Total_Inversiones_raw'] = 0
         st.warning("No se encontraron columnas 'K_GTO' o 'K_GTI' para calcular Total Inversiones.")

    # Crear columnas faltantes con 0 si no existen o no se pudieron calcular
    if 'Eficiencia_Operativa_raw' not in df.columns: df['Eficiencia_Operativa_raw'] = 0
    if 'Eficiencia_Gestion_raw' not in df.columns: df['Eficiencia_Gestion_raw'] = 0
    if 'Costos_Var_Interanual' not in df.columns: df['Costos_Var_Interanual'] = 0

    st.write("Columnas finales antes de retornar:", df.columns.tolist()) # Debug
    return df

# --- INICIO DE LA APLICACIÓN ---
st.title("🎯 Indicadores de Eficiencia")
st.write("Análisis de la variación de costos e indicadores clave.")

uploaded_file = st.file_uploader("📂 Cargue aquí su archivo Excel o CSV de Eficiencia", type=["xlsx", "csv"]) # Permitir ambos tipos
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
    
    # Usar Años (numérico) y Meses (string) para los filtros
    filter_cols_config = {
        'Años': 'Años', 'Meses': 'Meses'
    }
    filter_cols_keys = list(filter_cols_config.keys()) # ['Años', 'Meses']

    # Inicializar estado de sesión si no existe
    if 'eff_selections' not in st.session_state:
        # Guardar años como números y meses como strings
        initial_selections = {
            'Años': get_sorted_unique_options(df, 'Año'),
            'Meses': get_sorted_unique_options(df, 'Mes')
            }
        # Asegurar que los años sean numéricos si es posible
        if all(isinstance(y, int) for y in initial_selections['Años']):
             pass # Ya son números
        else:
             try: initial_selections['Años'] = [int(y) for y in initial_selections['Años']]
             except: pass # Dejar como string si no se pueden convertir

        st.session_state.eff_selections = initial_selections
        st.rerun() # Volver a ejecutar para asegurar que el estado se aplique

    # Botón de Reset
    if st.sidebar.button("🔄 Resetear Filtros", use_container_width=True, key="reset_filters"):
        initial_selections = {
             'Años': get_sorted_unique_options(df, 'Año'),
             'Meses': get_sorted_unique_options(df, 'Mes')
             }
        st.session_state.eff_selections = initial_selections
        st.rerun()

    st.sidebar.markdown("---")

    # Guardar selecciones antiguas para detectar cambios
    old_selections = {k: list(v) for k, v in st.session_state.eff_selections.items()}

    # Renderizar filtros multiselect
    for col_key, title in filter_cols_config.items():
        # Obtener opciones disponibles basadas en otras selecciones
        available_options = get_available_options(df, st.session_state.eff_selections, col_key)
        
        # Obtener la selección actual del estado, asegurándose de que los valores todavía estén disponibles
        # Convertir la selección actual al mismo tipo que las opciones (int para años, str para meses)
        current_selection_raw = st.session_state.eff_selections.get(col_key, [])
        if col_key == 'Años':
            current_selection = [sel for sel in current_selection_raw if sel in available_options]
        else: # Meses (y otros si los hubiera) son strings
            current_selection = [str(sel) for sel in current_selection_raw if str(sel) in available_options]

        # Crear el multiselect
        selected = st.sidebar.multiselect(
            title,
            options=available_options, # Usar las opciones disponibles dinámicamente
            default=current_selection, # Usar la selección actual filtrada
            key=f"multiselect_{col_key}"
        )
        # Actualizar el estado de sesión con la nueva selección
        st.session_state.eff_selections[col_key] = selected


    # Si las selecciones cambiaron, volver a ejecutar el script
    if old_selections != st.session_state.eff_selections:
        st.rerun()

    # Aplicar filtros al DataFrame principal
    filtered_df = apply_all_filters(df, st.session_state.eff_selections)

    st.write(f"Después de aplicar los filtros, se muestran **{format_integer_es(len(filtered_df))}** registros.")
    st.markdown("---")

    # --- Lógica para KPIs y Deltas ---
    all_years_sorted_in_df = get_sorted_unique_options(df, 'Año') # Años disponibles en los datos originales
    all_months_sorted_in_df = get_sorted_unique_options(df, 'Mes') # Meses disponibles en los datos originales

    selected_years = st.session_state.eff_selections.get('Años', [])
    selected_months = st.session_state.eff_selections.get('Meses', [])

    # Obtener el último período filtrado y el anterior a ese
    df_for_kpis = filtered_df.sort_values(by=['Año', 'Mes_Num']).copy()

    latest_period_df = pd.DataFrame()
    previous_period_df = pd.DataFrame() # DataFrame para el período anterior

    if not df_for_kpis.empty:
        # Identificar los periodos únicos (Año, Mes_Num) presentes en los datos filtrados
        unique_periods_filtered = df_for_kpis[['Año', 'Mes_Num']].drop_duplicates().sort_values(by=['Año', 'Mes_Num'])

        if not unique_periods_filtered.empty:
            # El último periodo es el último en la lista ordenada de periodos filtrados
            latest_period_info = unique_periods_filtered.iloc[-1]
            latest_period_df = df_for_kpis[
                (df_for_kpis['Año'] == latest_period_info['Año']) &
                (df_for_kpis['Mes_Num'] == latest_period_info['Mes_Num'])
            ].copy() # Usar .copy() para evitar SettingWithCopyWarning

            # El periodo anterior es el penúltimo en la lista ordenada
            if len(unique_periods_filtered) > 1:
                previous_period_info = unique_periods_filtered.iloc[-2]
                previous_period_df = df_for_kpis[
                    (df_for_kpis['Año'] == previous_period_info['Año']) &
                    (df_for_kpis['Mes_Num'] == previous_period_info['Mes_Num'])
                ].copy() # Usar .copy()

    # Calcular KPIs para el período actual (sumar si hay múltiples filas para el mismo mes/año)
    eff_total_current = latest_period_df['Eficiencia_Total_raw'].sum() if not latest_period_df.empty else 0
    eff_operativa_current = latest_period_df['Eficiencia_Operativa_raw'].sum() if not latest_period_df.empty else 0
    eff_gestion_current = latest_period_df['Eficiencia_Gestion_raw'].sum() if not latest_period_df.empty else 0
    total_inversiones_current = latest_period_df['Total_Inversiones_raw'].sum() if not latest_period_df.empty else 0

    # Calcular KPIs para el período anterior (sumar si hay múltiples filas)
    eff_total_prev = previous_period_df['Eficiencia_Total_raw'].sum() if not previous_period_df.empty else None # Usar None si no hay datos previos
    eff_operativa_prev = previous_period_df['Eficiencia_Operativa_raw'].sum() if not previous_period_df.empty else None
    eff_gestion_prev = previous_period_df['Eficiencia_Gestion_raw'].sum() if not previous_period_df.empty else None
    total_inversiones_prev = previous_period_df['Total_Inversiones_raw'].sum() if not previous_period_df.empty else None

    # Determinar el nombre del período actual para las etiquetas
    kpi_period_label = "Período Seleccionado"
    if not latest_period_df.empty:
        # Usar el Mes y Año del DataFrame del último período
        # Recuperar el nombre del mes usando el mapa
        spanish_months_map_inv = {v:k for k,v in spanish_months_map.items()} # Invertir mapa si es necesario
        latest_month_name_kpi = spanish_months_map.get(latest_period_df['Mes_Num'].iloc[0], '')
        latest_year_kpi = latest_period_df['Año'].iloc[0]
        kpi_period_label = f"{latest_month_name_kpi} {latest_year_kpi}"
    elif not filtered_df.empty: # Fallback si latest_period_df está vacío pero filtered_df no
        unique_years = filtered_df['Año'].unique()
        unique_months = filtered_df['Mes'].unique()
        if len(unique_years) == 1 and len(unique_months) == 1:
            kpi_period_label = f"{unique_months[0]} {unique_years[0]}"
        elif len(unique_years) == 1:
            kpi_period_label = f"Año {unique_years[0]}"
        else: # Si hay múltiples años/meses, usar un rango o etiqueta genérica
             try:
                 min_p = filtered_df['Periodo'].min().strftime('%b-%Y')
                 max_p = filtered_df['Periodo'].max().strftime('%b-%Y')
                 if min_p == max_p: kpi_period_label = min_p
                 else: kpi_period_label = f"{min_p} a {max_p}"
             except: # En caso de error de fecha
                  kpi_period_label = "Múltiples Períodos"


    # Mostrar las métricas en 4 columnas usando st.metric directamente
    col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)

    delta_total_str = get_delta_string(eff_total_current, eff_total_prev)
    delta_operativa_str = get_delta_string(eff_operativa_current, eff_operativa_prev)
    delta_gestion_str = get_delta_string(eff_gestion_current, eff_gestion_prev)
    delta_inversiones_str = get_delta_string(total_inversiones_current, total_inversiones_prev)

    # Usar st.markdown para controlar completamente el HTML y CSS
    with col_kpi1:
         st.markdown(f"""
             <div data-testid="stMetric">
                 <label data-testid="stMetricLabel">Eficiencia Total<br>({kpi_period_label})</label>
                 <div data-testid="stMetricValue">{format_number_es(eff_total_current)}</div>
                 <div data-testid="stMetricDelta">{delta_total_str if delta_total_str else '<div class="delta-container"></div>'}</div>
             </div>
             """, unsafe_allow_html=True)

    with col_kpi2:
         st.markdown(f"""
             <div data-testid="stMetric">
                 <label data-testid="stMetricLabel">Eficiencia Operativa<br>({kpi_period_label})</label>
                 <div data-testid="stMetricValue">{format_number_es(eff_operativa_current)}</div>
                 <div data-testid="stMetricDelta">{delta_operativa_str if delta_operativa_str else '<div class="delta-container"></div>'}</div>
             </div>
             """, unsafe_allow_html=True)

    with col_kpi3:
         st.markdown(f"""
             <div data-testid="stMetric">
                 <label data-testid="stMetricLabel">Eficiencia Gestión<br>({kpi_period_label})</label>
                 <div data-testid="stMetricValue">{format_number_es(eff_gestion_current)}</div>
                 <div data-testid="stMetricDelta">{delta_gestion_str if delta_gestion_str else '<div class="delta-container"></div>'}</div>
             </div>
             """, unsafe_allow_html=True)

    with col_kpi4:
         st.markdown(f"""
             <div data-testid="stMetric">
                 <label data-testid="stMetricLabel">Total Inversiones<br>({kpi_period_label})</label>
                 <div data-testid="stMetricValue">{format_number_es(total_inversiones_current)}</div>
                 <div data-testid="stMetricDelta">{delta_inversiones_str if delta_inversiones_str else '<div class="delta-container"></div>'}</div>
             </div>
             """, unsafe_allow_html=True)

    # El script de animación JS ya no es necesario si usamos st.metric
    st.markdown("<br>", unsafe_allow_html=True)

    # Tabs
    tab_variacion_interanual, tab_variacion_mensual, tab_detalle_indicadores = st.tabs(["Variación Interanual", "Variación Mensual", "Detalle de Indicadores"])

    with tab_variacion_interanual:
        st.subheader("Variación Interanual (Costos)")
        # --- Modificación: Filtrar Año 2024 ---
        # Asegurarse que la columna Año sea numérica para la comparación
        df_interanual = filtered_df[filtered_df['Año'] != 2024].copy()

        if not df_interanual.empty and 'Costos_Var_Interanual' in df_interanual.columns:
            # Asegurar el orden correcto de los periodos antes de graficar/tabular
            df_interanual = df_interanual.sort_values(by='Periodo').copy()
            df_interanual['Periodo_Formatted'] = df_interanual['Periodo'].dt.strftime('%b-%y')

            # --- Gráfico ---
            st.markdown("##### Gráfico de Variación Interanual")

            # Crear el gráfico base
            chart_interanual = alt.Chart(df_interanual).mark_bar(color='#5b9bd5').encode(
                x=alt.X('Periodo_Formatted:N',
                        # Ordenar el eje X basado en la fecha original para asegurar el orden cronológico
                        sort=alt.EncodingSortField(field="Periodo", op="min", order='ascending'),
                        title='Período'),
                y=alt.Y('Costos_Var_Interanual:Q', title='Variación Interanual ($)', axis=alt.Axis(format='$,.0f')), # Usar formato $, directamente
                tooltip=[
                    alt.Tooltip('Periodo_Formatted', title='Período'),
                    alt.Tooltip('Costos_Var_Interanual', title='Variación ($)', format='$,.2f')
                ]
            ).properties(
                # title='Variación Interanual de Costos por Período' # Título opcional
            ).interactive()

            # Añadir etiquetas de valor sobre las barras
            text_labels = chart_interanual.mark_text(
                align='center',
                baseline='bottom', # Colocar justo encima de la barra
                dy=-5, # Ajuste vertical ligero
                color='black' # Color del texto
            ).encode(
                text=alt.Text('Costos_Var_Interanual:Q', format='$,.0f') # Formato $, para las etiquetas
            )

            st.altair_chart((chart_interanual + text_labels), use_container_width=True)

            # --- Tabla ---
            st.markdown("##### Tabla de Variación Interanual")
            # Preparar datos para la tabla, manteniendo el orden
            table_interanual = df_interanual[['Periodo_Formatted', 'Costos_Var_Interanual']].rename(
                columns={'Periodo_Formatted': 'Período', 'Costos_Var_Interanual': 'Variación ($)'}
            )
            # Aplicar formato de moneda a la columna de variación
            table_interanual_display = table_interanual.style.format({'Variación ($)': lambda x: f"${format_number_es(x)}"})

            st.dataframe(table_interanual_display.set_properties(**{'text-align': 'right'}, subset=['Variación ($)']).hide(axis="index"),
                         use_container_width=True)

            generate_download_buttons(table_interanual, 'Costos_Var_Interanual', '_interanual')
        else:
            st.info("No hay datos de variación interanual (excluyendo 2024) para mostrar con los filtros seleccionados, o la columna 'Costos_Var_Interanual' no existe.")


    with tab_variacion_mensual:
        st.subheader("Variación Mensual (Próximamente)")
        st.info("Esta sección aún no está implementada. Volveré pronto con nuevas características!")

    with tab_detalle_indicadores:
        st.subheader("Detalle de Indicadores")
        st.markdown("##### Valores por Período")

        # Seleccionar y renombrar columnas para mostrar
        # Usamos los nombres estándar calculados/esperados
        cols_to_show_standard = ['Periodo', 'Eficiencia_Total_raw', 'Eficiencia_Operativa_raw', 'Eficiencia_Gestion_raw', 'Total_Inversiones_raw']
        display_cols_standard = {
            'Periodo': 'Período',
            'Eficiencia_Total_raw': 'Eficiencia Total',
            'Eficiencia_Operativa_raw': 'Eficiencia Operativa',
            'Eficiencia_Gestion_raw': 'Eficiencia Gestión',
            'Total_Inversiones_raw': 'Total Inversiones'
        }

        # Filtrar columnas existentes en el DataFrame
        existing_cols_standard = [col for col in cols_to_show_standard if col in filtered_df.columns]
        df_indicadores_display = filtered_df[existing_cols_standard].copy()

        # Renombrar columnas según el mapeo
        df_indicadores_display.rename(columns={k:v for k,v in display_cols_standard.items() if k in existing_cols_standard}, inplace=True)

        # Ordenar por Periodo y formatear fecha
        if 'Período' in df_indicadores_display.columns:
             df_indicadores_display = df_indicadores_display.sort_values(by='Período')
             df_indicadores_display['Período'] = df_indicadores_display['Período'].dt.strftime('%b-%Y')

        # Formatear columnas numéricas como moneda (o número simple si prefieres)
        # numeric_display_cols_standard = [display_cols_standard[k] for k in existing_cols_standard if k != 'Periodo']
        # Usar los nombres finales después del rename para el formateo
        numeric_display_cols_final = [col for col in df_indicadores_display.columns if col != 'Período']
        formatters = {col: lambda x: f"{format_number_es(x)}" for col in numeric_display_cols_final} # Formato numérico

        # Mostrar DataFrame formateado
        st.dataframe(
            df_indicadores_display.style.format(formatters).set_properties(**{'text-align': 'right'}, subset=numeric_display_cols_final).hide(axis="index"),
            use_container_width=True
        )

        # Botones de descarga (usar el DataFrame *antes* de aplicar el formato de string para exportar números correctamente)
        df_download = filtered_df[existing_cols_standard].copy()
        if 'Periodo' in df_download.columns:
            df_download = df_download.sort_values(by='Periodo')
            # Exportar fecha en formato YYYY-MM-DD para compatibilidad
            df_download['Periodo'] = df_download['Periodo'].dt.strftime('%Y-%m-%d')
        df_download.rename(columns={k:v for k,v in display_cols_standard.items() if k in existing_cols_standard}, inplace=True)
        generate_download_buttons(df_download, 'Detalle_Indicadores', '_detalle')


else:
    st.info("Por favor, cargue un archivo Excel o CSV para comenzar el análisis.")

