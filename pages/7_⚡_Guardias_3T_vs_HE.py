import streamlit as st
import pandas as pd
import numpy as np
import io
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- Configuración de la página ---
st.set_page_config(layout="wide", page_title="Guardias 3T vs Horas Extras", page_icon="⚡")

# --- Estilos CSS Profesionales ---
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

# --- Funciones de Formato en Español ---
def format_integer_es(num):
    if pd.isna(num) or not isinstance(num, (int, float, np.number)): return ""
    return f"{int(round(num)):,}".replace(",", ".")

def format_decimal_es(num, decimals=1):
    if pd.isna(num) or not isinstance(num, (int, float, np.number)): return ""
    return f"{num:,.{decimals}f}".replace(",", "TEMP").replace(".", ",").replace("TEMP", ".")

def format_percentage_es(num, decimals=2):
    if pd.isna(num) or not isinstance(num, (int, float, np.number)): return "0,00%"
    return f"{num:,.{decimals}f}%".replace(",", "TEMP").replace(".", ",").replace("TEMP", ".")

def format_currency_es(num, decimals=2):
    if pd.isna(num) or not isinstance(num, (int, float, np.number)): return "$ 0,00"
    return f"${num:,.{decimals}f}".replace(",", "TEMP").replace(".", ",").replace("TEMP", ".")

def format_currency_millions(num):
    if pd.isna(num) or not isinstance(num, (int, float, np.number)): return "$ 0,00"
    if abs(num) >= 1_000_000:
        return f"${num/1_000_000:,.1f} M".replace(",", "TEMP").replace(".", ",").replace("TEMP", ".")
    elif abs(num) >= 1_000:
        return f"${num/1_000:,.1f} mil".replace(",", "TEMP").replace(".", ",").replace("TEMP", ".")
    return format_currency_es(num, 0)

def generate_download_buttons(df_to_download, filename_prefix, key_suffix=""):
    st.markdown("##### Opciones de Descarga:")
    col_dl1, col_dl2 = st.columns(2)
    csv_buffer = io.StringIO()
    df_to_download.to_csv(csv_buffer, index=False)
    with col_dl1:
        st.download_button(label="⬇️ Descargar como CSV", data=csv_buffer.getvalue(), file_name=f"{filename_prefix}.csv", mime="text/csv", key=f"csv_{filename_prefix}{key_suffix}")
    excel_buffer = io.BytesIO()
    df_to_download.to_excel(excel_buffer, index=False, engine='openpyxl')
    excel_buffer.seek(0)
    with col_dl2:
        st.download_button(label="📊 Descargar como Excel", data=excel_buffer.getvalue(), file_name=f"{filename_prefix}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key=f"excel_{filename_prefix}{key_suffix}")

# --- Carga y Procesamiento de Datos ---
@st.cache_data
def load_and_process_g3t(uploaded_file):
    try:
        xls = pd.ExcelFile(uploaded_file, engine='openpyxl')
        sheet_target = 'Data' if 'Data' in xls.sheet_names else xls.sheet_names[0]
        df = pd.read_excel(xls, sheet_name=sheet_target)
        
        # Eliminar columnas sin nombre
        df = df.loc[:, ~df.columns.astype(str).str.startswith('Unnamed:')]
        
        # Mapeo de columnas con nombres flexibles
        col_rename = {}
        for c in df.columns:
            cs = str(c).strip()
            if cs.lower() in ['leg', 'legajo']: col_rename[c] = 'Legajo'
            elif cs.lower() in ['ni', 'nivel']: col_rename[c] = 'Nivel'
            elif cs.lower() in ['subni', 'subnivel']: col_rename[c] = 'Subnivel'
            elif 'periodo' in cs.lower() or 'período' in cs.lower(): col_rename[c] = 'Periodo'
            elif 'tipo de liquid' in cs.lower(): col_rename[c] = 'Tipo de Liquidación'
            elif 'ubicaci' in cs.lower(): col_rename[c] = 'Ubicación'
        df = df.rename(columns=col_rename)

        # Normalizar columnas numéricas de Guardias e Importes
        num_cols = [
            'G3T ($)', 'G3T (Q)',
            'HE al 50 % ($)', 'HE al 50 % Sábados ($)', 'HE al 100 % ($)',
            'HE al 50 % (Q)', 'HE al 50 % Sábados (Q)', 'HE al 100 % (Q)'
        ]
        for nc in num_cols:
            if nc in df.columns:
                df[nc] = pd.to_numeric(df[nc], errors='coerce').fillna(0.0)
            else:
                df[nc] = 0.0

        # Total de Horas Extras en Cantidad (Q) y en Pesos ($)
        df['Total HE (Q)'] = df['HE al 50 % (Q)'] + df['HE al 50 % Sábados (Q)'] + df['HE al 100 % (Q)']
        df['Total HE ($)'] = df['HE al 50 % ($)'] + df['HE al 50 % Sábados ($)'] + df['HE al 100 % ($)']

        # Mapeo universal de Período a nombre de mes en español
        mapa_num_mes = {1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril', 5: 'mayo', 6: 'junio', 7: 'julio', 8: 'agosto', 9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre'}
        mapa_str_mes = {'ene': 'enero', 'feb': 'febrero', 'mar': 'marzo', 'abr': 'abril', 'may': 'mayo', 'jun': 'junio', 'jul': 'julio', 'ago': 'agosto', 'sep': 'septiembre', 'oct': 'octubre', 'nov': 'noviembre', 'dic': 'diciembre'}

        def resolver_periodo(val):
            if pd.isna(val): return 'otro'
            dt_val = pd.to_datetime(val, errors='coerce')
            if pd.notna(dt_val):
                return mapa_num_mes.get(dt_val.month, 'otro')
            val_s = str(val).strip().lower()
            for k, v in mapa_str_mes.items():
                if val_s.startswith(k):
                    return v
            return val_s

        if 'Periodo' in df.columns:
            df['Periodo_Label'] = df['Periodo'].apply(resolver_periodo)
        else:
            df['Periodo_Label'] = 'General'

        # Normalizar Legajo
        if 'Legajo' in df.columns:
            df['Legajo'] = pd.to_numeric(df['Legajo'], errors='coerce').astype('Int64').astype(str)
            df['Legajo'] = df['Legajo'].replace(['<NA>', 'nan'], 'no disponible')
        else:
            df['Legajo'] = 'no disponible'

        # Limpieza de columnas de texto (incluyendo Ubicación)
        text_cols = ['Apellido y Nombre', 'Nivel', 'Subnivel', 'Gerencia', 'CeCo', 'Distrito', 'Sede', 'Ubicación', 'Tipo de Liquidación']
        for tc in text_cols:
            if tc in df.columns:
                df[tc] = df[tc].astype(str).replace(['nan', 'None', '<NA>'], 'no disponible').str.strip()
            else:
                df[tc] = 'no disponible'

        # Parsear coordenadas
        if 'Coordenadas' in df.columns:
            def parse_lat_lon(coord_val):
                try:
                    p = str(coord_val).split(',')
                    return float(p[0].strip()), float(p[1].strip())
                except:
                    return np.nan, np.nan
            coords = df['Coordenadas'].apply(parse_lat_lon)
            df['Latitud'] = [c[0] for c in coords]
            df['Longitud'] = [c[1] for c in coords]
        else:
            df['Latitud'] = np.nan
            df['Longitud'] = np.nan

        return df
    except Exception as e:
        st.error(f"Error al procesar el archivo Excel: {e}")
        return pd.DataFrame()

# --- UI Principal ---
st.title("⚡ Análisis de Guardias de 3 Turnos (G3T) vs. Horas Extras")
st.write("Seguimiento comparativo de costos, cantidades asignadas, impacto territorial y ranking por legajo.")

uploaded_file = st.file_uploader("📂 Cargue aquí su archivo Excel de Guardias 3T vs HE", type=["xlsx", "xlsm"])
st.markdown("---")

if uploaded_file is not None:
    with st.spinner("Procesando datos de Guardias y Horas Extras..."):
        df_raw = load_and_process_g3t(uploaded_file)

    if df_raw.empty:
        st.error("El archivo cargado no contiene datos válidos.")
        st.stop()

    st.success(f"Se procesaron con éxito **{format_integer_es(len(df_raw))}** registros de liquidaciones.")
    st.markdown("---")

    # --- Barra Lateral de Filtros ---
    st.sidebar.header("Filtros del Módulo")

    orden_meses_std = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']
    meses_presentes = [m for m in orden_meses_std if m in df_raw['Periodo_Label'].unique()]
    if not meses_presentes:
        meses_presentes = sorted(list(df_raw['Periodo_Label'].unique()))

    # Filtros categóricos generales (ahora incluye Ubicación Laboral)
    filter_dict = {
        'Periodo_Label': ('Período (Mes)', meses_presentes),
        'Tipo de Liquidación': ('Tipo de Liquidación', sorted(df_raw['Tipo de Liquidación'].unique().tolist())),
        'Gerencia': ('Gerencia', sorted(df_raw['Gerencia'].unique().tolist())),
        'Distrito': ('Distrito', sorted(df_raw['Distrito'].unique().tolist())),
        'Ubicación': ('Ubicación Laboral', sorted([u for u in df_raw['Ubicación'].unique().tolist() if u != 'no disponible'])),
        'CeCo': ('Centro de Costo (CeCo)', sorted(df_raw['CeCo'].unique().tolist())),
        'Nivel': ('Nivel', sorted(df_raw['Nivel'].unique().tolist()))
    }

    # Opciones de Legajos ordenadas numéricamente
    opts_legajos_raw = set(df_raw['Legajo'].dropna().unique())
    opts_legajos = sorted(
        [str(o).strip() for o in opts_legajos_raw if str(o).strip() not in ['no disponible', 'nan', 'None', '<NA>']],
        key=lambda x: int(x) if str(x).isdigit() else 999999
    )

    if 'g3t_selections_v2' not in st.session_state or st.sidebar.button("🔄 Resetear Filtros", use_container_width=True):
        st.session_state.g3t_selections_v2 = {k: list(v[1]) for k, v in filter_dict.items()}
        st.session_state.g3t_sel_legajo = []
        st.rerun()

    filtered_df = df_raw.copy()

    # Filtrado categórico estándar
    for col, (label, opts) in filter_dict.items():
        curr_defaults = [x for x in st.session_state.g3t_selections_v2.get(col, opts) if x in opts]
        sel = st.sidebar.multiselect(label, options=opts, default=curr_defaults, key=f"sel_g3t_v2_{col}")
        st.session_state.g3t_selections_v2[col] = sel

        if len(sel) == 0:
            filtered_df = filtered_df.iloc[0:0]
        elif len(sel) < len(opts):
            filtered_df = filtered_df[filtered_df[col].isin(sel)]

    # Filtro de búsqueda puntual por Legajo
    st.sidebar.markdown("---")
    sel_legajo = st.sidebar.multiselect(
        "Legajo (Búsqueda puntual):",
        options=opts_legajos,
        default=st.session_state.get('g3t_sel_legajo', []),
        help="Deje vacío para incluir a todos los colaboradores, o seleccione agentes puntuales.",
        key="sel_g3t_legajo"
    )
    st.session_state.g3t_sel_legajo = sel_legajo

    if len(sel_legajo) > 0:
        filtered_df = filtered_df[filtered_df['Legajo'].isin(sel_legajo)]

    if filtered_df.empty:
        st.warning("⚠️ No se encontraron registros con los filtros seleccionados. Ajuste los filtros en la barra lateral.")
        st.stop()

    # --- KPIs PRINCIPALES ---
    total_g3t_pesos = filtered_df['G3T ($)'].sum()
    total_g3t_cant = filtered_df['G3T (Q)'].sum()
    total_he_cant = filtered_df['Total HE (Q)'].sum()
    total_he_pesos = filtered_df['Total HE ($)'].sum()
    total_legajos = filtered_df['Legajo'].nunique()
    total_he_100_q = filtered_df['HE al 100 % (Q)'].sum()

    pct_he_100_val = (total_he_100_q / total_he_cant * 100) if total_he_cant > 0 else 0.0
    pct_he_100_str = format_percentage_es(pct_he_100_val)

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
            margin-bottom: 25px;
        }}
        .hero-kpi-g3t {{
            flex: 1 1 240px;
            background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%);
            padding: 22px 18px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            color: white;
            text-align: center;
            border-right: 1px solid rgba(255,255,255,0.15);
        }}
        .hero-kpi-he {{
            flex: 1 1 240px;
            background: linear-gradient(135deg, #0077b6 0%, #023e8a 100%);
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
        .hero-val {{
            font-size: 2.6rem;
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
        .metric-box .sub {{ font-size: 0.75rem; color: #0284c7; font-weight: 600; }}
    </style>
    <div class="summary-container">
        <div class="hero-kpi-g3t">
            <div class="hero-title">G3T Total ($)</div>
            <div class="hero-val">{format_currency_millions(total_g3t_pesos)}</div>
            <div class="hero-sub">{format_integer_es(total_g3t_cant)} guardias asignadas</div>
        </div>
        <div class="hero-kpi-he">
            <div class="hero-title">Total Horas Extras (Q)</div>
            <div class="hero-val">{format_decimal_es(total_he_cant, 1)} hs</div>
            <div class="hero-sub">{format_currency_millions(total_he_pesos)} en costo HE</div>
        </div>
        <div class="summary-breakdown">
            <div class="metric-box">
                <div class="label">Legajos Activos</div>
                <div class="val">👥 {format_integer_es(total_legajos)}</div>
                <div class="sub">Personal con liquidación</div>
            </div>
            <div class="metric-box">
                <div class="label">HE al 100 % (Q)</div>
                <div class="val">⏱️ {format_decimal_es(total_he_100_q, 1)} hs</div>
                <div class="sub">{pct_he_100_str} del total HE</div>
            </div>
            <div class="metric-box">
                <div class="label">Costo Total Combinado</div>
                <div class="val">💰 {format_currency_millions(total_g3t_pesos + total_he_pesos)}</div>
                <div class="sub">Guardias 3T + Horas Extras</div>
            </div>
        </div>
    </div>
    """
    st.components.v1.html(card_html, height=250)
    st.markdown("<br>", unsafe_allow_html=True)

    # --- Pestañas de Análisis ---
    tab_intro, tab_ranking, tab_geo, tab_cruda = st.tabs([
        "📋 Intro - Síntesis",
        "🏆 Ranking por Legajo",
        "🗺️ Distribución Geográfica",
        "📄 Data Cruda (Info)"
    ])

    # =========================================================================
    # --- PESTAÑA 1: INTRO - SÍNTESIS ---
    # =========================================================================
    with tab_intro:
        st.subheader("Guardias 3T vs HExtras - Evolución Mensual")

        meses_sel = [m for m in orden_meses_std if m in filtered_df['Periodo_Label'].unique()]
        if not meses_sel:
            meses_sel = sorted(list(filtered_df['Periodo_Label'].unique()))

        df_tabla1 = filtered_df.groupby('Periodo_Label', sort=False).agg(
            G3T_Pesos=('G3T ($)', 'sum'),
            G3T_Q=('G3T (Q)', 'sum'),
            HE_50_Pesos=('HE al 50 % ($)', 'sum'),
            HE_50_Sab_Pesos=('HE al 50 % Sábados ($)', 'sum'),
            HE_100_Pesos=('HE al 100 % ($)', 'sum'),
            HE_50_Q=('HE al 50 % (Q)', 'sum'),
            HE_50_Sab_Q=('HE al 50 % Sábados (Q)', 'sum'),
            HE_100_Q=('HE al 100 % (Q)', 'sum'),
            Total_HE_Q=('Total HE (Q)', 'sum')
        ).reindex(meses_sel, fill_value=0.0).reset_index()

        tot_row_t1 = pd.DataFrame({
            'Periodo_Label': ['Total'],
            'G3T_Pesos': [df_tabla1['G3T_Pesos'].sum()],
            'G3T_Q': [df_tabla1['G3T_Q'].sum()],
            'HE_50_Pesos': [df_tabla1['HE_50_Pesos'].sum()],
            'HE_50_Sab_Pesos': [df_tabla1['HE_50_Sab_Pesos'].sum()],
            'HE_100_Pesos': [df_tabla1['HE_100_Pesos'].sum()],
            'HE_50_Q': [df_tabla1['HE_50_Q'].sum()],
            'HE_50_Sab_Q': [df_tabla1['HE_50_Sab_Q'].sum()],
            'HE_100_Q': [df_tabla1['HE_100_Q'].sum()],
            'Total_HE_Q': [df_tabla1['Total_HE_Q'].sum()]
        })
        df_tabla1_display = pd.concat([df_tabla1, tot_row_t1], ignore_index=True)

        rename_t1 = {
            'Periodo_Label': 'Periodo (Mes)',
            'G3T_Pesos': 'G3T ($)',
            'G3T_Q': 'G3T (Q)',
            'HE_50_Pesos': 'HE al 50 % ($)',
            'HE_50_Sab_Pesos': 'HE al 50 % Sábados ($)',
            'HE_100_Pesos': 'HE al 100 % ($)',
            'HE_50_Q': 'HE al 50 % (Q)',
            'HE_50_Sab_Q': 'HE al 50 % Sábados (Q)',
            'HE_100_Q': 'HE al 100 % (Q)',
            'Total_HE_Q': 'Total HE (Q)'
        }
        df_tabla1_show = df_tabla1_display.rename(columns=rename_t1)

        st.markdown("##### Guardias 3T vs HExtras Tabla 1")
        st.dataframe(
            df_tabla1_show.style.format({
                'G3T ($)': format_currency_millions,
                'G3T (Q)': format_integer_es,
                'HE al 50 % ($)': format_currency_millions,
                'HE al 50 % Sábados ($)': format_currency_millions,
                'HE al 100 % ($)': format_currency_millions,
                'HE al 50 % (Q)': lambda x: format_decimal_es(x, 1) if x % 1 != 0 else format_integer_es(x),
                'HE al 50 % Sábados (Q)': lambda x: format_decimal_es(x, 1) if x % 1 != 0 else format_integer_es(x),
                'HE al 100 % (Q)': lambda x: format_decimal_es(x, 1) if x % 1 != 0 else format_integer_es(x),
                'Total HE (Q)': lambda x: format_decimal_es(x, 1) if x % 1 != 0 else format_integer_es(x)
            }),
            use_container_width=True,
            height=340,
            hide_index=True
        )
        generate_download_buttons(df_tabla1_show, "guardias_3t_vs_he_tabla1", key_suffix="_t1")

        st.markdown("---")

        # --- FILA 1: EVOLUCIÓN MENSUAL EN CANTIDADES Y EN PESOS ---
        col_g_q, col_g_p = st.columns(2)

        with col_g_q:
            st.markdown("##### Evolución Mensual en Cantidades (Q)")
            fig_q = make_subplots(specs=[[{"secondary_y": True}]])
            
            fig_q.add_trace(go.Bar(x=df_tabla1['Periodo_Label'], y=df_tabla1['HE_50_Q'], name='HE al 50 % (Q)', marker_color='#457b9d'), secondary_y=False)
            fig_q.add_trace(go.Bar(x=df_tabla1['Periodo_Label'], y=df_tabla1['HE_50_Sab_Q'], name='HE al 50 % Sábados (Q)', marker_color='#1d3557'), secondary_y=False)
            fig_q.add_trace(go.Bar(x=df_tabla1['Periodo_Label'], y=df_tabla1['HE_100_Q'], name='HE al 100 % (Q)', marker_color='#2a9d8f'), secondary_y=False)

            fig_q.add_trace(go.Scatter(
                x=df_tabla1['Periodo_Label'],
                y=df_tabla1['G3T_Q'],
                name='G3T (Q)',
                mode='lines+markers',
                line=dict(color='#0284c7', width=3),
                marker=dict(size=7)
            ), secondary_y=True)

            fig_q.update_layout(
                barmode='stack',
                legend=dict(orientation="h", y=1.12, x=0.5, xanchor='center'),
                margin=dict(t=30, b=30, l=10, r=10),
                height=350,
                hovermode="x unified"
            )
            fig_q.update_yaxes(title_text="Cantidad HE (hs)", secondary_y=False, showgrid=True)
            fig_q.update_yaxes(title_text="Cantidad G3T", secondary_y=True, showgrid=False)
            st.plotly_chart(fig_q, use_container_width=True)

        with col_g_p:
            st.markdown("##### Evolución Mensual en Pesos ($)")
            fig_p = make_subplots(specs=[[{"secondary_y": True}]])

            fig_p.add_trace(go.Bar(x=df_tabla1['Periodo_Label'], y=df_tabla1['HE_50_Pesos'], name='HE al 50 % ($)', marker_color='#457b9d'), secondary_y=False)
            fig_p.add_trace(go.Bar(x=df_tabla1['Periodo_Label'], y=df_tabla1['HE_50_Sab_Pesos'], name='HE al 50 % Sábados ($)', marker_color='#1d3557'), secondary_y=False)
            fig_p.add_trace(go.Bar(x=df_tabla1['Periodo_Label'], y=df_tabla1['HE_100_Pesos'], name='HE al 100 % ($)', marker_color='#2a9d8f'), secondary_y=False)

            fig_p.add_trace(go.Scatter(
                x=df_tabla1['Periodo_Label'],
                y=df_tabla1['G3T_Pesos'],
                name='G3T ($)',
                mode='lines+markers',
                line=dict(color='#0284c7', width=3),
                marker=dict(size=7)
            ), secondary_y=True)

            fig_p.update_layout(
                barmode='stack',
                legend=dict(orientation="h", y=1.12, x=0.5, xanchor='center'),
                margin=dict(t=30, b=30, l=10, r=10),
                height=350,
                hovermode="x unified"
            )
            fig_p.update_yaxes(title_text="Importe HE ($)", secondary_y=False, showgrid=True)
            fig_p.update_yaxes(title_text="Importe G3T ($)", secondary_y=True, showgrid=False)
            st.plotly_chart(fig_p, use_container_width=True)

        st.markdown("---")

        # --- FILA 2: GRÁFICOS DE TOTALES ---
        col_tot_combo, col_pie_g3t, col_pie_he = st.columns([1.6, 1.2, 1.2])
        paleta_donuts = ['#1f77b4', '#aec7e8', '#ff7f0e', '#ffbb78', '#2ca02c', '#98df8a', '#d62728', '#ff9896', '#9467bd', '#c5b0d5']

        # 1. Gráfico Combinado: Total HE (Q) y G3T (Q) por Período
        with col_tot_combo:
            st.markdown("##### Total HE (Q) y G3T (Q) por Periodo (Mes)")
            fig_tot_combo = make_subplots(specs=[[{"secondary_y": True}]])

            fig_tot_combo.add_trace(go.Bar(
                x=df_tabla1['Periodo_Label'],
                y=df_tabla1['Total_HE_Q'],
                name='Total HE (Q)',
                marker_color='#2563eb'
            ), secondary_y=False)

            fig_tot_combo.add_trace(go.Scatter(
                x=df_tabla1['Periodo_Label'],
                y=df_tabla1['G3T_Q'],
                name='G3T (Q)',
                mode='lines+markers',
                line=dict(color='#0284c7', width=3),
                marker=dict(size=7)
            ), secondary_y=True)

            fig_tot_combo.update_layout(
                legend=dict(orientation="h", y=1.15, x=0.5, xanchor='center'),
                margin=dict(t=30, b=30, l=10, r=10),
                height=320,
                hovermode="x unified"
            )
            fig_tot_combo.update_yaxes(title_text="Total HE (hs)", secondary_y=False, showgrid=True)
            fig_tot_combo.update_yaxes(title_text="G3T (Q)", secondary_y=True, showgrid=False)
            st.plotly_chart(fig_tot_combo, use_container_width=True)

        # 2. Torta / Donut: Período (Mes) por G3T ($)
        with col_pie_g3t:
            st.markdown("##### Período (Mes) por G3T ($)")
            df_pie_g3t = df_tabla1[df_tabla1['G3T_Pesos'] > 0].copy()
            fig_pie_g3t = px.pie(
                df_pie_g3t,
                names='Periodo_Label',
                values='G3T_Pesos',
                hole=0.45,
                color_discrete_sequence=paleta_donuts
            )
            fig_pie_g3t.update_traces(
                sort=False,
                textinfo='percent',
                textposition='inside',
                insidetextorientation='horizontal',
                direction='clockwise'
            )
            fig_pie_g3t.update_layout(
                showlegend=True,
                legend=dict(orientation="v", y=0.5, x=1.02, font=dict(size=10), traceorder="normal"),
                margin=dict(t=20, b=20, l=10, r=10),
                height=320
            )
            st.plotly_chart(fig_pie_g3t, use_container_width=True)

        # 3. Torta / Donut: Período (Mes) por Total HE (Q)
        with col_pie_he:
            st.markdown("##### Período (Mes) por Total HE (Q)")
            df_pie_he = df_tabla1[df_tabla1['Total_HE_Q'] > 0].copy()
            fig_pie_he = px.pie(
                df_pie_he,
                names='Periodo_Label',
                values='Total_HE_Q',
                hole=0.45,
                color_discrete_sequence=paleta_donuts
            )
            fig_pie_he.update_traces(
                sort=False,
                textinfo='percent',
                textposition='inside',
                insidetextorientation='horizontal',
                direction='clockwise'
            )
            fig_pie_he.update_layout(
                showlegend=True,
                legend=dict(orientation="v", y=0.5, x=1.02, font=dict(size=10), traceorder="normal"),
                margin=dict(t=20, b=20, l=10, r=10),
                height=320
            )
            st.plotly_chart(fig_pie_he, use_container_width=True)

    # =========================================================================
    # --- PESTAÑA 2: RANKING POR LEGAJO ---
    # =========================================================================
    with tab_ranking:
        st.subheader("Guardias 3T vs HExtras Tabla 2 - Ranking de Agentes")

        grp_leg = ['Legajo', 'Apellido y Nombre', 'Nivel', 'Subnivel', 'Gerencia', 'CeCo', 'Tipo de Liquidación']
        df_rank = filtered_df.groupby(grp_leg, as_index=False).agg(
            G3T_Pesos=('G3T ($)', 'sum'),
            HE_50_Q=('HE al 50 % (Q)', 'sum'),
            HE_50_Sab_Q=('HE al 50 % Sábados (Q)', 'sum'),
            HE_100_Q=('HE al 100 % (Q)', 'sum'),
            Total_HE_Q=('Total HE (Q)', 'sum')
        ).sort_values(by='Total_HE_Q', ascending=False).reset_index(drop=True)

        rename_t2 = {
            'G3T_Pesos': 'G3T ($)',
            'HE_50_Q': 'HE al 50 % (Q)',
            'HE_50_Sab_Q': 'HE al 50 % Sábados (Q)',
            'HE_100_Q': 'HE al 100 % (Q)',
            'Total_HE_Q': 'Total HE (Q)'
        }
        df_rank_display = df_rank.rename(columns=rename_t2)

        tot_row_t2 = pd.DataFrame({
            'Legajo': ['Total'],
            'Apellido y Nombre': [''],
            'Nivel': [''],
            'Subnivel': [''],
            'Gerencia': [''],
            'CeCo': [''],
            'Tipo de Liquidación': [''],
            'G3T ($)': [df_rank['G3T_Pesos'].sum()],
            'HE al 50 % (Q)': [df_rank['HE_50_Q'].sum()],
            'HE al 50 % Sábados (Q)': [df_rank['HE_50_Sab_Q'].sum()],
            'HE al 100 % (Q)': [df_rank['HE_100_Q'].sum()],
            'Total HE (Q)': [df_rank['Total_HE_Q'].sum()]
        })
        df_rank_final = pd.concat([df_rank_display, tot_row_t2], ignore_index=True)

        st.dataframe(
            df_rank_final.style.format({
                'G3T ($)': format_currency_es,
                'HE al 50 % (Q)': lambda x: format_decimal_es(x, 1) if pd.notna(x) and str(x) != '' and x % 1 != 0 else (format_integer_es(x) if pd.notna(x) and str(x) != '' else ""),
                'HE al 50 % Sábados (Q)': lambda x: format_decimal_es(x, 1) if pd.notna(x) and str(x) != '' and x % 1 != 0 else (format_integer_es(x) if pd.notna(x) and str(x) != '' else ""),
                'HE al 100 % (Q)': lambda x: format_decimal_es(x, 1) if pd.notna(x) and str(x) != '' and x % 1 != 0 else (format_integer_es(x) if pd.notna(x) and str(x) != '' else ""),
                'Total HE (Q)': lambda x: format_decimal_es(x, 1) if pd.notna(x) and str(x) != '' and x % 1 != 0 else (format_integer_es(x) if pd.notna(x) and str(x) != '' else "")
            }),
            use_container_width=True,
            height=420,
            hide_index=True
        )
        generate_download_buttons(df_rank_display, "ranking_guardias_he_agentes", key_suffix="_rank")

        st.markdown("---")

        st.markdown("##### TOP 20: Total HE (Q) y G3T ($) por Legajo")
        df_top20 = df_rank.head(20).copy()

        fig_top20 = make_subplots(specs=[[{"secondary_y": True}]])

        fig_top20.add_trace(go.Bar(
            x=df_top20['Legajo'],
            y=df_top20['Total_HE_Q'],
            name='Total HE (Q)',
            text=[format_decimal_es(v, 1) if v % 1 != 0 else format_integer_es(v) for v in df_top20['Total_HE_Q']],
            textposition='outside',
            marker_color='#2563eb'
        ), secondary_y=False)

        fig_top20.add_trace(go.Scatter(
            x=df_top20['Legajo'],
            y=df_top20['G3T_Pesos'],
            name='G3T ($)',
            mode='lines+markers',
            line=dict(color='#ea580c', width=2.5),
            marker=dict(size=7, color='#ea580c'),
            hovertemplate='Legajo: %{x}<br>G3T ($): %{y:$,.2f}<extra></extra>'
        ), secondary_y=True)

        fig_top20.update_layout(
            legend=dict(orientation="h", y=1.12, x=0.5, xanchor='center'),
            margin=dict(t=30, b=40, l=10, r=10),
            height=420,
            xaxis_tickangle=-45
        )
        fig_top20.update_xaxes(type='category')
        fig_top20.update_yaxes(title_text="Total HE (Horas)", secondary_y=False, showgrid=True)
        fig_top20.update_yaxes(title_text="G3T ($)", secondary_y=True, showgrid=False)
        st.plotly_chart(fig_top20, use_container_width=True)

    # =========================================================================
    # --- PESTAÑA 3: DISTRIBUCIÓN GEOGRÁFICA ---
    # =========================================================================
    with tab_geo:
        st.subheader("Casos por Distrito - Acumulado a la Fecha")

        col_geo_t, col_geo_m = st.columns([1.1, 1.9])

        df_geo_dist = filtered_df.groupby(['Gerencia', 'Distrito'], as_index=False).agg(
            Casos=('Legajo', 'count'),
            Total_G3T_Pesos=('G3T ($)', 'sum'),
            Total_HE_Q=('Total HE (Q)', 'sum')
        ).sort_values(by='Casos', ascending=False).reset_index(drop=True)

        with col_geo_t:
            st.markdown("##### Casos por Distrito")
            tot_row_geo = pd.DataFrame({
                'Gerencia': ['Total'],
                'Distrito': [''],
                'Casos': [df_geo_dist['Casos'].sum()],
                'Total_G3T_Pesos': [df_geo_dist['Total_G3T_Pesos'].sum()],
                'Total_HE_Q': [df_geo_dist['Total_HE_Q'].sum()]
            })
            df_geo_display = pd.concat([df_geo_dist, tot_row_geo], ignore_index=True)

            st.dataframe(
                df_geo_display[['Gerencia', 'Distrito', 'Casos']].style.format({
                    'Casos': format_integer_es
                }),
                use_container_width=True,
                height=520,
                hide_index=True
            )
            generate_download_buttons(df_geo_dist, "casos_por_distrito_guardias_he", key_suffix="_geo")

        with col_geo_m:
            st.markdown("##### Mapa de Concentración por Distrito")
            
            df_map_data = filtered_df.dropna(subset=['Latitud', 'Longitud']).groupby(['Distrito'], as_index=False).agg(
                Latitud=('Latitud', 'first'),
                Longitud=('Longitud', 'first'),
                Casos=('Legajo', 'count'),
                Total_G3T=('G3T ($)', 'sum'),
                Total_HE=('Total HE (Q)', 'sum')
            )

            if not df_map_data.empty:
                mapbox_access_token = "pk.eyJ1Ijoic2FuZHJhcXVldmVkbyIsImEiOiJjbWYzOGNkZ2QwYWg0MnFvbDJucWc5d3VwIn0.bz6E-qxAwk6ZFPYohBsdMw"
                px.set_mapbox_access_token(mapbox_access_token)

                fig_map = px.scatter_mapbox(
                    df_map_data,
                    lat="Latitud",
                    lon="Longitud",
                    size="Casos",
                    color="Casos",
                    hover_name="Distrito",
                    hover_data={
                        "Latitud": False,
                        "Longitud": False,
                        "Casos": ":,.0f",
                        "Total_G3T": ":$,.2f",
                        "Total_HE": ":,.1f"
                    },
                    color_continuous_scale=px.colors.sequential.Blues,
                    size_max=40,
                    zoom=6.1,
                    center={"lat": -31.8, "lon": -60.8},
                    mapbox_style="satellite-streets"
                )
                fig_map.update_layout(
                    margin=dict(l=0, r=0, t=0, b=0),
                    height=520,
                    coloraxis_colorbar=dict(title="Casos")
                )
                st.plotly_chart(fig_map, use_container_width=True)
            else:
                st.info("No se encontraron coordenadas válidas para mostrar el mapa.")

    # =========================================================================
    # --- PESTAÑA 4: DATA CRUDA (INFO) ---
    # =========================================================================
    with tab_cruda:
        st.subheader("Data Cruda de Liquidaciones")

        cols_display_cruda = [
            'Legajo', 'Apellido y Nombre', 'Nivel', 'Subnivel', 'Gerencia', 'CeCo',
            'Tipo de Liquidación', 'Periodo_Label', 'G3T ($)', 'G3T (Q)',
            'HE al 50 % ($)', 'HE al 50 % Sábados ($)', 'HE al 100 % ($)',
            'HE al 50 % (Q)', 'HE al 50 % Sábados (Q)', 'HE al 100 % (Q)',
            'Total HE (Q)', 'Distrito', 'Ubicación', 'Sede'
        ]
        cols_presentes = [c for c in cols_display_cruda if c in filtered_df.columns]
        df_cruda_show = filtered_df[cols_presentes].copy().rename(columns={'Periodo_Label': 'Periodo (Mes)'})

        st.dataframe(
            df_cruda_show.style.format({
                'G3T ($)': format_currency_es,
                'G3T (Q)': format_integer_es,
                'HE al 50 % ($)': format_currency_es,
                'HE al 50 % Sábados ($)': format_currency_es,
                'HE al 100 % ($)': format_currency_es,
                'HE al 50 % (Q)': lambda x: format_decimal_es(x, 1) if x % 1 != 0 else format_integer_es(x),
                'HE al 50 % Sábados (Q)': lambda x: format_decimal_es(x, 1) if x % 1 != 0 else format_integer_es(x),
                'HE al 100 % (Q)': lambda x: format_decimal_es(x, 1) if x % 1 != 0 else format_integer_es(x),
                'Total HE (Q)': lambda x: format_decimal_es(x, 1) if x % 1 != 0 else format_integer_es(x)
            }),
            use_container_width=True,
            height=550,
            hide_index=True
        )
        generate_download_buttons(df_cruda_show, "data_cruda_guardias_3t_vs_he", key_suffix="_cruda")

else:
    st.info("Por favor, cargue un archivo Excel (.xlsx o .xlsm) para comenzar el análisis.")
