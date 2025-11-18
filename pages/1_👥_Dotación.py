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
from PIL import Image, ImageDraw


# --- Configuración de la página y Estilos CSS ---
# MODIFICADO: Título de la página genérico
st.set_page_config(layout="wide", page_title="Dotacion", page_icon="👥")

# --- CSS Personalizado para un Estilo Profesional y RESPONSIVE ---
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

/* --- ESTILOS PARA BORDES REDONDEADOS Y ZÓCALOS --- */

/* Regla #1: Redondea el MAPA INDIVIDUAL (Plotly Chart) */
div[data-testid="stPlotlyChart"] {
    border-radius: 0.8rem;
    overflow: hidden;
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}

/* Regla #2: Elimina el zócalo blanco SOLO de la columna del mapa individual */
div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:has(div[data-testid="stPlotlyChart"]) [data-testid="stVerticalBlock"] {
    gap: 0;
}

/* Regla #3: Agrega una sombra al contenedor del comparador para consistencia visual */
.img-comp-container {
   box-shadow: 0 4px 8px rgba(0,0,0,0.1);
   border-radius: 0.8rem; /* Esto ayuda a que la sombra también se vea redondeada */
}

/* --- FIN DE ESTILOS AGREGADOS --- */

/* --- CSS MOVIDO a 'cards_html' (línea 1420) para asegurar la carga en el iframe --- */


/* --- REGLAS RESPONSIVE GENERALES --- */
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

    .stTabs {
        overflow-x: auto;
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

# --- AÑADIDO: Función de formato de moneda (Req 3) ---
def format_currency_es(num, decimals=2):
    if pd.isna(num) or not isinstance(num, (int, float, np.number)): return ""
    # Formato $ 1.234,56
    return f"${num:,.{decimals}f}".replace(",", "TEMP").replace(".", ",").replace("TEMP", ".")

# --- Funciones Auxiliares ---
def create_rounded_image_with_matte(im, rad, background_color='#f0f2f6'):
    # Creamos la máscara "a mano" para máxima compatibilidad
    mask = Image.new('L', im.size, 0)
    draw = ImageDraw.Draw(mask)

    # Dibujamos las partes rectas de la máscara
    draw.rectangle((rad, 0, im.size[0] - rad, im.size[1]), fill=255)
    draw.rectangle((0, rad, im.size[0], im.size[1] - rad), fill=255)

    # Dibujamos las 4 esquinas circulares en la máscara
    draw.pieslice((0, 0, rad * 2, rad * 2), 180, 270, fill=255)
    draw.pieslice((im.size[0] - rad * 2, 0, im.size[0], rad * 2), 270, 360, fill=255)
    draw.pieslice((0, im.size[1] - rad * 2, rad * 2, im.size[1]), 90, 180, fill=255)
    draw.pieslice((im.size[0] - rad * 2, im.size[1] - rad * 2, im.size[0], im.size[1]), 0, 90, fill=255)

    # Creamos el fondo
    background = Image.new('RGB', im.size, background_color)

    # Pegamos la imagen original usando la máscara que acabamos de dibujar
    background.paste(im.convert('RGB'), (0, 0), mask)
    return background

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

# --- INICIO: NUEVA FUNCIÓN HELPER PARA SIPAF ---
def get_legajo_variations(df_base, periodo_actual, periodo_previo, detail_cols, compare_cols):
    """
    Compara dos períodos y devuelve dataframes de Ingresos, Egresos,
    Cambios (Nivelaciones) y un DF total de todas las variaciones.
    """
    
    # 1. Preparar DataFrames base
    df_actual_raw = df_base[df_base['Periodo'] == periodo_actual]
    df_previo_raw = df_base[df_base['Periodo'] == periodo_previo]
    
    df_actual_legajos = df_actual_raw[detail_cols].drop_duplicates(subset=['LEGAJO'])
    df_previo_legajos = df_previo_raw[detail_cols].drop_duplicates(subset=['LEGAJO'])

    # 2. Realizar el merge 'outer'
    df_merged = pd.merge(
        df_actual_legajos,
        df_previo_legajos,
        on='LEGAJO',
        how='outer',
        suffixes=('_actual', '_previo')
    )

    # 3. Identificar INGRESOS
    col_check_prev = f"{compare_cols[0]}_previo"
    df_ingresos_raw = df_merged[df_merged[col_check_prev].isna()]
    cols_ingresos = [col if col == 'LEGAJO' else f"{col}_actual" for col in detail_cols]
    df_ingresos = df_ingresos_raw[cols_ingresos].rename(
        columns=lambda x: x.replace('_actual', '')
    )
    df_ingresos['Tipo_Variacion'] = 'Ingreso'

    # 4. Identificar EGRESOS
    col_check_actual = f"{compare_cols[0]}_actual"
    df_egresos_raw = df_merged[df_merged[col_check_actual].isna()]
    cols_egresos = [col if col == 'LEGAJO' else f"{col}_previo" for col in detail_cols]
    df_egresos = df_egresos_raw[cols_egresos].rename(
        columns=lambda x: x.replace('_previo', '')
    )
    df_egresos['Tipo_Variacion'] = 'Egreso'

    # 5. Identificar CAMBIOS (Nivelaciones)
    df_comunes = df_merged.dropna(subset=[col_check_actual, col_check_prev]).copy()
    df_comunes['hubo_cambio'] = False
    for col in compare_cols:
        if f'{col}_actual' in df_comunes.columns and f'{col}_previo' in df_comunes.columns:
            df_comunes.loc[df_comunes[f'{col}_actual'] != df_comunes[f'{col}_previo'], 'hubo_cambio'] = True
    df_cambios = df_comunes[df_comunes['hubo_cambio'] == True]

    df_cambios_display_list = []
    for _, row in df_cambios.iterrows():
        row_prev = {col: row[col] if col == 'LEGAJO' else row[f'{col}_previo'] for col in detail_cols}
        row_prev['Tipo_Variacion'] = f"Nivelación ({row['LEGAJO']} - Anterior)"
        df_cambios_display_list.append(row_prev)
        
        row_actual = {col: row[col] if col == 'LEGAJO' else row[f'{col}_actual'] for col in detail_cols}
        row_actual['Tipo_Variacion'] = f"Nivelación ({row['LEGAJO']} - Actual)"
        df_cambios_display_list.append(row_actual)

    df_cambios_final = pd.DataFrame(df_cambios_display_list)
    
    # 6. Combinar todas las variaciones
    df_variaciones_total = pd.concat([df_ingresos, df_egresos, df_cambios_final], ignore_index=True)
    
    # Reordenar columnas
    cols_final_orden = ['Tipo_Variacion', 'Periodo'] + [col for col in detail_cols if col != 'Periodo']
    # Asegurarse que todas las columnas existan antes de reordenar
    cols_final_existentes = [c for c in cols_final_orden if c in df_variaciones_total.columns]
    df_variaciones_total = df_variaciones_total[cols_final_existentes]
    df_variaciones_total = df_variaciones_total.sort_values(by=['Tipo_Variacion', 'LEGAJO'])

    # Devolver los dataframes necesarios
    return df_ingresos, df_egresos, df_cambios, df_cambios_final, df_variaciones_total
# --- FIN: NUEVA FUNCIÓN HELPER PARA SIPAF ---

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

        # --- MODIFICADO: Nueva lógica de ordenamiento para Período ---
        elif column_name == 'Periodo':
            # Mapa para meses abreviados
            month_order_map = {
                'Ene': 1, 'Feb': 2, 'Mar': 3, 'Abr': 4, 'May': 5, 'Jun': 6,
                'Jul': 7, 'Ago': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dic': 12
            }
            # Mapa para meses completos (fallback)
            old_month_order = {
                'Enero': 1, 'Febrero': 2, 'Marzo': 3, 'Abril': 4, 'Mayo': 5, 'Junio': 6,
                'Julio': 7, 'Agosto': 8, 'Septiembre': 9, 'Octubre': 10, 'Noviembre': 11, 'Diciembre': 12
            }

            def get_periodo_sort_key(periodo_str):
                periodo_str_cap = periodo_str.capitalize()
                parts = periodo_str_cap.split('-')

                if len(parts) == 2:
                    # Formato 'Mes-Año' (ej: 'Dic-23')
                    month_str, year_str = parts
                    month = month_order_map.get(month_str, 99)
                    year = int(f"20{year_str}") # '23' -> 2023
                    return (year, month)
                else:
                    # Formato antiguo (ej: 'Enero')
                    month = old_month_order.get(periodo_str_cap, 99)
                    # Asumimos 2025 para datos antiguos sin año, como en la lógica original
                    return (2025, month)

            return sorted(unique_values, key=get_periodo_sort_key)

        # --- AÑADIDO: Lógica de ordenamiento para Año ---
        elif column_name == 'Año':
            try:
                # Ordenar numéricamente (ej: 2023, 2024, 2025)
                return sorted(unique_values, key=lambda x: int(x) if x.isdigit() else 9999)
            except:
                return sorted(unique_values) # Fallback a orden alfabético

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
        # Asumimos que la hoja sigue llamándose 'Dotacion_25' o el usuario usará un archivo con esa hoja
        df_excel = pd.read_excel(uploaded_file, sheet_name='Dotacion_25', engine='openpyxl')

        # --- AÑADIDO (PUNTO 3): Eliminar columnas "Unnamed" ---
        if not df_excel.empty:
            df_excel = df_excel.loc[:, ~df_excel.columns.astype(str).str.startswith('Unnamed:')]
        # --- FIN DE LA MODIFICACIÓN ---

    except Exception as e:
        st.error(f"ERROR CRÍTICO: No se pudo leer la hoja 'Dotacion_25' del archivo cargado. Mensaje: {e}")
        return pd.DataFrame()
    if df_excel.empty: return pd.DataFrame()

    # --- Normalizar y detectar columnas clave sin importar mayúsculas/minúsculas ---
    # Detectar columna Legajo (caso-insensible) y renombrarla temporalmente a 'LEGAJO' en el dataframe
    legajo_col = next((c for c in df_excel.columns if str(c).strip().lower() == 'legajo'), None)
    if legajo_col:
        # si el nombre real no es 'LEGAJO', creamos la columna estándar 'LEGAJO' a partir de ella
        if legajo_col != 'LEGAJO':
            df_excel['LEGAJO'] = df_excel[legajo_col]
    # Si no vino con ningún nombre 'legajo', no hacemos nada; luego lo normalizamos más abajo

    # Igual para CECO (por si la columna viene 'Ceco' o 'CECO' o similar)
    ceco_col = next((c for c in df_excel.columns if str(c).strip().lower() in ['ceco', 'centro de costo', 'centro de costos']), None)
    if ceco_col and ceco_col != 'CECO':
        df_excel['CECO'] = df_excel[ceco_col]

    # --- LEGAJO: convertir a num y luego a string para filtros multiselect (igual que CECO) ---
    if 'LEGAJO' in df_excel.columns:
        # Convertimos legajo a numérico para quitar formatos raros, luego a Int64 para permitir NA y finalmente a str
        df_excel['LEGAJO'] = pd.to_numeric(df_excel['LEGAJO'], errors='coerce').astype('Int64').astype(str)
        df_excel['LEGAJO'] = df_excel['LEGAJO'].replace('<NA>', 'no disponible')

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

    # --- MODIFICADO: Nueva lógica para 'Periodo' y creación de 'Año' ---
    if 'Periodo' in df_excel.columns:
        # 1. Intentar convertir Periodo a datetime
        # Esto manejará fechas como '2023-12-01'
        temp_dates = pd.to_datetime(df_excel['Periodo'], errors='coerce')

        # 2. Definir mapa de meses
        mapa_meses = {
            1: 'Ene', 2: 'Feb', 3: 'Mar', 4: 'Abr', 5: 'May', 6: 'Jun',
            7: 'Jul', 8: 'Ago', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dic'
        }

        # 3. Formatear la columna 'Periodo'
        # Si es una fecha válida (ej: 2023-12-01), la formatea a 'Dic-23'
        # Si no es una fecha (ej: 'Enero' o 'Dic-23' ya), la limpia y la mantiene
        df_excel['Periodo'] = np.where(
            temp_dates.notna(),
            temp_dates.dt.month.map(mapa_meses) + '-' + temp_dates.dt.strftime('%y'),
            df_excel['Periodo'].astype(str).str.strip().str.capitalize()
        )

        # 4. Crear la columna 'Año' basada en el 'Periodo' (ahora formateado)
        def get_year_from_periodo(periodo_str):
            match = re.search(r'(\d{2})$', periodo_str) # Busca 'XX' al final (ej: 'Dic-23')
            if match:
                year_suffix = match.group(1)
                if year_suffix == '23': return '2023'
                if year_suffix == '24': return '2024'
                if year_suffix == '25': return '2025'

            # Fallback para meses antiguos (asumiendo 2025 como en la lógica original)
            old_months = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
            if periodo_str in old_months:
                 return '2025'
            return 'no disponible'

        df_excel['Año'] = df_excel['Periodo'].apply(get_year_from_periodo)

    else:
        df_excel['Periodo'] = 'no disponible'
        df_excel['Año'] = 'no disponible'
    # --- FIN DE LA MODIFICACIÓN ---

    if 'CECO' in df_excel.columns:
        df_excel['CECO'] = pd.to_numeric(df_excel['CECO'], errors='coerce')
        df_excel.dropna(subset=['CECO'], inplace=True)
        df_excel['CECO'] = df_excel['CECO'].astype(int).astype(str)

    # --- MODIFICADO: Añadir 'Año', 'Apellido y Nombre', 'Subnivel' a la lista de columnas a normalizar ---
    text_cols_for_filters_charts = [
        'LEGAJO','Gerencia', 'Relación', 'Sexo', 'Función', 'Distrito',
        'Ministerio', 'Rango Antiguedad', 'Rango Edad', 'Periodo', 'Nivel',
        'CECO', 'Año', 'Apellido y Nombre', 'Subnivel' # <-- REQ 1 AÑADIDO
    ]

    for col in text_cols_for_filters_charts:
        if col not in df_excel.columns: df_excel[col] = 'no disponible'
        df_excel[col] = df_excel[col].astype(str).replace(['None', 'nan', ''], 'no disponible').str.strip()
        if col in ['Rango Antiguedad', 'Rango Edad']: df_excel[col] = df_excel[col].str.lower()
        elif col == 'Periodo': df_excel[col] = df_excel[col].str.capitalize()

    # --- INICIO: MODIFICACIÓN PARA 'Neto Pagado' Y 'SAC Pagado' (REQ 2) ---
    # Procesamos la columna 'Neto Pagado' que el usuario agregó
    if 'Neto Pagado' in df_excel.columns:
        # Convertimos a numérico, los errores (texto) se volverán NaN
        df_excel['Neto Pagado'] = pd.to_numeric(df_excel['Neto Pagado'], errors='coerce')
        # Reemplazamos NaN con 0 para evitar errores en sumas o cálculos
        df_excel['Neto Pagado'] = df_excel['Neto Pagado'].fillna(0)
    else:
        # Si el archivo cargado NO tiene la columna, la creamos con 0s
        df_excel['Neto Pagado'] = 0

    # Procesamos la nueva columna 'SAC Pagado'
    if 'SAC Pagado' in df_excel.columns:
        df_excel['SAC Pagado'] = pd.to_numeric(df_excel['SAC Pagado'], errors='coerce')
        df_excel['SAC Pagado'] = df_excel['SAC Pagado'].fillna(0)
    else:
        df_excel['SAC Pagado'] = 0

    # Creamos la columna combinada 'Neto + SAC'
    df_excel['Neto + SAC'] = df_excel['Neto Pagado'] + df_excel['SAC Pagado']
    # --- FIN: MODIFICACIÓN (REQ 2) ---

    return df_excel

# --- INICIO DE LA APLICACIÓN ---
# MODIFICADO: Título principal genérico
st.title("👥 Dotación")
st.write("Estructura y distribución geográfica y por gerencia de personal")

uploaded_file = st.file_uploader("📂 Cargue aquí su archivo Excel de dotación", type=["xlsx"])
st.markdown("---")

COORDS_URL = "https://raw.githubusercontent.com/Tincho2002/RRHH/main/coordenadas.csv"
df_coords = load_coords_from_url(COORDS_URL)

# --- INICIO REQ 2: Nueva función para deltas de tarjetas Neto ---
def get_delta_html_neto(current_val, prev_val):
    """
    Genera un string HTML para la variación (en $ y %) para las tarjetas de Neto Pagado.
    """
    if pd.isna(prev_val) or pd.isna(current_val) or prev_val == 0:
        # No hay datos previos o el valor previo es 0, no mostrar delta.
        return '<div class="metric-delta grey">vs. período anterior s/d</div>'

    diff_val = current_val - prev_val
    diff_pct = (diff_val / prev_val) * 100

    color = 'green' if diff_val >= 0 else 'red'
    arrow = '▲' if diff_val >= 0 else '▼'

    # Formatear strings
    # Asegurarse de que format_currency_es maneje números (no strings formateados)
    diff_val_str = format_currency_es(diff_val)
    diff_pct_str = format_percentage_es(diff_pct)

    # Evitar -0,0%
    if -0.05 < diff_pct < 0.05:
        color = 'grey'
        arrow = '▬'
        diff_pct_str = format_percentage_es(0.0)

    return f'<div class="metric-delta {color}">{arrow} {diff_val_str} ({diff_pct_str})</div>'
# --- FIN REQ 2 ---


if uploaded_file is not None:
    with st.spinner('Procesando archivo...'):
        df = load_and_clean_data(uploaded_file)
    if df.empty:
        st.error("El archivo cargado está vacío o no se pudo procesar correctamente.")
        st.stop()
    st.success(f"Se ha cargado un total de **{format_integer_es(len(df))}** registros de empleados.")
    st.markdown("---")

    st.sidebar.header('Filtros del Dashboard')

    # --- MODIFICADO: Añadido 'Año' al diccionario de filtros ---
    filter_cols_config = {
        'Año': 'Año',              # AÑADIDO
        'Periodo': 'Periodo',
        'Gerencia': 'Gerencia',
        'Relación': 'Relación',
        'Función': 'Función',
        'Distrito': 'Distrito',
        'Ministerio': 'Ministerio',
        'Rango Antiguedad': 'Antigüedad',
        'Rango Edad': 'Edad',
        'Sexo': 'Sexo',
        'Nivel': 'Nivel',
        'CECO': 'Centro de Costo',
        'LEGAJO': 'Legajo'
    }
    # --- FIN DE LA MODIFICACIÓN ---

    # Conservamos el orden tal cual está en dict (Python 3.7+ mantiene inserción)
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

    # Este bucle ahora creará automáticamente el filtro 'Año'
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
    # La lista 'all_periodos_sorted' ahora usará la nueva función de ordenamiento
    all_periodos_sorted = get_sorted_unique_options(df, 'Periodo') # Master sorted list
    selected_periodos = st.session_state.selections.get('Periodo', [])

    # Get the sorted list of *selected* periods
    sorted_selected_periods = [p for p in all_periodos_sorted if p in selected_periodos]

    previous_period = None
    if sorted_selected_periods:
        period_to_display = sorted_selected_periods[-1]
        # Find the *actual* previous period from the *selected* list
        current_index = sorted_selected_periods.index(period_to_display)
        if current_index > 0:
            previous_period = sorted_selected_periods[current_index - 1]

    # --- INICIO: Corrección de indentación ---
    # El bloque de "if not filtered_df.empty..." estaba mal indentado
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

        # --- START DELTA LOGIC ---
        delta_total_str, delta_convenio_str, delta_fc_str, delta_masculino_str, delta_femenino_str = "", "", "", "", ""

        def get_delta_string(current_val, prev_val):
            if prev_val > 0:
                delta_pct = ((current_val - prev_val) / prev_val) * 100
            elif current_val > 0:
                delta_pct = 100.0 # Crecimiento infinito si prev es 0 y current > 0
            else:
                delta_pct = 0.0 # Sin cambios si ambos son 0

            color = 'green' if delta_pct >= 0 else 'red'
            arrow = '▲' if delta_pct >= 0 else '▼'
            # Evitar mostrar -0.0%
            if -0.05 < delta_pct < 0.05:
                delta_pct = 0.0
                color = 'grey' # Opcional: color neutro para 0%
                arrow = '▬'    # Opcional: símbolo neutro

            return f'<div class="delta {color}">{arrow} {delta_pct:.1f}%</div>'

        if previous_period:
            # Use filtered_df to get previous period data, ensuring filters are applied
            df_previous_period = filtered_df[filtered_df['Periodo'] == previous_period].copy()
            total_dotacion_prev = len(df_previous_period)
            convenio_count_prev = df_previous_period[df_previous_period['Relación'] == 'Convenio'].shape[0]
            fc_count_prev = df_previous_period[df_previous_period['Relación'] == 'FC'].shape[0]
            masculino_count_prev = df_previous_period[df_previous_period['Sexo'] == 'Masculino'].shape[0]
            femenino_count_prev = df_previous_period[df_previous_period['Sexo'] == 'Femenino'].shape[0]

            delta_total_str = get_delta_string(total_dotacion, total_dotacion_prev)
            delta_convenio_str = get_delta_string(convenio_count, convenio_count_prev)
            delta_fc_str = get_delta_string(fc_count, fc_count_prev)
            delta_masculino_str = get_delta_string(masculino_count, masculino_count_prev)
            delta_femenino_str = get_delta_string(femenino_count, femenino_count_prev)
        # --- END DELTA LOGIC ---

        card_html = f"""
        <style>
            .summary-container {{ display: flex; background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); align-items: center; gap: 20px; border: 1px solid #e0e0e0; }}
            .summary-main-kpi {{ text-align: center; border-right: 2px solid #f0f2f6; padding-right: 20px; flex-grow: 1; }}
            .summary-main-kpi .title {{ font-size: 1.1rem; font-weight: bold; color: #2C3E50; margin-bottom: 5px; }}
            .summary-main-kpi .value {{ font-size: 3.5rem; font-weight: bold; color: #2C3E50; }}
            /* --- CSS DELTA MAIN --- */
            .summary-main-kpi .delta {{
                font-size: 1.2rem;
                font-weight: 600;
                margin-top: 5px;
            }}
            .summary-main-kpi .delta.green {{ color: #2ca02c; }}
            .summary-main-kpi .delta.red {{ color: #d62728; }}
            .summary-main-kpi .delta.grey {{ color: #7f7f7f; }} /* Color neutro */

            .summary-breakdown {{ display: flex; flex-direction: column; gap: 15px; flex-grow: 2; }}
            .summary-row {{ display: flex; justify-content: space-around; align-items: center; }}
            .summary-sub-kpi {{ text-align: left; display: flex; align-items: center; gap: 10px; width: 200px; }}
            .summary-sub-kpi .icon {{ font-size: 2rem; }}
            .summary-sub-kpi .details {{ display: flex; flex-direction: column; }}
            .summary-sub-kpi .value {{ font-size: 1.5rem; font-weight: bold; color: #34495E; }}
            .summary-sub-kpi .label {{ font-size: 0.9rem; color: #7F8C8D; }}
            /* --- CSS DELTA SUB --- */
            .summary-sub-kpi .delta {{
                font-size: 0.9rem;
                font-weight: 600;
            }}
            .summary-sub-kpi .delta.green {{ color: #2ca02c; }}
            .summary-sub-kpi .delta.red {{ color: #d62728; }}
            .summary-sub-kpi .delta.grey {{ color: #7f7f7f; }} /* Color neutro */

            @media (max-width: 768px) {{
                .summary-container {{
                    flex-direction: column;
                    padding: 15px;
                    gap: 15px;
                }}
                .summary-main-kpi {{
                    border-right: none;
                    border-bottom: 2px solid #f0f2f6;
                    padding-right: 0;
                    padding-bottom: 15px;
                    width: 100%;
                }}
                .summary-main-kpi .value {{ font-size: 2.8rem; }}
                .summary-row {{
                    flex-direction: column;
                    gap: 15px;
                    align-items: flex-start;
                    width: 100%;
                }}
                .summary-sub-kpi {{ width: 100%; }}
            }}
        </style>
        <div class="summary-container">
            <div class="summary-main-kpi">
                <div class="title">DOTACIÓN {period_to_display.upper()}</div>
                <div class="value" data-target="{total_dotacion}">👥 0</div>
                {delta_total_str}
            </div>
            <div class="summary-breakdown">
                <div class="summary-row">
                    <div class="summary-sub-kpi">
                        <div class="icon">📄</div>
                        <div class="details">
                            <div class="value" data-target="{convenio_count}">0</div>
                            <div class="label">Convenio ({format_percentage_es(convenio_pct)})</div>
                            {delta_convenio_str}
                        </div>
                    </div>
                    <div class="summary-sub-kpi">
                        <div class="icon">💼</div>
                        <div class="details">
                            <div class="value" data-target="{fc_count}">0</div>
                            <div class="label">Fuera de Convenio ({format_percentage_es(fc_pct)})</div>
                            {delta_fc_str}
                        </div>
                    </div>
                </div>
                <div class="summary-row">
                    <div class="summary-sub-kpi">
                        <div class="icon">👨</div>
                        <div class="details">
                            <div class="value" data-target="{masculino_count}">0</div>
                            <div class="label">Masculino ({format_percentage_es(masculino_pct)})</div>
                            {delta_masculino_str}
                        </div>
                    </div>
                    <div class="summary-sub-kpi">
                        <div class="icon">👩</div>
                        <div class="details">
                            <div class="value" data-target="{femenino_count}">0</div>
                            <div class="label">Femenino ({format_percentage_es(femenino_pct)})</div>
                            {delta_femenino_str}
                        </div>
                    </div>
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
                    let formattedVal = currentVal.toString().replace(/\B(?=(\d{{3}})+(?!\d))/g, ".");
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
    # --- FIN: Corrección de indentación ---

    # --- INICIO: CORRECCIÓN LÓGICA DE SOLAPAS (REQ 2) ---
    tab_names = ["📊 Resumen de Dotación", "📊 Dotación SIPAF", "⏳ Edad y Antigüedad", "📈 Desglose por Categoría", "💰 Neto Pagado", "📈 Evolución de Pagos", "📋 Datos Brutos"]

    if not df_coords.empty:
        # Insertar las solapas de mapas después de Dotación SIPAF
        tab_names.insert(2, "🗺️ Comparador de Mapas")
        tab_names.insert(3, "🗺️ Mapa Geográfico")

    tabs = st.tabs(tab_names)

    # Re-indexar las variables de las solapas
    tab_index = 0
    tab_resumen = tabs[tab_index]; tab_index += 1
    tab_sipaf = tabs[tab_index]; tab_index += 1

    tab_map_comparador = None
    tab_map_individual = None
    if not df_coords.empty:
        tab_map_comparador = tabs[tab_index]; tab_index += 1
        tab_map_individual = tabs[tab_index]; tab_index += 1

    tab_edad_antiguedad = tabs[tab_index]; tab_index += 1
    tab_desglose = tabs[tab_index]; tab_index += 1
    tab_neto_pagado = tabs[tab_index]; tab_index += 1
    tab_evolucion_pagos = tabs[tab_index]; tab_index += 1
    tab_brutos = tabs[tab_index]; tab_index += 1
    # --- FIN: CORRECCIÓN LÓGICA DE SOLAPAS (REQ 2) ---

    with tab_resumen:
        st.header('Resumen General de la Dotación')
        if filtered_df.empty:
            st.warning("No hay datos para mostrar con los filtros seleccionados.")
        else:
            st.metric(label="Total de Empleados (filtrado)", value=format_integer_es(len(filtered_df)))
            st.subheader('Dotación por Periodo (Total)')
            col_table_periodo, col_chart_periodo = st.columns([1, 2])

            # Los datos se agrupan por 'Periodo'
            periodo_counts = filtered_df.groupby('Periodo').size().reset_index(name='Cantidad')
            # Se aplica el ordenamiento categórico usando la lista ya ordenada
            periodo_counts['Periodo'] = pd.Categorical(periodo_counts['Periodo'], categories=all_periodos_sorted, ordered=True)
            periodo_counts = periodo_counts.sort_values('Periodo').reset_index(drop=True)

            # --- MODIFICADO (PUNTO 1): Usar 'sorted_selected_periods' para el eje X ---
            # Solo filtramos el DF del gráfico, la tabla de la izquierda puede mostrar todo
            periodo_counts_chart = periodo_counts[periodo_counts['Periodo'].isin(sorted_selected_periods)]

            with col_chart_periodo:
                # El gráfico usará 'sorted_selected_periods' para el eje X
                line_periodo = alt.Chart(periodo_counts_chart).mark_line(point=True).encode(
                    x=alt.X('Periodo', sort=sorted_selected_periods, title='Periodo'),
                    y=alt.Y('Cantidad', title='Cantidad Total de Empleados', scale=alt.Scale(zero=False)),
                    tooltip=['Periodo', alt.Tooltip('Cantidad', format=',.0f')]
                )
                text_periodo = line_periodo.mark_text(align='center', baseline='bottom', dy=-10, color='black').encode(text='Cantidad:Q')
                st.altair_chart((line_periodo + text_periodo), use_container_width=True)
            with col_table_periodo:
                st.dataframe(periodo_counts.style.format({"Cantidad": format_integer_es}))
                generate_download_buttons(periodo_counts, 'dotacion_total_por_periodo', key_suffix="_resumen1")

            st.markdown('---')
            st.subheader('Distribución Comparativa por Sexo')
            col_table_sexo, col_chart_sexo = st.columns([1, 2])

            # --- MODIFICADO (PUNTO 1): Usar 'sorted_selected_periods' para el reindex ---
            # El pivoteo y reindexación con 'sorted_selected_periods' asegura el orden cronológico
            sexo_pivot = filtered_df.groupby(['Periodo', 'Sexo']).size().unstack(fill_value=0).reindex(sorted_selected_periods, fill_value=0).reset_index()

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

                    # --- MODIFICADO (PUNTO 1): Usar 'sorted_selected_periods' para el eje X ---
                    fig_sexo.update_xaxes(categoryorder='array', categoryarray=sorted_selected_periods)

                    fig_sexo.update_layout(title_text="Distribución Comparativa por Sexo", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                    st.plotly_chart(fig_sexo, use_container_width=True, key="sexo_chart")
            with col_table_sexo:
                sexo_pivot['Total'] = sexo_pivot.get('Masculino', 0) + sexo_pivot.get('Femenino', 0)
                st.dataframe(sexo_pivot.style.format(formatter=format_integer_es, subset=[c for c in ['Masculino', 'Femenino', 'Total'] if c in sexo_pivot.columns]))
                generate_download_buttons(sexo_pivot, 'distribucion_sexo_por_periodo', key_suffix="_resumen2")

            st.markdown('---')
            st.subheader('Distribución Comparativa por Relación')
            col_table_rel, col_chart_rel = st.columns([1, 2])

            # --- MODIFICADO (PUNTO 1): Usar 'sorted_selected_periods' para el reindex ---
            rel_pivot = filtered_df.groupby(['Periodo', 'Relación']).size().unstack(fill_value=0).reindex(sorted_selected_periods, fill_value=0).reset_index()

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

                    # --- MODIFICADO (PUNTO 1): Usar 'sorted_selected_periods' para el eje X ---
                    fig_rel.update_xaxes(categoryorder='array', categoryarray=sorted_selected_periods)

                    fig_rel.update_layout(title_text="Distribución Comparativa por Relación", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                    st.plotly_chart(fig_rel, use_container_width=True, key="rel_chart")
            with col_table_rel:
                rel_pivot['Total'] = rel_pivot.get('Convenio', 0) + rel_pivot.get('FC', 0)
                st.dataframe(rel_pivot.style.format(formatter=format_integer_es, subset=[c for c in ['Convenio', 'FC', 'Total'] if c in rel_pivot.columns]))
                generate_download_buttons(rel_pivot, 'distribucion_relacion_por_periodo', key_suffix="_resumen3")

            st.markdown('---')
            st.subheader('Variación Mensual de Dotación')
            col_table_var, col_chart_var = st.columns([1, 2])

            # --- MODIFICADO (PUNTO 1): Usar 'sorted_selected_periods' para el reindex ---
            # Primero obtenemos todos los datos para los cálculos
            var_counts_full = filtered_df.groupby('Periodo').size().reindex(all_periodos_sorted, fill_value=0).reset_index(name='Cantidad_Actual')
            var_counts_full['Variacion_Cantidad'] = var_counts_full['Cantidad_Actual'].diff()
            var_counts_full['Variacion_%'] = (var_counts_full['Variacion_Cantidad'] / var_counts_full['Cantidad_Actual'].shift(1) * 100).replace([np.inf, -np.inf], 0)

            # Filtramos solo los seleccionados para la tabla y el gráfico
            var_counts = var_counts_full[var_counts_full['Periodo'].isin(sorted_selected_periods)]
            var_counts['label'] = var_counts.apply(lambda r: f"{format_integer_es(r['Variacion_Cantidad'])} ({format_percentage_es(r['Variacion_%'], 2)})" if pd.notna(r['Variacion_Cantidad']) and r.name > 0 else "", axis=1)

            with col_table_var:
                st.dataframe(var_counts.style.format({"Cantidad_Actual": format_integer_es, "Variacion_Cantidad": format_integer_es, "Variacion_%": lambda x: format_percentage_es(x, 2)}))
                generate_download_buttons(var_counts, 'variacion_mensual_total', key_suffix="_resumen4")
            with col_chart_var:

                # --- MODIFICADO (PUNTO 1): Usar 'sorted_selected_periods' para el eje X ---
                chart_var = alt.Chart(var_counts.iloc[1:]).mark_bar().encode(
                    x=alt.X('Periodo', sort=sorted_selected_periods),
                    y=alt.Y('Variacion_Cantidad', title='Variación'),
                    color=alt.condition(alt.datum.Variacion_Cantidad > 0, alt.value("green"), alt.value("red")),
                    tooltip=['Periodo', 'Variacion_Cantidad', alt.Tooltip('Variacion_%', format='.2f')]
                )
                text_var = chart_var.mark_text(align='center', baseline='middle', dy=alt.expr("datum.Variacion_Cantidad > 0 ? -10 : 15"), color='white').encode(text='label:N')
                st.altair_chart(chart_var + text_var, use_container_width=True)

    # --- INICIO: SOLAPA SIPAF (MODIFICADA) ---
    with tab_sipaf:
        st.header("Análisis Comparativo de Dotación (SIPAF)")
        
        # --- INICIO MODIFICACIÓN: Definir columnas de análisis aquí ---
        # Definir columnas de detalle y de comparación
        detail_cols = ['LEGAJO', 'Apellido y Nombre', 'Periodo', 'Nivel', 'Subnivel', 'CECO', 'Gerencia', 'Ministerio', 'Distrito', 'Función']
        compare_cols = ['Nivel', 'Subnivel'] # Columnas que si cambian, marcan una modificación

        # Asegurarnos que solo tomamos las columnas que existen en el DF
        detail_cols_existentes = [col for col in detail_cols if col in filtered_df.columns]
        compare_cols_existentes = [col for col in compare_cols if col in filtered_df.columns]
        # --- FIN MODIFICACIÓN ---

        if filtered_df.empty or len(sorted_selected_periods) < 1:
            st.warning("No hay datos para mostrar con los filtros seleccionados. Por favor, ajuste los filtros en la barra lateral.")
        elif len(sorted_selected_periods) < 2:
            st.info("Por favor, seleccione al menos dos períodos en la barra lateral para poder comparar.")
  D        else:
            # Controles de selección de período
            st.subheader("Selección de Períodos a Comparar (A vs B)")
            col_sel_1, col_sel_2 = st.columns(2)
            with col_sel_1:
                periodo_actual_sipaf = st.selectbox(
                    "Seleccionar Período Principal (A):",
                    sorted_selected_periods,
                    index=len(sorted_selected_periods)-1, # Default: último período
                    key="sipaf_periodo_actual"
                )
            with col_sel_2:
                periodo_previo_sipaf = st.selectbox(
                    "Seleccionar Período de Comparación (B):",
                    sorted_selected_periods,
                    index=len(sorted_selected_periods)-2, # Default: anteúltimo período
                    key="sipaf_periodo_previo"
                )

            # Selector de Categoría
            st.subheader("Desglose por Categoría")
            # --- MODIFICADO REQ 1: Selector Múltiple ---
            categorias_sipaf = st.multiselect(
                "Seleccionar categorías para el desglose (el orden importa):",
                options=["Ministerio", "Gerencia", "Función", "Nivel", "Subnivel"],
                default=["Ministerio", "Nivel", "Subnivel"], # Default como la imagen
                key="sipaf_categorias"
            )
            st.markdown("---")

            if not categorias_sipaf:
                st.warning("Por favor, seleccione al menos una categoría para el desglose.")
            else:
                # Data Processing
                # --- INICIO MODIFICACIÓN: Usar filtered_df para el análisis de legajos ---
                df_actual_raw = filtered_df[filtered_df['Periodo'] == periodo_actual_sipaf]
                df_previo_raw = filtered_df[filtered_df['Periodo'] == periodo_previo_sipaf]
                # --- FIN MODIFICACIÓN ---

                # Renombrar columnas para claridad en la tabla final
                col_actual = f"Dotación {periodo_actual_sipaf} (A)"
                col_previo = f"Dotación {periodo_previo_sipaf} (B)"
                col_var = 'Variaciones (A - B)'

                actual_counts = df_actual_raw.groupby(categorias_sipaf).size().rename(col_actual)
                previo_counts = df_previo_raw.groupby(categorias_sipaf).size().rename(col_previo)

                # Combinar los dos dataframes
                df_comparativo = pd.concat([actual_counts, previo_counts], axis=1).fillna(0).astype(int)

                # Calcular Variaciones
                df_comparativo[col_var] = df_comparativo[col_actual] - df_comparativo[col_previo]

                # Ordenar por el período actual
                df_comparativo = df_comparativo.sort_values(by=categorias_sipaf)

                # --- INICIO: NUEVA LÓGICA DE SUBTOTALES (REQ 1) ---
                df_display_list = []

                # Columnas de agrupación (ej: Función, Nivel, Subnivel)
                group_cols = df_comparativo.index.names

                # Nivel principal de agrupación (ej: Función)
                main_group_col = group_cols[0]

                # Iterar por cada grupo principal (ej: 'Personal administrativo', 'Personal operativo')
                for main_group_name, df_main_group in df_comparativo.groupby(level=0):

                    # 1. Crear y añadir la fila de SUBTOTAL para este grupo
                    subtotal = df_main_group.sum()
                    subtotal_row = {
                        main_group_col: f"**{main_group_name}**",
                        col_actual: subtotal[col_actual],
                        col_previo: subtotal[col_previo],
                        col_var: subtotal[col_var]
                    }
                    # Rellenar otras columnas de agrupación con ''
                    for col in group_cols[1:]:
                        subtotal_row[col] = ''
                    df_display_list.append(subtotal_row)

                    # 2. Añadir las filas de DETALLE para este grupo
                    df_detail_reset = df_main_group.reset_index()
                    for _, detail_row in df_detail_reset.iterrows():
                        detail_dict = detail_row.to_dict()
                        # "Indentar" visualmente borrando el nombre del grupo principal
                        detail_dict[main_group_col] = ''
                        df_display_list.append(detail_dict)

                # 3. Crear el DataFrame final
                df_display = pd.DataFrame(df_display_list)

                # 4. Añadir Fila de TOTAL GENERAL
                total_actual = df_comparativo[col_actual].sum()
                total_previo = df_comparativo[col_previo].sum()
                total_variacion = df_comparativo[col_var].sum()

                total_row_data = {
                    main_group_col: ['**TOTAL GENERAL**'],
                    col_actual: [total_actual],
                    col_previo: [total_previo],
                    col_var: [total_variacion]
                }
                for col in group_cols[1:]:
                    total_row_data[col] = ['']

                total_row_df = pd.DataFrame(total_row_data)

                df_display = pd.concat([df_display, total_row_df], ignore_index=True)

                # Reordenar columnas para que las de agrupación estén primero
                ordered_cols = list(group_cols) + [col_actual, col_previo, col_var]
                df_display = df_display[ordered_cols]
                # --- FIN: NUEVA LÓGICA DE SUBTOTALES ---

                # Mostrar la tabla
                st.subheader(f"Comparativa por: {', '.join(categorias_sipaf)}")

                # Formatear columnas numéricas
                format_dict = {
                    col_actual: format_integer_es,
                    col_previo: format_integer_es,
                    col_var: format_integer_es
                }

                st.dataframe(
                    df_display.style.format(format_dict),
                    use_container_width=True,
                    hide_index=True # Ocultar el índice numérico
                )

                # Botones de descarga (usar el df comparativo original, reseteado)
                download_filename = f'comparativa_sipaf_{"_".join(categorias_sipaf)}_{periodo_actual_sipaf}_vs_{periodo_previo_sipaf}'
                generate_download_buttons(
                    df_comparativo.reset_index(), # Descargar los datos crudos, sin subtotales
                    download_filename,
                    key_suffix="_sipaf"
                )

                # --- INICIO: SECCIÓN DE ANÁLISIS DE VARIACIONES (MODIFICADA) ---
                st.markdown("---")
                st.subheader(f"Análisis de Variaciones de Legajos: {periodo_actual_sipaf} vs. {periodo_previo_sipaf}")

                # --- INICIO MODIFICACIÓN: Llamar a la función helper ---
                df_ingresos, df_egresos, df_cambios, df_cambios_final, df_variaciones_total = get_legajo_variations(
                    filtered_df, 
                    periodo_actual_sipaf, 
                    periodo_previo_sipaf, 
                    detail_cols_existentes, 
                    compare_cols_existentes
section
                )
                # --- FIN MODIFICACIÓN: El bloque de ~60 líneas fue reemplazado ---


                # --- INICIO: NUEVO (REQ 1) - Preparar datos para el gráfico ---
                # Renombrar "Cambios" a "Nivelaciones" (REQ 2)
                chart_data = {
                    'Tipo': ['Ingresos', 'Egresos', 'Nivelaciones'],
                    'Cantidad': [len(df_ingresos), len(df_egresos), len(df_cambios)]
                }
                df_chart = pd.DataFrame(chart_data).query('Cantidad > 0') # Solo mostrar si hay datos
                # --- FIN: NUEVO (REQ 1) ---
                
                # (El código de df_cambios_final y df_variaciones_total ahora está dentro de la función)

                # Formatear Legajo para visualización
                df_display_variaciones = df_variaciones_total.copy()
                if 'LEGAJO' in df_display_variaciones.columns:
                    df_display_variaciones['LEGAJO'] = df_display_variaciones['LEGAJO'].apply(
                        lambda x: format_integer_es(int(x)) if (pd.notna(x) and x != 'no disponible' and str(x).isdigit()) else ('' if x=='no disponible' else x)
                    )
                # --- INICIO: MODIFICACIÓN (REQ 1) - Añadir gráfico y columnas ---
                col_chart_var, col_table_var = st.columns(2)

                with col_chart_var:
                    if not df_chart.empty:
                        fig_donut = px.pie(
                            df_chart, 
                            names='Tipo', 
                            values='Cantidad', 
                            title=f'Composición de la Variación ({df_chart["Cantidad"].sum()} legajos)', 
                            hole=0.4, # Esto lo hace un gráfico de anillo
                            color_discrete_map={ # Asignar colores fijos
                                'Ingresos': '#28a745', # verde
                                'Egresos': '#dc3545',  # rojo
                                'Nivelaciones': '#007bff' # azul
s/d
                            }
                        )
                        fig_donut.update_traces(
                            textinfo='percent+label+value', 
                            textposition='outside',
                            pull=[0.05 if t == 'Ingresos' or t == 'Egresos' else 0 for t in df_chart['Tipo']] # Destacar
                        )
                        fig_donut.update_layout(legend_title_text='Tipo de Variación')
                        st.plotly_chart(fig_donut, use_container_width=True)
                    else:
                        st.info("No se encontraron variaciones de legajos (Ingresos, Egresos o Nivelaciones) entre los períodos seleccionados.")

                with col_table_var:
                    st.dataframe(df_display_variaciones, use_container_width=True, height=400, hide_index=True)
                    
                    generate_download_buttons(
                        df_variaciones_total, # Descargar el DF sin formato de legajo
                        f'detalle_variaciones_sipaf_{periodo_actual_sipaf}_vs_{periodo_previo_sipaf}',
                        key_suffix="_sipaf_variaciones"
                    )
                # --- FIN: SECCIÓN DE ANÁLISIS DE VARIACIONES (MODIFICADA) ---
            
            # --- INICIO: NUEVA SECCIÓN DE EVOLUCIÓN MENSUAL ---
            st.markdown("---")
            st.subheader("Análisis de Evolución Mensual (desde Dic-23)")
            
            start_period = "Dic-23"
            month_to_month_periods = []
            
            # Usamos 'sorted_selected_periods' que ya respeta los filtros del sidebar
            if start_period in sorted_selected_periods:
                start_index = sorted_selected_periods.index(start_period)
                month_to_month_periods = sorted_selected_periods[start_index:]
            
            if len(month_to_month_periods) < 2:
                st.warning(f"No hay suficientes datos de períodos (desde {start_period}) seleccionados en el filtro lateral para mostrar la evolución mensual.")
            else:
                # --- INICIO: REFACTORIZACIÓN (MODIFICACIÓN SOLICITADA) ---
                # 1. Mover el multiselect de categorías aquí arriba
                categorias_evolucion = st.multiselect(
                    "Seleccionar categorías para el desglose de la planta (el orden importa):",
                    options=["Ministerio", "Gerencia", "Función", "Nivel", "Subnivel"],
                    default=["Ministerio", "Nivel", "Subnivel"], # Mismo default que A vs B
                    key="sipaf_categorias_evolucion" # Nueva key
                )
                
                if not categorias_evolucion:
                    st.warning("Por favor, seleccione al menos una categoría para el desglose de la planta.")
                else:
                    # 2. Calcular el df_planta_pivot UNA VEZ
                    df_planta_pivot = None
                    try:
                        with st.spinner("Calculando datos base de planta..."):
                            df_planta_raw = filtered_df[filtered_df['Periodo'].isin(month_to_month_periods)]
                            df_planta_pivot = pd.pivot_table(
                                df_planta_raw,
                                index=categorias_evolucion,
                                columns='Periodo',
                                aggfunc='size',
                                fill_value=0
  _fin
                            )
                            # Reordenar columnas cronológicamente
                            df_planta_pivot = df_planta_pivot.reindex(columns=month_to_month_periods, fill_value=0)
                    except Exception as e:
                        st.error(f"Ocurrió un error al generar la grilla de planta de cargos: {e}")
                        st.info("Intente seleccionar menos categorías o verifique los datos.")
                        st.stop() # Detener si la tabla base falla
                    
                    # 3. SECCIÓN: "Planta de Cargos Mes a Mes" (Usa df_planta_pivot)
                    st.markdown("---") # Separador
                    st.markdown("##### Planta de Cargos Mes a Mes")

                    with st.spinner("Generando grilla de planta de cargos..."):
                        # Lógica de Subtotales (adaptada de "A vs B")
                        df_display_list = []
                        group_cols = df_planta_pivot.index.names
                        main_group_col = group_cols[0]
                        period_cols = list(month_to_month_periods) # Columnas de datos

                        for main_group_name, df_main_group in df_planta_pivot.groupby(level=0):
                            # Fila de Subtotal
                            subtotal_row = {}
                            subtotal_row[main_group_col] = f"**{main_group_name}**"
                            for col in group_cols[1:]: # Rellenar cols de categoría
                                subtotal_row[col] = ''
                            
                            subtotal_data = df_main_group.sum() # Suma todas las columnas de período
                            for p_col in period_cols: # Rellenar cols de período
                                if p_col in subtotal_data:
	
                                    subtotal_row[p_col] = subtotal_data[p_col]
                                else:
                                    subtotal_row[p_col] = 0 # Asegurar que la columna existe
                            df_display_list.append(subtotal_row)

                            # Filas de Detalle
                            df_detail_reset = df_main_group.reset_index()
                            for _, detail_row in df_detail_reset.iterrows():
                                detail_dict = detail_row.to_dict()
          S                         detail_dict[main_group_col] = '' # Indentar
                                df_display_list.append(detail_dict)

                        # DataFrame final y Fila de Total
                        df_display_planta = pd.DataFrame(df_display_list)
                        
                        total_row_data = {}
                        total_row_data[main_group_col] = ['**TOTAL GENERAL**']
                        for col in group_cols[1:]:
                            total_row_data[col] = ['']
                        
                        total_general_data = df_planta_pivot.sum() # Suma total
                        for p_col in period_cols:
                            if p_col in total_general_data:
                                total_row_data[p_col] = [total_general_data[p_col]]
                            else:
                                total_row_data[p_col] = [0] # Asegurar que la columna existe
	
                        
                        total_row_df = pd.DataFrame(total_row_data)
                        df_display_planta = pd.concat([df_display_planta, total_row_df], ignore_index=True)

                        # Ordenar columnas y mostrar
                        ordered_cols = list(group_cols) + period_cols
                        # Asegurarse que todas las columnas existan en el df final
                    	
                        ordered_cols_existentes = [c for c in ordered_cols if c in df_display_planta.columns]
                        df_display_planta = df_display_planta[ordered_cols_existentes]
                        
                        format_dict = {p_col: format_integer_es for p_col in period_cols}
                        
                        st.dataframe(
                            df_display_planta.style.format(format_dict),
                            use_container_width=True,
                            hide_index=True
                  S     )
                        
                        # Botón de Descarga
                        generate_download_buttons(
                            df_planta_pivot.reset_index(), # Descargar datos pivoteados (sin subtotales)
                            'planta_cargos_mes_a_mes',
                            key_suffix="_sipaf_planta_evolucion"
                        )
                
                    # --- FIN SECCIÓN "Planta de Cargos Mes a Mes" ---

                    # --- INICIO: SECCIÓN REEMPLAZADA (Evolución de Legajos) ---
                    # Esta sección ahora analiza la *Planta de Cargos* (df_planta_pivot)
section
                    st.markdown("---") 
                    st.markdown("##### Análisis de Variaciones de Planta de Cargos (Mensual)")
                    
                    evolution_data_planta = []
                    period_cols = list(month_to_month_periods) # Ya la teníamos de antes
                    
                    with st.spinner(f"Calculando evolución de planta mes a mes desde {start_period}..."a):
                        for i in range(1, len(period_cols)):
                            p_actual = period_cols[i]
                            p_previo = period_cols[i-1]
                            
                            # Comparar las dos series (columnas) del pivot
                            series_actual = df_planta_pivot[p_actual]
                        	
                            series_previo = df_planta_pivot[p_previo]
                            
                            # Combinar en un DF temporal
                            df_comp = pd.DataFrame({'Actual': series_actual, 'Previo': series_previo})
                            
                            # Ingresos: 0 en Previo, > 0 en Actual
                            ingresos_planta = df_comp[(df_comp['Previo'] == 0) & (df_comp['Actual'] > 0)]['Actual'].count()
                            
                    	
                            # Egresos: > 0 in Previo, 0 en Actual
                            egresos_planta = df_comp[(df_comp['Previo'] > 0) & (df_comp['Actual'] == 0)]['Previo'].count()
S
                            # Cambios: > 0 en ambos, pero valores diferentes (cambio en el headcount)
                            cambios_planta_df = df_comp[
                                (df_comp['Previo'] > 0) & (df_comp['Actual'] > 0) & (df_comp['Actual'] != df_comp['Previo'])
                      	
                            ]
                            modificados_planta = len(cambios_planta_df)
                            
                            # Dotación (Total de cargos/puestos activos)
                      	
                            dotacion_planta = df_comp[df_comp['Actual'] > 0]['Actual'].count()
                            
                            evolution_data_planta.append({
                          	
                                "Periodo": p_actual,
                                "Dotación Planta": dotacion_planta,
                                "Nuevos Cargos": ingresos_planta,
                            	
                                "Cargos Eliminados": egresos_planta,
                                "Cargos Modificados": modificados_planta,
                            	
                                "Var. Neta (N-E)": ingresos_planta - egresos_planta
                        	
                            })
                    
                    if not evolution_data_planta:
                    	
                        st.info("No se generaron datos de evolución de planta.")
                    	
                    else:
                    	
                        df_evolution_planta = pd.DataFrame(evolution_data_planta)
                    	
                        # --- Mostrar Gráfico y Tabla ---
                    	
                        col_evo_chart, col_evo_table = st.columns([2, 1])
                    	
                        with col_evo_chart:
                    	
                            st.markdown("##### Gráfico de Evolución de Planta de Cargos")
                    	
                            fig_evo_planta = make_subplots(specs=[[{"secondary_y": True}]])
                    	
                            # Eje 1: Dotación Planta
section
                            fig_evo_planta.add_trace(go.Bar(
                    	
                                x=df_evolution_planta['Periodo'], 
                    	
                                y=df_evolution_planta['Dotación Planta'], 
                    	
                                name='Dotación Planta (Cargos)',
                    	
                                marker_color='#5b9bd5',
                    	
                                text=df_evolution_planta['Dotación Planta'],
                    	
                                textposition='outside'
                    	
                            ), secondary_y=False)
                    	
                            # Eje 2: Variaciones de Planta
                    	
                            fig_evo_planta.add_trace(go.Scatter(
                    	
                                x=df_evolution_planta['Periodo'], 
                    	
                                y=df_evolution_planta['Nuevos Cargos'], 
                    	
                                name='Nuevos Cargos', 
                    	
                                mode='lines+markers', 
                    	
                                line=dict(color='#28a745')
            S         	
                            ), secondary_y=True)
                    	
                            fig_evo_planta.add_trace(go.Scatter(
                    	
                                x=df_evolution_planta['Periodo'], 
                    	
                            	
                                y=df_evolution_planta['Cargos Eliminados'], 
                    	
                            	
                                name='Cargos Eliminados', 
                    	
                            	
          S                         mode='lines+markers', 
                    	
                            	
                                line=dict(color='#dc3545')
            	
                            ), secondary_y=True)

    	
                            fig_evo_planta.add_trace(go.Scatter(
                    	
                                x=df_evolution_planta['Periodo'], 
            	
                                y=df_evolution_planta['Cargos Modificados'], 
            	
                            	
                                name='Cargos Modificados', 
            	
                            	
                                mode='lines+markers', 
          	
                            	
                                line=dict(color='#007bff', dash='dot')
            	
                            ), secondary_y=True)

    	
                            # Ajustar Eje Y (Dotación Planta)
          	
                            try:
              	
                                min_v, max_v = df_evolution_planta['Dotación Planta'].min(), df_evolution_planta['Dotación Planta'].max()
          	
                            	
                                rng = max_v - min_v
            	
                                pad = max(1, rng * 0.1) if rng > 0 else max(1, abs(min_v * 0.1))
            	
                            	
                                fig_evo_planta.update_yaxes(
section
              	
                                    title_text="Dotación Planta (Cargos)", 
              	
                            	
                                    range=[min_v - pad, max_v + pad * 1.5], 
            	
                            	
                                    secondary_y=False, 
          	
                            	
                    S                 showgrid=False
              	
                            	
                  S             )
          	
                            except: # Fallback si hay datos vacíos
      	
                                fig_evo_planta.update_yaxes(title_text="Dotación Planta (Cargos)", secondary_y=False, showgrid=False)
          	
                            
      	
                            # Ajustar Eje Y (Variaciones)
      	
                            fig_evo_planta.update_yaxes(
      	
                                title_text="Variaciones de Cargos", 
      	
                                secondary_y=True, 
  	
                                showgrid=True
      	
                            )

  	
                            fig_evo_planta.update_xaxes(
      	
                                categoryorder='array', 
    	
        _fin
                                categoryarray=df_evolution_planta['Periodo']
      	
                            )
      	
                            fig_evo_planta.update_layout(
      	
                                title_text="Evolución Mensual de Planta de Cargos vs. Variaciones",s/d
      	
                            	
                                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
aS
                    	
                            	
                                height=500,
        	
                            	
                                hovermode="x unified"
      	
                            )
      	
                            st.plotly_chart(fig_evo_planta, use_container_width=True)

      	
                        with col_evo_table:
      	
                            st.markdown("##### Resumen de Evolución de Planta")
      	
                        	
                            df_display_evo_planta = df_evolution_planta.set_index("Periodo")
        	
                        	
                            st.dataframe(
      	
                                df_display_evo_planta.style.format(
      	
                              </i>
                                    "Dotación Planta": format_integer_es, 
      	
                            	
                                    "Nuevos Cargos": format_integer_es, 
      	
                            	
                                    "Cargos Eliminados": format_integer_es, 
      	
                            	
                                    "Cargos Modificados": format_integer_es, 
      	
                            	
                                    "Var. Neta (N-E)": format_integer_es
      	
                            	
                                }
      	
                            ),
      	
                                height=500
aS
                    	
                            )
      	
                            generate_download_buttons(
      	
    	
                                df_evolution_planta, 
      	
                            	
                                'evolucion_planta_cargos_sipaf', 
      	
                            	
                                key_suffix="_sipaf_evolucion_planta"
      	
                        	
        S                     )
section
                    # --- FIN: SECCIÓN REEMPLAZADA ---
            # --- FIN: REFACTORIZACIÓN (MODIFICACIÓN SOLICITADA) ---


    # --- FIN: SOLAPA SIPAF (MODIFICADA) ---
    # --- FIN: SOLAPA SIPAF (MODIFICADA) ---

    # --- INICIO: CORRECCIÓN LÓGICA DE SOLAPAS (REQ 2) ---
    # El código de las solapas de mapa ahora se comprueba y se ejecuta DESPUÉS de SIPAF
    if tab_map_comparador and period_to_display:
    # --- FIN: CORRECCIÓN LÓGICA DE SOLAPAS (REQ 2) ---
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

            show_map_comparison = st.checkbox("✅ Mostrar Comparación de Mapas", value=st.session_state.get('show_map_comp_check', False), key="show_map_comp_check")

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

            if show_map_comparison:
                df_mapa_display = filtered_df[filtered_df['Periodo'] == period_to_display]

                if 'Distrito' not in df_mapa_display.columns or 'Distrito' not in df_coords.columns:
                    st.warning("La columna 'Distrito' no se encuentra en los datos o en el archivo de coordenadas.")
                else:
                    comp_col1, comp_col2 = st.columns([3, 2])
                    with comp_col1:
                        # 1. Abrimos el div con la nueva clase
                        #st.markdown('<div class="map-comparator-container">', unsafe_allow_html=True)
                        with st.spinner(f"Generando mapas ({style1_name} vs {style2_name})..."):
                            try:
                                fig1 = generate_map_figure(df_mapa_display, map_style_options[style1_name])
                                fig2 = generate_map_figure(df_mapa_display, map_style_options[style2_name])
                                if fig1 and fig2:
                                    img1_bytes = fig1.to_image(format="png", scale=2, engine="kaleido")
                                    img2_bytes = fig2.to_image(format="png", scale=2, engine="kaleido")

                                    # Ya no convertimos a RGBA
                                    img1_pil = Image.open(io.BytesIO(img1_bytes))
                                    img2_pil = Image.open(io.BytesIO(img2_bytes))

                                    # --- Usamos la nueva función ---
                                    radius = 30
                                    img1_final = create_rounded_image_with_matte(img1_pil, radius)
                                    img2_final = create_rounded_image_with_matte(img2_pil, radius)
                                    # -----------------------------

                                    image_comparison(
                                        img1=img1_final, # Usamos la nueva imagen final
                                        img2=img2_final, # Usamos la nueva imagen final
                                        label1=style1_name,
                                        label2=style2_name,
                                    )
                                else:
                                    st.warning("No hay datos de ubicación para mostrar en el mapa para el período seleccionado.")
                            except Exception as e:
                                st.error(f"Ocurrió un error al generar las imágenes del mapa: {e}")
                                st.info("Intente recargar la página o seleccionar un período con menos datos.")
                        # 2. Cerramos el div
                        #st.markdown('</div>', unsafe_allow_html=True)
                    with comp_col2:
                            pivot_table = pd.pivot_table(data=df_mapa_display, index='Distrito', columns='Relación', aggfunc='size', fill_value=0)
                            if 'Convenio' not in pivot_table.columns: pivot_table['Convenio'] = 0
                            if 'FC' not in pivot_table.columns: pivot_table['FC'] = 0
                            pivot_table['Total'] = pivot_table['Convenio'] + pivot_table['FC']
                            pivot_table.sort_values(by='Total', ascending=False, inplace=True)
                            total_row = pd.DataFrame({'Distrito': ['**TOTAL GENERAL**'], 'Convenio': [pivot_table['Convenio'].sum()], 'FC': [pivot_table['FC'].sum()], 'Total': [pivot_table['Total'].sum()]})
                            df_final_table = pd.concat([pivot_table.reset_index(), total_row], ignore_index=True)
                            st.dataframe(df_final_table.style.format({'Convenio': '{:,}', 'FC': '{:,}', 'Total': '{:,}'}).set_properties(**{'text-align': 'right'}), use_container_width=True, height=470, hide_index=True)

            else:
                st.info("Seleccione los estilos de mapa deseados y marque la casilla 'Mostrar Comparación de Mapas' para visualizar y generar la comparación.")

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
                pivot_table = pd.pivot_table(data=df_mapa_display, index='Distrito', columns='Relación', aggfunc='size', fill_value=0)
                if 'Convenio' not in pivot_table.columns: pivot_table['Convenio'] = 0
                if 'FC' not in pivot_table.columns: pivot_table['FC'] = 0
                pivot_table['Total'] = pivot_table['Convenio'] + pivot_table['FC']
                pivot_table.sort_values(by='Total', ascending=False, inplace=True)
                total_row = pd.DataFrame({'Distrito': ['**TOTAL GENERAL**'], 'Convenio': [pivot_table['Convenio'].sum()], 'FC': [pivot_table['FC'].sum()], 'Total': [pivot_table['Total'].sum()]})
                df_final_table = pd.concat([pivot_table.reset_index(), total_row], ignore_index=True)
                st.dataframe(df_final_table.style.format({'Convenio': '{:,}', 'FC': '{:,}', 'Total': '{:,}'}).set_properties(**{'text-align': 'right'}), use_container_width=True, height=455, hide_index=True)

    with tab_edad_antiguedad:
        st.header('Análisis de Edad y Antigüedad por Periodo')
        if filtered_df.empty or not selected_periodos: st.warning("No hay datos para mostrar con los filtros seleccionados.")
        else:
            # 'sorted_selected_periods' ya tiene el orden cronológico correcto
            periodo_a_mostrar_edad = st.selectbox('Selecciona un Periodo:', sorted_selected_periods, index=len(sorted_selected_periods) - 1 if sorted_selected_periods else 0, key='periodo_selector_edad')
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

                # --- AÑADIDO (PUNTO 2): Fila de Total para Edad ---
                try:
                    total_row_edad = edad_table.sum().to_frame().T
                    total_row_edad.index = ['**TOTAL**']
                    edad_table_display = pd.concat([edad_table, total_row_edad])
                except Exception:
                    edad_table_display = edad_table # Fallback por si hay error

                st.dataframe(edad_table_display.style.format(format_integer_es))
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

                # --- AÑADIDO (PUNTO 2): Fila de Total para Antigüedad ---
                try:
                    total_row_ant = antiguedad_table.sum().to_frame().T
                    total_row_ant.index = ['**TOTAL**']
                    antiguedad_table_display = pd.concat([antiguedad_table, total_row_ant])
                except Exception:
                    antiguedad_table_display = antiguedad_table # Fallback

                st.dataframe(antiguedad_table_display.style.format(format_integer_es))
                generate_download_buttons(antiguedad_table.reset_index(), f'distribucion_antiguedad_{periodo_a_mostrar_edad}', key_suffix="_antiguedad")

    # --- INICIO: MODIFICACIÓN SOLAPA DESGLOSE (REQ 1) ---
    with tab_desglose:
        st.header('Desglose Detallado por Categoría por Periodo')
        if filtered_df.empty or not selected_periodos:
            st.warning("No hay datos para mostrar.")
        else:
            periodo_a_mostrar_desglose = st.selectbox(
                'Seleccionar Periodo:',
                sorted_selected_periods,
                index=len(sorted_selected_periods) - 1 if sorted_selected_periods else 0,
                key='periodo_selector_desglose'
            )

            df_periodo_desglose = filtered_df[filtered_df['Periodo'] == periodo_a_mostrar_desglose]

            # --- INICIO REQ 1: Checkbox para cambiar vista ---
            vista_jerarquica = st.checkbox("Mostrar vista jerárquica (Treemap)", value=True, key="desglose_vista_toggle")
            st.markdown("---")

            if vista_jerarquica:
                # --- VISTA JERÁRQUICA (TREEMAP) ---
                opciones_desglose_jerarq = ['Ministerio', 'Gerencia', 'Función', 'Nivel']
                cat_seleccionada = st.selectbox('Seleccionar Categoría Principal:', opciones_desglose_jerarq, key='cat_selector_desglose_jerarq')

                st.subheader(f'Desglose Jerárquico para {periodo_a_mostrar_desglose}')
                col_chart_cat, col_table_cat = st.columns([2, 1])

                with col_chart_cat:
                    # Definir dinámicamente el path para evitar duplicados
                    if cat_seleccionada == 'Nivel':
                        path_jerarquico = ['Nivel', 'Subnivel']
                        st.markdown(f"##### Treemap por: Nivel -> Subnivel")
                    else:
                        path_jerarquico = [cat_seleccionada, 'Nivel', 'Subnivel']
                        st.markdown(f"##### Treemap por: {cat_seleccionada} -> Nivel -> Subnivel")

                    # Preparar datos para el treemap
                    df_treemap = df_periodo_desglose.groupby(path_jerarquico).size().reset_index(name='Cantidad')
                    df_treemap = df_treemap.dropna(subset=path_jerarquico)

                    if df_treemap.empty:
                        st.warning(f"No hay datos para construir el treemap con la jerarquía: {' -> '.join(path_jerarquico)}.")
                    else:
                        path_treemap = [px.Constant(f"Total {periodo_a_mostrar_desglose}")] + path_jerarquico

                        # Crear el Treemap
                        fig_treemap = px.treemap(
                            df_treemap,
                            path=path_treemap, # Usar el path dinámico
                            values='Cantidad',
                            title=f"Jerarquía de Dotación por {cat_seleccionada}",
                            color=cat_seleccionada, # Colorear por la categoría principal
                            hover_data={'Cantidad': True} # Mostrar cantidad en hover
                        )

                        fig_treemap.update_traces(
                            textinfo="label+value+percent entry",
                            textfont=dict(size=12)
                        )
                        fig_treemap.update_layout(
                            margin = dict(t=50, l=10, r=10, b=10), # Ajustar márgenes
                            height=600 # Darle una altura fija
                        )
                        st.plotly_chart(fig_treemap, use_container_width=True)

                with col_table_cat:
                    st.markdown("##### Datos Agrupados (Jerarquía)")
                    table_data = df_treemap.sort_values('Cantidad', ascending=False)

                    try:
                        # Crear fila de total dinámicamente
                        total_row_data = {'Cantidad': [table_data['Cantidad'].sum()]}
                        for i, col in enumerate(path_jerarquico):
                            total_row_data[col] = ['**TOTAL**' if i == 0 else '-']

                        total_row_desglose = pd.DataFrame(total_row_data)

                        table_data_display = pd.concat([table_data, total_row_desglose], ignore_index=True)
                    except Exception:
                        table_data_display = table_data # Fallback

                    st.dataframe(
                        table_data_display.style.format({"Cantidad": format_integer_es}),
                        height=600 # Misma altura que el gráfico
                    )
                    generate_download_buttons(
                        table_data,
                        f'dotacion_jerarquia_{cat_seleccionada.lower()}_{periodo_a_mostrar_desglose}',
                        key_suffix="_desglose_v2_jerarq"
                    )

            else:
                # --- VISTA SIMPLE (GRÁFICO DE BARRAS) ---
                opciones_desglose_simple = ['Gerencia', 'Ministerio', 'Función', 'Distrito', 'Nivel']
                cat_seleccionada = st.selectbox('Seleccionar Categoría:', opciones_desglose_simple, key='cat_selector_desglose_simple')

                st.subheader(f'Dotación por {cat_seleccionada} para {periodo_a_mostrar_desglose}')
                col_table_cat, col_chart_cat = st.columns([1, 2])

                with col_chart_cat:
                    chart = alt.Chart(df_periodo_desglose).mark_bar().encode(
                        x=alt.X(f'{cat_seleccionada}:N', sort='-y'),
                        y=alt.Y('count():Q', title='Cantidad'),
                        color=f'{cat_seleccionada}:N',
                        tooltip=[alt.Tooltip('count()', format=',.0f'), cat_seleccionada]
                    )
                    text_labels = chart.mark_text(align='center', baseline='middle', dy=-10).encode(text='count():Q')
                    st.altair_chart(chart + text_labels, use_container_width=True)

                with col_table_cat:
                    table_data = df_periodo_desglose.groupby(cat_seleccionada).size().reset_index(name='Cantidad').sort_values('Cantidad', ascending=False)

                    try:
                        total_row_desglose = pd.DataFrame({cat_seleccionada: ['**TOTAL**'], 'Cantidad': [table_data['Cantidad'].sum()]})
                        table_data_display = pd.concat([table_data, total_row_desglose], ignore_index=True)
                    except Exception:
                        table_data_display = table_data # Fallback

                    st.dataframe(table_data_display.style.format({"Cantidad": format_integer_es}))
                    generate_download_buttons(
                        table_data,
                        f'dotacion_{cat_seleccionada.lower()}_{periodo_a_mostrar_desglose}',
                        key_suffix="_desglose_v2_simple" # Key diferente
                    )
            # --- FIN REQ 1 ---
    # --- FIN: MODIFICACIÓN SOLAPA DESGLOSE (REQ 1) ---


    # --- INICIO: REFACTORIZACIÓN TOTAL DE LA SOLAPA 'Neto Pagado' ---
    with tab_neto_pagado:
        st.header(f"Análisis de Pagos por Período")

        if filtered_df.empty or not selected_periodos:
            st.warning("No hay datos para mostrar con los filtros seleccionados. Por favor, ajuste los filtros en la barra lateral.")
        else:

            # --- INICIO REQ 2: Nuevo Selector de Tipo de Pago ---
            opciones_pago = ["Neto Pagado", "SAC Pagado", "Neto Pagado + SAC Pagado"]
            tipo_pago_seleccionado = st.selectbox(
                "Seleccionar tipo de pago a analizar:",
                opciones_pago,
                key="selector_tipo_pago"
            )

            # --- AÑADIDO: Recordatorio contextual para SAC ---
            if tipo_pago_seleccionado == "SAC Pagado":
                st.info("💡 **Recordatorio:** 'SAC Pagado' generalmente solo contiene valores en los períodos de Junio y Diciembre. Es normal ver $0,00 en otros meses.", icon="💡")
            # --- FIN AÑADIDO ---

            # Mapear la selección a la columna real del DataFrame
            columna_pago_map = {
                "Neto Pagado": "Neto Pagado",
                "SAC Pagado": "SAC Pagado",
                "Neto Pagado + SAC Pagado": "Neto + SAC"
            }
            columna_a_usar = columna_pago_map[tipo_pago_seleccionado]
            # --- FIN REQ 2 ---

            # --- MODIFICACIÓN REQ 1: Cambiar selectbox por multiselect ---
            # Por defecto, selecciona solo el último período de la lista de períodos seleccionados
            default_selection = [sorted_selected_periods[-1]] if sorted_selected_periods else []

            periodos_a_mostrar_neto = st.multiselect(
                'Seleccionar Períodos para Analizar:',
                sorted_selected_periods,
                default=default_selection,
                key='periodo_selector_neto_multi'
            )
            # --- FIN MODIFICACIÓN REQ 1 ---

            # Verificamos que la columna exista
            if columna_a_usar not in filtered_df.columns:
                st.error(f"La columna '{columna_a_usar}' no se encontró en el archivo.")
            else:

                # --- INICIO MODIFICACIÓN REQ 1: Bucle por cada período seleccionado ---
                if not periodos_a_mostrar_neto:
                    st.info("Por favor, seleccione uno o más períodos para analizar.")

                for periodo_actual in periodos_a_mostrar_neto:

                    st.markdown(f"### Análisis de **{tipo_pago_seleccionado}** para **{periodo_actual}**")

                    # --- INICIO REQ 2: Lógica para período anterior (con lógica SAC) ---
                    prev_periodo_str = None
                    try:
                        current_index_in_sidebar = sorted_selected_periods.index(periodo_actual)

                        if tipo_pago_seleccionado == "SAC Pagado":
                            current_month_name = periodo_actual.split('-')[0]
                            # Buscar hacia atrás en la lista de períodos seleccionados
                            target_month = None
                            if 'Jun' in current_month_name: # Flexible a 'Jun' o 'Junio'
                                target_month = 'Dic'
                            elif 'Dic' in current_month_name: # Flexible a 'Dic' o 'Diciembre'
                                target_month = 'Jun'

                            if target_month:
                                # Iterar hacia atrás desde la posición actual
                                for i in range(current_index_in_sidebar - 1, -1, -1):
                                    periodo_candidato = sorted_selected_periods[i]
                                    if periodo_candidato.startswith(target_month):
                                        prev_periodo_str = periodo_candidato
                                        break # Encontramos el SAC anterior más cercano

                        else: # Lógica original para Neto Pagado y Neto + SAC
                            if current_index_in_sidebar > 0:
                                prev_periodo_str = sorted_selected_periods[current_index_in_sidebar - 1]

                    except ValueError:
                        pass # No se encontró el período, etc.
                    # --- FIN REQ 2 ---

                    # Obtener dataframes (actual y previo)
                    df_periodo_neto = filtered_df[filtered_df['Periodo'] == periodo_actual]
                    # --- MODIFICADO REQ 2: Usar columna_a_usar ---
                    df_neto = df_periodo_neto[df_periodo_neto[columna_a_usar] >= 0].copy()

                    df_periodo_neto_prev = pd.DataFrame()
                    df_neto_prev = pd.DataFrame()
                    if prev_periodo_str:
                        df_periodo_neto_prev = filtered_df[filtered_df['Periodo'] == prev_periodo_str]
                        # --- MODIFICADO REQ 2: Usar columna_a_usar ---
                        df_neto_prev = df_periodo_neto_prev[df_periodo_neto_prev[columna_a_usar] >= 0].copy()
                    # --- FIN REQ 2 ---

                    if df_neto.empty:
                        st.warning(f"No hay datos de '{tipo_pago_seleccionado}' (>= 0) para {periodo_actual} con los filtros seleccionados.")
                        st.markdown("---")
                        continue

                    min_val = 0.0
                    # --- MODIFICADO REQ 2: Usar columna_a_usar ---
                    max_val = float(df_neto[columna_a_usar].max())

                    # --- INICIO: CORRECCIÓN ERROR SLIDER 0.0 ---
                    if max_val == 0.0:
                        st.info(f"Todos los registros de '{tipo_pago_seleccionado}' para {periodo_actual} tienen el valor: {format_currency_es(0.0)}")
                        st.markdown("---") # Separador de período
                        continue # Salta al siguiente período del bucle
                    # --- FIN: CORRECCIÓN ERROR SLIDER 0.0 ---


                    st.markdown("##### Controles del Histograma")
                    col_cont1, col_cont2 = st.columns(2)

                    with col_cont1:
                        slider_range_key = f"slider_range_neto_{periodo_actual}_{columna_a_usar}"
                        selected_range = st.slider(
                            f"Seleccionar rango de {tipo_pago_seleccionado}:",
                            min_value=min_val,
                            max_value=max_val,
                            value=(min_val, max_val),
                            key=slider_range_key,
                            step=100.0
                        )

                    with col_cont2:
                        slider_bins_key = f"slider_bins_neto_{periodo_actual}_{columna_a_usar}"
                        num_bins = st.slider(
                            "Seleccionar número de 'bins' (columnas):",
                            min_value=5,
                            max_value=100,
                            value=30,
                            key=slider_bins_key
                        )

                    # --- MODIFICADO REQ 2: Usar columna_a_usar ---
                    df_to_plot = df_neto[
                        (df_neto[columna_a_usar] >= selected_range[0]) &
                        (df_neto[columna_a_usar] <= selected_range[1])
                    ]

                    df_to_plot_prev = pd.DataFrame()
                    if not df_neto_prev.empty:
                        # --- MODIFICADO REQ 2: Usar columna_a_usar ---
                        df_to_plot_prev = df_neto_prev[
                            (df_neto_prev[columna_a_usar] >= selected_range[0]) &
                            (df_neto_prev[columna_a_usar] <= selected_range[1])
                        ]
                    # --- FIN REQ 2 ---

                    if df_to_plot.empty:
                        st.warning(f"No hay datos de '{tipo_pago_seleccionado}' en el rango seleccionado para {periodo_actual}.")
                        st.markdown("---")
                        continue

                    st.markdown("---")

                    # --- INICIO: CORRECCIÓN RENDERIZADO DE TARJETAS (REQ 1) ---
                    st.markdown("##### Estadísticas (Rango Seleccionado)")

                    # --- MODIFICADO REQ 2: Usar columna_a_usar ---
                    promedio_actual = df_to_plot[columna_a_usar].mean()
                    mediana_actual = df_to_plot[columna_a_usar].median()
                    suma_actual = df_to_plot[columna_a_usar].sum()

                    promedio_prev = np.nan
                    mediana_prev = np.nan
                    suma_prev = np.nan

                    if not df_to_plot_prev.empty:
                        # --- MODIFICADO REQ 2: Usar columna_a_usar ---
                        promedio_prev = df_to_plot_prev[columna_a_usar].mean()
                        mediana_prev = df_to_plot_prev[columna_a_usar].median()
                        suma_prev = df_to_plot_prev[columna_a_usar].sum()

                    delta_promedio_html = get_delta_html_neto(promedio_actual, promedio_prev)
                    delta_mediana_html = get_delta_html_neto(mediana_actual, mediana_prev)
                    delta_suma_html = get_delta_html_neto(suma_actual, suma_prev)

                    # --- MODIFICADO REQ 2: Títulos de tarjetas dinámicos ---
                    # --- CORRECCIÓN REQ 1: Mover CSS adentro del HTML ---
                    cards_html = f"""
                    <style>
                        .metric-card-neto {{
                            background-color: #ffffff;
                            border-radius: 0.5rem;
                            padding: 1rem;
                            border-left: 5px solid #007bff; /* Color por defecto */
                            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
                            transition: all 0.3s ease-in-out;
                        }}
                        .metric-card-neto:hover {{
                            box-shadow: 0 6px 10px rgba(0, 0, 0, 0.1);
                            transform: translateY(-2px);
                        }}
                        .metric-card-neto.green {{ border-color: #28a745; }}
                        .metric-card-neto.orange {{ border-color: #fd7e14; }}

                        .metric-title {{
                            font-size: 0.9rem;
                            font-weight: 600;
                            color: #555;
                            margin-bottom: 0.25rem;
                        }}
                        .metric-value {{
                            font-size: 1.75rem;
                            font-weight: 700;
                            color: #222;
                            line-height: 1.2;
                        }}
                        .metric-delta {{
                            font-size: 0.85rem;
                            font-weight: 600;
                            margin-top: 0.5rem;
                        }}
                        .metric-delta .green {{ color: #28a745; }}
                        .metric-delta .red {{ color: #dc3545; }}
                        .metric-delta .grey {{ color: #6c757d; }}
                    </style>
                    <div style="display: flex; gap: 1rem; flex-wrap: wrap;">
                        <div style="flex: 1; min-width: 200px;">
                            <div class="metric-card-neto">
                                <div class="metric-title">Promedio {tipo_pago_seleccionado}</div>
                                <div class="metric-value">{format_currency_es(promedio_actual)}</div>
                                {delta_promedio_html}
                            </div>
                        </div>
                        <div style="flex: 1; min-width: 200px;">
                            <div class="metric-card-neto green">
                                <div class="metric-title">Mediana {tipo_pago_seleccionado}</div>
                                <div class="metric-value">{format_currency_es(mediana_actual)}</div>
                                {delta_mediana_html}
                            </div>
                        </div>
                        <div style="flex: 1; min-width: 200px;">
                            <div class="metric-card-neto orange">
                                <div class="metric-title">Suma Total {tipo_pago_seleccionado}</div>
                                <div class="metric-value">{format_currency_es(suma_actual)}</div>
                                {delta_suma_html}
                            </div>
                        </div>
                    </div>
                    """
                    st.components.v1.html(cards_html, height=140)
                    st.markdown("<br>", unsafe_allow_html=True)
                    # --- FIN: CORRECCIÓN RENDERIZADO DE TARJETAS (REQ 1) ---

                    try:
                        # --- MODIFICADO REQ 2: Usar columna_a_usar ---
                        df_to_plot['Bin'] = pd.cut(df_to_plot[columna_a_usar], bins=num_bins)
                    except ValueError as e:
                        st.error(f"No se pudo generar el histograma para {periodo_actual}. Intente ajustar el número de 'bins' o el rango. Error: {e}")
                        st.markdown("---")
                        continue

                    # --- MODIFICADO REQ 2: Usar columna_a_usar ---
                    df_hist_agg = df_to_plot.groupby('Bin', observed=True)[columna_a_usar].agg(['count', 'sum']).reset_index()
                    df_hist_agg.columns = ['Bin', 'Cantidad', 'Total Pagado']

                    df_hist_agg['Rango'] = df_hist_agg['Bin'].apply(
                        lambda x: f"{format_currency_es(x.left)} - {format_currency_es(x.right)}"
                    )

                    df_hist_agg['Total Pagado Formateado'] = df_hist_agg['Total Pagado'].apply(lambda x: format_currency_es(x))
                    df_for_download = df_hist_agg[['Rango', 'Cantidad', 'Total Pagado']].copy()

                    title_range_start = format_currency_es(selected_range[0], decimals=0)
                    title_range_end = format_currency_es(selected_range[1], decimals=0)
                    # --- MODIFICADO REQ 2: Título de gráfico dinámico ---
                    title = f"Distribución de {tipo_pago_seleccionado} (Rango: {title_range_start} - {title_range_end})"

                    st.subheader(f"Histograma ({format_integer_es(df_to_plot.shape[0])} registros)")

                    col_chart, col_table = st.columns([2, 1])

                    with col_chart:
                        fig_hist = px.bar(
                            df_hist_agg,
                            x='Rango',
                            y='Cantidad',
                            text='Cantidad',
                            title=title,
                            labels={'Rango': f'Rango {tipo_pago_seleccionado}', 'Cantidad': 'Cantidad de Empleados'},
                            hover_data=['Total Pagado Formateado']
                        )

                        fig_hist.update_xaxes(categoryorder='array', categoryarray=df_hist_agg['Rango'])

                        fig_hist.update_traces(
                            textposition='outside',
                            hovertemplate=f'Rango: %{{x}}<br>Empleados: %{{y}}<br>Total {tipo_pago_seleccionado}: %{{customdata[0]}}'
                        )
                        fig_hist.update_layout(
                            bargap=0.1,
                            xaxis_title=f"Rango {tipo_pago_seleccionado} ($)",
                            yaxis_title="Cantidad de Empleados",
                            height=600
                        )
                        st.plotly_chart(fig_hist, use_container_width=True)

                    with col_table:
                        st.markdown("##### Datos del Histograma")
                        df_hist_display = df_hist_agg[['Rango', 'Cantidad', 'Total Pagado']].copy()

                        total_row = pd.DataFrame({
                            'Rango': ['**TOTAL**'],
                            'Cantidad': [df_hist_display['Cantidad'].sum()],
                            'Total Pagado': [df_hist_display['Total Pagado'].sum()]
                        })
                        df_hist_display = pd.concat([df_hist_display, total_row], ignore_index=True)

                        df_hist_display['Cantidad'] = df_hist_display['Cantidad'].apply(
                            lambda x: format_integer_es(x) if isinstance(x, (int, np.integer, float)) else x
                        )
                        df_hist_display['Total Pagado'] = df_hist_display['Total Pagado'].apply(
                            lambda x: format_currency_es(x) if isinstance(x, (int, np.integer, float)) else x
                        )

                        st.dataframe(
                            df_hist_display,
                            use_container_width=True,
                            hide_index=True,
                            height=600
                        )

                        generate_download_buttons(
                            df_for_download,
                            f'histograma_{tipo_pago_seleccionado}_{periodo_actual}',
                            key_suffix=f"_neto_hist_{periodo_actual}_{columna_a_usar}"
                        )

                    # --- INICIO MODIFICACIÓN REQ 4: Tabla de Detalle ---
                    st.markdown("---") # Separador
                    st.subheader(f"Detalle de Empleados ({periodo_actual} / Rango Seleccionado)")

                    # --- MODIFICADO REQ 2: Añadir columnas de pago ---
                    cols_detalle = [
                        'LEGAJO', 'Apellido y Nombre', 'Nivel', 'Subnivel', 'CECO',
                        'Gerencia', 'Ministerio', 'Distrito', 'Función', # <-- Añadido Función
                        'Neto Pagado', 'SAC Pagado', 'Neto + SAC', # <-- Columnas de pago
                        'Bin'
                    ]

                    cols_existentes = [col for col in cols_detalle if col in df_to_plot.columns]
                    df_detalle = df_to_plot[cols_existentes].copy()

                    if 'Bin' in df_detalle.columns:
                        df_detalle['Rango'] = df_detalle['Bin'].apply(
                            lambda x: f"{format_currency_es(x.left)} - {format_currency_es(x.right)}"
                        )

                    df_detalle_download = df_detalle.copy()
                    if 'Bin' in df_detalle_download.columns:
                        df_detalle_download = df_detalle_download.drop(columns=['Bin'])

                    # --- MODIFICADO REQ 2: Formatear todas las columnas de pago ---
                    if 'Neto Pagado' in df_detalle.columns:
                        df_detalle['Neto Pagado'] = df_detalle['Neto Pagado'].apply(format_currency_es)
                    if 'SAC Pagado' in df_detalle.columns:
                        df_detalle['SAC Pagado'] = df_detalle['SAC Pagado'].apply(format_currency_es)
                    if 'Neto + SAC' in df_detalle.columns:
                        df_detalle['Neto + SAC'] = df_detalle['Neto + SAC'].apply(format_currency_es)
                    if 'LEGAJO' in df_detalle.columns:
                         df_detalle['LEGAJO'] = df_detalle['LEGAJO'].apply(lambda x: format_integer_es(int(x)) if (pd.notna(x) and x != 'no disponible' and str(x).isdigit()) else ('' if x=='no disponible' else x))

                    # --- MODIFICADO REQ 2: Reordenar columnas para mostrar ---
                    cols_display_final = [
                        col for col in [
                            'LEGAJO', 'Apellido y Nombre', 'Nivel', 'Subnivel', 'CECO',
                            'Gerencia', 'Ministerio', 'Distrito', 'Función',
                            'Neto Pagado', 'SAC Pagado', 'Neto + SAC', 'Rango'
                        ] if col in df_detalle.columns
                    ]
                    st.dataframe(df_detalle[cols_display_final], use_container_width=True, hide_index=True)

                    generate_download_buttons(
                        df_detalle_download,
                        f'detalle_pagos_{periodo_actual}',
                        key_suffix=f"_neto_detalle_{periodo_actual}_{columna_a_usar}"
                    )
                    # --- FIN MODIFICACIÓN REQ 4 ---

                    st.markdown("---") # Separador de período (REQ 1)
                # --- FIN DEL BUCLE FOR ---
    # --- FIN: REFACTORIZACIÓN 'Neto Pagado' ---

    # --- INICIO: NUEVA SOLAPA DE EVOLUCIÓN DE PAGOS ---
    with tab_evolucion_pagos:
        st.header("Evolución Mensual de Pagos")

        if filtered_df.empty or not selected_periodos:
            st.warning("No hay datos para mostrar con los filtros seleccionados. Por favor, ajuste los filtros en la barra lateral.")
        else:
            # --- INICIO: MODIFICACIÓN GRÁFICO DOBLE EJE ---

            # 1. Definir las métricas disponibles
            metric_map = {
                "Suma Neto Pagado": {"col": "Suma_Neto", "color": "#1f77b4"},
                "Suma SAC Pagado": {"col": "Suma_SAC", "color": "#ff7f0e"},
                "Suma Neto + SAC": {"col": "Suma_Total_Neto_SAC", "color": "#2ca02c"},
                "Promedio Neto Pagado": {"col": "Promedio_Neto", "color": "#d62728"},
                "Promedio SAC Pagado": {"col": "Promedio_SAC", "color": "#9467bd"},
                "Promedio Neto + SAC": {"col": "Promedio_Total_Neto_SAC", "color": "#8c564b"}
            }
            metric_options = list(metric_map.keys())

            # 2. Crear los selectores multiselect
            st.subheader("Controles del Gráfico de Evolución")
            col_sel1, col_sel2 = st.columns(2)
            with col_sel1:
                opciones_eje1 = st.multiselect(
                    "Métricas Eje Y (Principal):",
                    options=metric_options,
                    default=["Suma Neto Pagado"],
                    key="select_eje_1"
                )
            with col_sel2:
                opciones_eje2 = st.multiselect(
                    "Métricas Eje Y (Secundario):",
                    options=metric_options,
                    default=[],
                    key="select_eje_2"
                )
            st.markdown("---")

            # 3. Preparar los datos (esto no cambia)
            df_evolucion = filtered_df.groupby('Periodo').agg(
                Suma_Neto=('Neto Pagado', 'sum'),
                Promedio_Neto=('Neto Pagado', 'mean'),
                Suma_SAC=('SAC Pagado', 'sum'),
                Promedio_SAC=('SAC Pagado', 'mean'),
                Suma_Total_Neto_SAC=('Neto + SAC', 'sum'),
                Promedio_Total_Neto_SAC=('Neto + SAC', 'mean')
            ).reset_index()

            # Ordenar cronológicamente
            df_evolucion['Periodo'] = pd.Categorical(df_evolucion['Periodo'], categories=all_periodos_sorted, ordered=True)
            df_evolucion = df_evolucion.sort_values('Periodo')

            # Filtrar solo a los períodos seleccionados en la sidebar
            df_evolucion = df_evolucion[df_evolucion['Periodo'].isin(sorted_selected_periods)].reset_index(drop=True)

            if df_evolucion.empty:
                st.warning("No hay datos de evolución para los períodos seleccionados.")
            else:
                col_graf, col_tabla = st.columns([2, 1])

                with col_graf:
                    st.subheader("Gráfico de Evolución Combinado")

                    # --- AÑADIDO: Chequeo para gráfico vacío ---
                    if not opciones_eje1 and not opciones_eje2:
                        st.info("Por favor, seleccione al menos una métrica en los controles de arriba para construir el gráfico.")
                        # Placeholder para mantener el layout
                        st.markdown("<div style='height: 600px;'></div>", unsafe_allow_html=True)

                    else:
                        # 4. Crear gráfico con doble eje
                        fig_evolucion = make_subplots(specs=[[{"secondary_y": True}]])

                        # Añadir trazas Eje 1 (Principal)
                        for metric_name in opciones_eje1:
                            config = metric_map[metric_name]
                            col_name = config["col"]
                            color = config["color"]
                            fig_evolucion.add_trace(go.Scatter(
                                x=df_evolucion['Periodo'],
                                y=df_evolucion[col_name],
                                name=metric_name,
                                mode='lines+markers', # Sin texto para más limpieza
                                line=dict(color=color)
                            ), secondary_y=False)

                        # Añadir trazas Eje 2 (Secundario)
                        for metric_name in opciones_eje2:
                            config = metric_map[metric_name]
                            col_name = config["col"]
                            color = config["color"]
                            fig_evolucion.add_trace(go.Scatter(
                                x=df_evolucion['Periodo'],
                                y=df_evolucion[col_name],
                                name=f"{metric_name} (Sec.)",
                                mode='lines+markers',
                                line=dict(color=color, dash='dash') # Estilo punteado
                            ), secondary_y=True)

                        # 5. Títulos de Ejes Dinámicos
                        def get_axis_title(options):
                            has_suma = any('Suma' in s for s in options)
                            has_prom = any('Promedio' in s for s in options)
                            if has_suma and not has_prom: return "Suma Total ($)"
                            if has_prom and not has_suma: return "Promedio ($)"
                            if has_suma and has_prom: return "Valor Mixto ($)"
                            return "Valor ($)"

                        title_eje_1 = get_axis_title(opciones_eje1)
                        title_eje_2 = get_axis_title(opciones_eje2)

                        fig_evolucion.update_layout(
                            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                            height=600,
                            hovermode="x unified"
                        )
                        fig_evolucion.update_xaxes(title_text="Período", categoryorder='array', categoryarray=sorted_selected_periods)
                        fig_evolucion.update_yaxes(title_text=f"<b>{title_eje_1}</b> (Principal)", secondary_y=False)
                        fig_evolucion.update_yaxes(title_text=f"<b>{title_eje_2}</b> (Secundario)", secondary_y=True, showgrid=False)

                        st.plotly_chart(fig_evolucion, use_container_width=True)
                        # --- FIN: Lógica del gráfico movida al 'else' ---

                with col_tabla:
                    st.subheader("Datos Agregados")

                    df_display_evolucion = df_evolucion.copy()

                    # 6. Formatear y mostrar TODAS las columnas en la tabla
                    cols_to_format = [
                        'Suma_Neto', 'Promedio_Neto', 'Suma_SAC', 'Promedio_SAC',
                        'Suma_Total_Neto_SAC', 'Promedio_Total_Neto_SAC'
                    ]
                    cols_to_show = ['Periodo'] + cols_to_format # Mostrar todas

                    for col in cols_to_format:
                        if col in df_display_evolucion.columns:
                            df_display_evolucion[col] = df_display_evolucion[col].apply(format_currency_es)

                    st.dataframe(
                        df_display_evolucion[cols_to_show],
                        use_container_width=True,
                        hide_index=True,
                        height=600
                    )

                    generate_download_buttons(
                        df_evolucion, # Descargar datos crudos (sin formato)
                        f'evolucion_pagos_agregados',
                        key_suffix="_evolucion_pagos"
                    )
            # --- FIN: MODIFICACIÓN GRÁFICO DOBLE EJE ---
    # --- FIN: NUEVA SOLAPA DE EVOLUCIÓN DE PAGOS ---

    with tab_brutos:
        st.header('Tabla de Datos Filtrados')
        display_df = filtered_df.copy()

        # Formatear columnas numéricas para visualización
        if 'LEGAJO' in display_df.columns:
            display_df['LEGAJO'] = display_df['LEGAJO'].apply(lambda x: format_integer_es(int(x)) if (pd.notna(x) and x != 'no disponible' and str(x).isdigit()) else ('' if x=='no disponible' else x))

        # --- MODIFICADO REQ 2: Formatear todas las columnas de pago ---
        if 'Neto Pagado' in display_df.columns:
            display_df['Neto Pagado'] = display_df['Neto Pagado'].apply(
                lambda x: format_currency_es(x) if x > 0 else ("$ 0,00" if x == 0 else "")
            )
        if 'SAC Pagado' in display_df.columns:
            display_df['SAC Pagado'] = display_df['SAC Pagado'].apply(
                lambda x: format_currency_es(x) if x > 0 else ("$ 0,00" if x == 0 else "")
            )
        if 'Neto + SAC' in display_df.columns:
            display_df['Neto + SAC'] = display_df['Neto + SAC'].apply(
                lambda x: format_currency_es(x) if x > 0 else ("$ 0,00" if x == 0 else "")
            )
        # --- FIN MODIFICADO REQ 2 ---

        st.dataframe(display_df)
        generate_download_buttons(filtered_df, 'datos_filtrados_dotacion', key_suffix="_brutos")

else:
    st.info("Por favor, cargue un archivo Excel para comenzar el análisis.")
