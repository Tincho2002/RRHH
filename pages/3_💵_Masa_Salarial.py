import streamlit as st
import pandas as pd
import altair as alt
from io import BytesIO
from fpdf import FPDF
import numpy as np

# --- Configuración de la página (DEBE SER LO PRIMERO) ---
st.set_page_config(
    layout="wide", 
    page_title="Masa Salarial Pro", 
    page_icon="💸",
    initial_sidebar_state="expanded"
)

# --- CSS Personalizado Mejorado ---
st.markdown("""
<style>
/* Variables CSS */
:root {
    --primary-color: #6C5CE7;
    --bg-color: #f0f2f6;
    --card-bg: #ffffff;
    --text-color: #1a1a2e;
    --font: 'Source Sans Pro', sans-serif;
}

.stApp { font-family: var(--font); }

/* Botones de descarga */
div[data-testid="stDownloadButton"] button {
    background-color: var(--primary-color);
    color: white;
    border-radius: 8px;
    border: none;
    transition: all 0.2s ease;
}
div[data-testid="stDownloadButton"] button:hover {
    background-color: #5A4ADF;
    box-shadow: 0 4px 8px rgba(0,0,0,0.15);
}

/* Gráficos */
[data-testid="stAltairChart"] {
    background: var(--card-bg);
    border-radius: 12px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    padding: 15px;
}

/* KPI Cards - Grid Fluido */
.metrics-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 15px;
    margin-bottom: 25px;
}

.metric-card {
    background: white;
    border-radius: 10px;
    padding: 15px 20px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    border-top: 4px solid #e2e8f0;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}

.metric-card:hover { transform: translateY(-2px); transition: transform 0.2s; }
.metric-title { font-size: 0.8rem; color: #64748b; font-weight: 700; text-transform: uppercase; margin-bottom: 5px; }
.metric-value { font-size: 1.6rem; font-weight: 800; color: #1e293b; margin: 0; }
.metric-delta { font-size: 0.8rem; font-weight: 600; margin-top: 8px; display: flex; align-items: center; }

/* Colores */
.border-blue { border-color: #3b82f6; }
.border-cyan { border-color: #06b6d4; }
.border-violet { border-color: #8b5cf6; }
.border-pink { border-color: #ec4899; }

.delta-pos { background: #dcfce7; color: #166534; padding: 2px 8px; border-radius: 12px; }
.delta-neg { background: #fee2e2; color: #991b1b; padding: 2px 8px; border-radius: 12px; }
.delta-neu { background: #f1f5f9; color: #64748b; padding: 2px 8px; border-radius: 12px; }

/* Mensaje Bienvenida */
.upload-prompt {
    text-align: center;
    padding: 3rem;
    background: white;
    border-radius: 12px;
    border: 2px dashed #cbd5e1;
    margin-top: 2rem;
}
</style>
""", unsafe_allow_html=True)

# --- Configuración Altair ---
custom_format_locale = {
    "decimal": ",", "thousands": ".", "grouping": [3], "currency": ["$", ""]
}
alt.renderers.set_embed_options(formatLocale=custom_format_locale)

# --- Funciones de Formato ---
def format_number_es(num):
    if pd.isna(num) or not isinstance(num, (int, float, np.number)): return ""
    return f"{num:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def format_integer_es(num):
    if pd.isna(num) or not isinstance(num, (int, float, np.number)): return ""
    return f"{int(num):,}".replace(",", ".")

# --- Funciones de Exportación ---
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Datos')
    return output.getvalue()

def to_pdf(df, periodo):
    periodo_str = ", ".join(periodo) if isinstance(periodo, list) else str(periodo)
    cols_to_keep = list(df.columns[:8]) 
    df_short = df[cols_to_keep].head(100)
    
    html_table = df_short.to_html(index=False, border=0, classes='table')
    html_content = f"""
    <div style="font-family: Helvetica, Arial, sans-serif;">
        <h2 style="text-align:center; color:#444;">Reporte Ejecutivo de Masa Salarial</h2>
        <p style="text-align:center; font-size:12px; color:#666;">Período: {periodo_str}</p>
        <style>
            table {{ width: 100%; border-collapse: collapse; font-size: 9px; }}
            th {{ background-color: #f8f9fa; font-weight: bold; padding: 5px; text-align: left; border-bottom: 1px solid #999; }}
            td {{ padding: 4px; border-bottom: 1px solid #eee; }}
        </style>
        {html_table}
        <p style="font-size:8px; color:#999; margin-top:10px;">Nota: Se muestran las primeras 100 filas.</p>
    </div>
    """
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    pdf.write_html(html_content)
    return bytes(pdf.output())

# --- Lógica de Filtros Inteligentes (PRESERVADA Y OPTIMIZADA) ---
def get_sorted_unique_options(dataframe, column_name):
    if column_name in dataframe.columns:
        # Usamos dropna y unique sobre categorias es muy rápido
        unique_values = dataframe[column_name].dropna().unique()
        
        # Si es category, ya tiene orden, pero convertimos a lista para streamlit
        unique_values = unique_values.tolist()
        unique_values = [v for v in unique_values if str(v) != 'no disponible']
        
        if column_name == 'Mes':
            # Mes es category ordenada en load_data, así que sort() funcionará por orden lógico
            return sorted(unique_values, key=lambda x: x) 
            
        return sorted(unique_values, key=lambda x: str(x))
    return []

def get_available_options(df, selections, target_column):
    # Filtramos el DF excluyendo el filtro de la columna objetivo
    # para ver qué opciones quedan disponibles según las OTRAS selecciones
    _df = df.copy()
    for col, values in selections.items():
        if col != target_column and values:
            _df = _df[_df[col].isin(values)]
    return get_sorted_unique_options(_df, target_column)

def apply_filters(df, selections):
    # Filtro final
    mask = pd.Series(True, index=df.index)
    for col, values in selections.items():
        if values:
            mask &= df[col].isin(values)
    return df[mask]

# --- Carga de Datos ---
@st.cache_data(ttl=3600, show_spinner="Procesando motor de cálculo...")
def load_data(file):
    try:
        df = pd.read_excel(file, sheet_name='masa_salarial', engine='openpyxl')
    except Exception as e:
        st.error(f"Error: {e}")
        return pd.DataFrame()
        
    df.columns = [str(col).strip() for col in df.columns]
    
    if 'Período' not in df.columns:
        return pd.DataFrame() # Error controlado

    # Fechas
    df['Período'] = pd.to_datetime(df['Período'], errors='coerce')
    df.dropna(subset=['Período'], inplace=True)
    df['Mes_Num'] = df['Período'].dt.month.astype(int)
    
    meses_map = {1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio', 
                 7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'}
    
    # Mes como Categoría Ordenada (Clave para gráficos)
    df['Mes'] = pd.Categorical(
        df['Mes_Num'].map(meses_map), 
        categories=list(meses_map.values()), 
        ordered=True
    )

    rename_dict = {'Clasificación Ministerio de Hacienda': 'Clasificacion_Ministerio', 'Nro. de Legajo': 'Legajo'}
    df.rename(columns=rename_dict, inplace=True)

    # OPTIMIZACIÓN: Convertir a Category para velocidad en filtros
    cols_to_category = ['Gerencia', 'Nivel', 'Clasificacion_Ministerio', 'Relación', 'Ceco']
    for col in cols_to_category:
        if col in df.columns:
            df[col] = df[col].fillna('no disponible').astype(str).astype('category')
        else:
            df[col] = pd.Categorical(['no disponible'] * len(df))

    if 'Legajo' in df.columns:
        df['Legajo'] = pd.to_numeric(df['Legajo'], errors='coerce').fillna(0).astype(int).astype(str)
    
    numeric_cols = ['Total Mensual', 'Dotación']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    return df

# --- MAIN APP ---
def main():
    st.title('💵 Dashboard de Masa Salarial')

    uploaded_file = st.sidebar.file_uploader("📂 Cargar Excel Masa Salarial", type=["xlsx"])

    if uploaded_file is None:
        st.markdown("""
        <div class="upload-prompt">
            <h3>👋 Bienvenido</h3>
            <p style="color: #666;">Por favor carga tu archivo Excel para comenzar.</p>
        </div>
        """, unsafe_allow_html=True)
        st.stop()

    df = load_data(uploaded_file)
    if df.empty: st.error("El archivo no tiene el formato correcto."); st.stop()

    # --- FILTROS INTELIGENTES ---
    st.sidebar.header('Filtros Dinámicos')
    filter_cols = ['Gerencia', 'Nivel', 'Clasificacion_Ministerio', 'Relación', 'Mes', 'Ceco', 'Legajo']
    
    # Inicializar estado
    if 'ms_selections' not in st.session_state:
        st.session_state.ms_selections = {col: [] for col in filter_cols} # Iniciar vacío

    if st.sidebar.button("🔄 Resetear Filtros"):
        st.session_state.ms_selections = {col: [] for col in filter_cols}
        st.rerun()

    # Renderizar Filtros
    for col in filter_cols:
        label = col.replace('_', ' ')
        # Aquí está la magia: Las opciones dependen de lo seleccionado en OTROS filtros
        available_options = get_available_options(df, st.session_state.ms_selections, col)
        
        # Validar que la selección actual siga siendo válida
        current_selection = st.session_state.ms_selections.get(col, [])
        valid_selection = [x for x in current_selection if x in available_options]
        
        selected = st.sidebar.multiselect(
            label,
            options=available_options,
            default=valid_selection,
            key=f"multi_{col}"
        )
        
        # Si cambia la selección, guardamos y reruneamos para actualizar los OTROS filtros
        if selected != st.session_state.ms_selections[col]:
            st.session_state.ms_selections[col] = selected
            st.rerun()

    df_filtered = apply_filters(df, st.session_state.ms_selections)

    if df_filtered.empty:
        st.warning("No hay datos que coincidan con los filtros.")
        st.stop()

    # --- KPIS (Lógica Original + Tarjetas Fix) ---
    # Mes actual y anterior (basado en selección o último disponible)
    selected_months = st.session_state.ms_selections.get('Mes', [])
    all_months_ordered = sorted(df['Mes'].unique()) # Meses disponibles en general
    
    if selected_months:
        # Si hay filtro de mes, tomamos el último seleccionado y el penúltimo seleccionado
        meses_filtrados_ordenados = sorted([m for m in selected_months], key=lambda x: all_months_ordered.index(x))
        latest_month = meses_filtrados_ordenados[-1]
        prev_month = meses_filtrados_ordenados[-2] if len(meses_filtrados_ordenados) > 1 else None
    else:
        # Si no hay filtro, tomamos el último de los datos disponibles
        available_in_filtered = sorted(df_filtered['Mes'].unique(), key=lambda x: all_months_ordered.index(x))
        if not available_in_filtered: st.stop()
        latest_month = available_in_filtered[-1]
        prev_idx = all_months_ordered.index(latest_month) - 1
        prev_month = all_months_ordered[prev_idx] if prev_idx >= 0 else None

    # Calculo de métricas (Lógica original mejorada)
    # Importante: Para calcular variación, necesitamos los datos de esos meses específicos
    # PERO aplicando el resto de los filtros (Gerencia, etc)
    filters_no_month = st.session_state.ms_selections.copy()
    filters_no_month['Mes'] = [] # Quitamos filtro de mes para buscar el mes anterior libremente
    df_base_metrics = apply_filters(df, filters_no_month)
    
    def get_metrics(d, mes):
        if mes is None: return 0, 0, 0, 0
        d_mes = d[d['Mes'] == mes]
        if d_mes.empty: return 0, 0, 0, 0
        
        total = d_mes['Total Mensual'].sum()
        dot = d_mes['Legajo'].nunique()
        
        fc = d_mes[d_mes['Nivel'] == 'FC']
        conv = d_mes[d_mes['Nivel'] != 'FC']
        
        avg_fc = fc['Total Mensual'].sum() / fc['Legajo'].nunique() if not fc.empty else 0
        avg_conv = conv['Total Mensual'].sum() / conv['Legajo'].nunique() if not conv.empty else 0
        
        return total, dot, avg_conv, avg_fc

    curr_vals = get_metrics(df_base_metrics, latest_month)
    prev_vals = get_metrics(df_base_metrics, prev_month)

    # HTML Cards FIX: Sin indentación en el string HTML para evitar bloque de código
    def kpi_card(title, val, prev, style_class, is_currency=False):
        delta = ((val - prev) / prev * 100) if prev > 0 else 0
        delta_cls = "delta-pos" if delta >= 0 else "delta-neg" # Simplificado
        arrow = "▲" if delta >= 0 else "▼"
        fmt_val = f"${format_number_es(val)}" if is_currency else format_integer_es(val)
        
        # IMPORTANTE: Todo en una línea o concatenado sin espacios al inicio de línea
        return f"""<div class="metric-card {style_class}"><div class="metric-title">{title} ({latest_month})</div><div class="metric-value">{fmt_val}</div><div class="metric-delta"><span class="{delta_cls}">{arrow} {abs(delta):.1f}%</span><span style="margin-left:5px; color:#888; font-weight:400;">vs mes ant.</span></div></div>"""

    html_cards = f"""
    <div class="metrics-grid">
        {kpi_card("Masa Salarial", curr_vals[0], prev_vals[0], "border-blue", True)}
        {kpi_card("Dotación", curr_vals[1], prev_vals[1], "border-cyan", False)}
        {kpi_card("Costo Medio Conv.", curr_vals[2], prev_vals[2], "border-violet", True)}
        {kpi_card("Costo Medio FC", curr_vals[3], prev_vals[3], "border-pink", True)}
    </div>
    """
    st.markdown(html_cards, unsafe_allow_html=True)

    # --- TABS (Restaurando estructura original + Conceptos) ---
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Evolución", "📊 Distribución", "📑 Conceptos / SIPAF", "📋 Tabla Detallada"])

    # 1. EVOLUCIÓN
    with tab1:
        st.subheader("Evolución Mensual")
        evol_data = df_filtered.groupby('Mes', observed=True)['Total Mensual'].sum().reset_index()
        
        col_chart, col_data = st.columns([3, 1])
        with col_chart:
            chart = alt.Chart(evol_data).mark_line(point=True, strokeWidth=3).encode(
                x=alt.X('Mes', title=None),
                y=alt.Y('Total Mensual', title='Masa ($)', axis=alt.Axis(format='$,.2s')),
                tooltip=['Mes', alt.Tooltip('Total Mensual', format='$,.2f')]
            ).interactive()
            st.altair_chart(chart, use_container_width=True)
        
        with col_data:
            st.dataframe(evol_data.style.format({'Total Mensual': '${:,.2f}'}), hide_index=True, use_container_width=True)

    # 2. DISTRIBUCIÓN
    with tab2:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Por Gerencia")
            ger_data = df_filtered.groupby('Gerencia', observed=True)['Total Mensual'].sum().reset_index().sort_values('Total Mensual', ascending=False)
            ch_ger = alt.Chart(ger_data).mark_bar().encode(
                x=alt.X('Total Mensual', title='Masa ($)'),
                y=alt.Y('Gerencia', sort='-x'),
                color=alt.value('#6C5CE7'),
                tooltip=['Gerencia', alt.Tooltip('Total Mensual', format='$,.2f')]
            )
            st.altair_chart(ch_ger, use_container_width=True)
        
        with c2:
            st.subheader("Por Clasificación")
            clas_data = df_filtered.groupby('Clasificacion_Ministerio', observed=True)['Total Mensual'].sum().reset_index()
            ch_clas = alt.Chart(clas_data).mark_arc(innerRadius=60).encode(
                theta='Total Mensual',
                color='Clasificacion_Ministerio',
                tooltip=['Clasificacion_Ministerio', alt.Tooltip('Total Mensual', format='$,.2f')]
            )
            st.altair_chart(ch_clas, use_container_width=True)

    # 3. CONCEPTOS / SIPAF (RESTAURADO)
    with tab3:
        st.subheader("Masa Salarial por Concepto / SIPAF")
        mode = st.radio("Vista:", ["Por Concepto", "Resumen SIPAF"], horizontal=True)
        
        # Columnas candidatas (Hardcoded de tu original para asegurar match)
        concept_cols = [c for c in df_filtered.columns if c not in filter_cols + ['Total Mensual', 'Dotación', 'Período', 'Mes_Num', 'Apellido y Nombres']]
        
        # SIPAF keywords simples para filtrar columnas
        sipaf_keywords = ['1.1.1', '1.1.3', '1.3.1', '1.3.3', '1.3.2', '1.1.4', '1.1.6', '1.1.7', '1.4']
        
        if mode == "Resumen SIPAF":
            cols_to_show = [c for c in concept_cols if any(k in c for k in sipaf_keywords)]
        else:
            # Mostrar todo lo que parezca monetario y no sea SIPAF explicito si es posible, o todo
            cols_to_show = [c for c in concept_cols if not any(k in c for k in sipaf_keywords)]
            if not cols_to_show: cols_to_show = concept_cols # Fallback
            
        if cols_to_show:
            # Agrupar y sumar
            concept_data = df_filtered[cols_to_show].sum().reset_index()
            concept_data.columns = ['Concepto', 'Total']
            concept_data = concept_data.sort_values('Total', ascending=False)
            concept_data = concept_data[concept_data['Total'] > 0] # Limpiar ceros
            
            c_concept, t_concept = st.columns([2, 1])
            with c_concept:
                ch_conc = alt.Chart(concept_data.head(20)).mark_bar().encode(
                    x=alt.X('Total', title='Monto ($)'),
                    y=alt.Y('Concepto', sort='-x'),
                    tooltip=['Concepto', alt.Tooltip('Total', format='$,.2f')]
                )
                st.altair_chart(ch_conc, use_container_width=True)
            with t_concept:
                st.dataframe(concept_data.style.format({'Total': '${:,.2f}'}), hide_index=True, use_container_width=True)
        else:
            st.info("No se encontraron columnas de conceptos con los filtros actuales.")

    # 4. TABLA DETALLADA
    with tab4:
        st.subheader("Detalle de Legajos")
        col_d1, col_d2, col_d3 = st.columns(3)
        with col_d1:
            st.download_button("📥 Excel Completo", data=to_excel(df_filtered), file_name="masa_salarial.xlsx")
        with col_d2:
            st.download_button("📥 CSV", data=df_filtered.to_csv(index=False).encode('utf-8'), file_name="masa_salarial.csv")
        with col_d3:
            # PDF simple
            pdf_df = df_filtered.copy()
            for c in ['Total Mensual']:
                if c in pdf_df.columns: pdf_df[c] = pdf_df[c].apply(lambda x: f"${format_number_es(x)}")
            st.download_button("📄 PDF Resumen", data=to_pdf(pdf_df, st.session_state.ms_selections.get('Mes', 'Varios')), file_name="reporte.pdf")
        
        st.dataframe(df_filtered, use_container_width=True)

if __name__ == "__main__":
    main()