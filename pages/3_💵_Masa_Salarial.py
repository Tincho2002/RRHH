import streamlit as st
import pandas as pd
import altair as alt
from io import BytesIO
from fpdf import FPDF
import numpy as np
import time

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
/* Variables CSS para tema consistente */
:root {
    --primary-color: #6C5CE7;
    --bg-color: #f0f2f6;
    --card-bg: #ffffff;
    --text-color: #1a1a2e;
    --font: 'Source Sans Pro', sans-serif;
}

/* Ajuste global */
.stApp { font-family: var(--font); }

/* Botones personalizados */
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

/* Estilo para gráficos Altair */
[data-testid="stAltairChart"] {
    background: var(--card-bg);
    border-radius: 12px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    padding: 15px;
}

/* Grid de KPIs fluido */
.metrics-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    gap: 1rem;
    margin-bottom: 2rem;
}

.metric-card {
    background: white;
    border-radius: 12px;
    padding: 1.5rem;
    box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    border-top: 4px solid #e2e8f0;
    transition: transform 0.2s;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}

.metric-card:hover { transform: translateY(-3px); }
.metric-title { font-size: 0.85rem; color: #64748b; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; }
.metric-value { font-size: 1.8rem; font-weight: 800; color: #1e293b; margin: 0.5rem 0; }
.metric-delta { font-size: 0.85rem; font-weight: 600; display: inline-flex; align-items: center; gap: 0.25rem; padding: 0.25rem 0.75rem; border-radius: 999px; width: fit-content; }

/* Colores de borde y delta */
.border-blue { border-color: #3b82f6; }
.border-cyan { border-color: #06b6d4; }
.border-violet { border-color: #8b5cf6; }
.border-pink { border-color: #ec4899; }

.delta-pos { background: #dcfce7; color: #166534; }
.delta-neg { background: #fee2e2; color: #991b1b; }
.delta-neu { background: #f1f5f9; color: #64748b; }

/* Mensaje de bienvenida */
.upload-prompt {
    text-align: center;
    padding: 4rem 2rem;
    background: white;
    border-radius: 16px;
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
    if pd.isna(num) or not isinstance(num, (int, float, np.number)): return "-"
    return f"{num:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def format_integer_es(num):
    if pd.isna(num) or not isinstance(num, (int, float, np.number)): return "-"
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
            table {{ width: 100%; border-collapse: collapse; font-size: 10px; }}
            th {{ background-color: #f8f9fa; font-weight: bold; padding: 8px; text-align: left; border-bottom: 2px solid #ddd; }}
            td {{ padding: 6px; border-bottom: 1px solid #eee; }}
            tr:nth-child(even) {{ background-color: #fcfcfc; }}
        </style>
        {html_table}
        <p style="font-size:9px; color:#999; margin-top:20px;">Nota: Se muestran las primeras 100 filas.</p>
    </div>
    """
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    pdf.write_html(html_content)
    return bytes(pdf.output())

# --- Carga de Datos Optimizada ---
@st.cache_data(ttl=3600, show_spinner="Procesando datos...")
def load_data(file_path_or_buffer):
    try:
        # Engine openpyxl es lento pero seguro.
        df = pd.read_excel(file_path_or_buffer, sheet_name='masa_salarial', engine='openpyxl')
    except Exception as e:
        st.error(f"Error al leer el archivo: {e}")
        return pd.DataFrame()
        
    # Limpieza básica de columnas
    df.columns = [str(col).strip() for col in df.columns]
    
    if 'Período' not in df.columns:
        st.error("Falta la columna 'Período'.")
        return pd.DataFrame()

    # Procesamiento de fechas
    df['Período'] = pd.to_datetime(df['Período'], errors='coerce')
    df = df.dropna(subset=['Período'])
    df['Mes_Num'] = df['Período'].dt.month.astype(int)
    
    meses_map = {1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio', 
                 7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'}
    # Usamos Categorical para ordenar correctamente los meses automáticamente en los gráficos
    df['Mes'] = pd.Categorical(
        df['Mes_Num'].map(meses_map), 
        categories=list(meses_map.values()), 
        ordered=True
    )

    # Renombramientos
    rename_dict = {'Clasificación Ministerio de Hacienda': 'Clasificacion_Ministerio', 'Nro. de Legajo': 'Legajo'}
    df.rename(columns=rename_dict, inplace=True)

    # OPTIMIZACIÓN DE MEMORIA: Convertir columnas de texto (baja cardinalidad) a Category
    cols_to_category = ['Gerencia', 'Nivel', 'Clasificacion_Ministerio', 'Relación', 'Ceco']
    for col in cols_to_category:
        if col in df.columns:
            df[col] = df[col].fillna('no disponible').astype(str).astype('category')
        else:
            df[col] = pd.Categorical(['no disponible'] * len(df)) # Placeholder seguro

    # Limpieza de Legajo (mantener como string para evitar operaciones matemáticas accidentales)
    if 'Legajo' in df.columns:
        df['Legajo'] = pd.to_numeric(df['Legajo'], errors='coerce').fillna(0).astype(int).astype(str)
        
    # Asegurar numéricos
    numeric_cols = ['Total Mensual', 'Dotación']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    return df

# --- Lógica de Filtros ---
def filter_dataframe(df, selections):
    """Aplica filtros usando máscaras booleanas (más rápido que query iterativo)"""
    mask = pd.Series(True, index=df.index)
    for col, values in selections.items():
        if values:
            # Manejo especial para Mes (Categorical)
            if col == 'Mes':
                mask &= df[col].isin(values)
            else:
                mask &= df[col].isin(values)
    return df[mask]

# --- Función Principal de la App ---
def main():
    st.title('💵 Dashboard de Masa Salarial')
    
    # --- MODIFICACIÓN: SOLO CARGA MANUAL ---
    uploaded_file = st.sidebar.file_uploader("📂 Cargar Excel Masa Salarial", type=["xlsx"])
    
    if uploaded_file is None:
        # Pantalla de bienvenida clara si no hay archivo
        st.markdown("""
        <div class="upload-prompt">
            <h3>👋 Bienvenido al Sistema de Análisis Salarial</h3>
            <p style="color: #64748b; margin-bottom: 20px;">
                Por razones de confidencialidad, los datos no se almacenan en el servidor.<br>
                Por favor, sube tu archivo Excel local para comenzar el análisis en tiempo real.
            </p>
            <p style="font-size: 0.9rem; color: #94a3b8;">
                Formato esperado: Archivo Excel (.xlsx) con hoja 'masa_salarial'.
            </p>
        </div>
        """, unsafe_allow_html=True)
        st.stop()
        
    # Si hay archivo, continuamos
    df = load_data(uploaded_file)
    if df.empty: st.stop()

    # --- Sidebar: Filtros ---
    st.sidebar.header('Filtros')
    
    # Configuración de filtros
    filter_cols = ['Gerencia', 'Nivel', 'Clasificacion_Ministerio', 'Relación', 'Mes']
    
    if 'selections' not in st.session_state:
        st.session_state.selections = {col: [] for col in filter_cols}

    # Reset button
    if st.sidebar.button("🔄 Limpiar Filtros"):
        st.session_state.selections = {col: [] for col in filter_cols}
        st.rerun()

    # Renderizado de filtros (Slicers)
    df_filtered_preview = df.copy()
    for col in filter_cols:
        # Obtener opciones válidas basadas en selecciones anteriores
        valid_options = df_filtered_preview[col].unique().tolist()
        
        # Ordenar opciones
        if col == 'Mes':
            valid_options = sorted(valid_options, key=lambda x: x) # Ya es categórico ordenado
        else:
            try:
                valid_options = sorted(valid_options)
            except:
                valid_options = [str(x) for x in valid_options]
        
        current = [x for x in st.session_state.selections[col] if x in valid_options]
        
        sel = st.sidebar.multiselect(
            col.replace('_', ' '), 
            options=valid_options, 
            default=current,
            key=f"sel_{col}"
        )
        st.session_state.selections[col] = sel
        
        # Filtrar df temporal para el siguiente filtro (efecto cascada)
        if sel:
            df_filtered_preview = df_filtered_preview[df_filtered_preview[col].isin(sel)]

    # Aplicar filtros finales al dataframe principal
    df_filtered = filter_dataframe(df, st.session_state.selections)
    
    if df_filtered.empty:
        st.warning("No hay datos con los filtros actuales.")
        st.stop()

    # --- Lógica de KPIs (Mes Actual vs Anterior) ---
    # Determinar el mes de análisis
    available_months = df_filtered['Mes'].unique().sort_values()
    if len(available_months) == 0: st.stop()
    
    last_month = available_months[-1]
    prev_month = available_months[-2] if len(available_months) > 1 else None
    
    # Datos mes actual y anterior
    df_curr = df_filtered[df_filtered['Mes'] == last_month]
    df_prev = df_filtered[df_filtered['Mes'] == prev_month] if prev_month else pd.DataFrame()

    # Función auxiliar KPIs
    def calc_metrics(d):
        if d.empty: return 0, 0, 0, 0
        masa = d['Total Mensual'].sum()
        dot = d['Legajo'].nunique()
        
        # Costo Medio FC vs Conv
        mask_fc = d['Nivel'] == 'FC'
        masa_fc = d.loc[mask_fc, 'Total Mensual'].sum()
        dot_fc = d.loc[mask_fc, 'Legajo'].nunique()
        avg_fc = masa_fc / dot_fc if dot_fc > 0 else 0
        
        masa_conv = d.loc[~mask_fc, 'Total Mensual'].sum()
        dot_conv = d.loc[~mask_fc, 'Legajo'].nunique()
        avg_conv = masa_conv / dot_conv if dot_conv > 0 else 0
        
        return masa, dot, avg_conv, avg_fc

    c_masa, c_dot, c_avg_conv, c_avg_fc = calc_metrics(df_curr)
    p_masa, p_dot, p_avg_conv, p_avg_fc = calc_metrics(df_prev)

    # Generar HTML KPIs
    def card_html(title, value, prev_value, border_class, fmt_money=False):
        delta_val = ((value - prev_value) / prev_value * 100) if prev_value > 0 else 0
        delta_cls = "delta-pos" if delta_val >= 0 else "delta-neg" # Lógica simple
        
        # Lógica de color para costos (Si sube el costo es "negativo" visualmente? 
        # Depende. Usaremos Verde=Sube, Rojo=Baja para consistencia, o neutro)
        arrow = "▲" if delta_val >= 0 else "▼"
        val_str = f"${format_number_es(value)}" if fmt_money else format_integer_es(value)
        
        return f"""
        <div class="metric-card {border_class}">
            <div class="metric-title">{title} ({last_month})</div>
            <div class="metric-value">{val_str}</div>
            <div class="metric-delta {delta_cls}">
                {arrow} {abs(delta_val):.1f}% <span style="font-weight:400; font-size:0.75rem; margin-left:4px; color:#666;">vs mes ant.</span>
            </div>
        </div>
        """

    st.markdown(f"""
    <div class="metrics-grid">
        {card_html("Masa Salarial", c_masa, p_masa, "border-blue", True)}
        {card_html("Dotación (Headcount)", c_dot, p_dot, "border-cyan", False)}
        {card_html("Costo Medio Conv.", c_avg_conv, p_avg_conv, "border-violet", True)}
        {card_html("Costo Medio FC", c_avg_fc, p_avg_fc, "border-pink", True)}
    </div>
    """, unsafe_allow_html=True)

    # --- Tabs de Análisis ---
    tabs = st.tabs(["📈 Evolución", "📊 Distribución", "🌡️ Mapa de Calor", "🧮 Simulador", "📑 Datos"])

    # 1. EVOLUCIÓN
    with tabs[0]:
        col1, col2 = st.columns([3, 1])
        
        # Agrupación
        evol = df_filtered.groupby('Mes', observed=True)['Total Mensual'].sum().reset_index()
        
        with col1:
            # Gráfico Evolución con Área y Línea
            base = alt.Chart(evol).encode(x=alt.X('Mes', title=None))
            
            area = base.mark_area(opacity=0.3, color='#6C5CE7').encode(
                y=alt.Y('Total Mensual', title='Masa Salarial', axis=alt.Axis(format='$,.2s'))
            )
            line = base.mark_line(point=True, color='#6C5CE7').encode(
                y='Total Mensual',
                tooltip=['Mes', alt.Tooltip('Total Mensual', format='$,.2f')]
            )
            
            st.altair_chart((area + line).interactive(), use_container_width=True)
            
        with col2:
            st.markdown("##### Datos Mensuales")
            evol_display = evol.copy()
            evol_display['Total Mensual'] = evol_display['Total Mensual'].apply(lambda x: f"${format_number_es(x)}")
            st.dataframe(evol_display, hide_index=True, use_container_width=True)

    # 2. DISTRIBUCIÓN
    with tabs[1]:
        c1, c2 = st.columns(2)
        
        with c1:
            st.subheader("Por Gerencia (Top 10)")
            top_gerencias = df_filtered.groupby('Gerencia', observed=True)['Total Mensual'].sum().nlargest(10).reset_index()
            
            chart_bar = alt.Chart(top_gerencias).mark_bar(cornerRadiusTopRight=10, cornerRadiusBottomRight=10).encode(
                x=alt.X('Total Mensual', axis=alt.Axis(format='$,.2s')),
                y=alt.Y('Gerencia', sort='-x'),
                color=alt.value('#6C5CE7'),
                tooltip=['Gerencia', alt.Tooltip('Total Mensual', format='$,.2f')]
            ).properties(height=300)
            st.altair_chart(chart_bar, use_container_width=True)
            
        with c2:
            st.subheader("Por Clasificación")
            class_data = df_filtered.groupby('Clasificacion_Ministerio', observed=True)['Total Mensual'].sum().reset_index()
            
            chart_pie = alt.Chart(class_data).mark_arc(innerRadius=50).encode(
                theta=alt.Theta("Total Mensual", stack=True),
                color=alt.Color("Clasificacion_Ministerio", legend=alt.Legend(orient='bottom', columns=2)),
                tooltip=['Clasificacion_Ministerio', alt.Tooltip('Total Mensual', format='$,.2f')]
            ).properties(height=300)
            st.altair_chart(chart_pie, use_container_width=True)

    # 3. MAPA DE CALOR (NUEVO)
    with tabs[2]:
        st.subheader("Análisis de Intensidad: Gerencia vs Mes")
        st.markdown("Este gráfico permite identificar rápidamente qué Gerencias han tenido los picos de gasto en qué meses.")
        
        heatmap_data = df_filtered.groupby(['Gerencia', 'Mes'], observed=True)['Total Mensual'].sum().reset_index()
        
        heatmap = alt.Chart(heatmap_data).mark_rect().encode(
            x=alt.X('Mes', title=None),
            y=alt.Y('Gerencia', title=None),
            color=alt.Color('Total Mensual', legend=alt.Legend(title="Masa Salarial"), scale=alt.Scale(scheme='viridis')),
            tooltip=['Gerencia', 'Mes', alt.Tooltip('Total Mensual', format='$,.2f')]
        ).properties(height=500)
        
        st.altair_chart(heatmap, use_container_width=True)

    # 4. SIMULADOR (NUEVO)
    with tabs[3]:
        st.subheader("🧮 Simulador de Ajustes Salariales")
        st.info("Simula un % de aumento sobre el último mes seleccionado para ver el impacto proyectado.")
        
        col_sim_1, col_sim_2 = st.columns([1, 2])
        
        with col_sim_1:
            pct_aumento = st.slider("Porcentaje de Aumento General", 0.0, 50.0, 5.0, 0.5) / 100
            aplicar_a = st.multiselect("Aplicar aumento a:", 
                                       options=df_filtered['Nivel'].unique(), 
                                       default=df_filtered['Nivel'].unique())
        
        with col_sim_2:
            # Calcular impacto
            df_sim = df_curr.copy() # Usamos el último mes como base
            
            # Máscara para filas afectadas
            mask_sim = df_sim['Nivel'].isin(aplicar_a)
            
            costo_actual = df_sim['Total Mensual'].sum()
            
            # Calculamos el incremento solo en las filas seleccionadas
            incremento = df_sim.loc[mask_sim, 'Total Mensual'].sum() * pct_aumento
            costo_futuro = costo_actual + incremento
            
            st.metric("Masa Salarial Actual (Mensual)", f"${format_number_es(costo_actual)}")
            st.metric("Impacto del Aumento (+)", f"${format_number_es(incremento)}", delta=f"{pct_aumento*100:.1f}%")
            st.metric("Nueva Masa Proyectada", f"${format_number_es(costo_futuro)}")

    # 5. DATOS
    with tabs[4]:
        st.subheader("Explorador de Datos")
        col_dl1, col_dl2, col_dl3 = st.columns(3)
        
        with col_dl1:
            st.download_button("📥 Descargar Excel Completo", data=to_excel(df_filtered), file_name="masa_salarial_filtrada.xlsx")
        with col_dl2:
            st.download_button("📥 Descargar CSV", data=df_filtered.to_csv(index=False).encode('utf-8'), file_name="masa_salarial.csv")
        with col_dl3:
             # Preparar datos para PDF (formato string limpio)
             pdf_df = df_filtered.copy()
             cols_money = ['Total Mensual', 'Total Sujeto a Retención'] # Añadir otras si existen
             for c in cols_money:
                 if c in pdf_df.columns: pdf_df[c] = pdf_df[c].apply(lambda x: f"${format_number_es(x)}")
             
             st.download_button("📄 Descargar Reporte PDF", data=to_pdf(pdf_df, st.session_state.selections.get('Mes', 'Varios')), file_name="reporte.pdf")

        st.dataframe(df_filtered, use_container_width=True, height=500)

if __name__ == "__main__":
    main()