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
import zipfile # Para capturar errores específicos de Excel
import logging # Para logging detallado
import openpyxl # Necesario para listar hojas

# Configurar logging
logging.basicConfig(level=logging.INFO)

# --- Configuración de la página ---
st.set_page_config(layout="wide", page_title="Indicadores HE y Guardias", page_icon="🎯") # Título cambiado

# --- CSS Personalizado ---
# (CSS Omitido por brevedad - similar a versiones anteriores, ajustado para KPIs)
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
/* Estilos base de la tarjeta KPI */
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
    sheet_name_to_find = 'eficiencia' # Nombre de hoja esperado (en minúsculas para comparación)

    # --- Leer SÓLO como Excel, buscando la hoja insensible a mayúsculas ---
    try:
        logging.info("Intentando leer como archivo Excel...")
        uploaded_file.seek(0)

        # 1. Obtener la lista de nombres de hojas
        try:
             xls = pd.ExcelFile(uploaded_file, engine='openpyxl')
             sheet_names = xls.sheet_names
             logging.info(f"Hojas encontradas: {sheet_names}")
        except Exception as e_list_sheets:
             st.error(f"Error al listar las hojas del archivo Excel: {e_list_sheets}")
             return pd.DataFrame()

        # 2. Buscar la hoja 'eficiencia' (insensible a mayúsculas/minúsculas y espacios)
        actual_sheet_name = None
        for name in sheet_names:
            if name.strip().lower() == sheet_name_to_find:
                actual_sheet_name = name
                logging.info(f"Hoja '{sheet_name_to_find}' encontrada como: '{actual_sheet_name}'")
                break

        # 3. Si no se encontró la hoja, mostrar error y salir
        if actual_sheet_name is None:
             st.error(f"ERROR CRÍTICO: No se encontró una hoja llamada '{sheet_name_to_find}' (o similar) en el archivo Excel.")
             st.info(f"Hojas disponibles: {', '.join(sheet_names)}")
             return pd.DataFrame()

        # 4. Leer la hoja encontrada, intentando header=0 y luego header=1
        try:
            # Intentar leer desde la primera fila (header=0)
            uploaded_file.seek(0) # Resetear para la lectura final
            df_read = pd.read_excel(uploaded_file, sheet_name=actual_sheet_name, header=0, engine='openpyxl')
            logging.info(f"Leído como Excel desde fila 1 (hoja '{actual_sheet_name}').")
            st.success("Archivo leído como Excel.") # Mensaje de éxito
        except Exception as e_h0:
            # Si falla header=0, intentar header=1 como fallback
            logging.warning(f"No se pudo leer Excel desde la fila 1 ({e_h0}). Intentando desde la fila 2...")
            uploaded_file.seek(0) # Reset pointer
            df_read = pd.read_excel(uploaded_file, sheet_name=actual_sheet_name, header=1, engine='openpyxl')
            logging.info(f"Leído como Excel desde fila 2 (hoja '{actual_sheet_name}').")
            st.success("Archivo leído como Excel (desde fila 2).") # Mensaje de éxito

    # --- Manejar otros errores específicos de Excel (formato, etc.) ---
    except (ValueError, zipfile.BadZipFile) as e_excel_format:
        if isinstance(e_excel_format, zipfile.BadZipFile):
             st.error("ERROR CRÍTICO: El archivo .xlsx parece estar corrupto o no es un archivo Excel válido.")
        else: # Other ValueErrors during read
             st.error(f"ERROR CRÍTICO: No se pudo leer el archivo Excel (posible problema de formato). Error: {e_excel_format}")
        return pd.DataFrame() # Retornar vacío si la lectura de Excel falla

    # --- Manejar otros errores inesperados ---
    except Exception as e_general:
        st.error(f"ERROR INESPERADO al leer el archivo Excel: {e_general}")
        return pd.DataFrame()

    # --- Proceder con la limpieza si la lectura fue exitosa ---
    if df_read.empty:
        st.error("El archivo parece estar vacío después de la lectura.")
        return pd.DataFrame()

    df = df_read.copy()
    # Mensaje de éxito ya mostrado

    # --- Identificar columna de Período ANTES de la limpieza agresiva ---
    original_columns_list = df.columns.tolist() # Guardar nombres originales
    periodo_col_original_name = None
    periodo_col_standard_name = 'Periodo' # Nombre estándar que usaremos

    possible_period_names_patterns = ['periodo', 'fecha']
    for original_col in original_columns_list:
        col_lower_stripped = str(original_col).strip().lower()
        if any(pattern in col_lower_stripped for pattern in possible_period_names_patterns):
             periodo_col_original_name = original_col
             logging.info(f"Columna de período original encontrada: '{periodo_col_original_name}'")
             break

    if not periodo_col_original_name:
        # Si no se encontró por nombre, asumir que es la primera columna
        periodo_col_original_name = original_columns_list[0]
        logging.warning(f"No se encontró 'Periodo' o 'Fecha'. Asumiendo que la primera columna '{periodo_col_original_name}' es la fecha.")
        original_first_col_str = str(periodo_col_original_name).lower()
        if 'periodo' not in original_first_col_str and 'fecha' not in original_first_col_str:
             st.warning(f"Advertencia: El nombre de la primera columna ('{periodo_col_original_name}') no sugiere que sea una fecha.")

    # Renombrar la columna de período encontrada a 'Periodo' estándar
    if periodo_col_original_name in df.columns:
        df.rename(columns={periodo_col_original_name: periodo_col_standard_name}, inplace=True)
        logging.info(f"Columna '{periodo_col_original_name}' renombrada a '{periodo_col_standard_name}'.")
    else:
        st.error(f"Error interno: La columna de período '{periodo_col_original_name}' no se encontró para renombrar.")
        return pd.DataFrame()


    # --- Limpieza robusta del RESTO de nombres de columna ---
    cleaned_columns_map = {}
    for col in df.columns:
        if col == periodo_col_standard_name: # No limpiar la columna de período ya estandarizada
             cleaned_columns_map[col] = col
             continue
        new_col = str(col).strip()
        new_col = new_col.replace('$', 'K_') # Reemplazar $ con K_ consistentemente
        new_col = new_col.replace('%', 'pct') # Reemplazar % con pct (sin guion bajo antes)
        new_col = re.sub(r'\s+', '_', new_col) # Reemplazar espacios intermedios con _
        new_col = new_col.replace('.', '_') # Reemplazar puntos por guiones bajos
        new_col = re.sub(r'[^a-zA-Z0-9_]+', '', new_col) # Eliminar otros caracteres no válidos
        new_col = new_col.strip('_')
        if not new_col: new_col = f"col_{len(cleaned_columns_map)}" # Evitar nombres vacíos
        # Manejar duplicados añadiendo sufijo
        count = 1
        final_col_name = new_col
        while final_col_name in cleaned_columns_map.values():
             final_col_name = f"{new_col}_{count}"
             count += 1
        cleaned_columns_map[col] = final_col_name

    df.rename(columns=cleaned_columns_map, inplace=True)
    logging.info(f"Columnas después de la limpieza: {df.columns.tolist()}")


    # --- Procesar Período ---
    if periodo_col_standard_name not in df.columns:
        st.error(f"ERROR INTERNO: La columna '{periodo_col_standard_name}' no está presente después del renombrado.")
        return pd.DataFrame()

    try:
        # Intentar convertir directamente
        df[periodo_col_standard_name] = pd.to_datetime(df[periodo_col_standard_name], errors='coerce')
    except Exception as e1:
         logging.warning(f"Conversión directa a fecha falló ({e1}). Intentando inferir formato...")
         # Si falla, intentar inferir formato
         try:
              df[periodo_col_standard_name] = pd.to_datetime(df[periodo_col_standard_name], infer_datetime_format=True, errors='coerce')
         except Exception as e_date:
              st.error(f"Error crítico al convertir la columna '{periodo_col_standard_name}' a fecha incluso infiriendo: {e_date}")
              return pd.DataFrame()

    df.dropna(subset=[periodo_col_standard_name], inplace=True)
    if df.empty:
         st.error(f"No quedan datos válidos después de procesar las fechas. Verifique el formato de la columna '{periodo_col_original_name}'.")
         return pd.DataFrame()

    df['Año'] = df[periodo_col_standard_name].dt.year
    df['Mes_Num'] = df[periodo_col_standard_name].dt.month
    spanish_months_map = {1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'}
    df['Mes'] = df['Mes_Num'].map(spanish_months_map)


    # --- Convertir todas las columnas numéricas posibles ---
    numeric_cols_found = []
    for col in df.columns:
        if col not in [periodo_col_standard_name, 'Año', 'Mes_Num', 'Mes']:
            original_dtype = df[col].dtype
            try:
                # Replace comma decimal separator if present, then convert
                if df[col].dtype == 'object':
                     # Handle potential non-string values before replace
                     df[col] = df[col].apply(lambda x: str(x).replace(',', '.') if pd.notna(x) else x)
                # Intentar convertir a numérico, forzando errores a NaN
                converted_col = pd.to_numeric(df[col], errors='coerce')
                # Si la conversión fue exitosa (no todos NaN), aplicar y llenar NaN con 0
                if not converted_col.isnull().all():
                     df[col] = converted_col.fillna(0)
                     numeric_cols_found.append(col)
                # else: # Si todos son NaN, no era numérica
                     # logging.warning(f"Columna '{col}' parecía numérica pero no se pudo convertir.")
            except Exception as e:
                logging.info(f"Columna '{col}' (dtype: {original_dtype}) no se convirtió a numérica. Error: {e}")
                pass # Dejar la columna como está si falla
    logging.info(f"Columnas numéricas identificadas y limpiadas: {numeric_cols_found}")


    # --- Calcular Totales HE y Guardias ---
    # !! Ajustar nombres de columnas si son diferentes después de la limpieza !!
    he_costo_cols = [c for c in ['K_50pct', 'K_100pct'] if c in df.columns]
    he_qty_cols = [c for c in ['hs_50pct', 'hs_100pct'] if c in df.columns]
    guardia_costo_cols = [c for c in ['K_Guardias_2T', 'K_Guardias_3T'] if c in df.columns]
    guardia_qty_cols = [c for c in ['ds_Guardias_2T', 'ds_Guardias_3T'] if c in df.columns]

    df['$K_Total_HE'] = df[he_costo_cols].sum(axis=1) if he_costo_cols else 0
    df['Cant_Total_HE'] = df[he_qty_cols].sum(axis=1) if he_qty_cols else 0
    df['$K_Total_Guardias'] = df[guardia_costo_cols].sum(axis=1) if guardia_costo_cols else 0
    df['Cant_Total_Guardias'] = df[guardia_qty_cols].sum(axis=1) if guardia_qty_cols else 0

    logging.info(f"Columnas HE Costo usadas: {he_costo_cols}")
    logging.info(f"Columnas HE Cantidad usadas: {he_qty_cols}")
    logging.info(f"Columnas Guardias Costo usadas: {guardia_costo_cols}")
    logging.info(f"Columnas Guardias Cantidad usadas: {guardia_qty_cols}")


    # --- Crear columnas 'Eficiencia' y 'Var Interanual' si no existen ---
    # (Usaremos los totales calculados arriba para los KPIs, estas son por si se usan en otro lado)
    if 'Eficiencia_Total_raw' not in df.columns: df['Eficiencia_Total_raw'] = 0
    if 'Eficiencia_Operativa_raw' not in df.columns: df['Eficiencia_Operativa_raw'] = 0
    if 'Eficiencia_Gestion_raw' not in df.columns: df['Eficiencia_Gestion_raw'] = 0
    if 'Total_Inversiones_raw' not in df.columns: df['Total_Inversiones_raw'] = 0 # Podrías calcularlo si existen K_GTO/K_GTI
    if 'Costos_Var_Interanual' not in df.columns: df['Costos_Var_Interanual'] = 0 # No hay datos para calcularlo

    logging.info(f"Columnas finales antes de retornar: {df.columns.tolist()}")
    return df

# --- INICIO DE LA APLICACIÓN ---
st.title("🎯 Indicadores HE y Guardias") # Título cambiado
st.write("Análisis de costos y cantidades de Horas Extras y Guardias.") # Subtítulo cambiado

uploaded_file = st.file_uploader("📂 Cargue aquí su archivo Excel de Eficiencia", type=["xlsx"]) # Aceptar solo Excel
st.markdown("---")

if uploaded_file is not None:
    # --- Carga y limpieza de datos ---
    with st.spinner('Procesando archivo Excel...'): # Mensaje específico
        df = load_and_clean_data(uploaded_file)

    # --- Verificación post-carga ---
    if df.empty:
        st.stop() # Mensajes de error ya mostrados en load_and_clean_data
    elif 'Periodo' not in df.columns or df['Periodo'].isnull().all():
        st.error("La columna 'Periodo' no se pudo procesar correctamente. Verifique el formato de fechas en la hoja 'eficiencia'.")
        st.stop()
    else:
        st.success(f"Se ha cargado un total de **{format_integer_es(len(df))}** registros desde la hoja 'eficiencia'.")
        st.markdown("---")

    # --- Resto del código (Filtros, KPIs, Tabs) ---
    st.sidebar.header('Filtros Generales')

    filter_cols_config = {
        'Años': 'Años', 'Meses': 'Meses'
    }
    filter_cols_keys = list(filter_cols_config.keys())

    # Inicializar estado de sesión si no existe
    if 'eff_selections' not in st.session_state:
        initial_selections = {
            'Años': get_sorted_unique_options(df, 'Año'),
            'Meses': get_sorted_unique_options(df, 'Mes')
            }
        # Asegurar años numéricos
        if all(isinstance(y, int) for y in initial_selections['Años']): pass
        else:
             try: initial_selections['Años'] = [int(y) for y in initial_selections['Años']]
             except: pass

        st.session_state.eff_selections = initial_selections
        st.rerun()

    # Botón de Reset
    if st.sidebar.button("🔄 Resetear Filtros", use_container_width=True, key="reset_filters"):
        initial_selections = {
             'Años': get_sorted_unique_options(df, 'Año'),
             'Meses': get_sorted_unique_options(df, 'Mes')
             }
        st.session_state.eff_selections = initial_selections
        st.rerun()

    st.sidebar.markdown("---")

    old_selections = {k: list(v) for k, v in st.session_state.eff_selections.items()}

    # Renderizar filtros multiselect
    for col_key, title in filter_cols_config.items():
        available_options = get_available_options(df, st.session_state.eff_selections, col_key)
        current_selection_raw = st.session_state.eff_selections.get(col_key, [])

        if col_key == 'Años':
            current_selection = [sel for sel in current_selection_raw if sel in available_options]
        else:
            current_selection = [str(sel) for sel in current_selection_raw if str(sel) in available_options]

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

    # --- Lógica para KPIs y Deltas (AHORA CON HE Y GUARDIAS) ---
    all_years_sorted_in_df = get_sorted_unique_options(df, 'Año')
    all_months_sorted_in_df = get_sorted_unique_options(df, 'Mes')

    selected_years = st.session_state.eff_selections.get('Años', [])
    selected_months = st.session_state.eff_selections.get('Meses', [])

    df_for_kpis = filtered_df.sort_values(by=['Año', 'Mes_Num']).copy()

    latest_period_df = pd.DataFrame()
    previous_period_df = pd.DataFrame()

    if not df_for_kpis.empty:
        unique_periods_filtered = df_for_kpis[['Año', 'Mes_Num']].drop_duplicates().sort_values(by=['Año', 'Mes_Num'])
        if not unique_periods_filtered.empty:
            latest_period_info = unique_periods_filtered.iloc[-1]
            latest_period_df = df_for_kpis[
                (df_for_kpis['Año'] == latest_period_info['Año']) &
                (df_for_kpis['Mes_Num'] == latest_period_info['Mes_Num'])
            ].copy()
            if len(unique_periods_filtered) > 1:
                previous_period_info = unique_periods_filtered.iloc[-2]
                previous_period_df = df_for_kpis[
                    (df_for_kpis['Año'] == previous_period_info['Año']) &
                    (df_for_kpis['Mes_Num'] == previous_period_info['Mes_Num'])
                ].copy()

    # Calcular KPIs actuales (usando columnas calculadas en load_and_clean)
    kpi_he_costo_current = latest_period_df['$K_Total_HE'].sum() if not latest_period_df.empty else 0
    kpi_he_cant_current = latest_period_df['Cant_Total_HE'].sum() if not latest_period_df.empty else 0
    kpi_guardia_costo_current = latest_period_df['$K_Total_Guardias'].sum() if not latest_period_df.empty else 0
    kpi_guardia_cant_current = latest_period_df['Cant_Total_Guardias'].sum() if not latest_period_df.empty else 0

    # Calcular KPIs previos
    kpi_he_costo_prev = previous_period_df['$K_Total_HE'].sum() if not previous_period_df.empty else None
    kpi_he_cant_prev = previous_period_df['Cant_Total_HE'].sum() if not previous_period_df.empty else None
    kpi_guardia_costo_prev = previous_period_df['$K_Total_Guardias'].sum() if not previous_period_df.empty else None
    kpi_guardia_cant_prev = previous_period_df['Cant_Total_Guardias'].sum() if not previous_period_df.empty else None

    # Etiqueta de período
    kpi_period_label = "Período Seleccionado"
    spanish_months_map = {1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'}
    if not latest_period_df.empty:
        latest_month_name_kpi = spanish_months_map.get(latest_period_df['Mes_Num'].iloc[0], '')
        latest_year_kpi = latest_period_df['Año'].iloc[0]
        kpi_period_label = f"{latest_month_name_kpi} {latest_year_kpi}"
    # ... (fallback label logic omitida por brevedad, es la misma)

    # Calcular deltas
    delta_he_costo_str = get_delta_string(kpi_he_costo_current, kpi_he_costo_prev)
    delta_he_cant_str = get_delta_string(kpi_he_cant_current, kpi_he_cant_prev)
    delta_guardia_costo_str = get_delta_string(kpi_guardia_costo_current, kpi_guardia_costo_prev)
    delta_guardia_cant_str = get_delta_string(kpi_guardia_cant_current, kpi_guardia_cant_prev)

    # Mostrar KPIs
    col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
    with col_kpi1:
         st.markdown(f"""
             <div data-testid="stMetric">
                 <label data-testid="stMetricLabel">Costo Total HE<br>({kpi_period_label})</label>
                 <div data-testid="stMetricValue">{format_number_es(kpi_he_costo_current)}</div>
                 <div data-testid="stMetricDelta">{delta_he_costo_str if delta_he_costo_str else '<div class="delta-container"></div>'}</div>
             </div>
             """, unsafe_allow_html=True)
    with col_kpi2:
         st.markdown(f"""
             <div data-testid="stMetric">
                 <label data-testid="stMetricLabel">Cantidad Total HE<br>({kpi_period_label})</label>
                 <div data-testid="stMetricValue">{format_number_es(kpi_he_cant_current)}</div> {/* Formato numérico */}
                 <div data-testid="stMetricDelta">{delta_he_cant_str if delta_he_cant_str else '<div class="delta-container"></div>'}</div>
             </div>
             """, unsafe_allow_html=True)
    with col_kpi3:
         st.markdown(f"""
             <div data-testid="stMetric">
                 <label data-testid="stMetricLabel">Costo Total Guardias<br>({kpi_period_label})</label>
                 <div data-testid="stMetricValue">{format_number_es(kpi_guardia_costo_current)}</div>
                 <div data-testid="stMetricDelta">{delta_guardia_costo_str if delta_guardia_costo_str else '<div class="delta-container"></div>'}</div>
             </div>
             """, unsafe_allow_html=True)
    with col_kpi4:
         st.markdown(f"""
             <div data-testid="stMetric">
                 <label data-testid="stMetricLabel">Cantidad Total Guardias<br>({kpi_period_label})</label>
                 <div data-testid="stMetricValue">{format_number_es(kpi_guardia_cant_current)}</div> {/* Formato numérico */}
                 <div data-testid="stMetricDelta">{delta_guardia_cant_str if delta_guardia_cant_str else '<div class="delta-container"></div>'}</div>
             </div>
             """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Tabs (Nombres ajustados para reflejar contenido)
    tab_variacion_interanual, tab_variacion_mensual, tab_detalle = st.tabs(["Variación Interanual", "Variación Mensual", "Detalle por Periodo"])

    # Columnas a usar en las pestañas de variaciones y detalle
    metric_cols = ['$K_Total_HE', 'Cant_Total_HE', '$K_Total_Guardias', 'Cant_Total_Guardias']
    metric_labels = {
        '$K_Total_HE': 'Costo HE',
        'Cant_Total_HE': 'Cantidad HE',
        '$K_Total_Guardias': 'Costo Guardias',
        'Cant_Total_Guardias': 'Cantidad Guardias'
    }

    with tab_variacion_interanual:
        st.subheader("Variación Interanual")
        df_interanual_base = filtered_df[filtered_df['Año'] != 2024].sort_values(by='Periodo').copy()

        if not df_interanual_base.empty and any(col in df_interanual_base.columns for col in metric_cols):
            # Selector para la métrica a visualizar
            selected_metric_inter = st.selectbox("Seleccionar Métrica:", options=metric_cols, format_func=lambda x: metric_labels.get(x, x), key="inter_metric_select")

            # Calcular variación interanual para la métrica seleccionada
            df_interanual = df_interanual_base[['Año', 'Mes_Num', 'Periodo', selected_metric_inter]].copy()
            df_interanual['Valor_Anio_Anterior'] = df_interanual.groupby('Mes_Num')[selected_metric_inter].shift(1)
            # Calcular variación absoluta
            df_interanual['Variacion_Interanual'] = df_interanual[selected_metric_inter] - df_interanual['Valor_Anio_Anterior']
            df_interanual.dropna(subset=['Variacion_Interanual'], inplace=True) # Eliminar filas sin año anterior para comparar

            df_interanual['Periodo_Formatted'] = df_interanual['Periodo'].dt.strftime('%b-%y')

            st.markdown(f"##### Gráfico de Variación Interanual ({metric_labels.get(selected_metric_inter, selected_metric_inter)})")
            is_cost_inter = selected_metric_inter.startswith('$K')
            axis_format_inter = '$,.0f' if is_cost_inter else ',.0f' # Formato para eje Y y etiquetas
            tooltip_format_inter = '$,.2f' if is_cost_inter else ',.2f' # Formato para tooltip

            chart_interanual = alt.Chart(df_interanual).mark_bar(color='#5b9bd5').encode(
                x=alt.X('Periodo_Formatted:N', sort=alt.EncodingSortField(field="Periodo", op="min", order='ascending'), title='Período'),
                y=alt.Y('Variacion_Interanual:Q', title=f'Variación Interanual ({metric_labels.get(selected_metric_inter, selected_metric_inter)})', axis=alt.Axis(format=axis_format_inter)),
                tooltip=[alt.Tooltip('Periodo_Formatted', title='Período'), alt.Tooltip('Variacion_Interanual', title='Variación', format=tooltip_format_inter)]
            ).interactive()
            text_labels_inter = chart_interanual.mark_text(align='center', baseline='bottom', dy=-5, color='black').encode(text=alt.Text('Variacion_Interanual:Q', format=axis_format_inter))
            st.altair_chart((chart_interanual + text_labels_inter), use_container_width=True)

            st.markdown(f"##### Tabla de Variación Interanual ({metric_labels.get(selected_metric_inter, selected_metric_inter)})")
            table_interanual = df_interanual[['Periodo_Formatted', 'Variacion_Interanual']].rename(columns={'Periodo_Formatted': 'Período', 'Variacion_Interanual': 'Variación'})
            formatter_inter = lambda x: f"${format_number_es(x)}" if is_cost_inter else format_number_es(x)
            table_interanual_display = table_interanual.style.format({'Variación': formatter_inter})
            st.dataframe(table_interanual_display.set_properties(**{'text-align': 'right'}, subset=['Variación']).hide(axis="index"), use_container_width=True)
            generate_download_buttons(table_interanual, f'Var_Interanual_{selected_metric_inter}', '_interanual')
        else:
            st.info("No hay datos suficientes para calcular la variación interanual (se necesitan al menos dos años con los mismos meses) o las columnas requeridas no existen.")


    with tab_variacion_mensual:
        st.subheader("Variación Mensual")
        df_mensual_base = filtered_df.sort_values(by='Periodo').copy()

        if not df_mensual_base.empty and any(col in df_mensual_base.columns for col in metric_cols):
            # Selector para la métrica
            selected_metric_mensual = st.selectbox("Seleccionar Métrica:", options=metric_cols, format_func=lambda x: metric_labels.get(x, x), key="mensual_metric_select")
            # Selector para tipo de variación
            tipo_variacion = st.radio("Mostrar como:", ["Valor Absoluto", "Porcentaje"], key="mensual_var_type", horizontal=True)

            # Calcular variación mensual
            df_mensual = df_mensual_base[['Periodo', selected_metric_mensual]].copy()
            df_mensual['Valor_Mes_Anterior'] = df_mensual[selected_metric_mensual].shift(1)
            df_mensual['Variacion_Absoluta'] = df_mensual[selected_metric_mensual] - df_mensual['Valor_Mes_Anterior']
            # Calcular variación porcentual
            df_mensual['Variacion_Porcentual'] = df_mensual.apply(
                lambda row: ((row[selected_metric_mensual] - row['Valor_Mes_Anterior']) / row['Valor_Mes_Anterior'] * 100)
                           if row['Valor_Mes_Anterior'] != 0 else (100.0 if row[selected_metric_mensual] > 0 else 0.0), axis=1
            )
            df_mensual.dropna(subset=['Variacion_Absoluta'], inplace=True) # Quitar la primera fila que no tiene mes anterior
            df_mensual['Periodo_Formatted'] = df_mensual['Periodo'].dt.strftime('%b-%y')

            # Determinar qué columna de variación usar
            col_variacion = 'Variacion_Porcentual' if tipo_variacion == "Porcentaje" else 'Variacion_Absoluta'
            y_title = f'Variación Mensual {"(%)" if tipo_variacion == "Porcentaje" else "($)" if selected_metric_mensual.startswith("$K") else "(Und)"}'
            is_cost_mensual = selected_metric_mensual.startswith('$K')
            
            # Formatos para gráfico y tabla
            if tipo_variacion == "Porcentaje":
                axis_format_mensual = ',.1f\'%\'' # Formato Altair para porcentaje
                tooltip_format_mensual = ',.2f' # Formato Altair para tooltip numérico (se añade % en tooltip)
                table_formatter = lambda x: format_percentage_es(x, 1)
                table_tooltip_suffix = "%"
            else: # Valor Absoluto
                axis_format_mensual = '$,.0f' if is_cost_mensual else ',.0f'
                tooltip_format_mensual = '$,.2f' if is_cost_mensual else ',.2f'
                table_formatter = lambda x: f"${format_number_es(x)}" if is_cost_mensual else format_number_es(x)
                table_tooltip_suffix = ""

            st.markdown(f"##### Gráfico de {y_title} ({metric_labels.get(selected_metric_mensual, selected_metric_mensual)})")
            chart_mensual = alt.Chart(df_mensual).mark_bar().encode(
                x=alt.X('Periodo_Formatted:N', sort=alt.EncodingSortField(field="Periodo", op="min", order='ascending'), title='Período'),
                y=alt.Y(f'{col_variacion}:Q', title=y_title, axis=alt.Axis(format=axis_format_mensual)),
                color=alt.condition(
                    alt.datum[col_variacion] > 0,
                    alt.value("green"),  # Positivo en verde
                    alt.value("red")     # Negativo en rojo
                ),
                tooltip=[
                    alt.Tooltip('Periodo_Formatted', title='Período'),
                    alt.Tooltip(f'{col_variacion}:Q', title='Variación', format=tooltip_format_mensual) # Añadir % manualmente si es pct
                ]
            ).interactive()
            text_labels_mensual = chart_mensual.mark_text(
                align='center',
                baseline='bottom',
                dy=alt.expr(f"datum.{col_variacion} > 0 ? -5 : 15"), # Ajuste para que no choque con la barra
                color='black'
            ).encode(
                text=alt.Text(f'{col_variacion}:Q', format=axis_format_mensual)
            )
            st.altair_chart((chart_mensual + text_labels_mensual), use_container_width=True)

            st.markdown(f"##### Tabla de {y_title} ({metric_labels.get(selected_metric_mensual, selected_metric_mensual)})")
            table_mensual = df_mensual[['Periodo_Formatted', col_variacion]].rename(columns={'Periodo_Formatted': 'Período', col_variacion: 'Variación'})
            table_mensual_display = table_mensual.style.format({'Variación': table_formatter})
            st.dataframe(table_mensual_display.set_properties(**{'text-align': 'right'}, subset=['Variación']).hide(axis="index"), use_container_width=True)
            generate_download_buttons(table_mensual, f'Var_Mensual_{selected_metric_mensual}_{tipo_variacion}', '_mensual')

        else:
            st.info("No hay datos suficientes para calcular la variación mensual (se necesita más de un período) o las columnas requeridas no existen.")


    with tab_detalle:
        st.subheader("Detalle por Periodo")
        st.markdown("##### Valores Calculados por Período")

        # Usar las columnas calculadas
        cols_to_show_detail = ['Periodo'] + metric_cols
        display_cols_detail = {'Periodo': 'Período', **metric_labels} # Usar el diccionario de etiquetas

        existing_cols_detail = [col for col in cols_to_show_detail if col in filtered_df.columns]
        df_detalle_display = filtered_df[existing_cols_detail].copy()
        df_detalle_display.rename(columns={k:v for k,v in display_cols_detail.items() if k in existing_cols_detail}, inplace=True)

        if 'Período' in df_detalle_display.columns:
             df_detalle_display = df_detalle_display.sort_values(by='Período')
             df_detalle_display['Período'] = df_detalle_display['Período'].dt.strftime('%b-%Y')

        # Formatear columnas numéricas (costo como moneda, cantidad como número)
        numeric_display_cols_final_detail = [col for col in df_detalle_display.columns if col != 'Período']
        formatters_detail = {}
        for col in numeric_display_cols_final_detail:
            if "Costo" in col:
                formatters_detail[col] = lambda x: f"${format_number_es(x)}"
            else: # Asumir cantidad
                formatters_detail[col] = lambda x: format_number_es(x) # Formato numérico con 2 decimales

        st.dataframe(
            df_detalle_display.style.format(formatters_detail).set_properties(**{'text-align': 'right'}, subset=numeric_display_cols_final_detail).hide(axis="index"),
            use_container_width=True
        )

        df_download_detail = filtered_df[existing_cols_detail].copy()
        if 'Periodo' in df_download_detail.columns:
            df_download_detail = df_download_detail.sort_values(by='Periodo')
            df_download_detail['Periodo'] = df_download_detail['Periodo'].dt.strftime('%Y-%m-%d')
        df_download_detail.rename(columns={k:v for k,v in display_cols_detail.items() if k in existing_cols_detail}, inplace=True)
        generate_download_buttons(df_download_detail, 'Detalle_HE_Guardias', '_detalle')


else:
    st.info("Por favor, cargue un archivo Excel para comenzar el análisis.")

