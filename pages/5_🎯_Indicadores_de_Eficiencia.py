# ===============================================================
# Visualizador de Eficiencia - V Estética (Código Completo y Corregido)
# ===============================================================

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from io import BytesIO
import numpy as np # <--- MANEJO DE VALORES INFINITOS
import traceback # PARA ERRORES DETALLADOS

# Configuración de la página para que ocupe todo el ancho
st.set_page_config(layout="wide", page_title="Visualizador de Eficiencia")

# ----------------- Funciones de Datos -----------------

@st.cache_data
def load_data(uploaded_file):
    """
    Carga los datos desde un archivo Excel, procesa las fechas,
    CALCULA TOTALES DE HORAS EXTRAS Y DÍAS de GUARDIA.
    Fusiona 'Dotación' desde 'masa_salarial' hacia 'eficiencia'.
    """
    if uploaded_file is None:
        return pd.DataFrame(), pd.DataFrame(), [], [], [], {}, [], []

    # Leer todas las hojas
    excel_file = pd.ExcelFile(uploaded_file)
    sheet_names = excel_file.sheet_names

    df_eficiencia = pd.DataFrame()
    df_indicadores = pd.DataFrame()

    k_cols, qty_cols, years, months_map = [], [], [], {}
    k_indicador_cols, qty_indicador_cols = [], []

    # --- Cargar Hoja 'eficiencia' ---
    if 'eficiencia' in sheet_names:
        try:
            df_eficiencia = pd.read_excel(excel_file, sheet_name='eficiencia', header=0)

            # CÁLCULO DE TOTALES
            he_costo_cols = ['$K_50%', '$K_100%']
            he_qty_cols = ['hs_50%', 'hs_100%']
            if all(col in df_eficiencia.columns for col in he_costo_cols):
                df_eficiencia['$K_Total_HE'] = df_eficiencia[he_costo_cols].fillna(0).sum(axis=1)
            if all(col in df_eficiencia.columns for col in he_qty_cols):
                df_eficiencia['hs_Total_HE'] = df_eficiencia[he_qty_cols].fillna(0).sum(axis=1)

            guardia_costo_cols = ['$K_Guardias_2T', '$K_Guardias_3T', '$K_GTO', '$K_GTI', '$K_TD']
            guardia_qty_cols = ['ds_Guardias_2T', 'ds_Guardias_3T', 'ds_GTO', 'ds_GTI', 'ds_TD']
            if all(col in df_eficiencia.columns for col in guardia_costo_cols):
                df_eficiencia['$K_Total_Guardias'] = df_eficiencia[guardia_costo_cols].fillna(0).sum(axis=1)
            if all(col in df_eficiencia.columns for col in guardia_qty_cols):
                df_eficiencia['ds_Total_Guardias'] = df_eficiencia[guardia_qty_cols].fillna(0).sum(axis=1)

            # Convertir fechas
            df_eficiencia['Período'] = pd.to_datetime(df_eficiencia['Período'])
            df_eficiencia['Año'] = df_eficiencia['Período'].dt.year
            df_eficiencia['Mes'] = df_eficiencia['Período'].dt.month
            df_eficiencia['Período_fmt'] = df_eficiencia['Período'].dt.strftime('%b-%y')

            # Agrupación Temporal
            df_eficiencia['Bimestre'] = (df_eficiencia['Mes'] - 1) // 2 + 1
            df_eficiencia['Trimestre'] = (df_eficiencia['Mes'] - 1) // 3 + 1
            df_eficiencia['Semestre'] = (df_eficiencia['Mes'] - 1) // 6 + 1

        except Exception as e:
            st.error(f"Error en hoja 'eficiencia': {e}")
            return pd.DataFrame(), pd.DataFrame(), [], [], [], {}, [], []
    else:
        st.error("No se encontró la hoja 'eficiencia'.")
        return pd.DataFrame(), pd.DataFrame(), [], [], [], {}, [], []

    # --- Cargar Hoja 'masa_salarial' ---
    if 'masa_salarial' in sheet_names:
        try:
            df_indicadores = pd.read_excel(excel_file, sheet_name='masa_salarial', header=0)
            df_indicadores.columns = df_indicadores.columns.str.strip()

            if 'Período' in df_indicadores.columns:
                periodo_original = df_indicadores['Período'].copy()
                try:
                    df_indicadores['Período'] = pd.to_datetime(periodo_original)
                except:
                    mes_map_es = {'ene':'Jan','feb':'Feb','mar':'Mar','abr':'Apr','may':'May','jun':'Jun',
                                 'jul':'Jul','ago':'Aug','sep':'Sep','oct':'Oct','nov':'Nov','dic':'Dec'}
                    per_str = periodo_original.astype(str).str.lower()
                    for k, v in mes_map_es.items(): per_str = per_str.str.replace(k, v)
                    df_indicadores['Período'] = pd.to_datetime(per_str, format='%b-%y', errors='coerce')

                if pd.api.types.is_datetime64_any_dtype(df_indicadores['Período']):
                    df_indicadores['Año'] = df_indicadores['Período'].dt.year
                    df_indicadores['Mes'] = df_indicadores['Período'].dt.month
                    df_indicadores['Período_fmt'] = df_indicadores['Período'].dt.strftime('%b-%y')
                    df_indicadores['Bimestre'] = (df_indicadores['Mes'] - 1) // 2 + 1
                    df_indicadores['Trimestre'] = (df_indicadores['Mes'] - 1) // 3 + 1
                    df_indicadores['Semestre'] = (df_indicadores['Mes'] - 1) // 6 + 1

            k_ind_def = ['Msalarial_$K', 'HExtras_$K', 'Guardias_$K']
            if 'Dotación' in df_indicadores.columns: k_ind_def.append('Dotación')
            qty_ind_def = ['HE_hs', 'Guardias_ds', 'Dotación']
            
            k_indicador_cols = [c for c in k_ind_def if c in df_indicadores.columns]
            qty_indicador_cols = [c for c in qty_ind_def if c in df_indicadores.columns]

        except Exception as e:
            st.error("Error en hoja 'masa_salarial'")
            df_indicadores = pd.DataFrame()

    # Fusionar Dotación
    if not df_eficiencia.empty and not df_indicadores.empty:
        if 'Dotación' in df_indicadores.columns and 'Período' in df_eficiencia.columns:
            df_dot = df_indicadores[['Período', 'Dotación']].copy()
            df_eficiencia = pd.merge(df_eficiencia, df_dot, on='Período', how='left')

    if not df_eficiencia.empty:
        k_cols = sorted(list(set([c for c in df_eficiencia.columns if c.startswith('$K_')] + (['Dotación'] if 'Dotación' in df_eficiencia.columns else []))))
        qty_cols = sorted(list(set([c for c in df_eficiencia.columns if c.startswith('hs_') or c.startswith('ds_')] + (['Dotación'] if 'Dotación' in df_eficiencia.columns else []))))
        years = sorted(df_eficiencia['Año'].unique(), reverse=True)
        months_map = {1:'Ene',2:'Feb',3:'Mar',4:'Abr',5:'May',6:'Jun',7:'Jul',8:'Ago',9:'Sep',10:'Oct',11:'Nov',12:'Dic'}

    return df_eficiencia, df_indicadores, k_cols, qty_cols, years, months_map, k_indicador_cols, qty_indicador_cols

# ----------------- Funciones de Formato -----------------

def format_number(x):
    if pd.isna(x): return ""
    return f"{float(x):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def format_number_int(x):
    if pd.isna(x): return ""
    return f"{float(x):,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")

def format_percentage(x):
    if pd.isna(x): return ""
    return f"{format_number(x)} %"

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Datos')
    output.seek(0)
    return output

# ----------------- Funciones de Gráficos -----------------

def plot_combined_chart(df_plot, primary_cols, secondary_cols, primary_title, secondary_title):
    fig = go.Figure()
    layout_args = {
        'title': "Evolución Combinada", 'template': 'plotly_white', 'xaxis_title': 'Período',
        'yaxis': {'title': primary_title, 'side': 'left', 'showgrid': False},
        'legend': {'orientation': 'h', 'yanchor': 'bottom', 'y': 1.02, 'xanchor': 'right', 'x': 1},
        'barmode': 'group'
    }

    sec_cols_filt = [c for c in secondary_cols if c != "Ninguna"]
    if sec_cols_filt and not df_plot.empty:
        all_sec = pd.Series(dtype=float)
        valid_sec = []
        for c in sec_cols_filt:
            if c in df_plot.columns:
                all_sec = pd.concat([all_sec, df_plot[c].dropna()])
                valid_sec.append(c)
        
        if valid_sec:
            s_min, s_max = 0, 1
            if not all_sec.empty:
                d_min, d_max = all_sec.min(), all_sec.max()
                pad = (d_max - d_min) * 0.1 if d_max != d_min else abs(d_max * 0.1 or 1.0)
                s_min = d_min - pad if d_min < 0 or (d_min - pad) < 0 else (d_min - pad)
                s_max = d_max + pad
                if d_min >= 0 and s_min < 0: s_min = 0

            layout_args['yaxis2'] = {'title': secondary_title, 'side': 'right', 'overlaying': 'y', 'showgrid': False, 'range': [s_min, s_max]}
            for c in valid_sec:
                fmt = format_number_int if c.startswith(('ds_','hs_')) or c in ['HE_hs','Guardias_ds','Dotación'] else format_number
                fig.add_trace(go.Bar(x=df_plot['Período_fmt'], y=df_plot[c], name=c, text=[fmt(v) for v in df_plot[c]], textposition='outside', yaxis='y2', opacity=0.7))

    if primary_cols and not df_plot.empty:
        for c in primary_cols:
            if c in df_plot.columns:
                fmt = format_number_int if c.startswith(('ds_','hs_')) or c in ['HE_hs','Guardias_ds','Dotación'] else format_number
                fig.add_trace(go.Scatter(x=df_plot['Período_fmt'], y=df_plot[c], name=c, mode='lines+markers+text', text=[fmt(v) for v in df_plot[c]], textposition='top center', yaxis='y1'))

    fig.update_layout(**layout_args)
    return fig

def calc_variation(df, columns, tipo='mensual'):
    cols_proc = [c for c in columns if c in df.columns]
    if not cols_proc or df.empty or 'Período' not in df.columns:
        return pd.DataFrame(), pd.DataFrame()

    df_var = df[['Período', 'Período_fmt', 'Año', 'Mes'] + cols_proc].copy().sort_values('Período')

    if tipo == 'interanual':
        df_prev = df_var.copy()
        df_prev['Año'] = df_prev['Año'] + 1
        rename_map = {c: f"{c}_prev" for c in cols_proc}
        df_prev.rename(columns=rename_map, inplace=True)
        df_merged = pd.merge(df_var, df_prev[['Año', 'Mes'] + list(rename_map.values())], on=['Año', 'Mes'], how='left')
        
        df_val = pd.DataFrame(index=df_merged.index)
        df_pct = pd.DataFrame(index=df_merged.index)
        df_val[['Período','Período_fmt']] = df_merged[['Período','Período_fmt']]
        df_pct[['Período','Período_fmt']] = df_merged[['Período','Período_fmt']]

        for c in cols_proc:
            c_prev = f"{c}_prev"
            df_val[c] = df_merged[c] - df_merged[c_prev]
            df_pct[c] = (df_val[c] / df_merged[c_prev]) * 100
            df_pct[c] = df_pct[c].replace([np.inf, -np.inf], np.nan)
    else:
        df_val = pd.DataFrame(index=df_var.index)
        df_pct = pd.DataFrame(index=df_var.index)
        df_val[['Período','Período_fmt']] = df_var[['Período','Período_fmt']]
        df_pct[['Período','Período_fmt']] = df_var[['Período','Período_fmt']]

        for c in cols_proc:
            df_val[c] = df_var[c].diff()
            df_pct[c] = (df_val[c] / df_var[c].shift(1)) * 100

    return df_val, df_pct

def plot_bar(df_plot, columns, title):
    fig = go.Figure()
    if not df_plot.empty and 'Período_fmt' in df_plot.columns:
        for c in columns:
            if c in df_plot.columns:
                fmt = format_number_int if c.startswith(('ds_','hs_')) or c in ['HE_hs', 'Guardias_ds', 'Dotación'] else format_number
                fig.add_trace(go.Bar(x=df_plot['Período_fmt'], y=df_plot[c], name=c, text=[fmt(v) for v in df_plot[c]], textposition='outside'))
    fig.update_layout(title=title, template='plotly_white', xaxis_title='Período', yaxis_title=title)
    return fig

def show_table(df_table, nombre, show_totals=False, is_percentage=False):
    if df_table.empty: return
    sort_col = 'Período' if 'Período' in df_table.columns else 'Período_fmt'
    df_sorted = df_table.sort_values(by=sort_col, ascending=False).copy()
    
    df_display = df_sorted.drop(columns=['Período'], errors='ignore').rename(columns={'Período_fmt': 'Período'}).reset_index(drop=True)

    if show_totals:
        num_cols = df_display.select_dtypes(include='number').columns
        tot_row = {c: df_display[c].sum() for c in num_cols}
        tot_row['Período'] = 'Total'
        df_display = pd.concat([df_display, pd.DataFrame([tot_row])], ignore_index=True)

    df_fmt = df_display.copy()
    for c in df_fmt.select_dtypes(include='number').columns:
        if is_percentage: df_fmt[c] = df_fmt[c].apply(format_percentage)
        elif c.startswith(('ds_','hs_')) or c in ['HE_hs','Guardias_ds','Dotación']: df_fmt[c] = df_fmt[c].apply(format_number_int)
        else: df_fmt[c] = df_fmt[c].apply(format_number)

    st.dataframe(df_fmt, use_container_width=True)
    c1, c2 = st.columns(2)
    c1.download_button(f"📥 CSV ({nombre})", df_fmt.to_csv(index=False).encode('utf-8'), f"{nombre}.csv", "text/csv", use_container_width=True)
    c2.download_button(f"📥 Excel ({nombre})", to_excel(df_fmt), f"{nombre}.xlsx", use_container_width=True)

def show_kpi_cards(df, var_list):
    if df.empty or 'Año' not in df.columns: return
    vars_ex = [v for v in var_list if v in df.columns]
    if not vars_ex: return

    df_24 = df[df['Año'] == 2024][vars_ex].sum()
    df_25 = df[df['Año'] == 2025][vars_ex].sum()
    cols = st.columns(5)
    
    label_map = {
        '$K_50%': 'HE 50%', '$K_100%': 'HE 100%', '$K_Total_HE': 'Total HE', '$K_GTO': 'GTO', '$K_GTI': 'GTI', 
        '$K_Guardias_2T': 'Guardias 2T', '$K_Guardias_3T': 'Guardias 3T', '$K_TD': 'TD', '$K_Total_Guardias': 'Total Guardias',
        'hs_50%': 'Hrs 50%', 'hs_100%': 'Hrs 100%', 'hs_Total_HE': 'Hrs HE', 'ds_GTO': 'Ds GTO', 'ds_GTI': 'Ds GTI',
        'ds_Guardias_2T': 'Ds G2T', 'ds_Guardias_3T': 'Ds G3T', 'ds_TD': 'Ds TD', 'ds_Total_Guardias': 'Ds Guardias'
    }

    colors = ['card-blue', 'card-azure', 'card-violet', 'card-purple', 'card-indigo']
    for i, var in enumerate(vars_ex):
        t24, t25 = df_24.get(var, 0), df_25.get(var, 0)
        delta = t25 - t24
        pct = (delta / v24 * 100) if t24 > 0 else (100.0 if t25 > 0 else 0.0)
        
        is_int = var.startswith(('ds_', 'hs_')) or var == 'Dotación'
        fmt_f = format_number_int if is_int else format_number
        
        val_str = f"{'$K ' if var.startswith('$K_') else ''}{fmt_f(t25)}"
        d_str = f"{'$K ' if var.startswith('$K_') else ''}{fmt_f(abs(delta))}"
        
        icon = "↑" if delta >= 0 else "↓"
        d_color = "#86efac" if delta >= 0 else "#fca5a5"
        d_html = f"<span style='color:{d_color}; font-weight:bold;'>{icon} {d_str} ({format_percentage(pct)})</span>"

        html = f"""<div class="metric-card {colors[i % 5]}">
                    <div class="metric-label">{label_map.get(var, var)}</div>
                    <div class="metric-value">{val_str}</div>
                    <div class="metric-delta">{d_html}</div>
                   </div>"""
        cols[i % 5].markdown(html, unsafe_allow_html=True)

def apply_time_filter(df_to_filter, filter_mode, filter_selection, opts):
    if df_to_filter.empty: return df_to_filter
    if filter_mode == 'Período Específico' and filter_selection:
        return df_to_filter[df_to_filter['Período_fmt'].isin(filter_selection)]
    elif filter_mode == 'Mes' and filter_selection:
        nums = [k for k,v in opts['months_map'].items() if v in filter_selection]
        return df_to_filter[df_to_filter['Mes'].isin(nums)]
    elif filter_mode == 'Bimestre' and filter_selection:
        return df_to_filter[df_to_filter['Bimestre'].isin(filter_selection)]
    elif filter_mode == 'Trimestre' and filter_selection:
        return df_to_filter[df_to_filter['Trimestre'].isin(filter_selection)]
    elif filter_mode == 'Semestre' and filter_selection:
        return df_to_filter[df_to_filter['Semestre'].isin(filter_selection)]
    return df_to_filter

# ----------------- Estilos -----------------

st.markdown("""<style>
    .metric-card { border-radius: 12px; padding: 12px 8px; color: white; display: flex; flex-direction: column; align-items: center; text-align: center; min-height: 110px; margin: 10px 0; }
    .metric-value { font-size: 1.4rem; font-weight: 700; }
    .metric-label { font-size: 0.85rem; opacity: 0.9; text-transform: uppercase; }
    .metric-delta { font-size: 0.75rem; }
    .card-blue { background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); }
    .card-azure { background: linear-gradient(135deg, #2193b0 0%, #6dd5fa 100%); }
    .card-violet { background: linear-gradient(135deg, #4a00e0 0%, #8e2de2 100%); }
    .card-purple { background: linear-gradient(135deg, #834d9b 0%, #d04ed6 100%); }
    .card-indigo { background: linear-gradient(135deg, #4b6cb7 0%, #182848 100%); }
</style>""", unsafe_allow_html=True)

# ----------------- Ejecución Principal -----------------

up = st.file_uploader("Cargue el archivo Excel", type="xlsx")
if not up: st.info("Cargue un archivo para comenzar."); st.stop()

df_ef, df_ind, k_cols, q_cols, all_yrs, m_map, k_i_cols, q_i_cols = load_data(up)
if df_ef.empty: st.stop()

st.sidebar.header("Filtros")
if 'selected_years' not in st.session_state: st.session_state.selected_years = all_yrs
sel_yrs = st.sidebar.multiselect("Años:", all_yrs, key='selected_years')
f_mode = st.sidebar.radio("Modo:", ['Mes','Bimestre','Trimestre','Semestre','Período Específico'], horizontal=True)

opts = {'months_map': m_map}
sel_val = []
if f_mode == 'Mes': sel_val = st.sidebar.multiselect("Meses:", list(m_map.values()), key='sm')
elif f_mode == 'Bimestre': sel_val = st.sidebar.multiselect("Bimestres:", sorted(df_ef['Bimestre'].unique()), key='sb')
elif f_mode == 'Trimestre': sel_val = st.sidebar.multiselect("Trimestres:", sorted(df_ef['Trimestre'].unique()), key='st')
elif f_mode == 'Semestre': sel_val = st.sidebar.multiselect("Semestres:", sorted(df_ef['Semestre'].unique()), key='ss')
else: sel_val = st.sidebar.multiselect("Períodos:", list(df_ef.sort_values('Período')['Período_fmt'].unique()), key='sp')

dff = df_ef[df_ef['Año'].isin(sel_yrs)] if sel_yrs else df_ef.copy()
dff = apply_time_filter(dff, f_mode, sel_val, opts).sort_values('Período')

dff_ind = df_ind[df_ind['Año'].isin(sel_yrs)] if not df_ind.empty and sel_yrs else df_ind.copy()
if not dff_ind.empty: dff_ind = apply_time_filter(dff_ind, f_mode, sel_val, opts).sort_values('Período')

tab1, tab2, tab3, tab4 = st.tabs(["Costos", "Cantidades", "Relaciones", "Indicadores"])

# --- TAB 1: COSTOS ---
with tab1:
    st.subheader("Totales Anuales (2025 vs 2024)")
    costo_list = ['$K_50%', '$K_100%', '$K_Total_HE', '$K_TD', '$K_GTO', '$K_GTI', '$K_Guardias_2T', '$K_Guardias_3T', '$K_Total_Guardias']
    show_kpi_cards(df_ef, costo_list)
    st.markdown("---")
    c1, c2 = st.columns(2)
    p_k = c1.multiselect("Eje Línea:", k_cols, [k_cols[0]] if k_cols else [], key="pk")
    s_k = c2.multiselect("Eje Barras:", ["Ninguna"] + k_cols, ["Ninguna"], key="sk")
    sel_k = list(dict.fromkeys(p_k + [c for c in s_k if c != "Ninguna"]))
    if sel_k and not dff.empty:
        st.plotly_chart(plot_combined_chart(dff, p_k, s_k, "$K (L)", "$K (B)"), use_container_width=True)
        show_table(dff[['Período', 'Período_fmt'] + [c for c in sel_k if c in dff.columns]], "Costos", True)
        
        st.subheader("Variación Mensual")
        v_m_v, v_m_p = calc_variation(apply_time_filter(df_ef, f_mode, sel_val, opts), sel_k, 'mensual')
        mode_m = st.selectbox("Formato:", ["Valores", "Porcentaje"], key="mk")
        d_m = v_m_p if mode_m == "Porcentaje" else v_m_v
        st.plotly_chart(plot_bar(d_m, sel_k, "Var Mensual"), use_container_width=True)
        show_table(d_m, "Costos_VarM", is_percentage=(mode_m=="Porcentaje"))

        st.subheader("Variación Interanual")
        v_i_v, v_i_p = calc_variation(apply_time_filter(df_ef, f_mode, sel_val, opts), sel_k, 'interanual')
        mode_i = st.selectbox("Formato:", ["Valores", "Porcentaje"], key="ak")
        d_i = v_i_p if mode_i == "Porcentaje" else v_i_v
        # CORRECCIÓN: SIN FILTRO != 2024
        st.plotly_chart(plot_bar(d_i, sel_k, "Var Interanual"), use_container_width=True)
        show_table(d_i, "Costos_VarI", is_percentage=(mode_i=="Porcentaje"))

# --- TAB 2: CANTIDADES ---
with tab2:
    st.subheader("Totales Anuales (2025 vs 2024)")
    qty_list = ['hs_50%', 'hs_100%', 'hs_Total_HE', 'ds_TD', 'ds_GTO', 'ds_GTI', 'ds_Guardias_2T', 'ds_Guardias_3T', 'ds_Total_Guardias']
    show_kpi_cards(df_ef, qty_list)
    st.markdown("---")
    c1, c2 = st.columns(2)
    p_q = c1.multiselect("Eje Línea:", q_cols, [q_cols[0]] if q_cols else [], key="pq")
    s_q = c2.multiselect("Eje Barras:", ["Ninguna"] + q_cols, ["Ninguna"], key="sq")
    sel_q = list(dict.fromkeys(p_q + [c for c in s_q if c != "Ninguna"]))
    if sel_q and not dff.empty:
        st.plotly_chart(plot_combined_chart(dff, p_q, s_q, "Cant (L)", "Cant (B)"), use_container_width=True)
        show_table(dff[['Período', 'Período_fmt'] + [c for c in sel_q if c in dff.columns]], "Cant", True)

        st.subheader("Variación Mensual")
        v_m_v_q, v_m_p_q = calc_variation(apply_time_filter(df_ef, f_mode, sel_val, opts), sel_q, 'mensual')
        mode_m_q = st.selectbox("Formato:", ["Valores", "Porcentaje"], key="mq")
        d_m_q = v_m_p_q if mode_m_q == "Porcentaje" else v_m_v_q
        st.plotly_chart(plot_bar(d_m_q, sel_q, "Var Mensual"), use_container_width=True)
        show_table(d_m_q, "Cant_VarM", is_percentage=(mode_m_q=="Porcentaje"))

        st.subheader("Variación Interanual")
        v_i_v_q, v_i_p_q = calc_variation(apply_time_filter(df_ef, f_mode, sel_val, opts), sel_q, 'interanual')
        mode_i_q = st.selectbox("Formato:", ["Valores", "Porcentaje"], key="aq")
        d_i_q = v_i_p_q if mode_i_q == "Porcentaje" else v_i_v_q
        # CORRECCIÓN: SIN FILTRO != 2024
        st.plotly_chart(plot_bar(d_i_q, sel_q, "Var Interanual"), use_container_width=True)
        show_table(d_i_q, "Cant_VarI", is_percentage=(mode_i_q=="Porcentaje"))

# --- TAB 3: RELACIONES ---
with tab3:
    if not dff_ind.empty:
        c1, c2 = st.columns(2)
        p_r = c1.multiselect("Línea:", k_i_cols + q_i_cols, [k_i_cols[0]] if k_i_cols else [], key="pr")
        s_r = c2.multiselect("Barras:", ["Ninguna"] + k_i_cols + q_i_cols, ["Ninguna"], key="sr")
        sel_r = list(dict.fromkeys(p_r + [c for c in s_r if c != "Ninguna"]))
        if sel_r:
            st.plotly_chart(plot_combined_chart(dff_ind, p_r, s_r, "Rel (L)", "Rel (B)"), use_container_width=True)
            show_table(dff_ind[['Período', 'Período_fmt'] + [c for c in sel_r if c in dff_ind.columns]], "Rel", True)

# --- TAB 4: INDICADORES ---
with tab4:
    if not dff_ind.empty:
        opts_ratio = sorted(list(set(k_i_cols + q_i_cols)))
        combos = [f"{n} / {d}" for n in opts_ratio for d in opts_ratio if n != d]
        sel_ratios = st.multiselect("Ratios:", combos)
        if sel_ratios:
            df_c = dff_ind[['Período', 'Período_fmt']].copy()
            for r in sel_ratios:
                n, d = r.split(' / ')
                df_c[r] = dff_ind[n].astype(float) / dff_ind[d].astype(float)
            df_c.replace([np.inf, -np.inf], np.nan, inplace=True)
            show_table(df_c, "Ratios")
