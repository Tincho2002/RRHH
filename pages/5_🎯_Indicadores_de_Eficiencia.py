# ===============================================================
# Visualizador de Eficiencia - V Estética (Estructura Original Completa)
# ===============================================================

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from io import BytesIO
import numpy as np # <--- AÑADIDO PARA MANEJAR inf
import traceback # Para mostrar errores detallados

# Configuración de la página para que ocupe todo el ancho
st.set_page_config(layout="wide", page_title="Visualizador de Eficiencia")

# ----------------- Funciones -----------------

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
        # Devuelve tuplas vacías extra para los nuevos datos
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
                # Si falla la conversión de fecha principal, retornar vacío
                return pd.DataFrame(), pd.DataFrame(), [], [], [], {}, [], []


            df_eficiencia['Año'] = df_eficiencia['Período'].dt.year
            df_eficiencia['Mes'] = df_eficiencia['Período'].dt.month
            df_eficiencia['Período_fmt'] = df_eficiencia['Período'].dt.strftime('%b-%y')  # Formato ej: Ene-25

            # --- Columnas de Agrupación Temporal ---
            df_eficiencia['Bimestre'] = (df_eficiencia['Mes'] - 1) // 2 + 1
            df_eficiencia['Trimestre'] = (df_eficiencia['Mes'] - 1) // 3 + 1
            df_eficiencia['Semestre'] = (df_eficiencia['Mes'] - 1) // 6 + 1

        except Exception as e_ef:
            st.error(f"Error general al procesar la hoja 'eficiencia': {e_ef}")
            return pd.DataFrame(), pd.DataFrame(), [], [], [], {}, [], []

    else:
        st.error("Error: No se encontró la hoja 'eficiencia' en el archivo Excel.")
        # Retorna dataframes vacíos si la hoja principal falta
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
                            st.warning("La pestaña 'Indicadores' no funcionará correctamente.")
                            # Mantener df_indicadores pero sin columna de fecha válida
                            df_indicadores = df_indicadores.drop(columns=['Período'], errors='ignore')
                            # Continuar sin las columnas de fecha calculadas

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


            # Definir las listas de columnas para la Tab 3
            # --- CORRECCIÓN: Asegurar $ ---
            k_indicador_cols_def = ['Msalarial_$K', 'HExtras_$K', 'Guardias_$K']
            qty_indicador_cols_def = ['HE_hs', 'Guardias_ds', 'Dotación']

            # --- MODIFICACIÓN: Añadir Dotación a k_indicador_cols si existe ---
            if 'Dotación' in df_indicadores.columns:
                 k_indicador_cols_def.append('Dotación')
            # --- FIN MODIFICACIÓN ---

            # Filtrar por las columnas que SÍ existen en el df_indicadores
            k_indicador_cols = [c for c in k_indicador_cols_def if c in df_indicadores.columns]
            qty_indicador_cols = [c for c in qty_indicador_cols_def if c in df_indicadores.columns]

        except Exception as e:
            st.error(f"Error general al procesar la hoja 'masa_salarial':")
            st.error(traceback.format_exc()) # Muestra el error completo
            # Continuar con df_indicadores vacío si falla
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
        # Elige el formateador.
        is_int_col = col.startswith(('ds_', 'hs_')) or col == 'Dotación'
        formatter = format_number_int if is_int_col else format_number

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

# --- FUNCIÓN PARA GRÁFICO COMBINADO ---
def plot_combined_chart(df_plot, primary_cols, secondary_cols, primary_title, secondary_title):
    """
    Genera un gráfico combinado con ejes multiselect.
    """
    fig = go.Figure()

    # --- Configuración del Layout (Base) ---
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

    # --- Eje Secundario (Barras) ---
    secondary_cols_filtered = [col for col in secondary_cols if col != "Ninguna"]

    if secondary_cols_filtered and not df_plot.empty and 'Período_fmt' in df_plot.columns:
        # --- Cálculo de rango manual para auto-escala ---
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
                    padding = data_range * 0.1 

                sec_min = data_min - padding
                sec_max = data_max + padding

                if data_min >= 0 and sec_min < 0:
                    sec_min = 0
            
            layout_args['yaxis2'] = {
                'title': secondary_title,
                'side': 'right',
                'overlaying': 'y',
                'showgrid': False,
                'range': [sec_min, sec_max] 
            }

            for col in valid_secondary_cols:
                is_int_col = col.startswith(('ds_', 'hs_')) or col in ['HE_hs', 'Guardias_ds', 'Dotación']
                formatter_secondary = format_number_int if is_int_col else format_number
                fig.add_trace(go.Bar(
                    x=df_plot['Período_fmt'],
                    y=df_plot[col],
                    name=col,
                    text=[formatter_secondary(v) for v in df_plot[col]],
                    textposition='outside',
                    yaxis='y2',
                    opacity=0.7
                ))

    # --- Eje Primario (Línea) ---
    if primary_cols and not df_plot.empty and 'Período_fmt' in df_plot.columns:
        valid_primary_cols = []
        for col in primary_cols:
            if col in df_plot.columns: 
                valid_primary_cols.append(col)

        if valid_primary_cols: 
            for col in valid_primary_cols:
                is_int_col = col.startswith(('ds_', 'hs_')) or col in ['HE_hs', 'Guardias_ds', 'Dotación']
                formatter_primary = format_number_int if is_int_col else format_number
                fig.add_trace(go.Scatter(
                    x=df_plot['Período_fmt'],
                    y=df_plot[col],
                    name=col,
                    mode='lines+markers+text',
                    text=[formatter_primary(v) for v in df_plot[col]],
                    textposition='top center',
                    yaxis='y1'
                ))

    fig.update_layout(**layout_args)
    return fig

def calc_variation(df, columns, tipo='mensual'):
    """
    Calcula la variación mensual o interanual de las columnas seleccionadas.
    MODIFICADO: La lógica interanual ahora usa un merge para manejar
    datos no continuos (filtrados).
    """

    columns_to_process = [col for col in columns if col in df.columns]
    if not columns_to_process or df.empty or 'Período' not in df.columns:
        return pd.DataFrame(), pd.DataFrame()

    df_var = df[['Período', 'Período_fmt', 'Año', 'Mes'] + columns_to_process].copy().sort_values('Período')

    if tipo == 'interanual':
        # 1. Separar datos del año anterior
        df_prev_ref = df_var.copy()
        df_prev_ref['Año'] = df_prev_ref['Año'] + 1 # Adelantamos para el merge

        rename_cols = {col: f"{col}_prev" for col in columns_to_process}
        df_prev_ref.rename(columns=rename_cols, inplace=True)

        df_merged = pd.merge(
            df_var.reset_index(), 
            df_prev_ref[['Año', 'Mes'] + list(rename_cols.values())],
            on=['Año', 'Mes'],
            how='left'
        ).set_index('index').sort_index() 

        df_val = pd.DataFrame(index=df_merged.index)
        df_pct = pd.DataFrame(index=df_merged.index)
        df_val['Período'] = df_merged['Período']
        df_val['Período_fmt'] = df_merged['Período_fmt']
        df_pct['Período'] = df_merged['Período']
        df_pct['Período_fmt'] = df_merged['Período_fmt']

        for col in columns_to_process:
            col_prev = f"{col}_prev"
            df_val[col] = df_merged[col] - df_merged[col_prev]
            df_pct[col] = (df_val[col] / df_merged[col_prev]) * 100
            df_pct[col] = df_pct[col].replace([np.inf, -np.inf], np.nan)

    else: # mensual
        df_val = pd.DataFrame(index=df_var.index)
        df_pct = pd.DataFrame(index=df_var.index)
        df_val['Período'] = df_var['Período']
        df_val['Período_fmt'] = df_var['Período_fmt']
        df_pct['Período'] = df_var['Período']
        df_pct['Período_fmt'] = df_var['Período_fmt']

        for col in columns_to_process:
            shift_period = 1
            df_val[col] = df_var[col].diff(periods=shift_period)
            df_pct[col] = (df_val[col] / df_var[col].shift(shift_period)) * 100

    return df_val, df_pct

def plot_bar(df_plot, columns, yaxis_title):
    """
    Genera un gráfico de barras con etiquetas de datos fuera de las barras.
    """
    fig = go.Figure()
    if not df_plot.empty and 'Período_fmt' in df_plot.columns:
        for col in columns:
            if col in df_plot.columns: 
                is_int_col = col.startswith(('ds_', 'hs_')) or col in ['HE_hs', 'Guardias_ds', 'Dotación']
                formatter = format_number_int if is_int_col else format_number

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
    """
    sort_col = 'Período' if 'Período' in df_table.columns else 'Período_fmt'

    if df_table.empty or sort_col not in df_table.columns:
        st.warning(f"Tabla '{nombre}' no se puede mostrar.")
        return

    if sort_col == 'Período_fmt':
        try:
            df_table['_temp_sort_date'] = pd.to_datetime(df_table['Período_fmt'], format='%b-%y')
            df_sorted = df_table.sort_values(by='_temp_sort_date', ascending=False).drop(columns=['_temp_sort_date'])
        except ValueError:
            df_sorted = df_table.sort_values(by='Período_fmt', ascending=False)
    else: 
        df_sorted = df_table.sort_values(by=sort_col, ascending=False)

    df_sorted = df_sorted.reset_index(drop=True)
    df_display = df_sorted.drop(columns=['Período'], errors='ignore')
    df_display.rename(columns={'Período_fmt': 'Período'}, inplace=True)

    if 'Período' in df_display.columns:
        cols = ['Período'] + [col for col in df_display.columns if col != 'Período']
        df_display = df_display[cols]
    else:
        return


    if show_totals:
        totals_row = {col: df_display[col].sum() for col in df_display.select_dtypes(include='number').columns}
        totals_row['Período'] = 'Total'
        totals_df = pd.DataFrame([totals_row])
        df_display = pd.concat([df_display, totals_df], ignore_index=True)

    df_formatted = df_display.copy()

    for col in df_formatted.select_dtypes(include='number').columns:
        if is_percentage:
            df_formatted[col] = df_formatted[col].apply(format_percentage)
        elif col.startswith(('ds_', 'hs_')) or col in ['HE_hs', 'Guardias_ds', 'Dotación']:
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

# --- FUNCIÓN KPI ---
def show_kpi_cards(df, var_list):
    if df.empty or 'Año' not in df.columns:
        st.warning("No se pueden calcular KPIs.")
        return

    vars_existentes = [v for v in var_list if v in df.columns]
    if not vars_existentes:
        return

    df_2024 = df[df['Año'] == 2024][vars_existentes].sum()
    df_2025 = df[df['Año'] == 2025][vars_existentes].sum()

    cols = st.columns(5)
    label_map = {
        '$K_50%': 'Costo HE 50%', '$K_100%': 'Costo HE 100%', '$K_Total_HE': 'Costo Total HE',
        '$K_GTO': 'Costo GTO', '$K_GTI': 'Costo GTI', '$K_Guardias_2T': 'Costo Guardias 2T',
        '$K_Guardias_3T': 'Costo Guardias 3T', '$K_TD': 'Costo TD', '$K_Total_Guardias': 'Costo Total Guardias',
        'hs_50%': 'Horas HE 50%', 'hs_100%': 'Horas HE 100%', 'hs_Total_HE': 'Horas Total HE',
        'ds_GTO': 'Días GTO', 'ds_GTI': 'Días GTI', 'ds_Guardias_2T': 'Días Guardias 2T',
        'ds_Guardias_3T': 'Días Guardias 3T', 'ds_TD': 'Días TD', 'ds_Total_Guardias': 'Días Total Guardias',
    }
    color_classes = ['card-blue', 'card-azure', 'card-violet', 'card-purple', 'card-indigo']

    col_index = 0
    for var in vars_existentes:
        total_2024 = df_2024.get(var, 0)
        total_2025 = df_2025.get(var, 0)
        delta_abs = total_2025 - total_2024
        delta_pct = (delta_abs / total_2024 * 100) if total_2024 > 0 else (100.0 if total_2025 > 0 else 0.0)

        is_int = var.startswith('ds_') or var.startswith('hs_') or var == 'Dotación'
        formatter_val = format_number_int if is_int else format_number
        val_str = formatter_val(total_2025)
        delta_abs_str = formatter_val(abs(delta_abs))
        delta_pct_fmt = format_percentage(delta_pct)

        if var.startswith('$K_'):
            value_fmt, delta_abs_fmt = f"$K {val_str}", f"$K {delta_abs_str}"
        elif var.startswith('hs_'):
            value_fmt, delta_abs_fmt = f"{val_str} hs", f"{delta_abs_str} hs"
        elif var.startswith('ds_'):
            value_fmt, delta_abs_fmt = f"{val_str} ds", f"{delta_abs_str} ds"
        elif var == 'Dotación':
             value_fmt, delta_abs_fmt = f"{val_str} pers.", f"{delta_abs_str} pers."
        else:
            value_fmt, delta_abs_fmt = val_str, delta_abs_str

        delta_icon = "↑" if delta_abs >= 0 else "↓"
        delta_color_style = "color: #86efac;" if delta_abs >= 0 else "color: #fca5a5;" 
        delta_str_html = f"<span style='{delta_color_style} font-weight: bold;'>{delta_icon} {delta_abs_fmt} ({delta_pct_fmt})</span>"

        current_col = cols[col_index % 5]
        label = label_map.get(var, var)
        color_class = color_classes[col_index % len(color_classes)]

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

# --- FUNCIÓN FILTRO TIEMPO ---
def apply_time_filter(df_to_filter, filter_mode, filter_selection, all_options_dict):
    if df_to_filter.empty or not all(c in df_to_filter.columns for c in ['Año', 'Mes', 'Bimestre', 'Trimestre', 'Semestre', 'Período_fmt']):
        return df_to_filter

    if filter_mode == 'Período Específico':
        if all_options_dict.get('all_periodos_especificos') and len(filter_selection) < len(all_options_dict['all_periodos_especificos']):
            return df_to_filter[df_to_filter['Período_fmt'].isin(filter_selection)].copy()
    elif filter_mode == 'Mes':
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
    return df_to_filter.copy()

# ----------------- Inicio de la App -----------------

st.title("Visualizador de Eficiencia")

CSS_STYLE = """
<style>
    .metric-card {
        border-radius: 12px; padding: 12px 8px; box-shadow: 0 3px 5px rgba(0, 0, 0, 0.15); color: white;
        transition: transform 0.2s ease, box-shadow 0.2s ease; border: none; display: flex; flex-direction: column;
        justify-content: center; align-items: center; text-align: center; height: auto; margin-top: 10px; margin-bottom: 10px; min-height: 110px;
    }
    .metric-card:hover { transform: translateY(-3px); box-shadow: 0 6px 12px rgba(0, 0, 0, 0.25); }
    .metric-value { font-size: 1.4rem; font-weight: 700; margin: 4px 0; line-height: 1.2; }
    .metric-label { font-size: 0.85rem; opacity: 0.9; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600; margin-bottom: 4px; line-height: 1.1; }
    .metric-delta { font-size: 0.75rem; margin-top: 4px; }
    .card-blue { background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); }
    .card-azure { background: linear-gradient(135deg, #2193b0 0%, #6dd5fa 100%); }
    .card-violet { background: linear-gradient(135deg, #4a00e0 0%, #8e2de2 100%); }
    .card-purple { background: linear-gradient(135deg, #834d9b 0%, #d04ed6 100%); }
    .card-indigo { background: linear-gradient(135deg, #182848 0%, #4b6cb7 100%); }
    div.stButton > button { width: 100%; border-radius: 8px; }
    [data-testid="column"] { padding: 0 0.75rem; }
</style>
"""
st.markdown(CSS_STYLE, unsafe_allow_html=True)

uploaded_file = st.file_uploader("Cargue el archivo 'eficiencia.xlsx'", type="xlsx")
if uploaded_file is None:
    st.info("Por favor, cargue un archivo Excel para comenzar.")
    st.stop()

# Captura de dataframes y definición de nombres globales
df_eficiencia, df_indicadores, k_columns, qty_columns, all_years, month_map, k_indicador_cols, qty_indicador_cols = load_data(uploaded_file)
df = df_eficiencia
df_indicadores_empty = df_indicadores.empty
if df.empty: st.stop()

# Diccionarios de opciones
all_opts = {
    'all_periodos_especificos': list(df.sort_values('Período')['Período_fmt'].unique()),
    'month_options': list(month_map.values()),
    'all_bimestres': sorted(df['Bimestre'].unique()),
    'all_trimestres': sorted(df['Trimestre'].unique()),
    'all_semestres': sorted(df['Semestre'].unique()),
    'months_map': month_map
}

# --- Sidebar ---
st.sidebar.header("Filtros Generales")
def reset_filters():
    st.session_state.selected_years = all_years
    st.session_state.filter_mode = 'Mes'
    st.session_state.sel_mes = all_opts['month_options']
    st.session_state.sel_bim = all_opts['all_bimestres']
    st.session_state.sel_tri = all_opts['all_trimestres']
    st.session_state.sel_sem = all_opts['all_semestres']
    st.session_state.sel_per = all_opts['all_periodos_especificos']

st.sidebar.button("🔄 Resetear Filtros", on_click=reset_filters, use_container_width=True)
st.sidebar.markdown("---")
if 'selected_years' not in st.session_state: reset_filters()

selected_years = st.sidebar.multiselect("Años:", all_years, key='selected_years')
st.sidebar.markdown("---")
filter_mode = st.sidebar.radio("Filtrar por:", ['Mes', 'Bimestre', 'Trimestre', 'Semestre', 'Período Específico'], key='filter_mode', horizontal=True)

filter_selection = []
if filter_mode == 'Mes': filter_selection = st.sidebar.multiselect("Meses:", all_opts['month_options'], key='sel_mes')
elif filter_mode == 'Bimestre': filter_selection = st.sidebar.multiselect("Bimestres:", all_opts['all_bimestres'], key='sel_bim')
elif filter_mode == 'Trimestre': filter_selection = st.sidebar.multiselect("Trimestres:", all_opts['all_trimestres'], key='sel_tri')
elif filter_mode == 'Semestre': filter_selection = st.sidebar.multiselect("Semestres:", all_opts['all_semestres'], key='sel_sem')
else: filter_selection = st.sidebar.multiselect("Períodos:", all_opts['all_periodos_especificos'], key='sel_per')

# --- Filtrado Visual de Evolución ---
df_filt_year = df[df['Año'].isin(selected_years)].copy() if selected_years else df.copy()
dff = apply_time_filter(df_filt_year, filter_mode, filter_selection, all_opts).sort_values('Período')

dff_indicadores = pd.DataFrame()
if not df_indicadores_empty:
    df_ind_base = df_indicadores[df_indicadores['Año'].isin(selected_years)].copy() if selected_years else df_indicadores.copy()
    dff_indicadores = apply_time_filter(df_ind_base, filter_mode, filter_selection, all_opts).sort_values('Período')

# --- Pestañas ---
tab1, tab2, tab3, tab4 = st.tabs(["$K (Costos)", "Cantidades (hs / ds)", "Relaciones", "Indicadores"])

# ===============================================================
# PESTAÑA COSTOS
# ===============================================================
with tab1:
    st.subheader("Totales Anuales (2025 vs 2024)")
    costo_vars = ['$K_50%', '$K_100%', '$K_Total_HE', '$K_TD', '$K_GTO', '$K_GTI', '$K_Guardias_2T', '$K_Guardias_3T', '$K_Total_Guardias']
    show_kpi_cards(df, costo_vars)
    st.markdown("---")

    st.subheader("Análisis de Costos ($K)")
    c1k, c2k = st.columns(2)
    with c1k:
        pk_vars = st.multiselect("Línea:", k_columns, default=[k_columns[0]] if k_columns else [], key="pk")
    with c2k:
        options_k_secondary = ["Ninguna"] + k_columns
        sk_vars = st.multiselect("Barras:", options_k_secondary, default=["Ninguna"], key="sk")

    selected_k_vars = list(dict.fromkeys(pk_vars + [c for c in sk_vars if c != "Ninguna"]))
    sk_plot = [c for c in sk_vars if c != "Ninguna"] if len(sk_vars) > 1 else sk_vars

    if not dff.empty and selected_k_vars:
        st.subheader("Evolución de Costos")
        fig_k = plot_combined_chart(dff, pk_vars, sk_plot, "$K (Línea)", "$K (Columnas)")
        st.plotly_chart(fig_k, use_container_width=True, key="evol_k")
        
        cols_tk = ['Período', 'Período_fmt'] + [c for c in selected_k_vars if c in dff.columns]
        show_table(dff[cols_tk].copy(), "Costos_Datos", show_totals=True)
        st.markdown("---")

        st.subheader("Variaciones Mensuales")
        tm_k = st.selectbox("Mostrar como:", ["Valores","Porcentaje"], key="mk")
        # Calculamos sobre el histórico (df) para tener referencia del mes previo
        df_cm_k = apply_time_filter(df, filter_mode, filter_selection, all_opts)
        val_mk, pct_mk = calc_variation(df_cm_k, selected_k_vars, 'mensual')
        res_mk_raw = pct_mk if tm_k == 'Porcentaje' else val_mk
        # FILTRO FINAL: Solo mostrar los años seleccionados por el usuario
        res_mk = res_mk_raw[res_mk_raw['Período'].dt.year.isin(selected_years)].copy() if selected_years else res_mk_raw.copy()
        
        st.plotly_chart(plot_bar(res_mk, selected_k_vars, "Variación Mensual"), use_container_width=True, key="var_mes_k")
        show_table(res_mk, "Costos_Var_Mensual", is_percentage=(tm_k=='Porcentaje'))
        st.markdown("---")

        st.subheader("Variaciones Interanuales")
        ta_k = st.selectbox("Mostrar como:", ["Valores","Porcentaje"], key="ak")
        df_ca_k = apply_time_filter(df, filter_mode, filter_selection, all_opts)
        val_ak, pct_ak = calc_variation(df_ca_k, selected_k_vars, 'interanual')
        res_ak_raw = pct_ak if ta_k == 'Porcentaje' else val_ak

        # --- CORRECCIÓN FINAL: NO EXCLUIR 2024 Y FILTRAR POR SELECCIÓN ---
        res_ak = res_ak_raw[res_ak_raw['Período'].dt.year.isin(selected_years)].copy() if selected_years else res_ak_raw.copy()

        st.plotly_chart(plot_bar(res_ak, selected_k_vars, "Variación Interanual"), use_container_width=True, key="var_anio_k")
        show_table(res_ak, "Costos_Var_Interanual", is_percentage=(ta_k=='Porcentaje'))

# ===============================================================
# PESTAÑA CANTIDADES
# ===============================================================
with tab2:
    st.subheader("Totales Anuales (2025 vs 2024)")
    qty_vars_tab2 = ['hs_50%', 'hs_100%', 'hs_Total_HE', 'ds_TD', 'ds_GTO', 'ds_GTI', 'ds_Guardias_2T', 'ds_Guardias_3T', 'ds_Total_Guardias']
    show_kpi_cards(df, qty_vars_tab2)
    st.markdown("---")

    st.subheader("Análisis de Cantidades (hs / ds)")
    c1q, c2q = st.columns(2)
    with c1q:
        pq_vars = st.multiselect("Línea:", qty_columns, default=[qty_columns[0]] if qty_columns else [], key="pq")
    with c2q:
        sq_vars = st.multiselect("Barras:", ["Ninguna"] + qty_columns, default=["Ninguna"], key="sq")

    selected_q_vars = list(dict.fromkeys(pq_vars + [c for c in sq_vars if c != "Ninguna"]))
    sq_plot = [c for c in sq_vars if c != "Ninguna"] if len(sq_vars) > 1 else sq_vars

    if not dff.empty and selected_q_vars:
        st.subheader("Evolución de Cantidades")
        fig_q = plot_combined_chart(dff, pq_vars, sq_plot, "Cant (L)", "Cant (B)")
        st.plotly_chart(fig_q, use_container_width=True, key="evol_qty")
        
        cols_tq = ['Período', 'Período_fmt'] + [c for c in selected_q_vars if c in dff.columns]
        show_table(dff[cols_tq].copy(), "Cant_Datos", show_totals=True)
        st.markdown("---")

        st.subheader("Variaciones Mensuales")
        tm_q = st.selectbox("Mostrar como:", ["Valores","Porcentaje"], key="mq")
        df_cm_q = apply_time_filter(df, filter_mode, filter_selection, all_opts)
        val_mq, pct_mq = calc_variation(df_cm_q, selected_q_vars, 'mensual')
        res_mq_raw = pct_mq if tm_q == 'Porcentaje' else val_mq
        res_mq = res_mq_raw[res_mq_raw['Período'].dt.year.isin(selected_years)].copy() if selected_years else res_mq_raw.copy()

        st.plotly_chart(plot_bar(res_mq, selected_q_vars, "Variación Mensual"), use_container_width=True, key="var_mes_qty")
        show_table(res_mq, "Cantidades_Var_Mensual", is_percentage=(tm_q=='Porcentaje'))
        st.markdown("---")

        st.subheader("Variaciones Interanuales")
        ta_q = st.selectbox("Mostrar como:", ["Valores","Porcentaje"], key="aq")
        df_ca_q = apply_time_filter(df, filter_mode, filter_selection, all_opts)
        val_aq, pct_aq = calc_variation(df_ca_q, selected_q_vars, 'interanual')
        res_aq_raw = pct_aq if ta_q == 'Porcentaje' else val_aq
        # NO EXCLUIR 2024
        res_aq = res_aq_raw[res_aq_raw['Período'].dt.year.isin(selected_years)].copy() if selected_years else res_aq_raw.copy()

        st.plotly_chart(plot_bar(res_aq, selected_q_vars, "Variación Interanual"), use_container_width=True, key="var_anio_qty")
        show_table(res_aq, "Cantidades_Var_Interanual", is_percentage=(ta_q=='Porcentaje'))

# ===============================================================
# PESTAÑA RELACIONES
# ===============================================================
with tab3:
    st.subheader("Análisis de Relaciones (Hoja: masa_salarial)")
    if not df_indicadores_empty and not dff_indicadores.empty:
        if k_indicador_cols:
            st.subheader("Relaciones de Costos ($K)")
            c1r, c2r = st.columns(2)
            with c1r:
                p_r = st.multiselect("Línea:", k_indicador_cols, default=[k_indicador_cols[0]] if k_indicador_cols else [], key="pr")
            with c2r:
                s_r = st.multiselect("Barras:", ["Ninguna"] + k_indicador_cols, default=["Ninguna"], key="sr")
            
            sel_r = list(dict.fromkeys(p_r + [c for c in s_r if c != "Ninguna"]))
            fig_r = plot_combined_chart(dff_indicadores, p_r, [c for c in s_r if c != "Ninguna"] if len(s_r) > 1 else s_r, "$K (L)", "$K (B)")
            st.plotly_chart(fig_r, use_container_width=True, key="evol_r")

            show_table(dff_indicadores[['Período','Período_fmt'] + [c for c in sel_r if c in dff_indicadores.columns]], "Rel_Costos", True)

            st.subheader("Variaciones Interanuales (Relaciones)")
            ta_r = st.selectbox("Mostrar como:", ["Valores","Porcentaje"], key="ar")
            df_cr = apply_time_filter(df_indicadores, filter_mode, filter_selection, all_opts)
            v_r, p_r_ = calc_variation(df_cr, sel_r, 'interanual')
            res_r_raw = p_r_ if ta_r == 'Porcentaje' else v_r
            # FILTRO DINÁMICO
            res_r = res_r_raw[res_r_raw['Período'].dt.year.isin(selected_years)].copy() if selected_years else res_r_raw.copy()
            
            st.plotly_chart(plot_bar(res_r, sel_r, "Var Interanual"), use_container_width=True)
            show_table(res_r, "Rel_Var_Interanual", is_percentage=(ta_r=='Porcentaje'))

# ===============================================================
# PESTAÑA INDICADORES (RATIOS)
# ===============================================================
with tab4:
    st.subheader("Cálculo de Indicadores (Hoja: masa_salarial)")
    if not df_indicadores_empty and not dff_indicadores.empty:
        opts_ratio = sorted(list(set(k_indicador_cols + qty_indicador_cols)))
        possible = [f"{num} / {den}" for num in opts_ratio for den in opts_ratio if num != den]
        possible.sort()
        sel_ratios = st.multiselect("Seleccione ratios:", possible, key="ind_ratios")
        if sel_ratios:
            df_ratio = dff_indicadores[['Período', 'Período_fmt']].copy().sort_values('Período')
            for r_str in sel_ratios:
                try:
                    num, den = r_str.split(' / ')
                    df_ratio[r_str] = dff_indicadores[num].astype(float) / dff_indicadores[den].astype(float)
                except: df_ratio[r_str] = np.nan
            df_ratio.replace([np.inf, -np.inf], np.nan, inplace=True)
            show_table(df_ratio, "Ratios_Resultados")
