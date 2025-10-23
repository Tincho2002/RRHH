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

# ----------------- Inicio de la App -----------------

st.title("Visualizador de Eficiencia")

uploaded_file = st.file_uploader("Cargue el archivo 'eficiencia.xlsx'", type="xlsx")

if uploaded_file is None:
    st.info("Por favor, cargue un archivo Excel para comenzar.")
    st.stop()

# df, k_columns, y qty_columns ahora contendrán los nuevos totales
df, k_columns, qty_columns, all_years, month_map = load_data(uploaded_file)

if df.empty:
    st.error("El archivo cargado está vacío o no se pudo procesar.")
    st.stop()

# ----------------- Filtros en la barra lateral -----------------
st.sidebar.header("Filtros Generales")
selected_years = st.sidebar.multiselect("Años:", all_years, default=all_years)
month_options = list(month_map.values())
selected_months_names = st.sidebar.multiselect("Meses:", month_options, default=month_options)
selected_months = [k for k,v in month_map.items() if v in selected_months_names]

dff = df[df['Año'].isin(selected_years) & df['Mes'].isin(selected_months)].copy()
dff = dff.sort_values('Período')

# ----------------- Pestañas de la aplicación -----------------
tab1, tab2 = st.tabs(["$K (Costos)", "Cantidades (hs / ds)"])

# ----------------- Pestaña de Costos -----------------
with tab1:
    st.header("Análisis de Costos ($K)")
    # El multiselect aquí ahora incluirá '$K_Total_HE' y '$K_Total_Guardias'
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
    st.header("Análisis de Cantidades (hs / ds)")
    # El multiselect aquí ahora incluirá 'hs_Total_HE' y 'ds_Total_Guardias'
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
