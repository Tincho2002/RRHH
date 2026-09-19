import streamlit as st
import pandas as pd
import numpy as np
import io
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- Configuración de la página y Estilos ---
st.set_page_config(layout="wide", page_title="Ausentismo y Licencias", page_icon="🩺")

st.markdown("""
<style>
div[data-testid="stSidebar"] div[data-testid="stButton"] button {
    border-radius: 0.5rem;
    font-weight: bold;
    width: 100%;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

div.stDownloadButton button {
    background-color: #28a745;
    color: white;
    font-weight: bold;
    padding: 0.75rem 1.25rem;
    border-radius: 0.5rem;
    border: none;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

@media (max-width: 768px) {
    h1 { font-size: 1.9rem; }
    h2 { font-size: 1.5rem; }
    h3 { font-size: 1.2rem; }
    div[data-testid="stHorizontalBlock"] {
        flex-wrap: wrap !important;
    }
}
</style>
""", unsafe_allow_html=True)

# --- Funciones de Formato ---
def format_integer_es(num):
    if pd.isna(num) or not isinstance(num, (int, float, np.number)): return ""
    return f"{int(round(num)):,}".replace(",", ".")

def format_percentage_es(num, decimals=2):
    if pd.isna(num) or not isinstance(num, (int, float, np.number)): return ""
    return f"{num:,.{decimals}f}%".replace(",", "TEMP").replace(".", ",").replace("TEMP", ".")

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

# --- Carga y Normalización de Datos ---
@st.cache_data
def load_and_process_data(uploaded_file):
    try:
        xls = pd.ExcelFile(uploaded_file, engine='openpyxl')
        sheet_au = 'Data_Au' if 'Data_Au' in xls.sheet_names else xls.sheet_names[0]
        df_au = pd.read_excel(xls, sheet_name=sheet_au)
        
        # Eliminar columnas Unnamed
        df_au = df_au.loc[:, ~df_au.columns.astype(str).str.startswith('Unnamed:')]
        
        # Normalizar columnas numéricas
        if 'Total (D)' in df_au.columns:
            df_au['Total (D)'] = pd.to_numeric(df_au['Total (D)'], errors='coerce').fillna(0)
        else:
            df_au['Total (D)'] = 0
            
        if 'Total (H)' in df_au.columns:
            df_au['Total (H)'] = pd.to_numeric(df_au['Total (H)'], errors='coerce').fillna(0)
        else:
            df_au['Total (H)'] = 0

        if 'Dias_Habiles' in df_au.columns:
            df_au['Dias_Habiles'] = pd.to_numeric(df_au['Dias_Habiles'], errors='coerce').fillna(21)
        else:
            df_au['Dias_Habiles'] = 21

        # Mapeo de meses y creación de etiquetas cronológicas (ej: 'Ene-26')
        mapa_meses = {1: 'Ene', 2: 'Feb', 3: 'Mar', 4: 'Abr', 5: 'May', 6: 'Jun', 7: 'Jul', 8: 'Ago', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dic'}
        if 'Período' in df_au.columns:
            temp_dt = pd.to_datetime(df_au['Período'], errors='coerce')
            df_au['Periodo_Label'] = temp_dt.dt.month.map(mapa_meses) + '-' + temp_dt.dt.strftime('%y')
            df_au['Periodo_DT'] = temp_dt
        elif 'Mes' in df_au.columns:
            df_au['Periodo_Label'] = df_au['Mes'].astype(str).str.capitalize()
            df_au['Periodo_DT'] = pd.to_datetime('2026-01-01')

        # Cargar dotación y normalizarla
        df_dot = None
        if 'Dotación' in xls.sheet_names:
            df_dot = pd.read_excel(xls, sheet_name='Dotación')
            df_dot = df_dot.loc[:, ~df_dot.columns.astype(str).str.startswith('Unnamed:')]
            if 'Periodo' in df_dot.columns:
                temp_dt_dot = pd.to_datetime(df_dot['Periodo'], errors='coerce')
                df_dot['Periodo_Label'] = temp_dt_dot.dt.month.map(mapa_meses) + '-' + temp_dt_dot.dt.strftime('%y')
                df_dot['Periodo_DT'] = temp_dt_dot
            
            # Normalizar columnas de texto en Dotación para filtros cruzados
            dot_filter_cols = ['Gerencia', 'Ministerio', 'Distrito', 'Relación', 'Nivel', 'Sexo']
            for c in dot_filter_cols:
                if c in df_dot.columns:
                    df_dot[c] = df_dot[c].astype(str).replace(['nan', 'None', '<NA>'], 'no disponible').str.strip()

        # Normalizar columnas de texto en Ausentismo
        filter_cols = ['Legajo', 'Gerencia', 'Ministerio', 'Distrito', 'Relación', 'Nivel', 'Sexo', 'Tipo', 'Descripción', 'Licencia']
        for c in filter_cols:
            if c in df_au.columns:
                df_au[c] = df_au[c].astype(str).replace(['nan', 'None', '<NA>'], 'no disponible').str.strip()
            else:
                df_au[c] = 'no disponible'

        return df_au, df_dot
    except Exception as e:
        st.error(f"Error al leer el archivo: {e}")
        return pd.DataFrame(), None

# --- UI Principal ---
st.title("🩺 Gestión de Ausentismo y Licencias")
st.write("Análisis integral de ausentismo en días y horas, capacidad teórica e impacto operativo.")

uploaded_file = st.file_uploader("📂 Cargue aquí su archivo Excel de Licencias / Ausentismo", type=["xlsx"])
st.markdown("---")

if uploaded_file is not None:
    with st.spinner("Procesando datos de ausentismo..."):
        df_au, df_dot = load_and_process_data(uploaded_file)

    if df_au.empty:
        st.error("No se encontraron registros en el archivo cargado.")
        st.stop()

    st.success(f"Se procesaron con éxito **{format_integer_es(len(df_au))}** registros de novedades y licencias.")
    st.markdown("---")

    # --- Barra Lateral de Filtros ---
    st.sidebar.header("Filtros de Ausentismo")

    filter_dict = {
        'Periodo_Label': 'Período',
        'Tipo': 'Tipo de Novedad',
        'Licencia': 'Licencia / Concepto',
        'Gerencia': 'Gerencia',
        'Ministerio': 'Ministerio',
        'Distrito': 'Distrito',
        'Relación': 'Relación Laboral',
        'Nivel': 'Nivel',
        'Sexo': 'Sexo'
    }

    periodos_ordenados = df_au.sort_values('Periodo_DT')['Periodo_Label'].dropna().unique().tolist()

    if 'au_selections' not in st.session_state:
        st.session_state.au_selections = {
            k: (periodos_ordenados if k == 'Periodo_Label' else sorted(df_au[k].unique().tolist()))
            for k in filter_dict.keys()
        }

    if st.sidebar.button("🔄 Resetear Filtros", use_container_width=True):
        st.session_state.au_selections = {
            k: (periodos_ordenados if k == 'Periodo_Label' else sorted(df_au[k].unique().tolist()))
            for k in filter_dict.keys()
        }
        st.rerun()

    filtered_df = df_au.copy()
    filtered_dot = df_dot.copy() if df_dot is not None else None

    # Aplicar filtros a Ausentismo y a Dotación en simultáneo
    for col, label in filter_dict.items():
        opts = periodos_ordenados if col == 'Periodo_Label' else sorted(df_au[col].unique().tolist())
        sel = st.sidebar.multiselect(label, options=opts, default=st.session_state.au_selections.get(col, opts), key=f"sel_{col}")
        st.session_state.au_selections[col] = sel
        if sel:
            filtered_df = filtered_df[filtered_df[col].isin(sel)]
            if filtered_dot is not None and col in filtered_dot.columns:
                filtered_dot = filtered_dot[filtered_dot[col].isin(sel)]
        else:
            filtered_df = filtered_df.iloc[0:0]
            if filtered_dot is not None and col in filtered_dot.columns:
                filtered_dot = filtered_dot.iloc[0:0]

    # Validaciones de filtros
    sel_periodos = [p for p in periodos_ordenados if p in st.session_state.au_selections.get('Periodo_Label', [])]

    if not sel_periodos:
        st.warning("⚠️ No hay ningún período seleccionado en el filtro **Período**. Seleccione al menos un mes en la barra lateral.")
        st.stop()

    if filtered_df.empty:
        st.warning("⚠️ No se encontraron registros con los filtros seleccionados.")
        st.stop()

    # --- CÁLCULO DE CAPACIDAD Y AUSENTISMO EXACTO (Total Acumulado) ---
    dias_habiles_por_mes = df_au.groupby('Periodo_Label')['Dias_Habiles'].first().to_dict()

    total_dias = filtered_df['Total (D)'].sum()
    total_horas = pd.to_numeric(filtered_df['Total (H)'], errors='coerce').fillna(0).sum()
    empleados_afectados = filtered_df['Legajo'].nunique()

    # Capacidad teórica total de los períodos seleccionados (con filtros de gerencia, etc. aplicados)
    capacidad_dias_total = 0
    dotacion_promedio = 0
    dotaciones_por_mes = []

    for p in sel_periodos:
        dh_p = dias_habiles_por_mes.get(p, 21)
        if filtered_dot is not None and not filtered_dot.empty:
            dot_p = filtered_dot[filtered_dot['Periodo_Label'] == p]['Legajo'].nunique()
        else:
            dot_p = filtered_df[filtered_df['Periodo_Label'] == p]['Legajo'].nunique()
        dotaciones_por_mes.append(dot_p)
        capacidad_dias_total += (dot_p * dh_p)

    capacidad_horas_total = capacidad_dias_total * 8
    dotacion_representativa = int(round(np.mean(dotaciones_por_mes))) if dotaciones_por_mes else empleados_afectados

    tasa_dias = (total_dias / capacidad_dias_total * 100) if capacidad_dias_total > 0 else 0
    tasa_horas = (total_horas / capacidad_horas_total * 100) if capacidad_horas_total > 0 else 0

    # Etiqueta de período (ej: "JUL-26" o "ENE-26 A JUL-26")
    if len(sel_periodos) == 1:
        periodo_txt = sel_periodos[0]
        dias_habiles_txt = f"📅 {int(dias_habiles_por_mes.get(sel_periodos[0], 21))}"
        sub_dias_hab = f"Período {periodo_txt}"
    else:
        periodo_txt = f"{sel_periodos[0]} a {sel_periodos[-1]}"
        total_dh_acum = sum(dias_habiles_por_mes.get(p, 21) for p in sel_periodos)
        dias_habiles_txt = f"📅 {int(total_dh_acum)}"
        sub_dias_hab = f"Acumulado {len(sel_periodos)} meses"

    card_html = f"""
    <style>
        .summary-container {{
            display: flex;
            flex-wrap: wrap;
            background-color: #ffffff;
            border-radius: 16px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.06);
            overflow: hidden;
            border: 1px solid #e2e8f0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        }}
        .hero-kpi-dias {{
            flex: 1 1 230px;
            background: linear-gradient(135deg, #0d9488 0%, #115e59 100%);
            padding: 22px 18px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            color: white;
            text-align: center;
            border-right: 1px solid rgba(255,255,255,0.15);
        }}
        .hero-kpi-horas {{
            flex: 1 1 230px;
            background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%);
            padding: 22px 18px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            color: white;
            text-align: center;
        }}
        .hero-title {{
            font-size: 0.85rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.8px;
            opacity: 0.95;
        }}
        .hero-percent {{
            font-size: 2.7rem;
            font-weight: 800;
            line-height: 1.1;
            margin: 6px 0;
        }}
        .hero-sub {{
            font-size: 0.95rem;
            opacity: 0.9;
            font-weight: 500;
        }}
        .summary-breakdown {{
            flex: 2 1 340px;
            padding: 16px 20px;
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            justify-content: center;
            align-content: center;
            background: #f8fafc;
        }}
        .metric-box {{
            flex: 1 1 140px;
            padding: 12px 14px;
            border-radius: 10px;
            background: #ffffff;
            border: 1px solid #e2e8f0;
            box-shadow: 0 2px 6px rgba(0,0,0,0.02);
            display: flex;
            flex-direction: column;
            justify-content: center;
        }}
        .metric-box .label {{ font-size: 0.75rem; color: #64748b; font-weight: 600; text-transform: uppercase; }}
        .metric-box .val {{ font-size: 1.35rem; color: #0f172a; font-weight: 800; margin: 3px 0; }}
        .metric-box .sub {{ font-size: 0.75rem; color: #0d9488; font-weight: 600; }}
    </style>
    <div class="summary-container">
        <div class="hero-kpi-dias">
            <div class="hero-title">Índice Ausentismo (Días)</div>
            <div class="hero-percent">{format_percentage_es(tasa_dias)}</div>
            <div class="hero-sub">{format_integer_es(total_dias)} días ausentes</div>
            <div style="font-size:0.75rem; opacity:0.8; margin-top:4px;">{periodo_txt}</div>
        </div>
        <div class="hero-kpi-horas">
            <div class="hero-title">Índice Ausentismo (Horas)</div>
            <div class="hero-percent">{format_percentage_es(tasa_horas)}</div>
            <div class="hero-sub">{format_integer_es(total_horas)} horas ausentes</div>
            <div style="font-size:0.75rem; opacity:0.8; margin-top:4px;">{periodo_txt}</div>
        </div>
        <div class="summary-breakdown">
            <div class="metric-box">
                <div class="label">Días Hábiles</div>
                <div class="val">{dias_habiles_txt}</div>
                <div class="sub">{sub_dias_hab}</div>
            </div>
            <div class="metric-box">
                <div class="label">Agentes con Novedad</div>
                <div class="val">👥 {format_integer_es(empleados_afectados)}</div>
                <div class="sub">{format_percentage_es((empleados_afectados/dotacion_representativa*100) if dotacion_representativa else 0)} del personal</div>
            </div>
            <div class="metric-box">
                <div class="label">Capacidad Teórica</div>
                <div class="val">🏢 {format_integer_es(capacidad_dias_total)} ds</div>
                <div class="sub">~{format_integer_es(dotacion_representativa)} agentes en dotación</div>
            </div>
        </div>
    </div>
    """
    st.components.v1.html(card_html, height=250)
    st.markdown("<br>", unsafe_allow_html=True)

    # --- Pestañas de Análisis ---
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Evolución e Índices",
        "📂 Motivos y Tipos de Licencia",
        "🏢 Distribución por Gerencia y Distrito",
        "📋 Detalle de Registros"
    ])

    # --- TAB 1: Evolución ---
    with tab1:
        st.subheader("Evolución Temporal del Ausentismo (Días y Horas)")
        
        evo_rows = []
        for p in sel_periodos:
            sub = filtered_df[filtered_df['Periodo_Label'] == p]
            d_sum = sub['Total (D)'].sum()
            h_sum = pd.to_numeric(sub['Total (H)'], errors='coerce').fillna(0).sum()
            agentes_sub = sub['Legajo'].nunique()
            
            # Dotación mensual con filtros activos
            if filtered_dot is not None and not filtered_dot.empty:
                dot_m = filtered_dot[filtered_dot['Periodo_Label'] == p]['Legajo'].nunique()
            else:
                dot_m = agentes_sub
                
            dh = dias_habiles_por_mes.get(p, 21)
            cap_d = dot_m * dh
            cap_h = cap_d * 8
            
            tasa_d = (d_sum / cap_d * 100) if cap_d > 0 else 0
            tasa_h = (h_sum / cap_h * 100) if cap_h > 0 else 0
            
            evo_rows.append({
                "Periodo": p,
                "Dias_Ausentes": d_sum,
                "Horas_Ausentes": h_sum,
                "Índice_Días": tasa_d,
                "Índice_Horas": tasa_h,
                "Agentes": agentes_sub
            })
            
        df_evo = pd.DataFrame(evo_rows)

        if not df_evo.empty:
            col_c, col_t = st.columns([2, 1])
            with col_c:
                fig_evo = make_subplots(specs=[[{"secondary_y": True}]])
                fig_evo.add_trace(go.Bar(
                    x=df_evo['Periodo'], y=df_evo['Dias_Ausentes'],
                    name='Días Ausentes', marker_color='#0d9488', text=df_evo['Dias_Ausentes'], textposition='outside'
                ), secondary_y=False)

                fig_evo.add_trace(go.Scatter(
                    x=df_evo['Periodo'], y=df_evo['Horas_Ausentes'],
                    name='Horas Ausentes', mode='lines+markers+text',
                    text=df_evo['Horas_Ausentes'], textposition='top center', line=dict(color='#f59e0b', width=3)
                ), secondary_y=True)

                fig_evo.update_layout(title="Total Días vs Horas Ausentes por Mes", hovermode="x unified", legend=dict(orientation="h", y=1.12, x=1, xanchor='right'))
                fig_evo.update_xaxes(categoryorder='array', categoryarray=sel_periodos)
                fig_evo.update_yaxes(title_text="Días Ausentes", secondary_y=False)
                fig_evo.update_yaxes(title_text="Horas Ausentes", secondary_y=True)
                st.plotly_chart(fig_evo, use_container_width=True)

            with col_t:
                st.markdown("##### Resumen Mensual")
                st.dataframe(df_evo.style.format({
                    "Dias_Ausentes": format_integer_es,
                    "Horas_Ausentes": format_integer_es,
                    "Índice_Días": lambda x: format_percentage_es(x, 2),
                    "Índice_Horas": lambda x: format_percentage_es(x, 2),
                    "Agentes": format_integer_es
                }), use_container_width=True, hide_index=True)
                generate_download_buttons(df_evo, "evolucion_ausentismo", key_suffix="_evo")
        else:
            st.info("No hay datos de evolución disponibles.")

    # --- TAB 2: Motivos y Licencias ---
    with tab2:
        st.subheader("Composición por Tipo y Motivo de Ausencia")
        c1, c2 = st.columns(2)
        with c1:
            df_tipo = filtered_df.groupby('Tipo', as_index=False).agg(
                Dias=('Total (D)', 'sum'),
                Horas=('Total (H)', 'sum'),
                Casos=('Legajo', 'count')
            )
            fig_pie_tipo = px.pie(df_tipo, names='Tipo', values='Dias', title='Distribución de Días por Tipo (Licencia vs Novedad)', hole=0.4, color_discrete_sequence=['#0f766e', '#0284c7', '#f59e0b'])
            fig_pie_tipo.update_traces(textinfo='percent+label+value')
            st.plotly_chart(fig_pie_tipo, use_container_width=True)

        with c2:
            df_motivos = (
                filtered_df.groupby('Licencia', as_index=False)
                .agg(Dias=('Total (D)', 'sum'), Horas=('Total (H)', 'sum'))
                .sort_values('Dias', ascending=False)
                .head(10)
            )
            fig_bar_mot = px.bar(df_motivos, x='Dias', y='Licencia', orientation='h', title='Top 10 Licencias por Días Ausentes', color='Dias', color_continuous_scale='Teal')
            fig_bar_mot.update_layout(yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig_bar_mot, use_container_width=True)

        st.markdown("##### Detalle de Todos los Motivos")
        df_lic_detail = (
            filtered_df.groupby(['Tipo', 'Licencia', 'Descripción'], as_index=False)
            .agg(Dias=('Total (D)', 'sum'), Horas=('Total (H)', 'sum'), Agentes=('Legajo', 'nunique'))
            .sort_values('Dias', ascending=False)
        )
        st.dataframe(df_lic_detail.style.format({"Dias": format_integer_es, "Horas": format_integer_es, "Agentes": format_integer_es}), use_container_width=True, hide_index=True)
        generate_download_buttons(df_lic_detail, "licencias_detalle", key_suffix="_lic")

    # --- TAB 3: Gerencia y Distrito ---
    with tab3:
        st.subheader("Impacto por Área Organizativa y Ubicación")
        agrupador = st.selectbox("Seleccionar Nivel de Análisis:", ["Gerencia", "Distrito", "Ministerio", "Relación"], key="sel_agrup")
        
        df_area = (
            filtered_df.groupby(agrupador, as_index=False)
            .agg(
                Dias=('Total (D)', 'sum'),
                Horas=('Total (H)', 'sum'),
                Agentes=('Legajo', 'nunique')
            )
            .sort_values('Dias', ascending=False)
            .reset_index(drop=True)
        )

        col_a1, col_a2 = st.columns([2, 1])
        with col_a1:
            fig_area = px.bar(
                df_area, 
                x=agrupador, 
                y='Dias', 
                text='Dias', 
                title=f'Días Ausentes por {agrupador}',
                color_discrete_sequence=['#0d9488']
            )
            fig_area.update_traces(
                textposition='outside',
                texttemplate='%{text:,.0f}'
            )
            fig_area.update_layout(
                xaxis_title=agrupador,
                yaxis_title="Días Ausentes",
                xaxis_tickangle=-45 if agrupador in ['Distrito', 'Ministerio'] else 0
            )
            st.plotly_chart(fig_area, use_container_width=True)

        with col_a2:
            st.dataframe(
                df_area.style.format({
                    "Dias": format_integer_es, 
                    "Horas": format_integer_es, 
                    "Agentes": format_integer_es
                }), 
                use_container_width=True, 
                hide_index=True
            )
            generate_download_buttons(df_area, f"ausentismo_{agrupador.lower()}", key_suffix="_area")

    # --- TAB 4: Datos Brutos ---
    with tab4:
        st.subheader("Registros Detallados")
        cols_mostrar = [c for c in ['Legajo', 'Apellido y Nombre', 'Periodo_Label', 'Tipo', 'Licencia', 'Total (D)', 'Total (H)', 'Gerencia', 'Distrito', 'Relación'] if c in filtered_df.columns]
        st.dataframe(filtered_df[cols_mostrar], use_container_width=True, hide_index=True)
        generate_download_buttons(filtered_df[cols_mostrar], "registros_ausentismo_filtrados", key_suffix="_bruto")
else:
    st.info("Por favor, cargue un archivo Excel para comenzar el análisis.")
