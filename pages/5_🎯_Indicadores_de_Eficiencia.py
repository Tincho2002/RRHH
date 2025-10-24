# ===============================================================
# Visualizador de Eficiencia - V Corregida y Mejorada
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
    CALCULA TOTALES DE HORAS EXTRAS Y DÍAS DE GUARDIA, y extrae
    nombres de columnas, años y meses.
    
    MODIFICADO: Ahora carga 'eficiencia' y 'masa_salarial' en
    dataframes separados, sin fusionarlos.
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
            
            # Listas de columnas para Tab 1 y Tab 2 (solo de la hoja eficiencia)
            k_cols = sorted([c for c in df_eficiencia.columns if c.startswith('$K_')])
            qty_cols = sorted([c for c in df_eficiencia.columns if c.startswith('hs_') or c.startswith('ds_')])

            # Filtros (basados en eficiencia)
            years = sorted(df_eficiencia['Año'].unique(), reverse=True)
            months_map = {1:'Ene',2:'Feb',3:'Mar',4:'Abr',5:'May',6:'Jun',7:'Jul',8:'Ago',9:'Sep',10:'Oct',11:'Nov',12:'Dic'}
        
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
            
            # Filtrar por las columnas que SÍ existen en el df_indicadores
            k_indicador_cols = [c for c in k_indicador_cols_def if c in df_indicadores.columns]
            qty_indicador_cols = [c for c in qty_indicador_cols_def if c in df_indicadores.columns]

        except Exception as e:
            st.error(f"Error general al procesar la hoja 'masa_salarial':")
            st.error(traceback.format_exc()) # Muestra el error completo
            # Continuar con df_indicadores vacío si falla
            df_indicadores = pd.DataFrame()

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
        # Elige el formateador. Todas las 'ds_' (incluida 'ds_Total_Guardias') usarán int.
        formatter = format_number_int if col.startswith(('ds_', 'hs_')) else format_number

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

# --- NUEVA FUNCIÓN PARA GRÁFICO COMBINADO (Intento 5 - Multiselect) ---
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

    # --- Eje Secundario (Barras) - PRIMERO ---
    # Filtrar "Ninguna" si está presente junto con otras selecciones
    secondary_cols_filtered = [col for col in secondary_cols if col != "Ninguna"]
    
    # Asegurarse que df_plot no esté vacío y tenga las columnas necesarias
    if secondary_cols_filtered and not df_plot.empty and 'Período_fmt' in df_plot.columns:
        # --- Cálculo de rango manual para auto-escala (para MÚLTIPLES columnas) ---
        all_sec_values = pd.Series(dtype=float)
        valid_secondary_cols = [] # Guardar columnas que sí existen
        for col in secondary_cols_filtered:
            if col in df_plot.columns: # Asegurarse que la columna existe
                all_sec_values = pd.concat([all_sec_values, df_plot[col].dropna()])
                valid_secondary_cols.append(col) # Añadir a la lista de válidas

        if valid_secondary_cols: # Solo continuar si hay columnas secundarias válidas
            sec_values = all_sec_values
            sec_min = 0
            sec_max = 1
            
            if not sec_values.empty:
                data_min = sec_values.min()
                data_max = sec_values.max()
                data_range = data_max - data_min
                
                if data_range == 0 or pd.isna(data_range):
                    # Si no hay rango (ej. un solo punto o todos iguales)
                    padding = abs(data_max * 0.1) if data_max != 0 else 1.0
                else:
                    padding = data_range * 0.1 # 10% de padding
                
                # Aplicar padding
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
                # --- MODIFICACIÓN FORMATTER ---
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
        valid_primary_cols = []
        for col in primary_cols:
            if col in df_plot.columns: # Asegurarse que la columna existe
                valid_primary_cols.append(col)

        if valid_primary_cols: # Solo dibujar si hay columnas primarias válidas
            for col in valid_primary_cols:
                # --- MODIFICACIÓN FORMATTER ---
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
    Calcula la variación mensual o interanual de las columnas seleccionadas.
    MODIFICADO: La lógica interanual ahora usa un merge para manejar
    datos no continuos (filtrados).
    """

    # --- MODIFICACIÓN ---
    # Asegurarnos de tener Año y Mes para el cálculo interanual
    # Asegurarnos de que columns no esté vacío y exista en df
    columns_to_process = [col for col in columns if col in df.columns]
    if not columns_to_process or df.empty or 'Período' not in df.columns:
        # Si no hay columnas válidas, devolver dataframes vacíos
        return pd.DataFrame(), pd.DataFrame()
        
    df_var = df[['Período', 'Período_fmt', 'Año', 'Mes'] + columns_to_process].copy().sort_values('Período')
    # --- FIN MODIFICACIÓN ---

    if tipo == 'interanual':
        # --- NUEVA LÓGICA INTERANUAL (ROBUSTA) ---

        # 1. Separar datos del año anterior
        df_last_year = df_var.copy()
        df_last_year['Año'] = df_last_year['Año'] + 1 # "Adelantamos" un año para el merge

        # 2. Renombrar columnas del año anterior para evitar conflicto
        rename_cols = {col: f"{col}_prev" for col in columns_to_process}
        df_last_year.rename(columns=rename_cols, inplace=True)

        # 3. Cruzar datos actuales con los del año anterior usando Año y Mes
        df_merged = pd.merge(
            df_var.reset_index(), # Guardar el índice original
            df_last_year[['Año', 'Mes'] + list(rename_cols.values())],
            on=['Año', 'Mes'],
            how='left'
        ).set_index('index').sort_index() # Restaurar el orden original

        # 4. Inicializar df_val y df_pct DESPUÉS del merge, basados en df_merged
        df_val = pd.DataFrame(index=df_merged.index)
        df_pct = pd.DataFrame(index=df_merged.index)
        df_val['Período'] = df_merged['Período']
        df_val['Período_fmt'] = df_merged['Período_fmt']
        df_pct['Período'] = df_merged['Período']
        df_pct['Período_fmt'] = df_merged['Período_fmt']

        # 5. Calcular la variación
        for col in columns_to_process:
            col_prev = f"{col}_prev"
            # Hacemos la resta/división
            df_val[col] = df_merged[col] - df_merged[col_prev]
            df_pct[col] = (df_val[col] / df_merged[col_prev]) * 100
            df_pct[col] = df_pct[col].replace([np.inf, -np.inf], np.nan)

        # --- FIN NUEVA LÓGICA ---
    else: # tipo == 'mensual'
        # --- MODIFICACIÓN: Adaptar esta rama a la nueva inicialización ---
        df_val = pd.DataFrame(index=df_var.index)
        df_pct = pd.DataFrame(index=df_var.index)
        df_val['Período'] = df_var['Período']
        df_val['Período_fmt'] = df_var['Período_fmt']
        df_pct['Período'] = df_var['Período']
        df_pct['Período_fmt'] = df_var['Período_fmt']
        # --- FIN MODIFICACIÓN ---

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
    # Asegurar que el df no esté vacío y tenga la columna X
    if not df_plot.empty and 'Período_fmt' in df_plot.columns:
        for col in columns:
            if col in df_plot.columns: # Asegurarse de que la columna Y existe
                # MODIFICADO: Abarcar 'hs_' y 'ds_'
                formatter = format_number_int if col.startswith(('ds_', 'hs_')) else format_number

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
        # Si ni 'Período' ni 'Período_fmt' existen después de todo, no mostrar tabla
        st.warning(f"Tabla '{nombre}' no se puede mostrar: falta columna de período formateada.")
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
        # MODIFICADO: Abarcar 'hs_' y 'ds_' y nuevas columnas
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

    df_2024 = df[df['Año'] == 2024][vars_existentes].sum()
    df_2025 = df[df['Año'] == 2025][vars_existentes].sum()

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
    for var in vars_existentes: # Iterar solo sobre las que existen
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

# --- MODIFICACIÓN: Capturar dataframes separados ---
df_eficiencia, df_indicadores, k_columns, qty_columns, all_years, month_map, k_indicador_cols, qty_indicador_cols = load_data(uploaded_file)
# --- FIN MODIFICACIÓN ---

# 'df' ahora se refiere a df_eficiencia para el resto de la app (Tabs 1, 2 y filtros)
df = df_eficiencia
df_indicadores_empty = df_indicadores.empty


if df.empty:
    # El error específico ya se muestra en load_data si falla 'eficiencia'
    st.stop()

# --- Definir listas de opciones "default" (todos seleccionados) ---
# Estas listas se basan en 'df' (eficiencia)
month_options = list(month_map.values()) if month_map else []
all_bimestres = sorted(df['Bimestre'].unique()) if 'Bimestre' in df.columns else []
all_trimestres = sorted(df['Trimestre'].unique()) if 'Trimestre' in df.columns else []
all_semestres = sorted(df['Semestre'].unique()) if 'Semestre' in df.columns else []
# Ordenar los períodos específicos cronológicamente
all_periodos_especificos = list(df.sort_values('Período')['Período_fmt'].unique()) if 'Período' in df.columns and 'Período_fmt' in df.columns else []


# Diccionario con todas las listas de opciones para la función de filtro
all_options_dict = {
    'all_periodos_especificos': all_periodos_especificos,
    'month_options': month_options,
    'all_bimestres': all_bimestres,
    'all_trimestres': all_trimestres,
    'all_semestres': all_semestres,
    'months_map': month_map
}
# --- FIN ---


# ----------------- Lógica de Filtros en Barra Lateral (MODIFICADA) -----------------
st.sidebar.header("Filtros Generales")

# --- NUEVO: Botón de Reseteo ---
# Ahora el reseteo también resetea el modo de filtro
def reset_filters():
    # Solo resetear si las listas de opciones no están vacías
    st.session_state.selected_years = all_years if all_years else []
    st.session_state.filter_mode = 'Mes' # Vuelve a 'Mes' por defecto
    # Reseteamos las selecciones específicas
    st.session_state.sel_mes = month_options if month_options else []
    st.session_state.sel_bim = all_bimestres if all_bimestres else []
    st.session_state.sel_tri = all_trimestres if all_trimestres else []
    st.session_state.sel_sem = all_semestres if all_semestres else []
    st.session_state.sel_per = all_periodos_especificos if all_periodos_especificos else []


st.sidebar.button("🔄 Resetear Filtros", on_click=reset_filters, use_container_width=True)
st.sidebar.markdown("---")

# --- MODIFICACIÓN: Inicializar Session State ---
if 'selected_years' not in st.session_state:
    reset_filters() # Llamar a la función que maneja listas vacías
# --- FIN MODIFICACIÓN ---

# Filtro de Año (sigue igual)
selected_years = st.sidebar.multiselect(
    "Años:",
    all_years if all_years else [], # Pasar lista vacía si no hay años
    key='selected_years'
)

st.sidebar.markdown("---")
# --- INICIO: NUEVA LÓGICA DE FILTRO DE TIEMPO EN CASCADA ---

# 1. Selector de MODO
filter_mode = st.sidebar.radio(
    "Filtrar por:",
    ['Mes', 'Bimestre', 'Trimestre', 'Semestre', 'Período Específico'],
    key='filter_mode',
    horizontal=True
)

# 2. Un multiselect DINÁMICO que depende del modo
filter_selection = [] # Variable para guardar la selección

# Mostrar multiselect solo si las opciones correspondientes existen
if filter_mode == 'Mes' and month_options:
    filter_selection = st.sidebar.multiselect("Meses:", month_options, key='sel_mes')
elif filter_mode == 'Bimestre' and all_bimestres:
    filter_selection = st.sidebar.multiselect("Bimestres:", all_bimestres, key='sel_bim')
elif filter_mode == 'Trimestre' and all_trimestres:
    filter_selection = st.sidebar.multiselect("Trimestres:", all_trimestres, key='sel_tri')
elif filter_mode == 'Semestre' and all_semestres:
    filter_selection = st.sidebar.multiselect("Semestres:", all_semestres, key='sel_sem')
elif filter_mode == 'Período Específico' and all_periodos_especificos:
    filter_selection = st.sidebar.multiselect("Período Específico (Mes-Año):", all_periodos_especificos, key='sel_per')
# --- FIN: NUEVA LÓGICA DE FILTRO DE TIEMPO ---


# --- LÓGICA DE FILTRADO (AHORA SIMPLIFICADA) ---

# Este dataframe 'dff' se usa para los gráficos de EVOLUCIÓN (Tabs 1 y 2)
# 1. Base: Siempre filtrar por Año (si hay años seleccionados)
if selected_years and 'Año' in df.columns:
    df_filtered_by_year = df[df['Año'].isin(selected_years)].copy()
else:
    df_filtered_by_year = df.copy() # O df vacío si falló la carga

# 2. Aplicar el filtro de tiempo único
dff = apply_time_filter(df_filtered_by_year, filter_mode, filter_selection, all_options_dict)
# Ordenar solo si el df no está vacío y tiene la columna
if not dff.empty and 'Período' in dff.columns:
    dff = dff.sort_values('Período')
# --- FIN ---

# --- NUEVO: Lógica de filtrado para df_indicadores (Tab 3) ---
dff_indicadores = pd.DataFrame() # Init empty
if not df_indicadores_empty:
    # Asegurarse de que df_indicadores tenga las columnas de filtro
    if all(col in df_indicadores.columns for col in ['Año', 'Mes', 'Bimestre', 'Trimestre', 'Semestre', 'Período_fmt']):
        # Aplicar los MISMOS filtros a df_indicadores
        if selected_years:
            df_ind_filtered_by_year = df_indicadores[df_indicadores['Año'].isin(selected_years)].copy()
        else:
            df_ind_filtered_by_year = df_indicadores.copy()
            
        dff_indicadores = apply_time_filter(df_ind_filtered_by_year, filter_mode, filter_selection, all_options_dict)
        # Ordenar solo si el df resultante no está vacío y tiene la columna
        if not dff_indicadores.empty and 'Período' in dff_indicadores.columns:
             dff_indicadores = dff_indicadores.sort_values('Período')
    else:
        st.sidebar.warning("Columnas de filtro ('Año', 'Mes', 'Período_fmt', etc.) no encontradas o inválidas en 'masa_salarial'. No se puede filtrar Tab 3.")
        dff_indicadores = df_indicadores.copy() # Usar df sin filtrar como fallback? O dejar vacío?
# --- FIN NUEVO ---


# ----------------- Pestañas de la aplicación -----------------
# --- MODIFICACIÓN: Añadir tab3 ---
tab1, tab2, tab3 = st.tabs(["$K (Costos)", "Cantidades (hs / ds)", "Indicadores"])
# --- FIN MODIFICACIÓN ---

# ----------------- Pestaña de Costos -----------------
with tab1:
    # --- SECCIÓN DE TARJETAS KPI (MODIFICADO) ---
    st.subheader("Totales Anuales (2025 vs 2024)")
    costo_vars_list = [
        '$K_50%', '$K_100%', '$K_Total_HE', '$K_TD', '$K_GTO', # Fila 1
        '$K_GTI', '$K_Guardias_2T', '$K_Guardias_3T', '$K_Total_Guardias' # Fila 2
    ]
    # Usamos 'df' (el original de eficiencia) para calcular totales
    show_kpi_cards(df, costo_vars_list)
    st.markdown("---")
    # --- FIN SECCIÓN TARJETAS ---

    st.subheader("Análisis de Costos ($K)")
    
    # --- MODIFICACIÓN: Dos multiselect en columnas ---
    col1_k, col2_k = st.columns(2)
    with col1_k:
        primary_k_vars = st.multiselect(
            "Eje Principal (Línea):", 
            k_columns, 
            default=[k_columns[0]] if k_columns else [], 
            key="primary_k"
        )
    with col2_k:
        options_k_secondary = ["Ninguna"] + k_columns
        secondary_k_vars = st.multiselect(
            "Eje Secundario (Columnas):", 
            options_k_secondary, 
            default=["Ninguna"], 
            key="secondary_k"
        )
    
    # Construir la lista 'selected_k_vars' para las tablas y variaciones
    selected_k_vars = list(primary_k_vars) # Empezar con las primarias
    secondary_k_vars_filtered = [col for col in secondary_k_vars if col != "Ninguna"]
    
    if secondary_k_vars_filtered:
        for col in secondary_k_vars_filtered:
            if col not in selected_k_vars: # Añadir solo si no está duplicada
                selected_k_vars.append(col)
    
    # Definir qué pasar al gráfico (si "Ninguna" está sola, pasarla)
    secondary_k_vars_plot = secondary_k_vars
    if "Ninguna" in secondary_k_vars and len(secondary_k_vars) > 1:
        secondary_k_vars_plot = secondary_k_vars_filtered # Quitar "Ninguna" si hay otras
    # --- FIN MODIFICACIÓN ---


    if not dff.empty and selected_k_vars: # Asegurar que dff no esté vacío
        st.subheader("Evolución de Costos")
        
        # --- MODIFICACIÓN: Llamar a la nueva función de gráfico ---
        # Usa 'dff' (eficiencia filtrado)
        fig = plot_combined_chart(
            dff, 
            primary_k_vars, # Pasar lista
            secondary_k_vars_plot, # Pasar lista filtrada
            f"$K (Línea)", 
            f"$K (Columnas)"
        )
        # --- FIN MODIFICACIÓN ---
        
        st.plotly_chart(fig, use_container_width=True, key="evol_k") 
        # Asegurarse que las columnas existan antes de seleccionar
        cols_for_table_k = ['Período', 'Período_fmt'] + [c for c in selected_k_vars if c in dff.columns]
        table_k = dff[cols_for_table_k].copy()
        show_table(table_k, "Costos_Datos", show_totals=True)
        st.markdown("---")

        st.subheader("Variaciones Mensuales")
        tipo_var_mes = st.selectbox("Mostrar como:", ["Valores","Porcentaje"], key="mes_k")

        # --- NUEVA LÓGICA DE FILTRO PARA VARIACIÓN ---
        df_for_var_mes_k = pd.DataFrame()
        if filter_mode == 'Período Específico':
            # Filtrar df original (eficiencia)
            df_for_var_mes_k = df[df['Período_fmt'].isin(filter_selection)].copy() if 'Período_fmt' in df.columns else pd.DataFrame()
        else:
            # Usa 'df' (eficiencia)
            df_for_var_mes_k = apply_time_filter(df, filter_mode, filter_selection, all_options_dict)
        # --- FIN NUEVA LÓGICA ---

        df_val_mes, df_pct_mes = calc_variation(df_for_var_mes_k, selected_k_vars,'mensual')
        is_pct_mes_k = (tipo_var_mes == 'Porcentaje')
        df_var_mes = df_pct_mes if is_pct_mes_k else df_val_mes
        fig_var_mes = plot_bar(df_var_mes, selected_k_vars, "Variación Mensual ($K)" if tipo_var_mes=='Valores' else "Variación Mensual (%)")
        st.plotly_chart(fig_var_mes, use_container_width=True, key="var_mes_k") 
        show_table(df_var_mes, "Costos_Var_Mensual", is_percentage=is_pct_mes_k)
        st.markdown("---")

        st.subheader("Variaciones Interanuales")
        tipo_var_anio = st.selectbox("Mostrar como:", ["Valores","Porcentaje"], key="inter_k") 

        # --- NUEVA LÓGICA DE FILTRO PARA VARIACIÓN ---
        df_for_var_anio_k = pd.DataFrame()
        if filter_mode == 'Período Específico' and 'Período_fmt' in df.columns:
            try:
                # Convertir selección a datetime para calcular año anterior
                selected_periods = pd.to_datetime(filter_selection, format='%b-%y', errors='coerce').dropna()
                if not selected_periods.empty:
                    compare_periods = selected_periods - pd.DateOffset(years=1)
                    all_relevant_periods = selected_periods.union(compare_periods)
                    all_relevant_fmt = all_relevant_periods.strftime('%b-%y').tolist()
                    df_for_var_anio_k = df[df['Período_fmt'].isin(all_relevant_fmt)].copy()
                else:
                    st.warning("No se pudieron procesar los períodos específicos seleccionados para la variación interanual.")
            except Exception as e:
                st.error(f"Error procesando períodos específicos para variación interanual: {e}")
        elif filter_mode != 'Período Específico':
            # Usa 'df' (eficiencia)
            df_for_var_anio_k = apply_time_filter(df, filter_mode, filter_selection, all_options_dict)
        # --- FIN NUEVA LÓGICA ---

        df_val_anio, df_pct_anio = calc_variation(df_for_var_anio_k, selected_k_vars,'interanual')
        is_pct_anio_k = (tipo_var_anio == 'Porcentaje')
        df_var_anio_raw = df_pct_anio if is_pct_anio_k else df_val_anio

        # --- MODIFICACIÓN: Excluir 2024 de Variaciones Interanuales ---
        if not df_var_anio_raw.empty and 'Período' in df_var_anio_raw.columns:
            df_var_anio = df_var_anio_raw[df_var_anio_raw['Período'].dt.year != 2024].copy()
        else:
            df_var_anio = df_var_anio_raw.copy()
        # --- FIN MODIFICACIÓN ---

        fig_var_anio = plot_bar(df_var_anio, selected_k_vars, "Variación Interanual ($K)" if tipo_var_anio=='Valores' else "Variación Interanual (%)")
        st.plotly_chart(fig_var_anio, use_container_width=True, key="var_anio_k") 

        show_table(df_var_anio, "Costos_Var_Interanual", is_percentage=is_pct_anio_k)
    elif not selected_k_vars:
         st.info("Seleccione al menos una variable de Costos ($K) para visualizar.")
    # else: # dff está vacío
    #     st.info("No hay datos de Costos para los filtros seleccionados.")


# ----------------- Pestaña de Cantidades -----------------
with tab2:
    # --- SECCIÓN DE TARJETAS KPI (MODIFICADO) ---
    st.subheader("Totales Anuales (2025 vs 2024)")
    qty_vars_list = [
        'hs_50%', 'hs_100%', 'hs_Total_HE', 'ds_TD', 'ds_GTO', # Fila 1
        'ds_GTI', 'ds_Guardias_2T', 'ds_Guardias_3T', 'ds_Total_Guardias' # Fila 2
    ]
    # Usamos 'df' (el original de eficiencia) para calcular totales
    show_kpi_cards(df, qty_vars_list)
    st.markdown("---")
    # --- FIN SECCIÓN TARJETAS ---

    st.subheader("Análisis de Cantidades (hs / ds)")
    
    # --- MODIFICACIÓN: Dos multiselect en columnas ---
    col1_q, col2_q = st.columns(2)
    with col1_q:
        primary_qty_vars = st.multiselect(
            "Eje Principal (Línea):", 
            qty_columns, 
            default=[qty_columns[0]] if qty_columns else [], 
            key="primary_qty"
        )
    with col2_q:
        options_q_secondary = ["Ninguna"] + qty_columns
        secondary_qty_vars = st.multiselect(
            "Eje Secundario (Columnas):", 
            options_q_secondary, 
            default=["Ninguna"], 
            key="secondary_qty"
        )

    # Construir la lista 'selected_qty_vars' para las tablas y variaciones
    selected_qty_vars = list(primary_qty_vars) # Empezar con las primarias
    secondary_qty_vars_filtered = [col for col in secondary_qty_vars if col != "Ninguna"]

    if secondary_qty_vars_filtered:
        for col in secondary_qty_vars_filtered:
            if col not in selected_qty_vars: # Añadir solo si no está duplicada
                selected_qty_vars.append(col)
                
    # Definir qué pasar al gráfico (si "Ninguna" está sola, pasarla)
    secondary_qty_vars_plot = secondary_qty_vars
    if "Ninguna" in secondary_qty_vars and len(secondary_qty_vars) > 1:
        secondary_qty_vars_plot = secondary_qty_vars_filtered # Quitar "Ninguna" si hay otras
    # --- FIN MODIFICACIÓN ---

    if not dff.empty and selected_qty_vars: # Asegurar que dff no esté vacío
        st.subheader("Evolución de Cantidades")
        
        # --- MODIFICACIÓN: Llamar a la nueva función de gráfico ---
        # Usa 'dff' (eficiencia filtrado)
        fig = plot_combined_chart(
            dff, 
            primary_qty_vars, # Pasar lista
            secondary_qty_vars_plot, # Pasar lista filtrada
            f"Cantidades (Línea)", 
            f"Cantidades (Columnas)"
        )
        # --- FIN MODIFICACIÓN ---
        
        st.plotly_chart(fig, use_container_width=True, key="evol_qty") 
        # Asegurarse que las columnas existan antes de seleccionar
        cols_for_table_q = ['Período', 'Período_fmt'] + [c for c in selected_qty_vars if c in dff.columns]
        table_qty = dff[cols_for_table_q].copy()
        show_table(table_qty, "Cantidades_Datos", show_totals=True)
        st.markdown("---")

        st.subheader("Variaciones Mensuales")
        tipo_var_mes_qty = st.selectbox("Mostrar como:", ["Valores","Porcentaje"], key="mes_qty") 

        # --- NUEVA LÓGICA DE FILTRO PARA VARIACIÓN ---
        df_for_var_mes_qty = pd.DataFrame()
        if filter_mode == 'Período Específico':
             # Filtrar df original (eficiencia)
            df_for_var_mes_qty = df[df['Período_fmt'].isin(filter_selection)].copy() if 'Período_fmt' in df.columns else pd.DataFrame()
        else:
            # Usa 'df' (eficiencia)
            df_for_var_mes_qty = apply_time_filter(df, filter_mode, filter_selection, all_options_dict)
        # --- FIN NUEVA LÓGICA ---

        df_val_mes_qty, df_pct_mes_qty = calc_variation(df_for_var_mes_qty, selected_qty_vars,'mensual')
        is_pct_mes_qty = (tipo_var_mes_qty == 'Porcentaje')
        df_var_mes_qty = df_pct_mes_qty if is_pct_mes_qty else df_val_mes_qty
        fig_var_mes_qty = plot_bar(df_var_mes_qty, selected_qty_vars, "Variación Mensual (Cantidad)" if tipo_var_mes_qty=='Valores' else "Variación Mensual (%)")
        st.plotly_chart(fig_var_mes_qty, use_container_width=True, key="var_mes_qty") 
        show_table(df_var_mes_qty, "Cantidades_Var_Mensual", is_percentage=is_pct_mes_qty)
        st.markdown("---")

        st.subheader("Variaciones Interanuales")
        tipo_var_anio_qty = st.selectbox("Mostrar como:", ["Valores","Porcentaje"], key="inter_qty") 

        # --- NUEVA LÓGICA DE FILTRO PARA VARIACIÓN ---
        df_for_var_anio_qty = pd.DataFrame()
        if filter_mode == 'Período Específico' and 'Período_fmt' in df.columns:
            try:
                # Convertir selección a datetime para calcular año anterior
                selected_periods = pd.to_datetime(filter_selection, format='%b-%y', errors='coerce').dropna()
                if not selected_periods.empty:
                    compare_periods = selected_periods - pd.DateOffset(years=1)
                    all_relevant_periods = selected_periods.union(compare_periods)
                    all_relevant_fmt = all_relevant_periods.strftime('%b-%y').tolist()
                    df_for_var_anio_qty = df[df['Período_fmt'].isin(all_relevant_fmt)].copy()
                else:
                    st.warning("No se pudieron procesar los períodos específicos seleccionados para la variación interanual.")

            except Exception as e:
                st.error(f"Error procesando períodos específicos para variación interanual: {e}")
        elif filter_mode != 'Período Específico':
            # Usa 'df' (eficiencia)
            df_for_var_anio_qty = apply_time_filter(df, filter_mode, filter_selection, all_options_dict)
        # --- FIN NUEVA LÓGICA ---


        df_val_anio_qty, df_pct_anio_qty = calc_variation(df_for_var_anio_qty, selected_qty_vars,'interanual')
        is_pct_anio_qty = (tipo_var_anio_qty == 'Porcentaje')
        df_var_anio_qty_raw = df_pct_anio_qty if is_pct_anio_qty else df_val_anio_qty

        # --- MODIFICACIÓN: Excluir 2024 de Variaciones Interanuales ---
        if not df_var_anio_qty_raw.empty and 'Período' in df_var_anio_qty_raw.columns:
            df_var_anio_qty = df_var_anio_qty_raw[df_var_anio_qty_raw['Período'].dt.year != 2024].copy()
        else:
            df_var_anio_qty = df_var_anio_qty_raw.copy()
        # --- FIN MODIFICACIÓN ---

        fig_var_anio_qty = plot_bar(df_var_anio_qty, selected_qty_vars, "Variación Interanual (Cantidad)" if tipo_var_anio_qty=='Valores' else "Variación Mensual (%)")
        st.plotly_chart(fig_var_anio_qty, use_container_width=True, key="var_anio_qty") 
        show_table(df_var_anio_qty, "Cantidades_Var_Interanual", is_percentage=is_pct_anio_qty)
    elif not selected_qty_vars:
        st.info("Seleccione al menos una variable de Cantidad (hs / ds) para visualizar.")
    # else: # dff está vacío
    #     st.info("No hay datos de Cantidades para los filtros seleccionados.")


# ----------------- NUEVA PESTAÑA DE INDICADORES -----------------
with tab3:
    st.subheader("Análisis de Indicadores (Hoja: masa_salarial)")

    # Verificar si los datos de indicadores se cargaron y si hay columnas para mostrar
    if df_indicadores_empty:
        # El error ya se muestra en load_data si falla la carga
        pass # No mostrar nada más aquí
    elif dff_indicadores.empty and (not df_indicadores_empty):
         st.info("Los datos de 'Indicadores' existen pero no coinciden con los filtros seleccionados (Año, Mes, etc.).")
    elif not k_indicador_cols and not qty_indicador_cols:
         st.warning("No se encontraron las columnas esperadas ('Msalarial_$K', 'HE_hs', etc.) en la hoja 'masa_salarial'.")
    else: # Si hay datos y columnas
        # --- Gráfico 1: Indicadores de Costos ($K) ---
        if k_indicador_cols: # Solo mostrar si hay columnas de costo
            st.subheader("Indicadores de Costos ($K)")
            
            col1_k_ind, col2_k_ind = st.columns(2)
            with col1_k_ind:
                primary_k_ind_vars = st.multiselect(
                    "Eje Principal ($K - Línea):", 
                    k_indicador_cols, 
                    default=[k_indicador_cols[0]] if k_indicador_cols else [], 
                    key="primary_k_ind"
                )
            with col2_k_ind:
                options_k_ind_secondary = ["Ninguna"] + k_indicador_cols
                secondary_k_ind_vars = st.multiselect(
                    "Eje Secundario ($K - Columnas):", 
                    options_k_ind_secondary, 
                    default=["Ninguna"], 
                    key="secondary_k_ind"
                )
            
            # Lógica para filtrar "Ninguna"
            secondary_k_ind_vars_plot = secondary_k_ind_vars
            if "Ninguna" in secondary_k_ind_vars and len(secondary_k_ind_vars) > 1:
                secondary_k_ind_vars_plot = [col for col in secondary_k_ind_vars if col != "Ninguna"]
            
            # --- MODIFICADO: Usar dff_indicadores ---
            if not dff_indicadores.empty:
                fig_k_ind = plot_combined_chart(
                    dff_indicadores, 
                    primary_k_ind_vars, 
                    secondary_k_ind_vars_plot, 
                    "$K (Línea)", 
                    "$K (Columnas)"
                )
                st.plotly_chart(fig_k_ind, use_container_width=True, key="evol_k_ind")
            else:
                 st.info("No hay datos de Indicadores de Costo para los filtros seleccionados.")


            st.markdown("---")

        # --- Gráfico 2: Indicadores de Cantidad (hs / ds / dotación) ---
        if qty_indicador_cols: # Solo mostrar si hay columnas de cantidad
            st.subheader("Indicadores de Cantidad (hs / ds / dotación)")
            
            col1_q_ind, col2_q_ind = st.columns(2)
            with col1_q_ind:
                primary_q_ind_vars = st.multiselect(
                    "Eje Principal (Cant. - Línea):", 
                    qty_indicador_cols, 
                    default=[qty_indicador_cols[0]] if qty_indicador_cols else [], 
                    key="primary_q_ind"
                )
            with col2_q_ind:
                options_q_ind_secondary = ["Ninguna"] + qty_indicador_cols
                secondary_q_ind_vars = st.multiselect(
                    "Eje Secundario (Cant. - Columnas):", 
                    options_q_ind_secondary, 
                    default=["Ninguna"], 
                    key="secondary_q_ind"
                )

            # Lógica para filtrar "Ninguna"
            secondary_q_ind_vars_plot = secondary_q_ind_vars
            if "Ninguna" in secondary_q_ind_vars and len(secondary_q_ind_vars) > 1:
                secondary_q_ind_vars_plot = [col for col in secondary_q_ind_vars if col != "Ninguna"]

            # --- MODIFICADO: Usar dff_indicadores ---
            if not dff_indicadores.empty:
                fig_q_ind = plot_combined_chart(
                    dff_indicadores, 
                    primary_q_ind_vars, 
                    secondary_q_ind_vars_plot, 
                    "Cantidades (Línea)", 
                    "Cantidades (Columnas)"
                )
                st.plotly_chart(fig_q_ind, use_container_width=True, key="evol_q_ind")
            else:
                 st.info("No hay datos de Indicadores de Cantidad para los filtros seleccionados.")