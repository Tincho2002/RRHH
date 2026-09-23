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

def format_decimal_es(num, decimals=1):
    if pd.isna(num) or not isinstance(num, (int, float, np.number)): return ""
    return f"{num:,.{decimals}f}".replace(",", "TEMP").replace(".", ",").replace("TEMP", ".")

def format_percentage_es(num, decimals=2):
    if pd.isna(num) or not isinstance(num, (int, float, np.number)): return "0,00%"
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
            df_au['Total (D)'] = pd.to_numeric(df_au['Total (D)'], errors='coerce').fillna(0.0)
        else:
            df_au['Total (D)'] = 0.0
            
        if 'Total (H)' in df_au.columns:
            df_au['Total (H)'] = pd.to_numeric(df_au['Total (H)'], errors='coerce').fillna(0.0)
        else:
            df_au['Total (H)'] = 0.0

        if 'Dias_Habiles' in df_au.columns:
            df_au['Dias_Habiles'] = pd.to_numeric(df_au['Dias_Habiles'], errors='coerce').fillna(21)
        else:
            df_au['Dias_Habiles'] = 21

        # Mapeo de meses y etiquetas cronológicas
        mapa_meses = {1: 'Ene', 2: 'Feb', 3: 'Mar', 4: 'Abr', 5: 'May', 6: 'Jun', 7: 'Jul', 8: 'Ago', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dic'}
        if 'Período' in df_au.columns:
            temp_dt = pd.to_datetime(df_au['Período'], errors='coerce')
            df_au['Periodo_Label'] = temp_dt.dt.month.map(mapa_meses) + '-' + temp_dt.dt.strftime('%y')
            df_au['Periodo_DT'] = temp_dt
        elif 'Mes' in df_au.columns:
            df_au['Periodo_Label'] = df_au['Mes'].astype(str).str.capitalize()
            df_au['Periodo_DT'] = pd.to_datetime('2026-01-01')

        # Normalizar fechas diarias (Desde Días y Hasta Días)
        if 'Desde (D)' in df_au.columns:
            df_au['Fecha_Diaria'] = pd.to_datetime(df_au['Desde (D)'], errors='coerce')
            df_au['Desde_Dias_Str'] = df_au['Fecha_Diaria'].dt.strftime('%d/%m/%Y')
        else:
            df_au['Fecha_Diaria'] = pd.NaT
            df_au['Desde_Dias_Str'] = None

        if 'Hasta (D)' in df_au.columns:
            df_au['Fecha_Hasta_D'] = pd.to_datetime(df_au['Hasta (D)'], errors='coerce')
            # Si no tiene fecha hasta pero sí fecha desde, asignamos la misma fecha desde
            df_au['Fecha_Hasta_D'] = df_au['Fecha_Hasta_D'].fillna(df_au['Fecha_Diaria'])
            df_au['Hasta_Dias_Str'] = df_au['Fecha_Hasta_D'].dt.strftime('%d/%m/%Y')
        else:
            df_au['Fecha_Hasta_D'] = df_au['Fecha_Diaria']
            df_au['Hasta_Dias_Str'] = df_au['Desde_Dias_Str']

        def extract_hour(val):
            if pd.isna(val): return None
            if hasattr(val, 'hour'): return val.hour
            val_s = str(val).strip()
            if ':' in val_s:
                try: return int(val_s.split(':')[0])
                except: pass
            return None

        def format_time_exact(val):
            if pd.isna(val): return None
            if hasattr(val, 'strftime'): return val.strftime('%H:%M:%S')
            val_s = str(val).strip()
            parts = val_s.split(':')
            if len(parts) >= 2:
                try:
                    h = int(parts[0])
                    m = int(parts[1])
                    s = int(parts[2]) if len(parts) > 2 else 0
                    return f"{h:02d}:{m:02d}:{s:02d}"
                except: pass
            return val_s

        if 'Desde (H)' in df_au.columns:
            df_au['Hora_Inicio'] = df_au['Desde (H)'].apply(extract_hour)
            df_au['Hora_Inicio_Label'] = df_au['Hora_Inicio'].apply(lambda h: f"{int(h):02d}:00 hs" if pd.notna(h) else "Otro Horario")
            df_au['Desde_H_Str'] = df_au['Desde (H)'].apply(format_time_exact)
        else:
            df_au['Hora_Inicio'] = None
            df_au['Hora_Inicio_Label'] = "Otro Horario"
            df_au['Desde_H_Str'] = None

        if 'Hasta (H)' in df_au.columns:
            df_au['Hora_Fin_Label'] = df_au['Hasta (H)'].apply(format_time_exact)
        else:
            df_au['Hora_Fin_Label'] = None

        def assign_rango_horario(h):
            if h is None or pd.isna(h): return 'Otro Horario'
            h = int(h)
            if 0 <= h < 4: return '00:00 a 04:00 hs'
            elif 4 <= h < 8: return '04:00 a 08:00 hs'
            elif 8 <= h < 12: return '08:00 a 12:00 hs'
            elif 12 <= h < 16: return '12:00 a 16:00 hs'
            elif 16 <= h < 20: return '16:00 a 20:00 hs'
            elif 20 <= h < 24: return '20:00 a 00:00 hs'
            return 'Otro Horario'

        df_au['Rango_Horario'] = df_au['Hora_Inicio'].apply(assign_rango_horario)

        # Normalizar Legajo
        if 'Legajo' in df_au.columns:
            df_au['Legajo'] = pd.to_numeric(df_au['Legajo'], errors='coerce').astype('Int64').astype(str)
            df_au['Legajo'] = df_au['Legajo'].replace(['<NA>', 'nan'], 'no disponible')

        # Cargar dotación
        df_dot = None
        if 'Dotación' in xls.sheet_names:
            df_dot = pd.read_excel(xls, sheet_name='Dotación')
            df_dot = df_dot.loc[:, ~df_dot.columns.astype(str).str.startswith('Unnamed:')]
            if 'Periodo' in df_dot.columns:
                temp_dt_dot = pd.to_datetime(df_dot['Periodo'], errors='coerce')
                df_dot['Periodo_Label'] = temp_dt_dot.dt.month.map(mapa_meses) + '-' + temp_dt_dot.dt.strftime('%y')
                df_dot['Periodo_DT'] = temp_dt_dot
            
            if 'Legajo' in df_dot.columns:
                df_dot['Legajo'] = pd.to_numeric(df_dot['Legajo'], errors='coerce').astype('Int64').astype(str)
                df_dot['Legajo'] = df_dot['Legajo'].replace(['<NA>', 'nan'], 'no disponible')

            dot_filter_cols = ['Gerencia', 'Ministerio', 'Distrito', 'Relación', 'Nivel', 'Sexo', 'Legajo', 'Sede']
            for c in dot_filter_cols:
                if c in df_dot.columns:
                    df_dot[c] = df_dot[c].astype(str).replace(['nan', 'None', '<NA>'], 'no disponible').str.strip()

        # Limpieza de columnas de texto en Ausentismo
        filter_cols = ['Legajo', 'Gerencia', 'Ministerio', 'Distrito', 'Relación', 'Nivel', 'Sexo', 'Tipo', 'Descripción', 'Licencia', 'Sede', 'Rango_Horario']
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
st.write("Análisis integral de ausentismo en días y horas, capacidad teórica e impacto territorial.")

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

    orden_rangos_def = [
        '00:00 a 04:00 hs', '04:00 a 08:00 hs', '08:00 a 12:00 hs',
        '12:00 a 16:00 hs', '16:00 a 20:00 hs', '20:00 a 00:00 hs', 'Otro Horario'
    ]

    filter_dict = {
        'Periodo_Label': 'Período',
        'Tipo': 'Tipo de Novedad',
        'Licencia': 'Licencia / Concepto',
        'Rango_Horario': 'Rango Horario',
        'Gerencia': 'Gerencia',
        'Ministerio': 'Ministerio',
        'Distrito': 'Distrito',
        'Sede': 'Sede',
        'Relación': 'Relación Laboral',
        'Nivel': 'Nivel',
        'Sexo': 'Sexo'
    }

    periodos_ordenados = df_au.sort_values('Periodo_DT')['Periodo_Label'].dropna().unique().tolist()

    def get_combined_options(col_name):
        if col_name == 'Rango_Horario':
            presentes = set(df_au['Rango_Horario'].unique())
            return [r for r in orden_rangos_def if r in presentes] or orden_rangos_def
        opts_au = set(df_au[col_name].dropna().unique()) if col_name in df_au.columns else set()
        opts_dot = set(df_dot[col_name].dropna().unique()) if (df_dot is not None and col_name in df_dot.columns) else set()
        total_opts = [str(o).strip() for o in opts_au.union(opts_dot) if str(o).strip() not in ['no disponible', 'nan', 'None', '<NA>']]
        return sorted(total_opts)

    all_possible_options = {
        k: (periodos_ordenados if k == 'Periodo_Label' else get_combined_options(k))
        for k in filter_dict.keys()
    }

    # Opciones de listas de búsqueda granular
    opts_legajos_raw = set(df_au['Legajo'].dropna().unique())
    if df_dot is not None and 'Legajo' in df_dot.columns:
        opts_legajos_raw = opts_legajos_raw.union(set(df_dot['Legajo'].dropna().unique()))
    opts_legajos = sorted(
        [str(o).strip() for o in opts_legajos_raw if str(o).strip() not in ['no disponible', 'nan', 'None', '<NA>']],
        key=lambda x: int(x) if str(x).isdigit() else 999999
    )

    fechas_desde_d_sorted = df_au.dropna(subset=['Fecha_Diaria']).sort_values('Fecha_Diaria')['Desde_Dias_Str'].unique().tolist()
    fechas_hasta_d_sorted = df_au.dropna(subset=['Fecha_Hasta_D']).sort_values('Fecha_Hasta_D')['Hasta_Dias_Str'].unique().tolist()
    horas_desde_h_sorted = sorted([h for h in df_au['Desde_H_Str'].dropna().unique() if h not in ['None', 'nan']])
    horas_hasta_h_sorted = sorted([h for h in df_au['Hora_Fin_Label'].dropna().unique() if h not in ['None', 'nan']])

    if 'au_selections_v8' not in st.session_state or st.sidebar.button("🔄 Resetear Filtros", use_container_width=True):
        st.session_state.au_selections_v8 = {k: list(v) for k, v in all_possible_options.items()}
        st.session_state.au_sel_legajo = []
        st.session_state.au_sel_desde_d = []
        st.session_state.au_sel_hasta_d = []
        st.session_state.au_sel_desde_h = []
        st.session_state.au_sel_hasta_h = []
        st.rerun()

    filtered_df = df_au.copy()
    filtered_dot = df_dot.copy() if df_dot is not None else None

    # Filtrado de variables generales
    for col, label in filter_dict.items():
        opts = all_possible_options[col]
        current_defaults = [x for x in st.session_state.au_selections_v8.get(col, opts) if x in opts]
        
        sel = st.sidebar.multiselect(
            label, 
            options=opts, 
            default=current_defaults, 
            key=f"sel_v8_{col}"
        )
        st.session_state.au_selections_v8[col] = sel

        if len(sel) == 0:
            filtered_df = filtered_df.iloc[0:0]
            if filtered_dot is not None and col in filtered_dot.columns:
                filtered_dot = filtered_dot.iloc[0:0]
        elif len(sel) < len(opts):
            if col in filtered_df.columns:
                filtered_df = filtered_df[filtered_df[col].isin(sel)]
            if filtered_dot is not None and col in filtered_dot.columns:
                filtered_dot = filtered_dot[filtered_dot[col].isin(sel)]

    # --- FILTROS PUNTUALES DE BÚSQUEDA ---
    st.sidebar.markdown("---")
    st.sidebar.markdown("##### Filtros de Fechas, Horas y Agentes")

    # 1. Desde (Días)
    sel_desde_d = st.sidebar.multiselect(
        "Desde (Días):",
        options=fechas_desde_d_sorted,
        default=st.session_state.get('au_sel_desde_d', []),
        help="Deje vacío para incluir todas las fechas de inicio, o elija una o más puntuales.",
        key="sel_v8_desde_d"
    )
    st.session_state.au_sel_desde_d = sel_desde_d
    if len(sel_desde_d) > 0:
        filtered_df = filtered_df[filtered_df['Desde_Dias_Str'].isin(sel_desde_d)]

    # 2. Hasta (Días)
    sel_hasta_d = st.sidebar.multiselect(
        "Hasta (Días):",
        options=fechas_hasta_d_sorted,
        default=st.session_state.get('au_sel_hasta_d', []),
        help="Deje vacío para incluir todas las fechas de fin, o elija una o más puntuales.",
        key="sel_v8_hasta_d"
    )
    st.session_state.au_sel_hasta_d = sel_hasta_d
    if len(sel_hasta_d) > 0:
        filtered_df = filtered_df[filtered_df['Hasta_Dias_Str'].isin(sel_hasta_d)]

    # 3. Desde (Horas)
    sel_desde_h = st.sidebar.multiselect(
        "Desde (Horas):",
        options=horas_desde_h_sorted,
        default=st.session_state.get('au_sel_desde_h', []),
        help="Deje vacío para todos los horarios de inicio, o elija franjas específicas.",
        key="sel_v8_desde_h"
    )
    st.session_state.au_sel_desde_h = sel_desde_h
    if len(sel_desde_h) > 0:
        filtered_df = filtered_df[filtered_df['Desde_H_Str'].isin(sel_desde_h)]

    # 4. Hasta (Horas)
    sel_hasta_h = st.sidebar.multiselect(
        "Hasta (Horas):",
        options=horas_hasta_h_sorted,
        default=st.session_state.get('au_sel_hasta_h', []),
        help="Deje vacío para todos los horarios de fin, o elija franjas específicas.",
        key="sel_v8_hasta_h"
    )
    st.session_state.au_sel_hasta_h = sel_hasta_h
    if len(sel_hasta_h) > 0:
        filtered_df = filtered_df[filtered_df['Hora_Fin_Label'].isin(sel_hasta_h)]

    # 5. Legajo
    sel_legajo = st.sidebar.multiselect(
        "Legajo (Búsqueda puntual):",
        options=opts_legajos,
        default=st.session_state.get('au_sel_legajo', []),
        help="Deje vacío para incluir a todos los colaboradores, o seleccione agentes puntuales.",
        key="sel_v8_legajo"
    )
    st.session_state.au_sel_legajo = sel_legajo
    if len(sel_legajo) > 0:
        filtered_df = filtered_df[filtered_df['Legajo'].isin(sel_legajo)]
        if filtered_dot is not None and 'Legajo' in filtered_dot.columns:
            filtered_dot = filtered_dot[filtered_dot['Legajo'].isin(sel_legajo)]

    # Validaciones de filtros
    sel_periodos = [p for p in periodos_ordenados if p in st.session_state.au_selections_v8.get('Periodo_Label', [])]

    if not sel_periodos:
        st.warning("⚠️ No hay ningún período seleccionado en el filtro **Período**. Seleccione al menos un mes en la barra lateral.")
        st.stop()

    if filtered_df.empty:
        st.warning("⚠️ No se encontraron registros con los filtros seleccionados.")
        st.stop()

    # --- CÁLCULO DE CAPACIDAD Y AUSENTISMO ---
    dias_habiles_por_mes = df_au.groupby('Periodo_Label')['Dias_Habiles'].first().to_dict()

    total_dias = filtered_df['Total (D)'].sum()
    total_horas = pd.to_numeric(filtered_df['Total (H)'], errors='coerce').fillna(0.0).sum()
    empleados_afectados = filtered_df['Legajo'].nunique()

    capacidad_dias_total = 0
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

    tasa_dias = (total_dias / capacidad_dias_total * 100) if capacidad_dias_total > 0 else 0.0
    tasa_horas = (total_horas / capacidad_horas_total * 100) if capacidad_horas_total > 0 else 0.0

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

    # --- Cálculo de Datos de Evolución Mensual ---
    evo_rows = []
    for p in sel_periodos:
        sub = filtered_df[filtered_df['Periodo_Label'] == p]
        d_sum = sub['Total (D)'].sum()
        h_sum = pd.to_numeric(sub['Total (H)'], errors='coerce').fillna(0.0).sum()
        agentes_sub = sub['Legajo'].nunique()
        
        if filtered_dot is not None and not filtered_dot.empty:
            dot_m = filtered_dot[filtered_dot['Periodo_Label'] == p]['Legajo'].nunique()
        else:
            dot_m = agentes_sub
            
        dh = dias_habiles_por_mes.get(p, 21)
        cap_d = dot_m * dh
        cap_h = cap_d * 8
        
        tasa_d = (d_sum / cap_d * 100) if cap_d > 0 else 0.0
        tasa_h = (h_sum / cap_h * 100) if cap_h > 0 else 0.0
        
        evo_rows.append({
            "Periodo": p,
            "Dias_Ausentes": d_sum,
            "Horas_Ausentes": h_sum,
            "Capacidad_Dias": cap_d,
            "Capacidad_Horas": cap_h,
            "Índice_Días": tasa_d,
            "Índice_Horas": tasa_h,
            "Agentes": agentes_sub
        })
        
    df_evo = pd.DataFrame(evo_rows)

    # --- Cálculo de Datos de Distribución Geográfica ---
    coord_dict = {}
    if 'Coordenadas' in df_au.columns:
        coord_dict.update(df_au.dropna(subset=['Coordenadas']).groupby('Distrito')['Coordenadas'].first().to_dict())
    if df_dot is not None and 'Coordenadas' in df_dot.columns:
        coord_dict.update(df_dot.dropna(subset=['Coordenadas']).groupby('Distrito')['Coordenadas'].first().to_dict())

    distritos_disponibles = sorted(list(set(filtered_df['Distrito'].unique())))
    distrito_data_rows = []

    for dist in distritos_disponibles:
        sub_au_dist = filtered_df[filtered_df['Distrito'] == dist]
        dias_tot = sub_au_dist['Total (D)'].sum()
        horas_tot = pd.to_numeric(sub_au_dist['Total (H)'], errors='coerce').fillna(0.0).sum()
        
        cap_d_tot = 0
        mes_indices_d = {}
        mes_indices_h = {}

        for p in sel_periodos:
            dh_p = dias_habiles_por_mes.get(p, 21)
            if filtered_dot is not None and not filtered_dot.empty:
                dot_dp = filtered_dot[(filtered_dot['Distrito'] == dist) & (filtered_dot['Periodo_Label'] == p)]['Legajo'].nunique()
            else:
                dot_dp = sub_au_dist[sub_au_dist['Periodo_Label'] == p]['Legajo'].nunique()
            
            cap_dp = dot_dp * dh_p
            cap_d_tot += cap_dp
            
            d_p = sub_au_dist[sub_au_dist['Periodo_Label'] == p]['Total (D)'].sum()
            h_p = pd.to_numeric(sub_au_dist[sub_au_dist['Periodo_Label'] == p]['Total (H)'], errors='coerce').fillna(0.0).sum()
            
            mes_indices_d[p] = (d_p / cap_dp * 100) if cap_dp > 0 else 0.0
            mes_indices_h[p] = (h_p / (cap_dp * 8) * 100) if cap_dp > 0 else 0.0

        iau_dias_dist = (dias_tot / cap_d_tot * 100) if cap_d_tot > 0 else 0.0
        iau_horas_dist = (horas_tot / (cap_d_tot * 8) * 100) if cap_d_tot > 0 else 0.0

        lat, lon = np.nan, np.nan
        coord_str = coord_dict.get(dist, "")
        if coord_str and ',' in str(coord_str):
            try:
                parts = str(coord_str).split(',')
                lat = float(parts[0].strip())
                lon = float(parts[1].strip())
            except:
                pass

        row_dict = {
            "Distrito": dist,
            "Total (D)": dias_tot,
            "Total (H)": horas_tot,
            "Capacidad (D)": cap_d_tot,
            "Índice Ausentismo (Días)": iau_dias_dist,
            "Índice Ausentismo (Horas)": iau_horas_dist,
            "Latitud": lat,
            "Longitud": lon,
            "Coordenadas": coord_str
        }
        for p in sel_periodos:
            row_dict[f"{p} (D)"] = mes_indices_d[p]
            row_dict[f"{p} (H)"] = mes_indices_h[p]

        distrito_data_rows.append(row_dict)

    df_geo_distritos = pd.DataFrame(distrito_data_rows)

    # --- Pestañas de Análisis ---
    tab_iau, tab_geo_d, tab_geo_h, tab_dias_caidos, tab_horas_caidas, tab_matriz_hc, tab_cronologia, tab_gantt, tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Tablero Ejecutivo IAU",
        "🗺️ Distribución Geográfica (Días)",
        "🗺️ Distribución Geográfica (Horas)",
        "📅 Días Caídos",
        "⏰ Horas Caídas",
        "⏱️ Horas Caídas por Horario",
        "📜 Cronología de Licencias",
        "📊 Cronograma de Licencias (Gantt)",
        "📈 Evolución de Volúmenes (Días y Horas)",
        "📂 Motivos y Tipos de Licencia",
        "🏢 Distribución por Gerencia y Distrito",
        "📋 Detalle de Registros"
    ])

    # =========================================================================
    # --- TABLERO EJECUTIVO IAU ---
    # =========================================================================
    with tab_iau:
        st.subheader("Tablero Comparativo de Índices de Ausentismo (IAU)")
        
        if not df_evo.empty:
            col_d1, col_line, col_d2 = st.columns([1.2, 2.2, 1.2])
            paleta_meses = ['#1f77b4', '#d62728', '#2ca02c', '#ff7f0e', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']

            with col_d1:
                st.markdown("<h5 style='text-align: center; color: #334155;'>IAU (Días) - Participación -</h5>", unsafe_allow_html=True)
                fig_pie_d = px.pie(
                    df_evo, 
                    names='Periodo', 
                    values='Índice_Días', 
                    hole=0.45,
                    color_discrete_sequence=paleta_meses
                )
                fig_pie_d.update_traces(
                    sort=False,
                    textinfo='percent', 
                    textposition='inside', 
                    insidetextorientation='horizontal',
                    direction='clockwise'
                )
                fig_pie_d.update_layout(
                    showlegend=True, 
                    legend=dict(orientation="v", y=0.5, x=1.05, font=dict(size=10), traceorder="normal"), 
                    margin=dict(t=20, b=20, l=10, r=10), 
                    height=280
                )
                st.plotly_chart(fig_pie_d, use_container_width=True)

            with col_line:
                st.markdown("<h5 style='text-align: center; color: #334155;'>IAU (Días) vs IAU (Horas) - Evolución Mensual -</h5>", unsafe_allow_html=True)
                fig_line = make_subplots(specs=[[{"secondary_y": True}]])

                fig_line.add_trace(go.Scatter(
                    x=df_evo['Periodo'],
                    y=df_evo['Índice_Días'],
                    name='IAU (Días)',
                    mode='lines+markers+text',
                    text=[f"{v:.2f}%".replace('.', ',') for v in df_evo['Índice_Días']],
                    textposition='top center',
                    textfont=dict(size=11, color='#2563eb'),
                    line=dict(color='#2563eb', width=3),
                    marker=dict(size=7)
                ), secondary_y=False)

                fig_line.add_trace(go.Scatter(
                    x=df_evo['Periodo'],
                    y=df_evo['Índice_Horas'],
                    name='IAU (Horas)',
                    mode='lines+markers+text',
                    text=[f"{v:.2f}%".replace('.', ',') for v in df_evo['Índice_Horas']],
                    textposition='top center',
                    textfont=dict(size=11, color='#dc2626'),
                    line=dict(color='#dc2626', width=2.5),
                    marker=dict(size=7)
                ), secondary_y=True)

                fig_line.update_layout(legend=dict(orientation="h", y=1.12, x=0.5, xanchor='center'), hovermode="x unified", margin=dict(t=30, b=20, l=10, r=10), height=280)
                fig_line.update_xaxes(categoryorder='array', categoryarray=sel_periodos)
                fig_line.update_yaxes(title_text="IAU Días (%)", secondary_y=False, showgrid=True)
                fig_line.update_yaxes(title_text="IAU Horas (%)", secondary_y=True, showgrid=False)
                st.plotly_chart(fig_line, use_container_width=True)

            with col_d2:
                st.markdown("<h5 style='text-align: center; color: #334155;'>IAU (Horas) - Participación -</h5>", unsafe_allow_html=True)
                fig_pie_h = px.pie(
                    df_evo, 
                    names='Periodo', 
                    values='Índice_Horas', 
                    hole=0.45,
                    color_discrete_sequence=paleta_meses
                )
                fig_pie_h.update_traces(
                    sort=False,
                    textinfo='percent', 
                    textposition='inside', 
                    insidetextorientation='horizontal',
                    direction='clockwise'
                )
                fig_pie_h.update_layout(
                    showlegend=True, 
                    legend=dict(orientation="v", y=0.5, x=1.05, font=dict(size=10), traceorder="normal"), 
                    margin=dict(t=20, b=20, l=10, r=10), 
                    height=280
                )
                st.plotly_chart(fig_pie_h, use_container_width=True)

            st.markdown("---")

            col_tbl_d, col_tbl_h = st.columns(2)
            with col_tbl_d:
                st.markdown("##### Índice Ausentismo (Días) - Evolución Mensual -")
                cols_periodos = list(df_evo['Periodo'])
                valores_dias = [format_percentage_es(val) for val in df_evo['Índice_Días']]
                tabla_dias_dict = {p: [v] for p, v in zip(cols_periodos, valores_dias)}
                tabla_dias_dict['Total general'] = [format_percentage_es(tasa_dias)]
                df_tbl_d = pd.DataFrame(tabla_dias_dict, index=['Índice Ausentismo (Días)'])
                st.dataframe(df_tbl_d, use_container_width=True)

            with col_tbl_h:
                st.markdown("##### Índice Ausentismo (Horas) - Evolución Mensual -")
                valores_horas = [format_percentage_es(val) for val in df_evo['Índice_Horas']]
                tabla_horas_dict = {p: [v] for p, v in zip(cols_periodos, valores_horas)}
                tabla_horas_dict['Total general'] = [format_percentage_es(tasa_horas)]
                df_tbl_h = pd.DataFrame(tabla_horas_dict, index=['Índice Ausentismo (Horas)'])
                st.dataframe(df_tbl_h, use_container_width=True)

            st.markdown("<br>", unsafe_allow_html=True)

            col_bar_d, col_bar_h = st.columns(2)
            with col_bar_d:
                st.markdown("##### Índice Ausentismo (Días) - Evolución Mensual -")
                fig_bar_d = go.Figure()
                fig_bar_d.add_trace(go.Bar(
                    x=df_evo['Periodo'],
                    y=df_evo['Índice_Días'],
                    text=[f"{v:.2f}%".replace('.', ',') for v in df_evo['Índice_Días']],
                    textposition='outside',
                    marker_color='#2563eb',
                    name='IAU Días'
                ))
                min_d = max(0, df_evo['Índice_Días'].min() - 5)
                max_d = df_evo['Índice_Días'].max() + 8
                fig_bar_d.update_layout(yaxis=dict(title="Índice Ausentismo (%)", range=[min_d, max_d]), xaxis=dict(categoryorder='array', categoryarray=sel_periodos), margin=dict(t=30, b=20, l=10, r=10), height=320)
                st.plotly_chart(fig_bar_d, use_container_width=True)

            with col_bar_h:
                st.markdown("##### Índice Ausentismo (Horas) - Evolución Mensual -")
                fig_bar_h = go.Figure()
                fig_bar_h.add_trace(go.Bar(
                    x=df_evo['Periodo'],
                    y=df_evo['Índice_Horas'],
                    text=[f"{v:.2f}%".replace('.', ',') for v in df_evo['Índice_Horas']],
                    textposition='outside',
                    marker_color='#0284c7',
                    name='IAU Horas'
                ))
                min_h = max(0, df_evo['Índice_Horas'].min() - 0.5)
                max_h = df_evo['Índice_Horas'].max() + 0.8
                fig_bar_h.update_layout(yaxis=dict(title="Índice Ausentismo (%)", range=[min_h, max_h]), xaxis=dict(categoryorder='array', categoryarray=sel_periodos), margin=dict(t=30, b=20, l=10, r=10), height=320)
                st.plotly_chart(fig_bar_h, use_container_width=True)
        else:
            st.info("No hay datos de evolución disponibles.")

    # =========================================================================
    # --- TAB DISTRIBUCIÓN GEOGRÁFICA (DÍAS) ---
    # =========================================================================
    with tab_geo_d:
        st.subheader("Ausentismo en Días (Licencias) por Distrito")
        
        if not df_geo_distritos.empty:
            df_geo_d_sorted = df_geo_distritos.sort_values(by="Índice Ausentismo (Días)", ascending=False).reset_index(drop=True)
            
            col_geo_left, col_geo_right = st.columns([1.1, 1.1])
            
            with col_geo_left:
                st.markdown("##### Ausentismo en Días (Licencias) por Distrito y por Mes")
                
                cols_meses_d = [f"{p} (D)" for p in sel_periodos]
                cols_table_d = ["Distrito"] + cols_meses_d + ["Índice Ausentismo (Días)"]
                
                df_tbl_show_d = df_geo_d_sorted[cols_table_d].copy()
                rename_dict_d = {f"{p} (D)": p for p in sel_periodos}
                rename_dict_d["Índice Ausentismo (Días)"] = "Total"
                df_tbl_show_d = df_tbl_show_d.rename(columns=rename_dict_d)
                
                total_row_dict_d = {"Distrito": "Total"}
                for p in sel_periodos:
                    val_mes = df_evo[df_evo['Periodo'] == p]['Índice_Días'].values
                    total_row_dict_d[p] = val_mes[0] if len(val_mes) > 0 else 0.0
                total_row_dict_d["Total"] = tasa_dias
                
                df_tbl_final_d = pd.concat([df_tbl_show_d, pd.DataFrame([total_row_dict_d])], ignore_index=True)
                
                format_cols_d = {col: lambda x: format_percentage_es(x, 2) for col in sel_periodos + ["Total"]}
                st.dataframe(df_tbl_final_d.style.format(format_cols_d), use_container_width=True, height=280)

                st.markdown("##### Ranking de Distritos - Índice Ausentismo (Días)")
                fig_bar_dist_d = px.bar(
                    df_geo_d_sorted.head(10),
                    x="Distrito",
                    y="Índice Ausentismo (Días)",
                    text="Índice Ausentismo (Días)",
                    color_discrete_sequence=['#2563eb']
                )
                fig_bar_dist_d.update_traces(
                    texttemplate='%{text:.2f}%',
                    textposition='outside'
                )
                fig_bar_dist_d.update_layout(
                    yaxis=dict(title="Índice Ausentismo (Días)", range=[0, df_geo_d_sorted['Índice Ausentismo (Días)'].max() * 1.25]),
                    xaxis_tickangle=-45,
                    height=300,
                    margin=dict(t=20, b=50, l=10, r=10)
                )
                st.plotly_chart(fig_bar_dist_d, use_container_width=True)

            with col_geo_right:
                st.markdown("##### Mapa de Coordenadas por Índice de Ausentismo (Días)")
                df_map_d = df_geo_distritos.dropna(subset=['Latitud', 'Longitud']).copy()
                
                if not df_map_d.empty:
                    mapbox_access_token = "pk.eyJ1Ijoic2FuZHJhcXVldmVkbyIsImEiOiJjbWYzOGNkZ2QwYWg0MnFvbDJucWc5d3VwIn0.bz6E-qxAwk6ZFPYohBsdMw"
                    px.set_mapbox_access_token(mapbox_access_token)

                    fig_map_d = px.scatter_mapbox(
                        df_map_d,
                        lat="Latitud",
                        lon="Longitud",
                        size="Índice Ausentismo (Días)",
                        color="Índice Ausentismo (Días)",
                        hover_name="Distrito",
                        hover_data={
                            "Latitud": False,
                            "Longitud": False,
                            "Índice Ausentismo (Días)": ":.2f",
                            "Total (D)": ":,.0f"
                        },
                        color_continuous_scale=px.colors.sequential.Plasma,
                        size_max=38,
                        zoom=6.1,
                        center={"lat": -31.8, "lon": -60.8},
                        mapbox_style="satellite-streets"
                    )
                    fig_map_d.update_layout(
                        margin=dict(l=0, r=0, t=0, b=0),
                        height=600,
                        coloraxis_colorbar=dict(title="IAU Días (%)", ticksuffix="%")
                    )
                    st.plotly_chart(fig_map_d, use_container_width=True)
                else:
                    st.warning("No se encontraron coordenadas válidas para mostrar el mapa.")
        else:
            st.info("No hay datos geográficos disponibles.")

    # =========================================================================
    # --- TAB DISTRIBUCIÓN GEOGRÁFICA (HORAS) ---
    # =========================================================================
    with tab_geo_h:
        st.subheader("Ausentismo en Horas (Novedades) por Distrito")
        
        if not df_geo_distritos.empty:
            df_geo_h_sorted = df_geo_distritos.sort_values(by="Índice Ausentismo (Horas)", ascending=False).reset_index(drop=True)
            
            col_geo_left_h, col_geo_right_h = st.columns([1.1, 1.1])
            
            with col_geo_left_h:
                st.markdown("##### Ausentismo en Horas (Novedades) por Distrito y por Mes")
                
                cols_meses_h = [f"{p} (H)" for p in sel_periodos]
                cols_table_h = ["Distrito"] + cols_meses_h + ["Índice Ausentismo (Horas)"]
                
                df_tbl_show_h = df_geo_h_sorted[cols_table_h].copy()
                rename_dict_h = {f"{p} (H)": p for p in sel_periodos}
                rename_dict_h["Índice Ausentismo (Horas)"] = "Total"
                df_tbl_show_h = df_tbl_show_h.rename(columns=rename_dict_h)
                
                total_row_dict_h = {"Distrito": "Total"}
                for p in sel_periodos:
                    val_mes_h = df_evo[df_evo['Periodo'] == p]['Índice_Horas'].values
                    total_row_dict_h[p] = val_mes_h[0] if len(val_mes_h) > 0 else 0.0
                total_row_dict_h["Total"] = tasa_horas
                
                df_tbl_final_h = pd.concat([df_tbl_show_h, pd.DataFrame([total_row_dict_h])], ignore_index=True)
                
                format_cols_h = {col: lambda x: format_percentage_es(x, 2) for col in sel_periodos + ["Total"]}
                st.dataframe(df_tbl_final_h.style.format(format_cols_h), use_container_width=True, height=280)

                st.markdown("##### Ranking de Distritos - Índice Ausentismo (Horas)")
                fig_bar_dist_h = px.bar(
                    df_geo_h_sorted.head(10),
                    x="Distrito",
                    y="Índice Ausentismo (Horas)",
                    text="Índice Ausentismo (Horas)",
                    color_discrete_sequence=['#0284c7']
                )
                fig_bar_dist_h.update_traces(
                    texttemplate='%{text:.2f}%',
                    textposition='outside'
                )
                fig_bar_dist_h.update_layout(
                    yaxis=dict(title="Índice Ausentismo (Horas)", range=[0, df_geo_h_sorted['Índice Ausentismo (Horas)'].max() * 1.25]),
                    xaxis_tickangle=-45,
                    height=300,
                    margin=dict(t=20, b=50, l=10, r=10)
                )
                st.plotly_chart(fig_bar_dist_h, use_container_width=True)

            with col_geo_right_h:
                st.markdown("##### Mapa de Coordenadas por Índice de Ausentismo (Horas)")
                df_map_h = df_geo_distritos.dropna(subset=['Latitud', 'Longitud']).copy()
                
                if not df_map_h.empty:
                    mapbox_access_token = "pk.eyJ1Ijoic2FuZHJhcXVldmVkbyIsImEiOiJjbWYzOGNkZ2QwYWg0MnFvbDJucWc5d3VwIn0.bz6E-qxAwk6ZFPYohBsdMw"
                    px.set_mapbox_access_token(mapbox_access_token)

                    fig_map_h = px.scatter_mapbox(
                        df_map_h,
                        lat="Latitud",
                        lon="Longitud",
                        size="Índice Ausentismo (Horas)",
                        color="Índice Ausentismo (Horas)",
                        hover_name="Distrito",
                        hover_data={
                            "Latitud": False,
                            "Longitud": False,
                            "Índice Ausentismo (Horas)": ":.2f",
                            "Total (H)": ":,.0f"
                        },
                        color_continuous_scale=px.colors.sequential.Blues,
                        size_max=38,
                        zoom=6.1,
                        center={"lat": -31.8, "lon": -60.8},
                        mapbox_style="satellite-streets"
                    )
                    fig_map_h.update_layout(
                        margin=dict(l=0, r=0, t=0, b=0),
                        height=600,
                        coloraxis_colorbar=dict(title="IAU Horas (%)", ticksuffix="%")
                    )
                    st.plotly_chart(fig_map_h, use_container_width=True)
                else:
                    st.warning("No se encontraron coordenadas válidas para mostrar el mapa.")
        else:
            st.info("No hay datos geográficos disponibles.")

    # =========================================================================
    # --- TAB DÍAS CAÍDOS ---
    # =========================================================================
    with tab_dias_caidos:
        st.subheader("Análisis de Días Caídos por Mes y Fecha")
        
        df_dc = filtered_df[filtered_df['Total (D)'] > 0].copy()
        
        if not df_dc.empty:
            col_dc1, col_dc2 = st.columns([1.3, 2.2])
            
            df_mes_dc = df_dc.groupby('Periodo_Label', sort=False)['Total (D)'].sum().reindex(sel_periodos, fill_value=0.0).reset_index()
            
            df_mes_dc['Var (Q)'] = df_mes_dc['Total (D)'].diff()
            if not df_mes_dc.empty:
                df_mes_dc.loc[0, 'Var (Q)'] = df_mes_dc.loc[0, 'Total (D)']
            
            df_mes_dc['% (mes)'] = df_mes_dc['Total (D)'].pct_change() * 100
            
            max_dias_val = df_mes_dc['Total (D)'].max()
            df_mes_dc['% (acum)'] = ((df_mes_dc['Total (D)'] - max_dias_val) / max_dias_val * 100) if max_dias_val > 0 else 0.0

            total_dias_gen = df_mes_dc['Total (D)'].sum()
            
            with col_dc1:
                st.markdown("##### Días Caídos por Mes")
                df_mes_dc_display = df_mes_dc.copy()
                total_row_dc = pd.DataFrame({
                    'Periodo_Label': ['Total'],
                    'Total (D)': [total_dias_gen],
                    'Var (Q)': [total_dias_gen],
                    '% (acum)': [df_mes_dc['% (acum)'].sum() if len(df_mes_dc) > 0 else 0.0],
                    '% (mes)': [np.nan]
                })
                df_mes_dc_display = pd.concat([df_mes_dc_display, total_row_dc], ignore_index=True)
                
                st.dataframe(
                    df_mes_dc_display.rename(columns={'Periodo_Label': 'Período'}).style.format({
                        'Total (D)': format_integer_es,
                        'Var (Q)': lambda x: f"{int(round(x)):,}".replace(",", ".") if pd.notna(x) else "-",
                        '% (acum)': lambda x: f"{x:,.2f}%".replace(",", "TEMP").replace(".", ",").replace("TEMP", ".") if pd.notna(x) else "-",
                        '% (mes)': lambda x: f"{x:,.2f}%".replace(",", "TEMP").replace(".", ",").replace("TEMP", ".") if pd.notna(x) else "-"
                    }),
                    use_container_width=True,
                    height=320,
                    hide_index=True
                )

            with col_dc2:
                st.markdown("##### Días Caídos por Mes (Evolución y Variación)")
                fig_combo_dc = make_subplots(specs=[[{"secondary_y": True}]])
                
                fig_combo_dc.add_trace(go.Bar(
                    x=df_mes_dc['Periodo_Label'],
                    y=df_mes_dc['Total (D)'],
                    name='Total (D)',
                    text=[format_integer_es(v) for v in df_mes_dc['Total (D)']],
                    textposition='outside',
                    marker_color='#2563eb'
                ), secondary_y=False)

                fig_combo_dc.add_trace(go.Bar(
                    x=df_mes_dc['Periodo_Label'],
                    y=df_mes_dc['Var (Q)'],
                    name='Var (Q)',
                    text=[format_integer_es(v) for v in df_mes_dc['Var (Q)']],
                    textposition='outside',
                    marker_color='#dc2626'
                ), secondary_y=False)

                fig_combo_dc.add_trace(go.Scatter(
                    x=df_mes_dc['Periodo_Label'],
                    y=df_mes_dc['% (acum)'],
                    name='% (acum)',
                    mode='lines+markers',
                    line=dict(color='#eab308', width=2.5),
                    marker=dict(size=6)
                ), secondary_y=True)

                fig_combo_dc.add_trace(go.Scatter(
                    x=df_mes_dc['Periodo_Label'],
                    y=df_mes_dc['% (mes)'],
                    name='% (mes)',
                    mode='lines+markers',
                    line=dict(color='#22c55e', width=2.5),
                    marker=dict(size=6)
                ), secondary_y=True)

                fig_combo_dc.update_layout(
                    barmode='group',
                    legend=dict(orientation="h", y=1.15, x=0.5, xanchor='center'),
                    margin=dict(t=30, b=40, l=10, r=10),
                    height=320
                )
                fig_combo_dc.update_yaxes(title_text="Días", secondary_y=False, showgrid=True)
                fig_combo_dc.update_yaxes(title_text="Variación (%)", secondary_y=True, showgrid=False, ticksuffix="%")
                st.plotly_chart(fig_combo_dc, use_container_width=True)

            st.markdown("---")

            col_fec_tbl_d, col_fec_chart_d = st.columns([1.1, 2.9])
            
            df_fechas_d = df_dc.dropna(subset=['Fecha_Diaria']).groupby('Fecha_Diaria')['Total (D)'].sum().reset_index()
            df_fechas_d = df_fechas_d.sort_values('Fecha_Diaria')
            
            mapa_meses_full = {1: 'ene', 2: 'feb', 3: 'mar', 4: 'abr', 5: 'may', 6: 'jun', 7: 'jul', 8: 'ago', 9: 'sep', 10: 'oct', 11: 'nov', 12: 'dic'}
            df_fechas_d['Fecha_Label'] = df_fechas_d['Fecha_Diaria'].apply(lambda d: f"{d.day} {mapa_meses_full.get(d.month, '')} {d.year}")
            
            with col_fec_tbl_d:
                st.markdown("##### Días Caídos por Fecha")
                df_fechas_d_show = df_fechas_d[['Fecha_Label', 'Total (D)']].copy().rename(columns={'Fecha_Label': 'Fecha'})
                total_fec_row_d = pd.DataFrame({'Fecha': ['Total'], 'Total (D)': [df_fechas_d_show['Total (D)'].sum()]})
                df_fechas_d_show = pd.concat([df_fechas_d_show, total_fec_row_d], ignore_index=True)
                
                st.dataframe(
                    df_fechas_d_show.style.format({'Total (D)': format_integer_es}),
                    use_container_width=True,
                    height=400,
                    hide_index=True
                )
                generate_download_buttons(df_fechas_d_show, "dias_caidos_por_fecha", key_suffix="_dc_fec")

            with col_fec_chart_d:
                st.markdown("##### Evolución de la cantidad de dias caídos por fecha")
                fig_line_fecha_d = go.Figure()
                fig_line_fecha_d.add_trace(go.Scatter(
                    x=df_fechas_d['Fecha_Diaria'],
                    y=df_fechas_d['Total (D)'],
                    mode='lines+markers',
                    name='Total (D)',
                    line=dict(color='#2563eb', width=2),
                    marker=dict(size=6, color='#2563eb'),
                    hovertemplate='Fecha: %{x|%d %b %Y}<br>Total (D): %{y:,.0f}<extra></extra>'
                ))
                fig_line_fecha_d.update_layout(
                    xaxis_title="Fecha",
                    yaxis_title="Total Días",
                    hovermode="x unified",
                    margin=dict(t=30, b=30, l=10, r=10),
                    height=400
                )
                st.plotly_chart(fig_line_fecha_d, use_container_width=True)

        else:
            st.info("No se registran novedades de días caídos en la selección actual.")

    # =========================================================================
    # --- TAB HORAS CAÍDAS ---
    # =========================================================================
    with tab_horas_caidas:
        st.subheader("Análisis de Horas Caídas por Franja Horaria y Fecha")
        
        df_hc = filtered_df[filtered_df['Total (H)'] > 0].copy()
        
        if not df_hc.empty:
            col_hc1, col_hc2, col_hc3 = st.columns([1.1, 1.4, 1.5])
            
            orden_rangos = [
                '00:00 a 04:00 hs',
                '04:00 a 08:00 hs',
                '08:00 a 12:00 hs',
                '12:00 a 16:00 hs',
                '16:00 a 20:00 hs',
                '20:00 a 00:00 hs',
                'Otro Horario'
            ]
            
            df_rango = df_hc.groupby('Rango_Horario')['Total (H)'].sum().reindex(orden_rangos, fill_value=0.0).reset_index()
            total_hc_general = df_rango['Total (H)'].sum()
            df_rango['Part. (%)'] = (df_rango['Total (H)'] / total_hc_general * 100) if total_hc_general > 0 else 0.0
            
            with col_hc1:
                st.markdown("##### Horas Caídas por Rango Horario")
                df_rango_display = df_rango.copy()
                total_row_rango = pd.DataFrame({
                    'Rango_Horario': ['Total'],
                    'Total (H)': [total_hc_general],
                    'Part. (%)': [100.0]
                })
                df_rango_display = pd.concat([df_rango_display, total_row_rango], ignore_index=True)
                st.dataframe(
                    df_rango_display.style.format({
                        'Total (H)': lambda x: format_decimal_es(x, 1) if x % 1 != 0 else format_integer_es(x),
                        'Part. (%)': lambda x: format_percentage_es(x, 2)
                    }),
                    use_container_width=True,
                    height=320,
                    hide_index=True
                )

            with col_hc2:
                st.markdown("##### Horas Caídas por Rango Horario")
                df_rango_chart = df_rango[df_rango['Total (H)'] > 0]
                
                fig_combo_rango = make_subplots(specs=[[{"secondary_y": True}]])
                fig_combo_rango.add_trace(go.Bar(
                    x=df_rango_chart['Rango_Horario'],
                    y=df_rango_chart['Total (H)'],
                    name='Total (H)',
                    text=[format_decimal_es(v, 1) if v % 1 != 0 else format_integer_es(v) for v in df_rango_chart['Total (H)']],
                    textposition='outside',
                    marker_color='#2563eb'
                ), secondary_y=False)

                fig_combo_rango.add_trace(go.Scatter(
                    x=df_rango_chart['Rango_Horario'],
                    y=df_rango_chart['Part. (%)'],
                    name='Part. (%)',
                    mode='lines+markers',
                    line=dict(color='#dc2626', width=2.5),
                    marker=dict(size=6)
                ), secondary_y=True)

                fig_combo_rango.update_layout(
                    legend=dict(orientation="h", y=1.15, x=0.5, xanchor='center'),
                    margin=dict(t=30, b=40, l=10, r=10),
                    height=320,
                    xaxis_tickangle=-35
                )
                fig_combo_rango.update_yaxes(title_text="Horas", secondary_y=False, showgrid=True)
                fig_combo_rango.update_yaxes(title_text="Participación (%)", secondary_y=True, showgrid=False, ticksuffix="%")
                st.plotly_chart(fig_combo_rango, use_container_width=True)

            with col_hc3:
                st.markdown("##### Horas Caídas por Hora (intervalo crítico)")
                df_horas_crit = df_hc.dropna(subset=['Hora_Inicio']).copy()
                df_horas_crit['Hora_Inicio'] = df_horas_crit['Hora_Inicio'].astype(int)
                
                df_hora_agg = df_horas_crit.groupby('Hora_Inicio')['Total (H)'].sum().reset_index()
                df_hora_agg['Hora_Label'] = df_hora_agg['Hora_Inicio'].apply(lambda h: f"{h:02d}:00 hs")
                df_hora_agg = df_hora_agg.sort_values('Hora_Inicio')

                fig_bar_hora = px.bar(
                    df_hora_agg,
                    x='Hora_Label',
                    y='Total (H)',
                    text='Total (H)',
                    color_discrete_sequence=['#2563eb']
                )
                fig_bar_hora.update_traces(
                    texttemplate='%{text:,.0f}',
                    textposition='outside'
                )
                fig_bar_hora.update_layout(
                    xaxis_title=None,
                    yaxis_title="Horas Caídas",
                    margin=dict(t=30, b=40, l=10, r=10),
                    height=320,
                    xaxis_tickangle=-45
                )
                st.plotly_chart(fig_bar_hora, use_container_width=True)

            st.markdown("---")

            col_fec_tbl, col_fec_chart = st.columns([1.1, 2.9])
            
            df_fechas = df_hc.dropna(subset=['Fecha_Diaria']).groupby('Fecha_Diaria')['Total (H)'].sum().reset_index()
            df_fechas = df_fechas.sort_values('Fecha_Diaria')
            
            mapa_meses_full = {1: 'ene', 2: 'feb', 3: 'mar', 4: 'abr', 5: 'may', 6: 'jun', 7: 'jul', 8: 'ago', 9: 'sep', 10: 'oct', 11: 'nov', 12: 'dic'}
            df_fechas['Fecha_Label'] = df_fechas['Fecha_Diaria'].apply(lambda d: f"{d.day} {mapa_meses_full.get(d.month, '')} {d.year}")
            
            with col_fec_tbl:
                st.markdown("##### Horas Caídas por Fecha")
                df_fechas_show = df_fechas[['Fecha_Label', 'Total (H)']].copy().rename(columns={'Fecha_Label': 'Fecha'})
                total_fec_row = pd.DataFrame({'Fecha': ['Total'], 'Total (H)': [df_fechas_show['Total (H)'].sum()]})
                df_fechas_show = pd.concat([df_fechas_show, total_fec_row], ignore_index=True)
                
                st.dataframe(
                    df_fechas_show.style.format({
                        'Total (H)': lambda x: format_decimal_es(x, 1) if x % 1 != 0 else format_integer_es(x)
                    }),
                    use_container_width=True,
                    height=400,
                    hide_index=True
                )
                generate_download_buttons(df_fechas_show, "horas_caidas_por_fecha", key_suffix="_hc_fec")

            with col_fec_chart:
                st.markdown("##### Evolución de la cantidad de horas caídas por fecha")
                fig_line_fecha = go.Figure()
                fig_line_fecha.add_trace(go.Scatter(
                    x=df_fechas['Fecha_Diaria'],
                    y=df_fechas['Total (H)'],
                    mode='lines+markers',
                    name='Total (H)',
                    line=dict(color='#2563eb', width=2),
                    marker=dict(size=6, color='#2563eb'),
                    hovertemplate='Fecha: %{x|%d %b %Y}<br>Total (H): %{y:,.1f}<extra></extra>'
                ))
                fig_line_fecha.update_layout(
                    xaxis_title="Fecha",
                    yaxis_title="Total Horas",
                    hovermode="x unified",
                    margin=dict(t=30, b=30, l=10, r=10),
                    height=400
                )
                st.plotly_chart(fig_line_fecha, use_container_width=True)

        else:
            st.info("No se registran novedades horarias en la selección actual.")

    # =========================================================================
    # --- TAB HORAS CAÍDAS SEGÚN HORA DE INICIO ---
    # =========================================================================
    with tab_matriz_hc:
        st.subheader("Matriz de Horas Caídas según Hora de Inicio y Hora de Fin")
        st.write("Cruce detallado de franjas horarias exactas con totales acumulados.")
        
        df_matriz_source = filtered_df[(filtered_df['Total (H)'] > 0) & (filtered_df['Hora_Fin_Label'].notna())].copy()
        
        if not df_matriz_source.empty:
            df_pivot_hc = pd.pivot_table(
                df_matriz_source,
                index='Hora_Inicio_Label',
                columns='Hora_Fin_Label',
                values='Total (H)',
                aggfunc='sum',
                fill_value=0.0
            )
            
            def get_sort_hour(label):
                try:
                    return int(str(label).split(':')[0])
                except:
                    return 99
            
            filas_ordenadas = sorted(df_pivot_hc.index.tolist(), key=get_sort_hour)
            columnas_ordenadas = sorted(df_pivot_hc.columns.tolist())
            
            df_pivot_hc = df_pivot_hc.reindex(index=filas_ordenadas, columns=columnas_ordenadas, fill_value=0.0)
            df_pivot_hc['Total'] = df_pivot_hc.sum(axis=1)
            
            total_general_row = df_pivot_hc.sum(axis=0).to_frame().T
            total_general_row.index = ['Total general']
            df_pivot_display = pd.concat([df_pivot_hc, total_general_row])
            
            def format_celda_horas(val):
                if pd.isna(val) or val == 0:
                    return "-"
                if val % 1 != 0:
                    return format_decimal_es(val, 1)
                return format_integer_es(val)
            
            st.markdown("##### Horas Caídas según Hora de Inicio")
            st.dataframe(
                df_pivot_display.style.format(format_celda_horas),
                use_container_width=True,
                height=550
            )
            
            df_download_matriz = df_pivot_hc.reset_index().rename(columns={'Hora_Inicio_Label': 'Hora de Inicio'})
            generate_download_buttons(df_download_matriz, "horas_caidas_segun_hora_inicio", key_suffix="_hc_matriz")
        else:
            st.info("No hay registros con información de horario de inicio y fin para la selección actual.")

    # =========================================================================
    # --- TAB CRONOLOGÍA POR TIPO Y POR LICENCIA ---
    # =========================================================================
    with tab_cronologia:
        st.subheader("Cronología por Tipo y por Licencia")
        st.write("Detalle consolidado por episodio de licencia ordenado por días acumulados.")

        # Agrupamos por cada episodio único (incluyendo su fecha de inicio y fin)
        cron_dim = [
            'Legajo', 'Apellido y Nombre', 'Tipo', 'Licencia',
            'Fecha_Diaria', 'Fecha_Hasta_D', 'Desde_H_Str', 'Hora_Fin_Label'
        ]
        
        # Aseguramos columnas presentes
        cols_existentes = [c for c in cron_dim if c in filtered_df.columns]

        df_cron_agg = filtered_df.groupby(cols_existentes, as_index=False).agg(
            Total_D=('Total (D)', 'sum'),
            Total_H=('Total (H)', 'sum')
        )

        # Filtramos los que tengan impacto en días u horas
        df_cron_agg = df_cron_agg[(df_cron_agg['Total_D'] > 0) | (df_cron_agg['Total_H'] > 0)].copy()

        if not df_cron_agg.empty:
            mapa_meses_full = {
                1: 'ene', 2: 'feb', 3: 'mar', 4: 'abr', 5: 'may', 6: 'jun',
                7: 'jul', 8: 'ago', 9: 'sep', 10: 'oct', 11: 'nov', 12: 'dic'
            }

            def format_date_str(d):
                if pd.isna(d): return "-"
                return f"{d.day} {mapa_meses_full.get(d.month, '')} {d.year}"

            # Formateo de fechas visibles
            df_cron_agg['Desde (D)'] = df_cron_agg['Fecha_Diaria'].apply(format_date_str)
            df_cron_agg['Hasta (D)'] = df_cron_agg['Fecha_Hasta_D'].apply(format_date_str)
            df_cron_agg['Desde (H)'] = df_cron_agg['Desde_H_Str'].fillna("-") if 'Desde_H_Str' in df_cron_agg.columns else "-"
            df_cron_agg['Hasta (H)'] = df_cron_agg['Hora_Fin_Label'].fillna("-") if 'Hora_Fin_Label' in df_cron_agg.columns else "-"

            # Orden idéntico a Looker: Total (D) descendente, luego fecha de inicio
            df_cron_final = df_cron_agg.sort_values(
                by=['Total_D', 'Fecha_Diaria'], 
                ascending=[False, True]
            ).reset_index(drop=True)

            cols_show = [
                'Legajo', 'Apellido y Nombre', 'Tipo', 'Licencia',
                'Desde (D)', 'Hasta (D)', 'Desde (H)', 'Hasta (H)',
                'Total_D', 'Total_H'
            ]
            df_cron_display = df_cron_final[cols_show].rename(
                columns={'Total_D': 'Total (D)', 'Total_H': 'Total (H)'}
            )

            st.dataframe(
                df_cron_display.style.format({
                    'Total (D)': lambda x: format_integer_es(x) if x > 0 else "-",
                    'Total (H)': lambda x: format_decimal_es(x, 1) if (x > 0 and x % 1 != 0) else (format_integer_es(x) if x > 0 else "-")
                }),
                use_container_width=True,
                height=550,
                hide_index=True
            )
            generate_download_buttons(df_cron_display, "cronologia_licencias_agentes", key_suffix="_cron")
        else:
            st.info("No hay registros cronológicos para los filtros seleccionados.")

    # =========================================================================
    # --- TAB CRONOGRAMA DE LICENCIAS (DIAGRAMA DE GANTT - IDÉNTICO A LOOKER) ---
    # =========================================================================
    with tab_gantt:
        st.subheader("Cronograma Visual de Licencias (Diagrama de Gantt)")
        st.write("Visualización cronológica de todas las ausencias por agente ordenada estrictamente por fecha de inicio.")

        # Tomamos todos los registros con fecha válida (Licencias y Novedades como PRP)
        df_gantt_base = filtered_df[
            (filtered_df['Fecha_Diaria'].notna()) & 
            (filtered_df['Fecha_Hasta_D'].notna())
        ].copy()

        if not df_gantt_base.empty:
            df_gantt_base = df_gantt_base[df_gantt_base['Fecha_Hasta_D'] >= df_gantt_base['Fecha_Diaria']]
            
            # Orden cronológico estricto por Fecha de Inicio
            df_gantt_sorted = df_gantt_base.sort_values(by=['Fecha_Diaria', 'Fecha_Hasta_D'], ascending=[True, True]).reset_index(drop=True)

            # Para que las licencias o permisos de 1 solo día no tengan ancho 0, extendemos 24hs
            df_gantt_sorted['Fecha_Grafico_Fin'] = df_gantt_sorted['Fecha_Hasta_D'] + pd.Timedelta(days=1)

            # Etiqueta visible idéntica a Looker
            def make_event_label_clean(row):
                lic = str(row['Licencia']).strip()
                lic_clean = ' - '.join([part.strip() for part in lic.split('-')])
                return f"{row['Legajo']} - {row['Apellido y Nombre']} - {lic_clean}"

            df_gantt_sorted['Label_Visible'] = df_gantt_sorted.apply(make_event_label_clean, axis=1)

            # Identificador único de fila para que Plotly no agrupe eventos repetidos del mismo agente
            df_gantt_sorted['ID_Renglon'] = [f"{lbl}\u200b" * (i % 5) + f" ({i+1})" for i, lbl in enumerate(df_gantt_sorted['Label_Visible'])]

            # Controles
            cant_max_disponible = len(df_gantt_sorted)
            cant_mostrar = st.slider(
                "Cantidad de registros a mostrar:",
                min_value=min(5, cant_max_disponible),
                max_value=cant_max_disponible,
                value=min(35, cant_max_disponible),
                step=5 if cant_max_disponible >= 5 else 1,
                key="gantt_cant_slider"
            )

            df_plot_gantt = df_gantt_sorted.head(cant_mostrar).copy()
            orden_renglones_cronologico = df_plot_gantt['ID_Renglon'].tolist()

            if not df_plot_gantt.empty:
                min_x = df_plot_gantt['Fecha_Diaria'].min() - pd.Timedelta(days=2)
                max_x = df_plot_gantt['Fecha_Grafico_Fin'].max() + pd.Timedelta(days=3)

                fig_gantt = px.timeline(
                    df_plot_gantt,
                    x_start="Fecha_Diaria",
                    x_end="Fecha_Grafico_Fin",
                    y="ID_Renglon",
                    color_discrete_sequence=['#2563eb'],
                    hover_name="Apellido y Nombre",
                    hover_data={
                        "Legajo": True,
                        "Licencia": True,
                        "Tipo": True,
                        "Fecha_Diaria": "|%d/%m/%Y",
                        "Fecha_Hasta_D": "|%d/%m/%Y",
                        "ID_Renglon": False,
                        "Fecha_Grafico_Fin": False
                    }
                )

                # Mapeamos los textos visibles en el eje Y
                fig_gantt.update_yaxes(
                    categoryorder="array",
                    categoryarray=orden_renglones_cronologico,
                    tickmode="array",
                    tickvals=df_plot_gantt['ID_Renglon'],
                    ticktext=df_plot_gantt['Label_Visible'],
                    autorange="reversed",
                    title=None
                )
                fig_gantt.update_xaxes(
                    title="Línea de Tiempo",
                    showgrid=True,
                    range=[min_x, max_x],
                    dtick="M1",
                    tickformat="%d/%m/%Y"
                )
                fig_gantt.update_layout(
                    height=max(450, cant_mostrar * 26),
                    margin=dict(l=10, r=20, t=20, b=30),
                    hovermode="closest"
                )
                st.plotly_chart(fig_gantt, use_container_width=True)
            else:
                st.info("No hay ausencias que coincidan con la selección.")
        else:
            st.info("No se registran ausencias con fechas válidas para construir el cronograma.")

    # --- TAB 1: Volúmenes Absolutos ---
    with tab1:
        st.subheader("Evolución Temporal del Ausentismo (Días y Horas)")
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

    # =========================================================================
    # --- TAB 2: MOTIVOS Y LICENCIAS ---
    # =========================================================================
    with tab2:
        st.subheader("Composición por Tipo y Motivo de Ausencia")
        
        analisis_pie = st.radio(
            "Seleccione la métrica para el gráfico de distribución:",
            options=["Días por Motivo de Licencia", "Horas por Concepto de Novedad", "Total de Casos (Licencias vs Novedades)"],
            horizontal=True,
            key="radio_pie_tab2"
        )
        st.markdown("<br>", unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            if analisis_pie == "Días por Motivo de Licencia":
                df_lic_dias = (
                    filtered_df[filtered_df['Total (D)'] > 0]
                    .groupby('Licencia', as_index=False)['Total (D)']
                    .sum()
                    .sort_values(by='Total (D)', ascending=False)
                )
                if not df_lic_dias.empty:
                    top_n = 5
                    if len(df_lic_dias) > top_n:
                        df_top = df_lic_dias.head(top_n).copy()
                        otros_val = df_lic_dias.iloc[top_n:]['Total (D)'].sum()
                        df_otros = pd.DataFrame([{'Licencia': 'Otras Licencias', 'Total (D)': otros_val}])
                        df_pie_final = pd.concat([df_top, df_otros], ignore_index=True)
                    else:
                        df_pie_final = df_lic_dias

                    fig_pie_mot = px.pie(
                        df_pie_final,
                        names='Licencia',
                        values='Total (D)',
                        title='Distribución de Días por Motivo de Licencia',
                        hole=0.4,
                        color_discrete_sequence=['#0d9488', '#0284c7', '#2563eb', '#f59e0b', '#ec4899', '#94a3b8']
                    )
                    fig_pie_mot.update_traces(textinfo='percent+value')
                    st.plotly_chart(fig_pie_mot, use_container_width=True)
                else:
                    st.info("No se registran días de licencias en la selección.")

            elif analisis_pie == "Horas por Concepto de Novedad":
                df_nov_horas = (
                    filtered_df[filtered_df['Total (H)'] > 0]
                    .groupby('Licencia', as_index=False)['Total (H)']
                    .sum()
                    .sort_values(by='Total (H)', ascending=False)
                )
                if not df_nov_horas.empty:
                    top_nh = 5
                    if len(df_nov_horas) > top_nh:
                        df_top_h = df_nov_horas.head(top_nh).copy()
                        otros_h = df_nov_horas.iloc[top_nh:]['Total (H)'].sum()
                        df_otros_h = pd.DataFrame([{'Licencia': 'Otras Novedades', 'Total (H)': otros_h}])
                        df_pie_nov_final = pd.concat([df_top_h, df_otros_h], ignore_index=True)
                    else:
                        df_pie_nov_final = df_nov_horas

                    fig_pie_nov = px.pie(
                        df_pie_nov_final,
                        names='Licencia',
                        values='Total (H)',
                        title='Distribución de Horas por Concepto de Novedad',
                        hole=0.4,
                        color_discrete_sequence=['#0284c7', '#0369a1', '#0d9488', '#14b8a6', '#f59e0b', '#94a3b8']
                    )
                    fig_pie_nov.update_traces(textinfo='percent+value')
                    st.plotly_chart(fig_pie_nov, use_container_width=True)
                else:
                    st.info("No se registran horas en la selección.")

            else:
                df_casos = filtered_df.groupby('Tipo', as_index=False)['Legajo'].count().rename(columns={'Legajo': 'Casos'})
                fig_pie_casos = px.pie(
                    df_casos,
                    names='Tipo',
                    values='Casos',
                    title='Distribución por Tipo de Registro (Casos)',
                    hole=0.4,
                    color_discrete_sequence=['#0d9488', '#0284c7']
                )
                fig_pie_casos.update_traces(textinfo='percent+label+value')
                st.plotly_chart(fig_pie_casos, use_container_width=True)

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
        cols_mostrar = [c for c in ['Legajo', 'Apellido y Nombre', 'Periodo_Label', 'Tipo', 'Licencia', 'Total (D)', 'Total (H)', 'Gerencia', 'Distrito', 'Sede', 'Relación'] if c in filtered_df.columns]
        st.dataframe(filtered_df[cols_mostrar], use_container_width=True, hide_index=True)
        generate_download_buttons(filtered_df[cols_mostrar], "registros_ausentismo_filtrados", key_suffix="_bruto")
else:
    st.info("Por favor, cargue un archivo Excel para comenzar el análisis.")
