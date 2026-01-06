# ===============================================================
# Visualizador de Eficiencia - Versión Final Completa Restaurada
# ===============================================================

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from io import BytesIO
import numpy as np # <--- AÑADIDO PARA MANEJAR inf
import traceback # Para mostrar errores detallados

# Configuración de la página para que ocupe todo el ancho
st.set_page_config(layout="wide", page_title="Visualizador de Eficiencia")

# ----------------- Funciones de Datos -----------------

@st.cache_data
def load_data(uploaded_file):
    """
    Carga los datos desde un archivo Excel, procesa las fechas,
    CALCULA TOTALES DE HORAS EXTRAS Y DÍAS de GUARDIA, y extrae
    nombres de columnas, años y meses.

    MODIFICADO: Ahora carga 'eficiencia' y 'masa_salarial' en
    dataframes separados, y LUEGO FUSIONA 'Dotación' desde
    'masa_salarial' hacia 'eficiencia' para que esté disponible
    en todas las pestañas.
    """
    if uploaded_file is None:
        return pd.DataFrame(), pd.DataFrame(), [], [], [], {}, [], []

    # Leer todas las hojas
    excel_file = pd.ExcelFile(uploaded_file)
    sheet_names = excel_file.sheet_names

    # Inicializar dataframes
    df_eficiencia = pd.DataFrame()
    df_indicadores = pd.DataFrame()

    # Listas de columnas (inicializar vacías)
    k_cols = []
    qty_cols = []
    years = []
    months_map = {}
    k_indicador_cols = []
    qty_indicador_cols = []

    # --- Cargar Hoja 'eficiencia' ---
    if 'eficiencia' in sheet_names:
        try:
            # Asumimos que la hoja eficiencia siempre tiene header en fila 1 (header=0)
            df_eficiencia = pd.read_excel(excel_file, sheet_name='eficiencia', header=0)

            # --- Procesamiento de df_eficiencia ---
            # ===============================================================
            # CÁLCULO DE TOTALES
            # ===============================================================
            he_costo_cols = ['$K_50%', '$K_100%']
            he_qty_cols = ['hs_50%', 'hs_100%']

            if all(col in df_eficiencia.columns for col in he_costo_cols):
                df_eficiencia['$K_Total_HE'] = df_eficiencia[he_costo_cols].fillna(0).sum(axis=1)

            if all(col in df_eficiencia.columns for col in he_qty_cols):
                df_eficiencia['hs_Total_HE'] = df_eficiencia[he_qty_cols].fillna(0).sum(axis=1)

            # --- 2. Total Guardias (GTO, GTI, 2T, 3T, TD) ---
            guardia_costo_cols = ['$K_Guardias_2T', '$K_Guardias_3T', '$K_GTO', '$K_GTI', '$K_TD']
            guardia_qty_cols = ['ds_Guardias_2T', 'ds_Guardias_3T', 'ds_GTO', 'ds_GTI', 'ds_TD']

            if all(col in df_eficiencia.columns for col in guardia_costo_cols):
                df_eficiencia['$K_Total_Guardias'] = df_eficiencia[guardia_costo_cols].fillna(0).sum(axis=1)

            if all(col in df_eficiencia.columns for col in guardia_qty_cols):
                df_eficiencia['ds_Total_Guardias'] = df_eficiencia[guardia_qty_cols].fillna(0).sum(axis=1)
            # ===============================================================

            # Intentar convertir 'Período' a datetime
            try:
                df_eficiencia['Período'] = pd.to_datetime(df_eficiencia['Período'])
            except Exception as e_fecha_ef:
                st.error(f"Error al convertir 'Período' en hoja 'eficiencia': {e_fecha_ef}")
                return pd.DataFrame(), pd.DataFrame(), [], [], [], {}, [], []


            df_eficiencia['Año'] = df_eficiencia['Período'].dt.year
            df_eficiencia['Mes'] = df_eficiencia['Período'].dt.month
            df_eficiencia['Período_fmt'] = df_eficiencia['Período'].dt.strftime('%b-%y')

            # --- Columnas de Agrupación Temporal ---
            df_eficiencia['Bimestre'] = (df_eficiencia['Mes'] - 1) // 2 + 1
            df_eficiencia['Trimestre'] = (df_eficiencia['Mes'] - 1) // 3 + 1
            df_eficiencia['Semestre'] = (df_eficiencia['Mes'] - 1) // 6 + 1

        except Exception as e_ef:
            st.error(f"Error general al procesar la hoja 'eficiencia': {e_ef}")
            return pd.DataFrame(), pd.DataFrame(), [], [], [], {}, [], []

    else:
        st.error("Error: No se encontró la hoja 'eficiencia' en el archivo Excel.")
        return pd.DataFrame(), pd.DataFrame(), [], [], [], {}, [], []


    # --- Cargar Hoja 'masa_salarial' ---
    if 'masa_salarial' in sheet_names:
        try:
            # Leer cabecera de la fila 1 (índice 0)
            df_indicadores = pd.read_excel(excel_file, sheet_name='masa_salarial', header=0)

            # Limpiar espacios en nombres de columnas
            df_indicadores.columns = df_indicadores.columns.str.strip()

            # --- Procesamiento robusto de fechas para 'masa_salarial' ---
            if 'Período' in df_indicadores.columns:

                # Crear una copia para intentar la conversión
                periodo_original = df_indicadores['Período'].copy()

                # 1. Intentar formato directo '%b-%y' (ej: Ene-24)
                try:
                    df_indicadores['Período'] = pd.to_datetime(periodo_original, format='%b-%y', errors='raise')
                except (ValueError, TypeError):
                    # 2. Si falla, intentar reemplazar meses en español y luego '%b-%y'
                    try:
                        mes_map_es = {
                            'ene': 'Jan', 'feb': 'Feb', 'mar': 'Mar', 'abr': 'Apr',
                            'may': 'May', 'jun': 'Jun', 'jul': 'Jul', 'ago': 'Aug',
                            'sep': 'Sep', 'oct': 'Oct', 'nov': 'Nov', 'dic': 'Dec'
                        }
                        per_str = periodo_original.astype(str).str.lower()
                        for k, v in mes_map_es.items():
                            per_str = per_str.str.replace(k, v)
                        df_indicadores['Período'] = pd.to_datetime(per_str, format='%b-%y', errors='raise')
                    except (ValueError, TypeError):
                        # 3. Si falla de nuevo, intentar que Pandas infiera (último recurso)
                        try:
                            df_indicadores['Período'] = pd.to_datetime(periodo_original, errors='raise')
                        except (ValueError, TypeError) as e_fecha_ind:
                            st.error(f"Error CRÍTICO al convertir 'Período' en 'masa_salarial' tras varios intentos: {e_fecha_ind}")
                            df_indicadores = df_indicadores.drop(columns=['Período'], errors='ignore')

                # --- Añadir columnas de fecha SOLO SI la conversión fue exitosa ---
                if pd.api.types.is_datetime64_any_dtype(df_indicadores.get('Período')):
                    df_indicadores['Año'] = df_indicadores['Período'].dt.year
                    df_indicadores['Mes'] = df_indicadores['Período'].dt.month
                    df_indicadores['Período_fmt'] = df_indicadores['Período'].dt.strftime('%b-%y')
                    df_indicadores['Bimestre'] = (df_indicadores['Mes'] - 1) // 2 + 1
                    df_indicadores['Trimestre'] = (df_indicadores['Mes'] - 1) // 3 + 1
                    df_indicadores['Semestre'] = (df_indicadores['Mes'] - 1) // 6 + 1
                else:
                    # Si 'Período' no es datetime, añadir columnas vacías o NaN para evitar errores
                    for col in ['Año', 'Mes', 'Período_fmt', 'Bimestre', 'Trimestre', 'Semestre']:
                        df_indicadores[col] = pd.NA

            else:
                st.error("Error: La columna 'Período' no se encontró en la hoja 'masa_salarial'.")
                df_indicadores = pd.DataFrame() # Resetear si falta la columna clave


            # Definir las listas de columnas para la Tab 3 y 4
            k_indicador_cols_def = ['Msalarial_$K', 'HExtras_$K', 'Guardias_$K']
            qty_indicador_cols_def = ['HE_hs', 'Guardias_ds', 'Dotación']

            # --- MODIFICACIÓN: Añadir Dotación a k_indicador_cols si existe ---
            if 'Dotación' in df_indicadores.columns:
                 k_indicador_cols_def.append('Dotación')

            # Filtrar por las columnas que SÍ existen en el df_indicadores
            k_indicador_cols = [c for c in k_indicador_cols_def if c in df_indicadores.columns]
            qty_indicador_cols = [c for c in qty_indicador_cols_def if c in df_indicadores.columns]

        except Exception as e:
            st.error(f"Error general al procesar la hoja 'masa_salarial':")
            st.error(traceback.format_exc()) # Muestra el error completo
            df_indicadores = pd.DataFrame()

    # --- NUEVO: Fusionar 'Dotación' en df_eficiencia (SI AMBOS DFs EXISTEN) ---
    if not df_eficiencia.empty and not df_indicadores.empty:
        # Asegurarse que 'Dotación' exista en indicadores y 'Período' (datetime) exista en ambos
        if 'Dotación' in df_indicadores.columns and \
           'Período' in df_indicadores.columns and \
           'Período' in df_eficiencia.columns and \
           pd.api.types.is_datetime64_any_dtype(df_indicadores['Período']) and \
           pd.api.types.is_datetime64_any_dtype(df_eficiencia['Período']):
           
            try:
                # Extraer solo 'Período' y 'Dotación' de indicadores
                df_dotacion = df_indicadores[['Período', 'Dotación']].copy()
                
                # Fusionar con df_eficiencia
                df_eficiencia = pd.merge(
                    df_eficiencia,
                    df_dotacion,
                    on='Período',
                    how='left'
                )
            except Exception as e_merge:
                st.warning(f"No se pudo fusionar 'Dotación' en la hoja 'eficiencia': {e_merge}")

    # --- NUEVA UBICACIÓN: Definir listas de columnas y filtros para Tabs 1 y 2 ---
    if not df_eficiencia.empty:
        # MODIFICADO: Incluir 'Dotación' si existe en df_eficiencia (después del merge)
        k_cols_base = [c for c in df_eficiencia.columns if c.startswith('$K_')]
        if 'Dotación' in df_eficiencia.columns:
            k_cols_base.append('Dotación')
        k_cols = sorted(list(set(k_cols_base))) # Usar set por si acaso
        
        # MODIFICADO: Incluir 'Dotación' si existe en df_eficiencia (después del merge)
        qty_cols_base = [c for c in df_eficiencia.columns if c.startswith('hs_') or c.startswith('ds_')]
        if 'Dotación' in df_eficiencia.columns:
            qty_cols_base.append('Dotación')
        qty_cols = sorted(list(set(qty_cols_base))) # Usar set por si acaso
        
        # Definir filtros basados en df_eficiencia
        if 'Año' in df_eficiencia.columns:
            years = sorted(df_eficiencia['Año'].unique(), reverse=True)
        months_map = {1:'Ene',2:'Feb',3:'Mar',4:'Abr',5:'May',6:'Jun',7:'Jul',8:'Ago',9:'Sep',10:'Oct',11:'Nov',12:'Dic'}

    # Retornar ambos dataframes por separado
    return df_eficiencia, df_indicadores, k_cols, qty_cols, years, months_map, k_indicador_cols, qty_indicador_cols


# ----------------- Funciones de Formateo -----------------

def format_number(x):
    """Formatea los números para visualización (2 DECIMALES): separador de miles con punto, decimales con coma."""
    if pd.isna(x): return ""
    try:
        if isinstance(x, (int, float)):
            return f"{float(x):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError): pass
    return x

def format_number_int(x):
    """Formatea los números para visualización (0 DECIMALES): separador de miles con punto."""
    if pd.isna(x): return ""
    try:
        if isinstance(x, (int, float)):
            return f"{float(x):,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError): pass
    return x

def format_percentage(x):
    """Formatea los números como porcentaje (2 DECIMALES) con el signo %."""
    if pd.isna(x): return ""
    try:
        if isinstance(x, (int, float)):
            # --- MODIFICACIÓN: Multiplicar por 100 ANTES de formatear ---
            val = float(x) * 100
            formatted_num = f"{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            return f"{formatted_num} %"
    except (ValueError, TypeError): pass
    return x

def to_excel(df):
    """Convierte un DataFrame a un objeto de bytes en formato Excel para su descarga."""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Datos')
    output.seek(0)
    return output


# ----------------- Funciones de Visualización -----------------

def plot_combined_chart(df_plot, primary_cols, secondary_cols, primary_title, secondary_title):
    """Genera un gráfico combinado con ejes multiselect."""
    fig = go.Figure()

    layout_args = {
        'title': "Evolución Combinada",
        'template': 'plotly_white',
        'xaxis_title': 'Período',
        'yaxis': {
            'title': primary_title,
            'side': 'left',
            'showgrid': False
        },
        'legend': {'orientation': 'h', 'yanchor': 'bottom', 'y': 1.02, 'xanchor': 'right', 'x': 1},
        'barmode': 'group' # Agrupar barras si hay varias
    }

    # --- Eje Secundario (Barras) - PRIMERO ---
    # Filtrar "Ninguna" si está presente junto con otras selecciones
    secondary_cols_filtered = [col for col in secondary_cols if col != "Ninguna"]

    if secondary_cols_filtered and not df_plot.empty and 'Período_fmt' in df_plot.columns:
        # --- Cálculo de rango manual para auto-escala (para MÚLTIPLES columnas) ---
        all_sec_values = pd.Series(dtype=float)
        valid_secondary_cols = [] 
        for col in secondary_cols_filtered:
            if col in df_plot.columns: 
                all_sec_values = pd.concat([all_sec_values, df_plot[col].dropna()])
                valid_secondary_cols.append(col)

        if valid_secondary_cols: 
            sec_values = all_sec_values
            sec_min = 0
            sec_max = 1

            if not sec_values.empty:
                data_min = sec_values.min()
                data_max = sec_values.max()
                data_range = data_max - data_min

                if data_range == 0 or pd.isna(data_range):
                    padding = abs(data_max * 0.1) if data_max != 0 else 1.0
                else:
                    padding = data_range * 0.1 # 10% de padding

                sec_min = data_min - padding
                sec_max = data_max + padding

                # Evitar que el eje baje de 0 si todos los datos son positivos
                if data_min >= 0 and sec_min < 0:
                    sec_min = 0
            
            # Aplicar el layout del eje Y2
            layout_args['yaxis2'] = {
                'title': secondary_title,
                'side': 'right',
                'overlaying': 'y',
                'showgrid': False,
                'range': [sec_min, sec_max] # Usar rango calculado
            }

            # Dibujar cada columna secundaria VÁLIDA
            for col in valid_secondary_cols:
                # --- MODIFICACIÓN FORMATTER (YA INCLUYE DOTACIÓN) ---
                is_int_col = col.startswith(('ds_', 'hs_')) or col in ['HE_hs', 'Guardias_ds', 'Dotación']
                formatter_secondary = format_number_int if is_int_col else format_number
                # --- FIN MODIFICACIÓN ---
                fig.add_trace(go.Bar(
                    x=df_plot['Período_fmt'],
                    y=df_plot[col],
                    name=col,
                    text=[formatter_secondary(v) for v in df_plot[col]],
                    textposition='outside',
                    yaxis='y2',
                    opacity=0.7
                ))
    # --- FIN EJE SECUNDARIO ---

    # --- Eje Primario (Línea) - SEGUNDO ---
    if primary_cols and not df_plot.empty and 'Período_fmt' in df_plot.columns:
        valid_primary_cols = [col for col in primary_cols if col in df_plot.columns]

        if valid_primary_cols: 
            for col in valid_primary_cols:
                # --- MODIFICACIÓN FORMATTER (YA INCLUYE DOTACIÓN) ---
                is_int_col = col.startswith(('ds_', 'hs_')) or col in ['HE_hs', 'Guardias_ds', 'Dotación']
                formatter_primary = format_number_int if is_int_col else format_number
                # --- FIN MODIFICACIÓN ---
                fig.add_trace(go.Scatter(
                    x=df_plot['Período_fmt'],
                    y=df_plot[col],
                    name=col,
                    mode='lines+markers+text',
                    text=[formatter_primary(v) for v in df_plot[col]],
                    textposition='top center',
                    yaxis='y1'
                ))
    # --- FIN EJE PRIMARIO ---

    fig.update_layout(**layout_args)
    return fig
# --- FIN NUEVA FUNCIÓN ---

def calc_variation(df, columns, tipo='mensual'):
    """
    Calcula la variación mensual o interanual de las columnas seleccionadas de forma dinámica.
    """
    columns_to_process = [col for col in columns if col in df.columns]
    if not columns_to_process or df.empty or 'Período' not in df.columns:
        # Si no hay columnas válidas, devolver dataframes vacíos
        return pd.DataFrame(), pd.DataFrame()

    # Ordenar por Período para asegurar cálculo correcto
    df_var = df[['Período', 'Período_fmt', 'Año', 'Mes'] + columns_to_process].copy().sort_values('Período')

    if tipo == 'interanual':
        # 1. Separar datos del año anterior
        df_last_year = df_var.copy()
        df_last_year['Año'] = df_last_year['Año'] + 1 # Adelantamos para el merge

        # 2. Renombrar columnas para el merge
        rename_cols = {col: f"{col}_prev" for col in columns_to_process}
        df_last_year.rename(columns=rename_cols, inplace=True)

        # 3. Cruzar datos actuales con los del año anterior (usando Año y Mes)
        df_merged = pd.merge(
            df_var.reset_index(),
            df_last_year[['Año', 'Mes'] + list(rename_cols.values())],
            on=['Año', 'Mes'],
            how='left'
        ).set_index('index').sort_index()

        df_val = pd.DataFrame(index=df_merged.index)
        df_pct = pd.DataFrame(index=df_merged.index)
        df_val[['Período', 'Período_fmt', 'Año']] = df_merged[['Período', 'Período_fmt', 'Año']]
        df_pct[['Período', 'Período_fmt', 'Año']] = df_merged[['Período', 'Período_fmt', 'Año']]

        for col in columns_to_process:
            col_prev = f"{col}_prev"
            df_val[col] = df_merged[col] - df_merged[col_prev]
            # Evitar división por cero
            df_pct[col] = df_val[col] / df_merged[col_prev]
            df_pct[col] = df_pct[col].replace([np.inf, -np.inf], np.nan)
            
    else: # tipo == 'mensual'
        df_val = df_var[['Período', 'Período_fmt', 'Año']].copy()
        df_pct = df_var[['Período', 'Período_fmt', 'Año']].copy()
        for col in columns_to_process:
            df_val[col] = df_var[col].diff(periods=1)
            # Evitar división por cero
            df_pct[col] = (df_val[col] / df_var[col].shift(1))
            df_pct[col] = df_pct[col].replace([np.inf, -np.inf], np.nan)

    return df_val, df_pct

def plot_bar(df_plot, columns, yaxis_title):
    """
    Genera un gráfico de barras con etiquetas de datos fuera de las barras.
    """
    fig = go.Figure()
    # Asegurar que el df no esté vacío y tenga la columna X
    if not df_plot.empty and 'Período_fmt' in df_plot.columns:
        for col in columns:
            if col in df_plot.columns: # Asegurarse de que la columna Y existe
                # --- MODIFICADO: Añadir 'Dotación' al formateo de enteros ---
                is_int_col = col.startswith(('ds_', 'hs_')) or col in ['HE_hs', 'Guardias_ds', 'Dotación']
                
                # --- NUEVA LÓGICA: Detectar si el título Y es Porcentaje ---
                is_pct_chart = " (%)" in yaxis_title
                
                if is_pct_chart:
                    formatter = format_percentage
                elif is_int_col:
                    formatter = format_number_int
                else:
                    formatter = format_number

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

# --- MODIFICADO: show_table ahora acepta column_formats ---
def show_table(df_table, nombre, show_totals=False, is_percentage=False, column_formats=None):
    """
    Muestra una tabla en Streamlit, ordenada, y agrega botones de descarga.
    Opcionalmente, añade una fila de totales.
    Acepta un flag 'is_percentage' para formatear con %.
    NUEVO: Acepta 'column_formats' para formateo por columna.
    """
    # Usar 'Período_fmt' si 'Período' (datetime) no existe, común en tablas de variación
    sort_col = 'Período' if 'Período' in df_table.columns else 'Período_fmt'

    if df_table.empty or sort_col not in df_table.columns:
        st.warning(f"Tabla '{nombre}' no se puede mostrar: datos vacíos o falta columna de período.")
        return

    # Si estamos usando Período_fmt para ordenar, necesitamos convertirlo temporalmente a fecha
    if sort_col == 'Período_fmt':
        try:
            df_table['_temp_sort_date'] = pd.to_datetime(df_table['Período_fmt'], format='%b-%y')
            df_sorted = df_table.sort_values(by='_temp_sort_date', ascending=False).drop(columns=['_temp_sort_date'])
        except ValueError:
            # Si falla la conversión, ordenar alfabéticamente como fallback
            df_sorted = df_table.sort_values(by='Período_fmt', ascending=False)
    else: # Ordenar por la columna 'Período' datetime
        df_sorted = df_table.sort_values(by='Período', ascending=False)

    df_sorted = df_sorted.reset_index(drop=True)

    # Eliminar la columna datetime 'Período' si existe, para mostrar solo 'Período_fmt'
    df_display = df_sorted.drop(columns=['Período'], errors='ignore')

    # Renombrar 'Período_fmt' a 'Período' para la visualización
    df_display.rename(columns={'Período_fmt': 'Período'}, inplace=True)

    # Reordenar columnas para que 'Período' (fmt) esté primero
    if 'Período' in df_display.columns:
        cols = ['Período'] + [col for col in df_display.columns if col != 'Período']
        df_display = df_display[cols]
    else:
        return


    if show_totals:
        num_cols_only = df_display.select_dtypes(include='number').columns
        if not num_cols_only.empty:
            totals_row = {col: df_display[col].sum() for col in num_cols_only}
            totals_row['Período'] = 'Total'
            df_display = pd.concat([df_display, pd.DataFrame([totals_row])], ignore_index=True)

    df_formatted = df_display.copy()

    # --- INICIO: Lógica de formateo actualizada ---
    for col in df_formatted.columns:
        # Saltar la columna 'Período'
        if col == 'Período':
            continue
            
        # Asegurarse de que la columna sea numérica antes de intentar formatear
        if not pd.api.types.is_numeric_dtype(df_formatted[col]):
            continue

        # 1. Chequear 'column_formats' primero (para Tab 4)
        if column_formats and col in column_formats:
            format_type = column_formats[col]
            if format_type == 'percent':
                df_formatted[col] = df_formatted[col].apply(format_percentage)
            elif format_type == 'currency':
                df_formatted[col] = df_formatted[col].apply(format_number)
            elif format_type == 'number':
                df_formatted[col] = df_formatted[col].apply(format_number) # 2 decimales para ratios
            elif format_type == 'integer':
                df_formatted[col] = df_formatted[col].apply(format_number_int)
        
        # 2. Fallback a 'is_percentage' (para variaciones %)
        elif is_percentage:
            df_formatted[col] = df_formatted[col].apply(format_percentage)
            
        # 3. Fallback a lógica original (enteros para hs/ds/dotación)
        elif col.startswith(('ds_', 'hs_')) or col in ['HE_hs', 'Guardias_ds', 'Dotación']:
            df_formatted[col] = df_formatted[col].apply(format_number_int)
            
        # 4. Default (moneda/número 2 decimales)
        else:
            df_formatted[col] = df_formatted[col].apply(format_number)
    # --- FIN: Lógica de formateo actualizada ---

    st.dataframe(df_formatted, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            label=f"📥 Descargar CSV ({nombre})",
            data=df_formatted.to_csv(index=False).encode('utf-8'),
            file_name=f"{nombre}.csv",
            mime='text/csv',
            use_container_width=True
        )
    with col2:
        st.download_button(
            label=f"📥 Descargar Excel ({nombre})",
            data=to_excel(df_formatted),
            file_name=f"{nombre}.xlsx",
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            use_container_width=True
        )
# --- FIN: show_table modificada ---

# --- FUNCIÓN PARA TARJETAS KPI (MODIFICADA) ---
def show_kpi_cards(df, var_list):
    """
    Calcula y muestra las tarjetas KPI para 2024 vs 2025 usando HTML/CSS.
    Usa el DataFrame *original* (df) para ignorar los filtros de mes/año.
    """
    # 1. Calcular totales
    # Asegurarse de que el dataframe no esté vacío y tenga 'Año'
    if df.empty or 'Año' not in df.columns:
        st.warning("No se pueden calcular KPIs (datos base vacíos o incompletos).")
        return

    # Filtrar solo las columnas var_list que SÍ existen en el df
    vars_existentes = [v for v in var_list if v in df.columns]
    if not vars_existentes:
        st.warning("Ninguna de las variables KPI especificadas existe en los datos.")
        return

    # Calculamos para 2024 y 2025 por defecto en las tarjetas superiores
    df_2024 = df[df['Año'] == 2024][vars_existentes].sum()
    df_2025 = df[df['Año'] == 2025][vars_existentes].sum()

    # 2. Definir layout (5 columnas)
    cols = st.columns(5)

    # Mapeo de nombres amigables (label)
    label_map = {
        '$K_50%': 'Costo HE 50%', '$K_100%': 'Costo HE 100%', '$K_Total_HE': 'Costo Total HE', 
        '$K_GTO': 'Costo GTO', '$K_GTI': 'Costo GTI', '$K_Guardias_2T': 'Costo Guardias 2T', 
        '$K_Guardias_3T': 'Costo Guardias 3T', '$K_TD': 'Costo TD', '$K_Total_Guardias': 'Costo Total Guardias', 
        'hs_50%': 'Horas HE 50%', 'hs_100%': 'Horas HE 100%', 'hs_Total_HE': 'Horas Total HE', 
        'ds_GTO': 'Días GTO', 'ds_GTI': 'Días GTI', 'ds_Guardias_2T': 'Días Guardias 2T', 
        'ds_Guardias_3T': 'Días Guardias 3T', 'ds_TD': 'Días TD', 'ds_Total_Guardias': 'Días Total Guardias'
    }

    # Lista de clases de color para asignar cíclicamente (Gama Azules/Violetas)
    color_classes = ['card-blue', 'card-azure', 'card-violet', 'card-purple', 'card-indigo']

    # 3. Iterar y crear métricas
    col_index = 0
    for var in vars_existentes: # Iterar solo sobre las que existen
        total_2024 = df_2024.get(var, 0)
        total_2025 = df_2025.get(var, 0)

        delta_abs = total_2025 - total_2024

        if total_2024 > 0 and not pd.isna(total_2024):
            # --- MODIFICACIÓN: No multiplicar por 100 ---
            delta_pct = (delta_abs / total_2024)
        elif (total_2024 == 0 or pd.isna(total_2024)) and total_2025 > 0:
            delta_pct = 1.0 # 100%
        else:
            delta_pct = 0.0 # Cubre 0 a 0

        # --- Formato con prefijo/sufijo ---
        # --- MODIFICADO: Añadir 'Dotación' al formateo de enteros ---
        is_int = var.startswith('ds_') or var.startswith('hs_') or var == 'Dotación'
        formatter_val = format_number_int if is_int else format_number

        val_str = formatter_val(total_2025)
        delta_abs_str = formatter_val(abs(delta_abs)) # Usamos abs() para el color
        
        # --- MODIFICACIÓN: format_percentage ahora multiplica x100 ---
        delta_pct_fmt = format_percentage(delta_pct)

        if var.startswith('$K_'):
            value_fmt = f"$K {val_str}"
            delta_abs_fmt = f"$K {delta_abs_str}"
        elif var.startswith('hs_'):
            value_fmt = f"{val_str} hs"
            delta_abs_fmt = f"{delta_abs_str} hs"
        elif var.startswith('ds_'):
            value_fmt = f"{val_str} ds"
            delta_abs_fmt = f"{delta_abs_str} ds"
        elif var == 'Dotación':
             value_fmt = f"{val_str} pers." # Asumimos "personas"
             delta_abs_fmt = f"{delta_abs_str} pers."
        else:
            value_fmt = val_str
            delta_abs_fmt = delta_abs_str

        # --- Lógica de color y formato de delta ---
        delta_icon = "↑" if delta_abs >= 0 else "↓"
        delta_color_style = "color: #86efac;" if delta_abs >= 0 else "color: #fca5a5;" 
        delta_str_html = f"<span style='{delta_color_style} font-weight: bold;'>{delta_icon} {pref if 'pref' in locals() else ''}{delta_abs_fmt}{suff if 'suff' in locals() else ''} ({delta_pct_fmt})</span>"

        # Asignar a la columna correcta
        current_col = cols[col_index % 5]
        label = label_map.get(var, var) # Usar nombre amigable

        # Asignar color cíclico
        color_class = color_classes[col_index % len(color_classes)]

        # --- MODIFICACIÓN: Construir y renderizar tarjeta HTML ---
        html_card = f"""
        <div class="metric-card {color_class}">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value_fmt}</div>
            <div class="metric-delta">
                {delta_str_html}
            </div>
        </div>
        """
        current_col.markdown(html_card, unsafe_allow_html=True)

        col_index += 1

# --- FUNCIÓN: TARJETAS ANUALES DE INDICADORES (TAB 4) ---
def show_annual_indicator_cards(df_ind_unfiltered):
    """
    Calcula y muestra tarjetas de KPI anualizadas para 2024 vs 2025 (Acum.)
    Usa el DataFrame *original* de 'masa_salarial' (sin filtrar).
    """
    if df_ind_unfiltered.empty or 'Año' not in df_ind_unfiltered.columns:
        st.info("No hay datos en 'masa_salarial' para calcular indicadores anuales.")
        return

    # 1. Definir los indicadores clave (numerador, denominador, formato)
    PREDEFINED_INDICATORS = {
        'HExtras_$K / Msalarial_$K (%)': ('HExtras_$K', 'Msalarial_$K', 'percent'),
        'Guardias_$K / Msalarial_$K (%)': ('Guardias_$K', 'Msalarial_$K', 'percent'),
        'HExtras_$K / HE_hs ($)': ('HExtras_$K', 'HE_hs', 'currency'),
        'Guardias_$K / Guardias_ds ($)': ('Guardias_$K', 'Guardias_ds', 'currency'),
        'Msalarial_$K / Dotación ($)': ('Msalarial_$K', 'Dotación', 'currency'),
        'HE_hs / Dotación (hs/pers)': ('HE_hs', 'Dotación', 'number'),
        'Guardias_ds / Dotación (ds/pers)': ('Guardias_ds', 'Dotación', 'number'),
    }

    # 2. Encontrar último mes de 2025 para la etiqueta dinámica
    df_2025_data = df_ind_unfiltered[df_ind_unfiltered['Año'] == 2025]
    if not df_2025_data.empty and 'Período' in df_2025_data.columns:
        last_month_2025 = df_2025_data['Período'].max()
        label_2025 = f"2025 (Acum. a {last_month_2025.strftime('%b-%y')})"
    else:
        label_2025 = "2025 (Sin Datos)"

    df_2024_data = df_ind_unfiltered[df_ind_unfiltered['Año'] == 2024]

    st.subheader("Indicadores Anualizados (2024 vs 2025 Acum.)")
    
    # 3. Preparar layout (4 columnas)
    col_layout = st.columns(4)
    card_index = 0

    # 4. Iterar y calcular
    for key, (num_col, den_col, fmt) in PREDEFINED_INDICATORS.items():
        
        # Verificar que las columnas existan en el DF original
        if not (num_col in df_ind_unfiltered.columns and den_col in df_ind_unfiltered.columns):
            continue # Saltar este indicador si faltan datos base

        # --- Cálculo 2024 ---
        val_2024_str = "-"
        if not df_2024_data.empty:
            num_2024 = df_2024_data[num_col].sum()
            
            # Lógica especial para Dotación: usar el PROMEDIO
            if den_col == 'Dotación':
                den_2024 = df_2024_data[den_col].mean()
            else:
                den_2024 = df_2024_data[den_col].sum()

            if den_2024 != 0 and not pd.isna(den_2024):
                ratio_2024 = num_2024 / den_2024
                # Formatear
                if fmt == 'percent':
                    val_2024_str = format_percentage(ratio_2024)
                elif fmt == 'currency':
                    val_2024_str = f"$ {format_number(ratio_2024)}" # Añadir $
                else: # 'number'
                    val_2024_str = format_number(ratio_2024) # 2 decimales
            else:
                val_2024_str = "N/A" # No hay datos o div por cero

        # --- Cálculo 2025 (Acumulado) ---
        val_2025_str = "-"
        if not df_2025_data.empty:
            num_2025 = df_2025_data[num_col].sum()
            
            # Lógica especial para Dotación: usar el PROMEDIO
            if den_col == 'Dotación':
                den_2025 = df_2025_data[den_col].mean()
            else:
                den_2025 = df_2025_data[den_col].sum()

            if den_2025 != 0 and not pd.isna(den_2025):
                ratio_2025 = num_2025 / den_2025
                # Formatear
                if fmt == 'percent':
                    val_2025_str = format_percentage(ratio_2025)
                elif fmt == 'currency':
                    val_2025_str = f"$ {format_number(ratio_2025)}" # Añadir $
                else: # 'number'
                    val_2025_str = format_number(ratio_2025) # 2 decimales
            else:
                val_2025_str = "N/A" # No hay datos o div por cero

        # --- Renderizar Tarjeta ---
        # Extraer el nombre base del indicador (ej: 'HExtras_$K / Msalarial_$K')
        label_base = key.split(' (')[0]
        
        html_card = f"""
        <div class="custom-annual-card">
            <div class="annual-label">{label_base}</div>
            <div class="annual-values-grid">
                <div class="annual-header">2024 (Anual)</div>
                <div class="annual-header">{label_2025}</div>
                <div class="annual-value">{val_2024_str}</div>
                <div class="annual-value">{val_2025_str}</div>
            </div>
        </div>
        """
        
        # Distribuir en 4 columnas
        current_col = col_layout[card_index % 4]
        current_col.markdown(html_card, unsafe_allow_html=True)
        card_index += 1

    # Añadir un separador antes del resto del contenido de la pestaña
    st.markdown("---")
# --- FIN: NUEVA FUNCIÓN ---


# --- NUEVA FUNCIÓN DE FILTRADO (REEMPLAZA A LA JERÁRQUICA) ---
def apply_time_filter(df_to_filter, filter_mode, filter_selection, all_options_dict):
    """
    Aplica el filtro de tiempo único basado en el modo seleccionado.
    """

    # Si el dataframe de entrada está vacío o no tiene columnas de fecha, devolverlo
    if df_to_filter.empty or not all(c in df_to_filter.columns for c in ['Año', 'Mes', 'Bimestre', 'Trimestre', 'Semestre', 'Período_fmt']):
        return df_to_filter

    # Si el filtro seleccionado está "vacío" (es decir, el usuario no ha tocado
    # el multiselect, y tiene *todas* las opciones seleccionadas por defecto),
    # entonces no aplicamos ningún filtro de tiempo.

    if filter_mode == 'Período Específico':
        # Asegurarse que all_periodos_especificos no esté vacío antes de comparar longitudes
        if all_options_dict.get('all_periodos_especificos') and len(filter_selection) < len(all_options_dict['all_periodos_especificos']):
            return df_to_filter[df_to_filter['Período_fmt'].isin(filter_selection)].copy()

    elif filter_mode == 'Mes':
        # Convertir nombres de mes (ej: 'Ene') a números (ej: 1)
        selected_months_nums = [k for k,v in all_options_dict['months_map'].items() if v in filter_selection]
        if all_options_dict.get('month_options') and len(selected_months_nums) < len(all_options_dict['month_options']):
            return df_to_filter[df_to_filter['Mes'].isin(selected_months_nums)].copy()

    elif filter_mode == 'Bimestre':
        if all_options_dict.get('all_bimestres') and len(filter_selection) < len(all_options_dict['all_bimestres']):
            return df_to_filter[df_to_filter['Bimestre'].isin(filter_selection)].copy()

    elif filter_mode == 'Trimestre':
        if all_options_dict.get('all_trimestres') and len(filter_selection) < len(all_options_dict['all_trimestres']):
            return df_to_filter[df_to_filter['Trimestre'].isin(filter_selection)].copy()

    elif filter_mode == 'Semestre':
        if all_options_dict.get('all_semestres') and len(filter_selection) < len(all_options_dict['all_semestres']):
            return df_to_filter[df_to_filter['Semestre'].isin(filter_selection)].copy()

    # Si no se cumple ninguna condición (ej: modo es 'Mes' pero todos los meses
    # están seleccionados), devolvemos el dataframe sin filtrar por tiempo.
    return df_to_filter.copy()
# --- FIN NUEVA FUNCIÓN ---

# ----------------- Inicio de la App -----------------

st.title("Visualizador de Eficiencia")

# --- CSS PARA ESTILOS DE TARJETAS (MODIFICADO CON GRADIENTES AZULES/VIOLETAS Y TAMAÑO COMPACTO) ---
CSS_STYLE = """
<style>
    /* Estilo base para la tarjeta (Más compacto y con Flexbox) */
    .metric-card {
        border-radius: 12px; 
        padding: 12px 8px;  
        box-shadow: 0 3px 5px rgba(0, 0, 0, 0.15);
        color: white;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        border: none;
        
        /* Flexbox para centrar y ajustar contenido */
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        text-align: center;
        
        /* FIX SUPERPOSICIÓN VERTICAL */
        height: auto;      
        margin-top: 10px;  
        margin-bottom: 10px; 
        min-height: 110px; 
    }

    .metric-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.25);
    }
    
    /* Tipografía ajustada */
    .metric-value {
        font-size: 1.4rem; 
        font-weight: 700;
        margin: 4px 0;    
        line-height: 1.2;
    }
    
    .metric-label {
        font-size: 0.85rem; 
        opacity: 0.9;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-weight: 600;
        margin-bottom: 4px;
        line-height: 1.1;
    }

    .metric-delta {
        font-size: 0.75rem; 
        margin-top: 4px;
    }
    
    /* Variaciones de color (Gama Azules, Celestes y Violáceos) */
    .card-blue { background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); }
    .card-azure { background: linear-gradient(135deg, #2193b0 0%, #6dd5fa 100%); }
    .card-violet { background: linear-gradient(135deg, #4a00e0 0%, #8e2de2 100%); }
    .card-purple { background: linear-gradient(135deg, #834d9b 0%, #d04ed6 100%); }
    .card-indigo { background: linear-gradient(135deg, #4b6cb7 0%, #182848 100%); }

    /* Estilo Tarjeta Anual (Tab 4) */
    .custom-annual-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        border: 1px solid #dee2e6;
        min-height: 140px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }

    .custom-annual-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 16px rgba(0,0,0,0.15);
    }

    .annual-label {
        font-size: 0.9rem;
        font-weight: 600;
        color: #007bff;
        text-align: center;
        margin-bottom: 10px;
        border-bottom: 1px solid #eee;
        padding-bottom: 8px;
    }

    .annual-values-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 5px 10px;
        text-align: center;
    }

    .annual-header {
        font-size: 0.8rem;
        color: #6c757d;
        font-weight: 500;
    }

    .annual-value {
        font-size: 1.1rem;
        font-weight: 700;
        color: #343a40;
    }

    /* Ajustes columnas para separación */
    [data-testid="column"] {
        padding: 0 0.75rem;
    }
</style>
"""
st.markdown(CSS_STYLE, unsafe_allow_html=True)
# --- FIN CSS ---


uploaded_file = st.file_uploader("Cargue el archivo 'eficiencia.xlsx'", type="xlsx")

if uploaded_file is None:
    st.info("Por favor, cargue un archivo Excel para comenzar.")
    st.stop()

# --- MODIFICACIÓN: Capturar dataframes separados ---
# --- 'k_cols' y 'qty_cols' ahora incluyen 'Dotación' ---
df_eficiencia, df_indicadores, k_cols, qty_cols, all_years, months_map, k_indicador_cols, qty_indicador_cols = load_data(uploaded_file)
# --- FIN MODIFICACIÓN ---

# 'df' ahora se refiere a df_eficiencia para el resto de la app
df = df_eficiencia
df_indicadores_empty = df_indicadores.empty


if df.empty:
    st.stop()

# --- Definir listas de opciones "default" (todos seleccionados) ---
month_options = list(months_map.values()) if months_map else []
all_options_dict = {
    'all_periodos_especificos': list(df.sort_values('Período')['Período_fmt'].unique()) if 'Período' in df.columns else [], 
    'month_options': month_options, 
    'all_bimestres': sorted(df['Bimestre'].unique()) if 'Bimestre' in df.columns else [], 
    'all_trimestres': sorted(df['Trimestre'].unique()) if 'Trimestre' in df.columns else [], 
    'all_semestres': sorted(df['Semestre'].unique()) if 'Semestre' in df.columns else [], 
    'months_map': months_map
}
# --- FIN ---


# ----------------- Lógica de Filtros en Barra Lateral -----------------
st.sidebar.header("Filtros Generales")

def reset_filters():
    st.session_state.selected_years = all_years
    st.session_state.filter_mode = 'Mes'
    st.session_state.sel_mes = month_options
    st.session_state.sel_bim = all_options_dict['all_bimestres']
    st.session_state.sel_tri = all_options_dict['all_trimestres']
    st.session_state.sel_sem = all_options_dict['all_semestres']
    st.session_state.sel_per = all_options_dict['all_periodos_especificos']


if st.sidebar.button("🔄 Resetear Filtros", use_container_width=True): 
    reset_filters()

# Asegurar inicialización de session_state si no existe
if 'selected_years' not in st.session_state:
    st.session_state.selected_years = all_years

# --- MODIFICACIÓN: default=all_years para carga total inmediata ---
selected_years = st.sidebar.multiselect("Años:", all_years, key='selected_years')

filter_mode = st.sidebar.radio("Filtrar por:", ['Mes', 'Bimestre', 'Trimestre', 'Semestre', 'Período Específico'], key='filter_mode', horizontal=True)

# --- MODIFICACIÓN: default=[todas_las_opciones] en cada multiselect de tiempo ---
filter_selection = []
if filter_mode == 'Mes': 
    filter_selection = st.sidebar.multiselect("Meses:", month_options, key='sel_mes')
elif filter_mode == 'Bimestre': 
    filter_selection = st.sidebar.multiselect("Bimestres:", all_options_dict['all_bimestres'], key='sel_bim')
elif filter_mode == 'Trimestre': 
    filter_selection = st.sidebar.multiselect("Trimestres:", all_options_dict['all_trimestres'], key='sel_tri')
elif filter_mode == 'Semestre': 
    filter_selection = st.sidebar.multiselect("Semestres:", all_options_dict['all_semestres'], key='sel_sem')
elif filter_mode == 'Período Específico': 
    filter_selection = st.sidebar.multiselect("Período:", all_options_dict['all_periodos_especificos'], key='sel_per')

# --- LÓGICA DE FILTRADO PARA GRÁFICOS DE EVOLUCIÓN ---
df_filtered_by_year = df[df['Año'].isin(selected_years)].copy() if selected_years else df.copy()
dff = apply_time_filter(df_filtered_by_year, filter_mode, filter_selection, all_options_dict)
if not dff.empty and 'Período' in dff.columns: dff = dff.sort_values('Período')

dff_indicadores = pd.DataFrame()
if not df_indicadores_empty:
    df_ind_f = df_indicadores[df_indicadores['Año'].isin(selected_years)].copy() if selected_years else df_indicadores.copy()
    dff_indicadores = apply_time_filter(df_ind_f, filter_mode, filter_selection, all_options_dict)
    if not dff_indicadores.empty: dff_indicadores = dff_indicadores.sort_values('Período')


# ----------------- Pestañas de la aplicación -----------------
tab1, tab2, tab3, tab4 = st.tabs(["$K (Costos)", "Cantidades (hs / ds)", "Relaciones", "Indicadores"])

# ----------------- Tab 1: COSTOS -----------------
with tab1:
    st.subheader("Totales Anuales (2025 vs 2024)")
    costo_vars_list = ['$K_50%', '$K_100%', '$K_Total_HE', '$K_TD', '$K_GTO', '$K_GTI', '$K_Guardias_2T', '$K_Guardias_3T', '$K_Total_Guardias']
    show_kpi_cards(df, costo_vars_list)
    st.markdown("---")
    
    st.subheader("Análisis de Costos ($K)")
    col1_k, col2_k = st.columns(2)
    with col1_k:
        pk_vars = st.multiselect("Eje Principal (Línea):", k_cols, default=[k_cols[0]] if k_cols else [], key="pk")
    with col2_k:
        sk_vars = st.multiselect("Eje Secundario (Barras):", ["Ninguna"] + k_cols, default=["Ninguna"], key="sk")
    
    selected_k_vars = list(set(pk_vars + [x for x in sk_vars if x != "Ninguna"]))
    
    if not dff.empty and selected_k_vars:
        st.plotly_chart(plot_combined_chart(dff, pk_vars, sk_vars, "$K (Línea)", "$K (Barras)"), use_container_width=True)
        show_table(dff[['Período', 'Período_fmt'] + [c for c in selected_k_vars if c in dff.columns]], "Costos_Datos", show_totals=True)
        st.markdown("---")
        
        # Variaciones Mensuales
        st.subheader("Variaciones Mensuales")
        tmk_sel = st.selectbox("Mostrar como:", ["Valores","Porcentaje"], key="tmk")
        # Calculamos sobre dataset filtrado por tiempo pero SIN filtro de año previo
        df_for_vm = apply_time_filter(df, filter_mode, filter_selection, all_options_dict)
        df_vm_v, df_vm_p = calc_variation(df_for_vm, selected_k_vars, 'mensual')
        is_p = (tmk_sel == 'Porcentaje')
        res_vm = df_vm_p if is_p else df_vm_v
        if selected_years:
            res_vm = res_vm[res_vm['Año'].isin(selected_years)]
        st.plotly_chart(plot_bar(res_vm, selected_k_vars, f"Variación Mensual ({'%' if is_p else '$K'})"), use_container_width=True)
        show_table(res_vm, "Costos_Var_Mensual", is_percentage=is_p)
        
        # Variaciones Interanuales
        st.subheader("Variaciones Interanuales")
        tik_sel = st.selectbox("Mostrar como:", ["Valores","Porcentaje"], key="tik")
        df_for_vi = apply_time_filter(df, filter_mode, filter_selection, all_options_dict)
        df_vi_v, df_vi_p = calc_variation(df_for_vi, selected_k_vars, 'interanual')
        is_p_i = (tik_sel == 'Porcentaje')
        res_vi_raw = df_vi_p if is_p_i else df_vi_v
        if selected_years:
            res_vi = res_vi_raw[res_vi_raw['Año'].isin(selected_years)].dropna(subset=selected_k_vars, how='all')
        else:
            res_vi = res_vi_raw.dropna(subset=selected_k_vars, how='all')
        st.plotly_chart(plot_bar(res_vi, selected_k_vars, f"Variación Interanual ({'%' if is_p_i else '$K'})"), use_container_width=True)
        show_table(res_vi, "Costos_Var_Interanual", is_percentage=is_p_i)

# ----------------- Tab 2: CANTIDADES -----------------
with tab2:
    st.subheader("Totales Anuales (2025 vs 2024)")
    qty_vars_list = ['hs_50%', 'hs_100%', 'hs_Total_HE', 'ds_TD', 'ds_GTO', 'ds_GTI', 'ds_Guardias_2T', 'ds_Guardias_3T', 'ds_Total_Guardias']
    show_kpi_cards(df, qty_vars_list)
    st.markdown("---")
    st.subheader("Análisis de Cantidades")
    col1_q, col2_q = st.columns(2)
    with col1_q:
        pq_vars = st.multiselect("Línea:", qty_cols, default=[qty_cols[0]] if qty_cols else [], key="pq")
    with col2_q:
        sq_vars = st.multiselect("Barras:", ["Ninguna"] + qty_cols, default=["Ninguna"], key="sq")
    
    selected_q_vars = list(set(pq_vars + [x for x in sq_vars if x != "Ninguna"]))
    if not dff.empty and selected_q_vars:
        st.plotly_chart(plot_combined_chart(dff, pq_vars, sq_vars, "Cantidades (Línea)", "Cantidades (Barras)"), use_container_width=True)
        show_table(dff[['Período', 'Período_fmt'] + [c for c in selected_q_vars if c in dff.columns]], "Cant_Datos", show_totals=True)
        st.markdown("---")
        
        st.subheader("Variaciones Mensuales")
        tmq_sel = st.selectbox("Mostrar como:", ["Valores","Porcentaje"], key="tmq")
        df_for_vmq = apply_time_filter(df, filter_mode, filter_selection, all_options_dict)
        df_vmq_v, df_vmq_p = calc_variation(df_for_vmq, selected_q_vars, 'mensual')
        res_vmq = df_vmq_p if tmq_sel == 'Porcentaje' else df_vmq_v
        if selected_years:
            res_vmq = res_vmq[res_vmq['Año'].isin(selected_years)]
        st.plotly_chart(plot_bar(res_vmq, selected_q_vars, f"Variación Mensual ({'%' if tmq_sel == 'Porcentaje' else 'Cant'})"), use_container_width=True)
        show_table(res_vmq, "Cant_Var_Mensual", is_percentage=(tmq_sel=='Porcentaje'))
        
        st.subheader("Variaciones Interanuales")
        tiq_sel = st.selectbox("Mostrar como:", ["Valores","Porcentaje"], key="tiq")
        df_for_viq = apply_time_filter(df, filter_mode, filter_selection, all_options_dict)
        df_vi_v, df_vi_p = calc_variation(df_for_viq, selected_q_vars, 'interanual')
        res_viq = df_vi_p if tiq_sel == 'Porcentaje' else df_vi_v
        if selected_years:
            res_viq = res_viq[res_viq['Año'].isin(selected_years)].dropna(subset=selected_q_vars, how='all')
        else:
            res_viq = res_viq.dropna(subset=selected_q_vars, how='all')
        st.plotly_chart(plot_bar(res_viq, selected_q_vars, f"Variación Interanual ({'%' if tiq_sel == 'Porcentaje' else 'Cant'})"), use_container_width=True)
        show_table(res_viq, "Cant_Var_Interanual", is_percentage=(tiq_sel=='Porcentaje'))

# ----------------- Tab 3: RELACIONES -----------------
with tab3:
    st.subheader("Análisis de Relaciones (Hoja: masa_salarial)")
    if not dff_indicadores.empty:
        st.subheader("Relaciones de Costo ($K)")
        col1_rk, col2_rk = st.columns(2)
        with col1_rk:
            prk_vars = st.multiselect("Línea:", k_indicador_cols, default=[k_indicador_cols[0]] if k_indicador_cols else [], key="prk")
        with col2_rk:
            srk_vars = st.multiselect("Barras:", ["Ninguna"] + k_indicador_cols, default=["Ninguna"], key="srk")
        
        selected_rk_vars = list(set(prk_vars + [x for x in srk_vars if x != "Ninguna"]))
        if selected_rk_vars:
            st.plotly_chart(plot_combined_chart(dff_indicadores, prk_vars, srk_vars, "$K (Línea)", "$K (Barras)"), use_container_width=True)
            show_table(dff_indicadores[['Período', 'Período_fmt'] + [c for c in selected_rk_vars if c in dff_indicadores.columns]], "Rel_Costo_Datos", show_totals=True)
            
            st.subheader("Variaciones Interanuales (Relaciones Costo)")
            tirk_sel = st.selectbox("Mostrar como:", ["Valores","Porcentaje"], key="tirk")
            df_for_virk = apply_time_filter(df_indicadores, filter_mode, filter_selection, all_options_dict)
            df_virk_v, df_virk_p = calc_variation(df_for_virk, selected_rk_vars, 'interanual')
            res_virk = df_virk_p if tirk_sel == 'Porcentaje' else df_virk_v
            if selected_years:
                res_virk = res_virk[res_virk['Año'].isin(selected_years)].dropna(subset=selected_rk_vars, how='all')
            else:
                res_virk = res_virk.dropna(subset=selected_rk_vars, how='all')
            st.plotly_chart(plot_bar(res_virk, selected_rk_vars, f"Variación Interanual ({'%' if tirk_sel=='Porcentaje' else '$K'})"), use_container_width=True)
            show_table(res_virk, "Rel_Costo_Var_Interanual", is_percentage=(tirk_sel=='Porcentaje'))
        
        st.markdown("---")
        st.subheader("Relaciones de Cantidad (hs / ds / dotación)")
        col1_rq, col2_rq = st.columns(2)
        with col1_rq:
            prq_vars = st.multiselect("Línea:", qty_indicador_cols, default=[qty_indicador_cols[0]] if qty_indicador_cols else [], key="prq")
        with col2_rq:
            srq_vars = st.multiselect("Barras:", ["Ninguna"] + qty_indicador_cols, default=["Ninguna"], key="srq")
        
        selected_rq_vars = list(set(prq_vars + [x for x in srq_vars if x != "Ninguna"]))
        if selected_rq_vars:
            st.plotly_chart(plot_combined_chart(dff_indicadores, prq_vars, srq_vars, "Cant (Línea)", "Cant (Barras)"), use_container_width=True)
            show_table(dff_indicadores[['Período', 'Período_fmt'] + [c for c in selected_rq_vars if c in dff_indicadores.columns]], "Rel_Cant_Datos", show_totals=True)
            
            st.subheader("Variaciones Interanuales (Relaciones Cantidad)")
            tirq_sel = st.selectbox("Mostrar como:", ["Valores","Porcentaje"], key="tirq")
            df_for_virq = apply_time_filter(df_indicadores, filter_mode, filter_selection, all_options_dict)
            df_virq_v, df_virq_p = calc_variation(df_for_virq, selected_rq_vars, 'interanual')
            res_virq = df_virq_p if tirq_sel == 'Porcentaje' else df_virq_v
            if selected_years:
                res_virq = res_virq[res_virq['Año'].isin(selected_years)].dropna(subset=selected_rq_vars, how='all')
            else:
                res_virq = res_virq.dropna(subset=selected_rq_vars, how='all')
            st.plotly_chart(plot_bar(res_virq, selected_rq_vars, f"Variación Interanual ({'%' if tirq_sel=='Porcentaje' else 'Cant'})"), use_container_width=True)
            show_table(res_virq, "Rel_Cant_Var_Interanual", is_percentage=(tirq_sel=='Porcentaje'))

# ----------------- Tab 4: INDICADORES -----------------
with tab4:
    st.subheader("Cálculo de Indicadores (Hoja: masa_salarial)")
    if not df_indicadores_empty:
        # 1. Tarjetas anuales de resumen (con lógica acumulada Sep-25)
        show_annual_indicator_cards(df_indicadores)
        
        # 2. Selectores de indicadores predefinidos
        PREDEF = {
            'HExtras_$K / Msalarial_$K (%)': ('HExtras_$K', 'Msalarial_$K', 'percent'), 
            'Guardias_$K / Msalarial_$K (%)': ('Guardias_$K', 'Msalarial_$K', 'percent'), 
            'HExtras_$K / HE_hs ($)': ('HExtras_$K', 'HE_hs', 'currency'), 
            'Guardias_$K / Guardias_ds ($)': ('Guardias_$K', 'Guardias_ds', 'currency'), 
            'Msalarial_$K / Dotación ($)': ('Msalarial_$K', 'Dotación', 'currency'), 
            'HE_hs / Dotación (hs/pers)': ('HE_hs', 'Dotación', 'number'), 
            'Guardias_ds / Dotación (ds/pers)': ('Guardias_ds', 'Dotación', 'number')
        }
        valid_p = [k for k,v in PREDEF.items() if v[0] in df_indicadores.columns and v[1] in df_indicadores.columns]
        
        st.subheader("Indicadores Predefinidos")
        sel_pre = st.multiselect("Indicadores Clave:", valid_p, key="sp", default=[])
        st.markdown("---")
        
        # 3. Selector de combinaciones personalizadas
        st.subheader("Indicadores Personalizados (Combinaciones)")
        options_l = sorted(list(set(k_indicador_cols + qty_indicador_cols)))
        possible = sorted([f"{n} / {d}" for n in options_l for d in options_l if n != d])
        sel_cust = st.multiselect("Seleccione Numerador / Denominador:", possible, key="sc", default=[])
        
        if sel_pre or sel_cust:
            # Usamos dff_indicadores (los datos filtrados por tiempo/año)
            res_calc = dff_indicadores[['Período', 'Período_fmt']].copy()
            fmts_dict = {}
            
            # Procesar predefinidos
            for k in sel_pre:
                n_c, d_c, f_t = PREDEF[k]
                try:
                    res_calc[k] = dff_indicadores[n_c].astype(float) / dff_indicadores[d_c].astype(float)
                    fmts_dict[k] = f_t
                except: res_calc[k] = np.nan
            
            # Procesar personalizados
            for k in sel_cust:
                try:
                    n_c, d_c = k.split(' / ')
                    res_calc[k] = dff_indicadores[n_c].astype(float) / dff_indicadores[d_c].astype(float)
                    fmts_dict[k] = 'number'
                except: res_calc[k] = np.nan
            
            res_calc.replace([np.inf, -np.inf], np.nan, inplace=True)
            st.subheader("Resultados Mensuales")
            show_table(res_calc, "Indicadores_Calculados", column_formats=fmts_dict)
        else:
            st.info("Seleccione indicadores de las listas superiores para visualizar la tabla mensual.")
