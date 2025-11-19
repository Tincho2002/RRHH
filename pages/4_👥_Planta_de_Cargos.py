import streamlit as st
import pandas as pd
import altair as alt
from pandas.tseries.offsets import MonthEnd
from datetime import datetime
import numpy as np
import plotly.express as px
import io

# 1. CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(layout="wide", page_title="Dashboard RH", page_icon="🏢")

# --- ESTILOS CSS PERSONALIZADOS (Aesthetics) ---
def local_css():
    st.markdown("""
    <style>
        /* Estilo para las tarjetas de métricas con gradientes y hover */
        .metric-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            color: white;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            text-align: center;
            margin-bottom: 20px;
        }
        .metric-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
        }
        .metric-value {
            font-size: 2.5rem;
            font-weight: bold;
            margin: 10px 0;
        }
        .metric-label {
            font-size: 1.1rem;
            opacity: 0.9;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        /* Variaciones de color para las tarjetas */
        .card-green { background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); color: #1a472a; }
        .card-red { background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 99%, #fecfef 100%); color: #5d1818; }
        .card-blue { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
        .card-orange { background: linear-gradient(135deg, #f6d365 0%, #fda085 100%); color: #5d3a1a; }

        /* Ajustes generales de Streamlit */
        div.stButton > button {
            width: 100%;
            border-radius: 8px;
        }
        [data-testid="stMetricValue"] {
            font-size: 2rem;
        }
        h1, h2, h3 {
            font-family: 'Helvetica Neue', sans-serif;
        }
    </style>
    """, unsafe_allow_html=True)

local_css()

# --- HELPER: RENDERING DE TARJETAS HTML ---
def display_custom_metric(label, value, color_class="card-blue", icon="📊"):
    html_card = f"""
    <div class="metric-card {color_class}">
        <div class="metric-label">{icon} {label}</div>
        <div class="metric-value">{value}</div>
    </div>
    """
    st.markdown(html_card, unsafe_allow_html=True)


# --- FUNCIÓN AUXILIAR PARA DESCARGAS ---
def create_download_buttons(df, file_prefix, key_suffix):
    """Genera botones de descarga para un DataFrame en CSV y Excel."""
    @st.cache_data
    def convert_df_to_csv(dataframe):
        return dataframe.to_csv(index=False).encode('utf-8')

    @st.cache_data
    def convert_df_to_excel(dataframe):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            dataframe.to_excel(writer, index=False, sheet_name='Datos')
        processed_data = output.getvalue()
        return processed_data

    csv_data = convert_df_to_csv(df)
    excel_data = convert_df_to_excel(df)

    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            label="📥 CSV",
            data=csv_data,
            file_name=f'{file_prefix}_{datetime.now().strftime("%Y%m%d")}.csv',
            mime='text/csv',
            key=f'csv_{key_suffix}',
            use_container_width=True
        )
    with col2:
        st.download_button(
            label="📥 Excel",
            data=excel_data,
            file_name=f'{file_prefix}_{datetime.now().strftime("%Y%m%d")}.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            key=f'excel_{key_suffix}',
            use_container_width=True
        )


# 2. FUNCIÓN DE CARGA Y PROCESAMIENTO DE DATOS
@st.cache_data
def load_data(uploaded_file):
    """Carga y procesa los datos del archivo Excel."""
    try:
        df = pd.read_excel(uploaded_file)
        COL_INGRESO = 'F. de Ingreso'
        COL_EGRESO = 'F. de Egreso'
        if COL_INGRESO not in df.columns:
            st.error(f"Error Crítico: No se encontró la columna '{COL_INGRESO}'.")
            return None
        df[COL_INGRESO] = pd.to_datetime(df[COL_INGRESO], errors='coerce')
        df[COL_EGRESO] = pd.to_datetime(df.get(COL_EGRESO), errors='coerce')
        df['Año Ingreso'] = df[COL_INGRESO].dt.year
        df['Mes Ingreso'] = df[COL_INGRESO].dt.month.map({
            1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio',
            7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
        })
        df['Año Egreso'] = df[COL_EGRESO].dt.year
        df['Mes Egreso'] = df[COL_EGRESO].dt.month.map({
            1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio',
            7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
        })
        if 'Convenio' in df.columns and 'Relación' not in df.columns:
            df.rename(columns={'Convenio': 'Relación'}, inplace=True)
        if 'Relación' not in df.columns:
            df['Relación'] = "No especificado"

        def map_relacion(rel):
            rel_lower = str(rel).strip().lower()
            if 'cct' in rel_lower: return 'CCT 885/07 (Convenio)'
            elif 'fuera' in rel_lower: return 'Fuera de Convenio (FC)'
            elif 'pasant' in rel_lower: return 'Pasantes universitarios (Pasante)'
            else: return 'No especificado'

        df['Relación'] = df['Relación'].apply(map_relacion)

        cols_to_clean = ['Gerencia', 'Sexo', 'Ministerio', 'Nivel', 'Distrito', 'Función', 'Motivo de Egreso', 'I. Activo']
        for col in cols_to_clean:
            if col in df.columns:
                df[col] = df[col].fillna("No especificado").astype(str).replace({'nan': "No especificado", 'None': "No especificado"})
            else:
                df[col] = "No especificado"
        return df
    except Exception as e:
        st.error(f"Ocurrió un error al cargar el archivo: {e}")
        return None


def get_sorted_unique_options(dataframe, column_name):
    if column_name in dataframe.columns and not dataframe.empty:
        unique_values = dataframe[column_name].dropna().unique()
        if "Año" in column_name:
            numeric_years = pd.to_numeric(unique_values, errors='coerce')
            return sorted([int(y) for y in numeric_years if not pd.isna(y)], reverse=True)
        if 'Mes' in column_name:
            month_order = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
            return [m for m in month_order if m in unique_values]
        return sorted(list(unique_values))
    return []

# --- FUNCIONES DE VISUALIZACIÓN ---

def create_dotacion_breakdown(df, breakdown_column, title, selected_gerencias):
    st.markdown("---")
    st.markdown(f"### {title}") # Usando markdown para header más limpio
    stacking_column = 'Relación' if breakdown_column == 'Gerencia' else 'Gerencia'
    pivot_df = pd.pivot_table(df, index=breakdown_column, columns=stacking_column, aggfunc='size', fill_value=0)
    if stacking_column == 'Relación':
        stack_cols = ['CCT 885/07 (Convenio)', 'Fuera de Convenio (FC)', 'Pasantes universitarios (Pasante)']
    else:
        stack_cols = [g for g in selected_gerencias if g in pivot_df.columns]
        if not stack_cols:
            st.info(f"No hay datos de dotación para las gerencias seleccionadas en la categoría '{breakdown_column}'.")
            return
    for col in stack_cols:
        if col not in pivot_df.columns: pivot_df[col] = 0
    pivot_df['Total'] = pivot_df[stack_cols].sum(axis=1)
    pivot_df = pivot_df[(pivot_df.index != "No especificado") & (pivot_df['Total'] > 0)].sort_values('Total', ascending=False)
    if pivot_df.empty:
        st.info(f"No hay datos para la apertura por {breakdown_column} con los filtros actuales.")
        return
    table_df = pivot_df.reset_index()
    total_row_data = {col: table_df[col].sum() for col in stack_cols + ['Total']}
    total_row_data[breakdown_column] = '**TOTAL**'
    display_df = pd.concat([table_df, pd.DataFrame([total_row_data])], ignore_index=True)
    altair_df = table_df.melt(id_vars=[breakdown_column, 'Total'], value_vars=stack_cols, var_name=stacking_column, value_name='Cantidad')
    
    col_chart, col_table = st.columns([1.5, 1])
    sort_order = table_df[breakdown_column].tolist()
    
    with col_chart:
        base_chart = alt.Chart(altair_df).mark_bar().encode(
            x=alt.X('sum(Cantidad):Q', title='Cantidad de Empleados', stack='zero'),
            y=alt.Y(f'{breakdown_column}:N', sort=sort_order, title=breakdown_column),
            color=alt.Color(f'{stacking_column}:N', scale=alt.Scale(scheme='tableau10'), legend=alt.Legend(title=stacking_column)),
            tooltip=[breakdown_column, stacking_column, 'Cantidad'])
        text_labels = alt.Chart(table_df).mark_text(align='left', baseline='middle', dx=5, fontSize=12).encode(
            y=alt.Y(f'{breakdown_column}:N', sort=sort_order), x=alt.X('Total:Q'),
            text=alt.Text('Total:Q', format='.0f'), color=alt.value('black'))
        final_chart = (base_chart + text_labels).properties(height=max(300, len(sort_order) * 35))
        st.altair_chart(final_chart, use_container_width=True)
    with col_table:
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        create_download_buttons(display_df, f"composicion_dotacion_{breakdown_column.lower()}", f"dot_{breakdown_column}")


def create_event_category_breakdown(df, breakdown_column, title):
    st.markdown(f"### {title}")
    if df.empty:
        st.warning(f"No hay datos de {title.lower().split('por')[0]} para mostrar con los filtros actuales.")
        return
    pivot_df = pd.pivot_table(df, index=breakdown_column, columns='Relación', aggfunc='size', fill_value=0)
    rel_cols = ['CCT 885/07 (Convenio)', 'Fuera de Convenio (FC)', 'Pasantes universitarios (Pasante)']
    for col in rel_cols:
        if col not in pivot_df.columns: pivot_df[col] = 0
    pivot_df['Total'] = pivot_df[rel_cols].sum(axis=1)
    pivot_df = pivot_df[(pivot_df.index != "No especificado") & (pivot_df['Total'] > 0)].sort_values('Total', ascending=False)
    if pivot_df.empty:
        st.warning(f"No hay datos de {title.lower().split('por')[0]} para la categoría '{breakdown_column}'.")
        return
    table_df = pivot_df.reset_index()
    total_row_data = {col: table_df[col].sum() for col in rel_cols + ['Total']}
    total_row_data[breakdown_column] = '**TOTAL**'
    display_df = pd.concat([table_df, pd.DataFrame([total_row_data])], ignore_index=True)
    altair_df = table_df.melt(id_vars=[breakdown_column, 'Total'], value_vars=rel_cols, var_name='Relación', value_name='Cantidad')
    col_chart, col_table = st.columns([1.5, 1])
    sort_order = table_df[breakdown_column].tolist()
    with col_chart:
        base_chart = alt.Chart(altair_df).mark_bar().encode(
            x=alt.X('sum(Cantidad):Q', title='Cantidad', stack='zero'),
            y=alt.Y(f'{breakdown_column}:N', sort=sort_order, title=breakdown_column),
            color=alt.Color('Relación:N', scale=alt.Scale(scheme='tableau10'), legend=alt.Legend(title='Relación')),
            tooltip=[breakdown_column, 'Relación', 'Cantidad'])
        text_labels = alt.Chart(table_df).mark_text(align='left', baseline='middle', dx=5, fontSize=12).encode(
            y=alt.Y(f'{breakdown_column}:N', sort=sort_order), x=alt.X('Total:Q'),
            text=alt.Text('Total:Q', format='.0f'), color=alt.value('black'))
        final_chart = (base_chart + text_labels).properties(height=max(300, len(sort_order) * 35))
        st.altair_chart(final_chart, use_container_width=True)
    with col_table:
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        file_event_type = "ingresos" if "Ingresos" in title else "egresos"
        create_download_buttons(display_df, f"composicion_{file_event_type}_{breakdown_column.lower()}", f"evt_{file_event_type}_{breakdown_column}")


# --- FUNCIÓN MODIFICADA: VISTA COMBINADA INLINE (SOLICITUD USUARIO) ---
def create_combined_event_view(df_ingresos, df_egresos, all_months_list):
    st.markdown("### Análisis de Dinámica Mensual")
    
    # 1. Preparar y combinar datos
    def prepare_counts(df, month_col, year_col, event_type):
        df_clean = df.dropna(subset=[month_col, year_col]).copy()
        if df_clean.empty:
            return pd.DataFrame(columns=['Periodo', event_type])
        df_clean[year_col] = df_clean[year_col].astype(int).astype(str)
        df_clean['Periodo'] = df_clean[month_col] + ' ' + df_clean[year_col]
        counts = df_clean.groupby('Periodo').size().reset_index(name=event_type)
        return counts

    ingresos_counts = prepare_counts(df_ingresos, 'Mes Ingreso', 'Año Ingreso', 'Ingresos')
    egresos_counts = prepare_counts(df_egresos, 'Mes Egreso', 'Año Egreso', 'Egresos')

    # 2. Pivotar y Ordenar
    df_pivot = pd.merge(ingresos_counts, egresos_counts, on='Periodo', how='outer').fillna(0).astype({'Ingresos': int, 'Egresos': int})
    
    if df_pivot.empty:
        st.warning("No hay Ingresos ni Egresos para mostrar.")
        return

    def period_to_date(period_str):
        parts = period_str.split(' ')
        month_name = parts[0]
        year = int(parts[1])
        month_num = all_months_list.index(month_name) + 1
        return datetime(year, month_num, 1)

    df_pivot['SortDate'] = df_pivot['Periodo'].apply(period_to_date)
    df_pivot = df_pivot.sort_values('SortDate').drop(columns=['SortDate']).reset_index(drop=True)
    period_order = df_pivot['Periodo'].tolist()

    # 3. Calcular Variación y Dotación
    df_pivot['Variación Neta'] = df_pivot['Ingresos'] - df_pivot['Egresos']
    df_pivot['Dotación Acumulada'] = df_pivot['Variación Neta'].cumsum()
    
    df_bars = df_pivot[['Periodo', 'Ingresos', 'Egresos']].melt(
        id_vars='Periodo', value_vars=['Ingresos', 'Egresos'], var_name='Tipo', value_name='Cantidad'
    )
    
    # 4. Crear Gráfico
    color_scale = alt.Scale(domain=['Ingresos', 'Egresos'], range=['#28a745', '#dc3545'])

    bars = alt.Chart(df_bars).mark_bar(opacity=0.8, size=15).encode(
        x=alt.X('Periodo:N', sort=period_order, title='Período (Mes/Año)', axis=alt.Axis(labelAngle=-45)),
        xOffset=alt.XOffset('Tipo:N', title=''),
        y=alt.Y('Cantidad:Q', title='Cantidad', axis=alt.Axis(titleColor='#333333')),
        color=alt.Color('Tipo:N', scale=color_scale, legend=alt.Legend(title="Eventos")),
        tooltip=['Periodo', 'Tipo', 'Cantidad']
    )
    
    dotacion_line = alt.Chart(df_pivot).mark_line(point=True, strokeWidth=3, opacity=0.8).encode(
        x=alt.X('Periodo:N', sort=period_order),
        y=alt.Y('Dotación Acumulada:Q', title='Dot. Acumulada', axis=alt.Axis(titleColor='#1e8449', titlePadding=35)),
        color=alt.value('#1e8449'),
        tooltip=[alt.Tooltip('Periodo:N'), alt.Tooltip('Dotación Acumulada:Q', title='Dot. Acum.')]
    )
    
    net_variation_line = alt.Chart(df_pivot).mark_line(point=True, strokeWidth=3, color='#007bff').encode(
        x=alt.X('Periodo:N', sort=period_order),
        y=alt.Y('Variación Neta:Q', title='Var. Neta', axis=alt.Axis(titleColor='#007bff')),
        tooltip=[alt.Tooltip('Variación Neta:Q', title='Var. Neta')]
    )

    left_axis_chart = alt.layer(bars, dotacion_line)
    final_chart = alt.layer(left_axis_chart, net_variation_line).resolve_scale(
        y='independent'
    ).resolve_axis(
        x='shared'
    ).properties(height=400) # Altura ajustada para inline

    # 5. LAYOUT INLINE (Gráfico izquierda, Tabla derecha)
    # Usamos st.columns para ponerlos uno al lado del otro
    col_main_chart, col_main_table = st.columns([2, 1], gap="large")

    with col_main_chart:
        st.markdown("##### Evolución Gráfica")
        st.altair_chart(final_chart, use_container_width=True)
        st.info("ℹ️ **Verde**: Ingresos, **Rojo**: Egresos, **Línea Verde Oscuro**: Dotación Acumulada.")

    with col_main_table:
        st.markdown("##### Resumen Numérico")
        summary = df_pivot[['Periodo', 'Ingresos', 'Egresos', 'Variación Neta', 'Dotación Acumulada']]
        total_row = pd.DataFrame([['**TOTAL**', summary['Ingresos'].sum(), summary['Egresos'].sum(), summary['Variación Neta'].sum(), summary['Dotación Acumulada'].iloc[-1] if not summary.empty else 0]], 
                                columns=['Periodo', 'Ingresos', 'Egresos', 'Variación Neta', 'Dotación Acumulada'])
        summary_display = pd.concat([summary, total_row], ignore_index=True)
        st.dataframe(summary_display, use_container_width=True, hide_index=True, height=400)
        create_download_buttons(summary, "resumen_ingresos_vs_egresos", "combined_summary")


def create_monthly_event_view(df, month_col, year_col, title, all_months_list):
    st.markdown("---")
    st.markdown(f"### {title}")
    if df.empty:
        st.warning(f"No hay datos de {title.lower()} para mostrar con los filtros actuales.")
        return

    df_plot = df.copy()
    month_order_map = {m: i for i, m in enumerate(all_months_list)}
    
    if month_col not in df_plot.columns:
        st.warning("No existe la columna de mes en los datos.")
        return
    
    df_plot = df_plot[df_plot[month_col].notna()]

    col_chart, col_table = st.columns([1.5, 1])

    with col_chart:
        st.markdown("##### Tendencia por Año y Mes")
        base = alt.Chart(df_plot).mark_bar().encode(
            x=alt.X(f'{month_col}:N', sort=all_months_list, title='Mes'),
            y=alt.Y('count():Q', title='Cantidad'),
            color=alt.Color(f'{year_col}:N', title='Año'),
            tooltip=[f'{year_col}:N', f'{month_col}:N', 'count():Q']
        )
        text = alt.Chart(df_plot).mark_text(dy=-8, fontSize=11).encode(
            x=alt.X(f'{month_col}:N', sort=all_months_list),
            y=alt.Y('count():Q'),
            text=alt.Text('count():Q')
        )
        st.altair_chart((base + text).properties(height=350), use_container_width=True)

        st.markdown("##### Variación Mensual (Absoluta y %)")
        totals = df_plot.groupby(month_col).size().reindex(all_months_list, fill_value=0).rename('Total').reset_index().rename(columns={'index': month_col})
        totals[month_col] = totals[month_col].fillna('')
        totals['month_num'] = totals[month_col].map(month_order_map)
        totals = totals.sort_values('month_num').drop(columns=['month_num'])
        totals['Delta'] = totals['Total'].diff().fillna(0)
        totals['PctChange'] = totals['Total'].pct_change().fillna(0) * 100

        line = alt.Chart(totals).mark_line(point=True).encode(
            x=alt.X(f'{month_col}:N', sort=all_months_list, title='Mes'),
            y=alt.Y('Delta:Q', title='Cambio absoluto'),
            tooltip=[f'{month_col}:N', 'Total:Q', 'Delta:Q', alt.Tooltip('PctChange:Q', format='.2f')]
        )
        text_var = alt.Chart(totals).mark_text(dy=-10, fontSize=11).encode(
            x=alt.X(f'{month_col}:N', sort=all_months_list),
            y=alt.Y('Delta:Q'),
            text=alt.Text('Delta:Q')
        )
        st.altair_chart((line + text_var).properties(height=300), use_container_width=True)


    with col_table:
        st.markdown("##### Detalle Mensual")
        rel_cols = ['CCT 885/07 (Convenio)', 'Fuera de Convenio (FC)', 'Pasantes universitarios (Pasante)']
        table_data = pd.pivot_table(df_plot, index=[year_col, month_col], columns='Relación', aggfunc='size', fill_value=0)
        for col in rel_cols:
            if col not in table_data.columns: table_data[col] = 0
        table_data = table_data.reset_index()
        table_data.rename(columns={year_col: 'Año', month_col: 'Mes'}, inplace=True)
        table_data['Año'] = pd.to_numeric(table_data['Año'], errors='coerce')
        table_data = table_data.dropna(subset=['Año']) 
        table_data['Año'] = table_data['Año'].astype(int)
        
        table_data['month_num'] = table_data['Mes'].map(month_order_map)
        table_data = table_data.sort_values(by=['Año', 'month_num']).drop(columns=['month_num'])
        table_data['Total'] = table_data[rel_cols].sum(axis=1)
        total_row_data = {col: table_data[col].sum() for col in rel_cols + ['Total']}
        total_row_data['Año'] = "**TOTAL**"
        total_row_data['Mes'] = ""
        total_row = pd.DataFrame([total_row_data])
        display_df = pd.concat([table_data, total_row], ignore_index=True)
        st.dataframe(display_df, hide_index=True, use_container_width=True)
        
        file_event_type = "ingresos" if "Ingreso" in month_col else "egresos"
        create_download_buttons(display_df, f"detalle_mensual_{file_event_type}", f"monthly_detail_{file_event_type}")

        st.markdown("##### Tabla Variaciones")
        totals_display = totals.copy()
        totals_display['PctChange'] = totals_display['PctChange'].round(2)
        st.dataframe(totals_display.reset_index(drop=True), use_container_width=True, hide_index=True)
        create_download_buttons(totals_display, f"variacion_mensual_{file_event_type}", f"monthly_variation_{file_event_type}")


# --- INICIO DE LA APLICACIÓN ---
st.title('🏢 Planta de Cargos 2025 - Analytics')
uploaded_file = st.file_uploader("Cargue aquí su archivo de personal", type=["xlsx", "csv"])

if uploaded_file:
    df_original = load_data(uploaded_file)
    if df_original is not None and not df_original.empty:
        all_months = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
        st.sidebar.header("Menú de Análisis")
        view_mode = st.sidebar.radio("Seleccione una vista:", ('Dotación Mensualizada', 'Ingresos y Egresos'), key='view_mode')
        st.sidebar.markdown("---")
        if 'file_name' not in st.session_state or st.session_state.file_name != uploaded_file.name:
            st.session_state.clear()
            st.session_state.file_name = uploaded_file.name

        # --- INICIO: LÓGICA DE 'Dotación Mensualizada' ---
        if view_mode == 'Dotación Mensualizada':
            st.sidebar.header("Filtros de Dotación")
            if st.sidebar.button("🔄 Resetear Filtros", key='reset_dotacion'):
                filter_keys_dotacion = ['Gerencia', 'Distrito', 'Función', 'Nivel', 'Sexo', 'Ministerio', 'Relación']
                if df_original['F. de Ingreso'].notna().any():
                    latest_date = df_original['F. de Ingreso'].max()
                    fecha_referencia = latest_date + MonthEnd(0)
                    df_contexto_reset = df_original[(df_original['F. de Ingreso'] <= fecha_referencia) & ((df_original['F. de Egreso'].isnull()) | (df_original['F. de Egreso'] > fecha_referencia))]
                else:
                    df_contexto_reset = pd.DataFrame()
                st.session_state['selections_dotacion'] = {key: get_sorted_unique_options(df_contexto_reset, key) for key in filter_keys_dotacion}
                st.rerun()
            
            if df_original['F. de Ingreso'].notna().any():
                latest_date = df_original['F. de Ingreso'].max()
                fecha_referencia = latest_date + MonthEnd(0)
                df_contexto = df_original[(df_original['F. de Ingreso'] <= fecha_referencia) & ((df_original['F. de Egreso'].isnull()) | (df_original['F. de Egreso'] > fecha_referencia))]
            else:
                df_contexto = pd.DataFrame()
                fecha_referencia = datetime.now()

            filter_keys = ['Gerencia', 'Distrito', 'Función', 'Nivel', 'Sexo', 'Ministerio', 'Relación']
            session_key = 'selections_dotacion'
            if session_key not in st.session_state:
                st.session_state[session_key] = {key: get_sorted_unique_options(df_contexto, key) for key in filter_keys}
            
            selections = st.session_state[session_key]
            selections_before = selections.copy()
            df_filtered_for_options = df_contexto.copy()
            
            for f_key in filter_keys:
                options = get_sorted_unique_options(df_filtered_for_options, f_key)
                if f_key == 'Relación': options = [opt for opt in options if opt != 'No especificado']
                default = [s for s in selections.get(f_key, []) if s in options]
                selections[f_key] = st.sidebar.multiselect(f"Filtro: {f_key}", options, default=default, key=f"dot_{f_key}")
                if selections[f_key]:
                    df_filtered_for_options = df_filtered_for_options[df_filtered_for_options[f_key].isin(selections[f_key])]
            
            if selections != selections_before: st.rerun()
            
            st.markdown(f"## Dotación a {fecha_referencia.strftime('%B de %Y')}")
            
            if df_filtered_for_options.empty:
                st.warning("No se encontraron datos para los filtros seleccionados.")
            else:
                resumen = df_filtered_for_options.groupby('Relación').size().reset_index(name='Cantidad')
                
                # --- TARJETA DE METRICA PERSONALIZADA ---
                col_metric, col_pie = st.columns([1, 2])
                with col_metric:
                    display_custom_metric("Total Dotación", int(df_filtered_for_options.shape[0]), "card-blue", "👥")
                    
                    st.markdown("##### Dotación Activa por Relación")
                    st.dataframe(resumen, use_container_width=True, hide_index=True)
                    create_download_buttons(resumen, "resumen_dotacion_relacion", "dot_relacion_summary")

                with col_pie:
                    st.markdown("##### Distribución por Relación")
                    resumen['Porcentaje'] = (resumen['Cantidad'] / resumen['Cantidad'].sum() * 100).round(1)
                    resumen['Etiqueta'] = resumen.apply(lambda row: f"{row['Cantidad']} ({row['Porcentaje']}%)", axis=1)
                    colores = ['#1f77b4', '#ff7f0e', '#2ca02c']
                    fig = px.pie(
                        resumen, names='Relación', values='Cantidad', color='Relación',
                        color_discrete_sequence=colores, hole=0.4, hover_data=['Cantidad', 'Porcentaje']
                    )
                    fig.update_traces(
                        text=resumen['Etiqueta'], textinfo='text', textposition='outside',
                        textfont=dict(size=12), insidetextorientation='radial',
                        pull=[0.05, 0.05, 0.05], automargin=True  
                    )
                    fig.update_layout(
                        showlegend=True, legend_title_text='Relación',
                        legend=dict(orientation='h', yanchor='bottom', y=-0.2, xanchor='center', x=0.5),
                        margin=dict(t=40, b=80, l=50, r=50)
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                breakdown_columns = {'Gerencia': 'Composición por Gerencia', 'Nivel': 'Composición por Nivel', 'Ministerio': 'Composición por Ministerio', 'Función': 'Composición por Función', 'Distrito': 'Composición por Distrito', 'Sexo': 'Composición por Sexo'}
                st.markdown("---")
                st.markdown("### Seleccionar Vistas de Composición")
                st.info("ℹ️ Para comenzar, seleccione una o más vistas de composición en el menú de abajo para generar los gráficos.")
                selected_breakdowns = st.multiselect("Elija las aperturas que desea visualizar:", options=list(breakdown_columns.keys()))
                selected_gerencias = selections.get('Gerencia', [])
                if selected_breakdowns:
                    for breakdown_key in selected_breakdowns:
                        create_dotacion_breakdown(df_filtered_for_options, breakdown_key, breakdown_columns[breakdown_key], selected_gerencias)
                
                with st.expander("Ver detalle completo de la dotación filtrada"):
                    st.dataframe(df_filtered_for_options)
                    create_download_buttons(df_filtered_for_options, "detalle_dotacion_completa", "dot_full_detail")

        # --- INICIO: LÓGICA DE 'Ingresos y Egresos' ---
        else: 
            st.sidebar.header("Filtros de Eventos")
            sidebar_filters = ['Gerencia', 'Distrito', 'Función', 'Nivel', 'Sexo', 'Ministerio', 'Relación', 'Motivo de Egreso']
            session_key = 'selections_eventos'

            if st.sidebar.button("🔄 Resetear Filtros", key='reset_eventos'):
                initial_selections = {}
                all_years = sorted(list(set(get_sorted_unique_options(df_original, 'Año Ingreso')) | set(get_sorted_unique_options(df_original, 'Año Egreso'))), reverse=True)
                initial_selections['Año'] = all_years if all_years else [] 
                initial_selections['Mes'] = all_months
                for key in sidebar_filters: initial_selections[key] = get_sorted_unique_options(df_original, key)
                st.session_state[session_key] = initial_selections
                st.rerun()

            if session_key not in st.session_state:
                selections = {}
                all_years = sorted(list(set(get_sorted_unique_options(df_original, 'Año Ingreso')) | set(get_sorted_unique_options(df_original, 'Año Egreso'))), reverse=True)
                selections['Año'] = all_years if all_years else [] 
                selections['Mes'] = all_months
                for key in sidebar_filters: selections[key] = get_sorted_unique_options(df_original, key)
                st.session_state[session_key] = selections
            
            selections = st.session_state[session_key]
            selections_before = selections.copy()
            
            st.header("Dinámica de Personal (Ingresos y Egresos)")
            
            # Filtros principales en contenedor más limpio
            with st.container():
                col_año, col_mes = st.columns(2)
                options_año = sorted(list(set(get_sorted_unique_options(df_original, 'Año Ingreso')) | set(get_sorted_unique_options(df_original, 'Año Egreso'))), reverse=True)
                options_mes = [m for m in all_months if m in set(get_sorted_unique_options(df_original, 'Mes Ingreso')) | set(get_sorted_unique_options(df_original, 'Mes Egreso'))]

                default_año = [s for s in selections.get('Año', []) if s in options_año]
                selections['Año'] = col_año.multiselect("Filtrar por Año:", options_año, default=default_año)
                
                default_mes = [s for s in selections.get('Mes', []) if s in options_mes]
                selections['Mes'] = col_mes.multiselect("Filtrar por Mes:", options_mes, default=default_mes)
            
            for f_key in sidebar_filters:
                options = get_sorted_unique_options(df_original, f_key)
                if f_key == 'Relación': 
                    options = [opt for opt in options if opt != 'No especificado']
                default = [s for s in selections.get(f_key, []) if s in options]
                selections[f_key] = st.sidebar.multiselect(f"Filtro: {f_key}", options, default=default, key=f"evt_{f_key}")
            
            if selections != selections_before: 
                st.rerun()

            df_filtered = df_original.copy()
            for key, values in selections.items():
                if values and key not in ['Año', 'Mes']: 
                    df_filtered = df_filtered[df_filtered[key].isin(values)]
            
            df_ingresos = df_filtered.dropna(subset=['F. de Ingreso']).copy()
            if selections.get('Año'): df_ingresos = df_ingresos[df_ingresos['Año Ingreso'].isin(selections['Año'])]
            if selections.get('Mes'): df_ingresos = df_ingresos[df_ingresos['Mes Ingreso'].isin(selections['Mes'])]
            
            df_egresos = df_filtered.dropna(subset=['F. de Egreso']).copy()
            if selections.get('Año'): df_egresos = df_egresos[df_egresos['Año Egreso'].isin(selections['Año'])]
            if selections.get('Mes'): df_egresos = df_egresos[df_egresos['Mes Egreso'].isin(selections['Mes'])]
            
            # --- TARJETAS DE MÉTRICAS MEJORADAS CON CSS ---
            col_ing_m, col_eg_m = st.columns(2)
            with col_ing_m:
                display_custom_metric("Ingresos", len(df_ingresos), "card-green", "✅")
            with col_eg_m:
                display_custom_metric("Egresos", len(df_egresos), "card-red", "❌")

            st.markdown("---")
            st.subheader("Seleccionar Vistas de Análisis de Eventos")
            st.info("ℹ️ Elija una o más aperturas para analizar la composición de los Ingresos y Egresos.")
            event_breakdowns = {'Mes/Año': 'Análisis por Mes/Año', 'Gerencia': 'Análisis por Gerencia', 'Nivel': 'Análisis por Nivel', 'Ministerio': 'Análisis por Ministerio', 'Función': 'Análisis por Función', 'Distrito': 'Análisis por Distrito', 'Sexo': 'Análisis por Sexo', 'Motivo de Egreso': 'Motivo de Egreso'}
            selected_event_breakdowns = st.multiselect("Elija las aperturas que desea visualizar:", options=list(event_breakdowns.keys()))

            if selected_event_breakdowns:
                for breakdown_key in selected_event_breakdowns:
                    st.markdown("---")
                    if breakdown_key == 'Mes/Año':
                        # ESTA FUNCIÓN AHORA MUESTRA GRÁFICO Y TABLA INLINE
                        create_combined_event_view(df_ingresos, df_egresos, all_months)
                        
                        create_monthly_event_view(df_ingresos, 'Mes Ingreso', 'Año Ingreso', "Tendencia y Variación de Ingresos", all_months)
                        create_monthly_event_view(df_egresos, 'Mes Egreso', 'Año Egreso', "Tendencia y Variación de Egresos", all_months)
                    elif breakdown_key == 'Motivo de Egreso':
                        if df_egresos.empty:
                            st.warning("No hay egresos para mostrar el Motivo de Egreso con los filtros actuales.")
                        else:
                            create_event_category_breakdown(df_egresos, 'Motivo de Egreso', "Composición de Egresos por Motivo de Egreso")
                    else:
                        create_event_category_breakdown(df_ingresos, breakdown_key, f"Composición de Ingresos por {breakdown_key}")
                        st.markdown("---")
                        create_event_category_breakdown(df_egresos, breakdown_key, f"Composición de Egresos por {breakdown_key}")

            st.markdown("---")
            with st.expander("Ver detalle de Ingresos"):
                st.dataframe(df_ingresos)
                create_download_buttons(df_ingresos, "detalle_ingresos", "ingresos_full_detail")
            with st.expander("Ver detalle de Egresos"):
                st.dataframe(df_egresos)
                create_download_buttons(df_egresos, "detalle_egresos", "egresos_full_detail")
else:
    st.info("Esperando a que se cargue un archivo Excel...")