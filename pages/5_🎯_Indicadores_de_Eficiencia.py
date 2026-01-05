# ===============================================================
# Visualizador de Eficiencia - Versión Completa y Corregida
# ===============================================================

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from io import BytesIO
import numpy as np
import traceback

# Configuración de la página
st.set_page_config(layout="wide", page_title="Visualizador de Eficiencia")

# ----------------- Funciones de Carga y Procesamiento -----------------

@st.cache_data
def load_data(uploaded_file):
    if uploaded_file is None:
        return pd.DataFrame(), pd.DataFrame(), [], [], [], {}, [], []

    excel_file = pd.ExcelFile(uploaded_file)
    sheet_names = excel_file.sheet_names

    df_eficiencia = pd.DataFrame()
    df_indicadores = pd.DataFrame()

    # --- Hoja 'eficiencia' ---
    if 'eficiencia' in sheet_names:
        try:
            df_eficiencia = pd.read_excel(excel_file, sheet_name='eficiencia', header=0)
            
            # Totales de Horas y Costos
            if all(c in df_eficiencia.columns for c in ['$K_50%', '$K_100%']):
                df_eficiencia['$K_Total_HE'] = df_eficiencia[['$K_50%', '$K_100%']].fillna(0).sum(axis=1)
            if all(c in df_eficiencia.columns for c in ['hs_50%', 'hs_100%']):
                df_eficiencia['hs_Total_HE'] = df_eficiencia[['hs_50%', 'hs_100%']].fillna(0).sum(axis=1)

            gc_cols = ['$K_Guardias_2T', '$K_Guardias_3T', '$K_GTO', '$K_GTI', '$K_TD']
            gq_cols = ['ds_Guardias_2T', 'ds_Guardias_3T', 'ds_GTO', 'ds_GTI', 'ds_TD']
            if all(c in df_eficiencia.columns for c in gc_cols):
                df_eficiencia['$K_Total_Guardias'] = df_eficiencia[gc_cols].fillna(0).sum(axis=1)
            if all(c in df_eficiencia.columns for c in gq_cols):
                df_eficiencia['ds_Total_Guardias'] = df_eficiencia[gq_cols].fillna(0).sum(axis=1)

            df_eficiencia['Período'] = pd.to_datetime(df_eficiencia['Período'])
            df_eficiencia['Año'] = df_eficiencia['Período'].dt.year
            df_eficiencia['Mes'] = df_eficiencia['Período'].dt.month
            df_eficiencia['Período_fmt'] = df_eficiencia['Período'].dt.strftime('%b-%y')
            df_eficiencia['Bimestre'] = (df_eficiencia['Mes'] - 1) // 2 + 1
            df_eficiencia['Trimestre'] = (df_eficiencia['Mes'] - 1) // 3 + 1
            df_eficiencia['Semestre'] = (df_eficiencia['Mes'] - 1) // 6 + 1
        except Exception as e:
            st.error(f"Error en hoja eficiencia: {e}")

    # --- Hoja 'masa_salarial' ---
    if 'masa_salarial' in sheet_names:
        try:
            df_indicadores = pd.read_excel(excel_file, sheet_name='masa_salarial', header=0)
            df_indicadores.columns = df_indicadores.columns.str.strip()
            if 'Período' in df_indicadores.columns:
                # Intento de conversión flexible
                df_indicadores['Período'] = pd.to_datetime(df_indicadores['Período'], errors='coerce')
                # Si falló (NaN), intentar con mapeo de meses en español
                if df_indicadores['Período'].isna().any():
                    mes_map = {'ene':'Jan','feb':'Feb','mar':'Mar','abr':'Apr','may':'May','jun':'Jun',
                               'jul':'Jul','ago':'Aug','sep':'Sep','oct':'Oct','nov':'Nov','dic':'Dic'}
                    per_str = df_indicadores['Período'].astype(str).str.lower()
                    for k,v in mes_map.items(): per_str = per_str.str.replace(k, v)
                    df_indicadores['Período'] = pd.to_datetime(per_str, format='%b-%y', errors='coerce')

                df_indicadores['Año'] = df_indicadores['Período'].dt.year
                df_indicadores['Mes'] = df_indicadores['Período'].dt.month
                df_indicadores['Período_fmt'] = df_indicadores['Período'].dt.strftime('%b-%y')
                df_indicadores['Bimestre'] = (df_indicadores['Mes'] - 1) // 2 + 1
                df_indicadores['Trimestre'] = (df_indicadores['Mes'] - 1) // 3 + 1
                df_indicadores['Semestre'] = (df_indicadores['Mes'] - 1) // 6 + 1

            k_ind_cols = [c for c in ['Msalarial_$K', 'HExtras_$K', 'Guardias_$K', 'Dotación'] if c in df_indicadores.columns]
            q_ind_cols = [c for c in ['HE_hs', 'Guardias_ds', 'Dotación'] if c in df_indicadores.columns]
        except Exception:
            df_indicadores = pd.DataFrame()
            k_ind_cols, q_ind_cols = [], []

    # Unificación de Dotación
    if not df_eficiencia.empty and not df_indicadores.empty and 'Dotación' in df_indicadores.columns:
        df_dot = df_indicadores[['Período', 'Dotación']].dropna()
        df_eficiencia = pd.merge(df_eficiencia, df_dot, on='Período', how='left')

    # Listas Finales
    k_cols = sorted(list(set([c for c in df_eficiencia.columns if c.startswith('$K_')] + (['Dotación'] if 'Dotación' in df_eficiencia.columns else []))))
    q_cols = sorted(list(set([c for c in df_eficiencia.columns if c.startswith('hs_') or c.startswith('ds_')] + (['Dotación'] if 'Dotación' in df_eficiencia.columns else []))))
    yrs = sorted(df_eficiencia['Año'].unique(), reverse=True) if not df_eficiencia.empty else []
    m_map = {1:'Ene',2:'Feb',3:'Mar',4:'Abr',5:'May',6:'Jun',7:'Jul',8:'Ago',9:'Sep',10:'Oct',11:'Nov',12:'Dic'}

    return df_eficiencia, df_indicadores, k_cols, q_cols, yrs, m_map, k_ind_cols, q_ind_cols

# ----------------- Funciones de Utilidad -----------------

def format_num(x, is_int=False):
    if pd.isna(x): return ""
    fmt = "{:,.0f}" if is_int else "{:,.2f}"
    return fmt.format(float(x)).replace(",", "X").replace(".", ",").replace("X", ".")

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

def calc_variation(df, columns, tipo='mensual'):
    cols = [c for c in columns if c in df.columns]
    if not cols or df.empty: return pd.DataFrame(), pd.DataFrame()
    
    df_v = df[['Período', 'Período_fmt', 'Año', 'Mes'] + cols].copy().sort_values('Período')
    
    if tipo == 'interanual':
        df_p = df_v.copy()
        df_p['Año'] = df_p['Año'] + 1
        df_merged = pd.merge(df_v, df_p, on=['Año', 'Mes'], how='left', suffixes=('','_prev'))
        df_val, df_pct = df_v[['Período','Período_fmt']].copy(), df_v[['Período','Período_fmt']].copy()
        for c in cols:
            df_val[c] = df_merged[c] - df_merged[c+'_prev']
            df_pct[c] = (df_val[c] / df_merged[c+'_prev']) * 100
    else:
        df_val, df_pct = df_v[['Período','Período_fmt']].copy(), df_v[['Período','Período_fmt']].copy()
        for c in cols:
            df_val[c] = df_v[c].diff()
            df_pct[c] = (df_val[c] / df_v[c].shift(1)) * 100
    
    return df_val, df_pct.replace([np.inf, -np.inf], np.nan)

# ----------------- Componentes UI -----------------

def show_kpi_cards(df, var_list):
    if df.empty: return
    vars_ex = [v for v in var_list if v in df.columns]
    df_24 = df[df['Año'] == 2024][vars_ex].sum()
    df_25 = df[df['Año'] == 2025][vars_ex].sum()
    
    cols = st.columns(5)
    clases = ['card-blue', 'card-azure', 'card-violet', 'card-purple', 'card-indigo']
    
    for i, v in enumerate(vars_ex):
        t24, t25 = df_24.get(v, 0), df_25.get(v, 0)
        delta = t25 - t24
        # CORRECCIÓN DE ERROR v24 -> t24
        pct = (delta / t24 * 100) if t24 > 0 else (100.0 if t25 > 0 else 0.0)
        
        is_int = v.startswith(('ds_','hs_')) or v == 'Dotación'
        val_str = f"{'$K ' if v.startswith('$K_') else ''}{format_num(t25, is_int)}"
        icon = "↑" if delta >= 0 else "↓"
        color = "#86efac" if delta >= 0 else "#fca5a5"
        
        html = f"""<div class="metric-card {clases[i % 5]}">
            <div class="metric-label">{v.replace('$K_','').replace('_',' ')}</div>
            <div class="metric-value">{val_str}</div>
            <div class="metric-delta"><span style="color:{color}; font-weight:bold;">{icon} {format_num(abs(delta), is_int)} ({format_num(pct)}%)</span></div>
        </div>"""
        cols[i % 5].markdown(html, unsafe_allow_html=True)

def show_data_block(df_plot, sel_cols, title, key_pfx):
    st.subheader(f"Evolución {title}")
    c1, c2 = st.columns(2)
    p_v = c1.multiselect("Línea:", sel_cols, [sel_cols[0]] if sel_cols else [], key=f"p_{key_pfx}")
    s_v = c2.multiselect("Barras:", ["Ninguna"] + sel_cols, ["Ninguna"], key=f"s_{key_pfx}")
    
    total_sel = list(dict.fromkeys(p_v + [x for x in s_v if x != "Ninguna"]))
    if total_sel and not df_plot.empty:
        # Gráfico Combinado Simplificado
        fig = go.Figure()
        for c in total_sel:
            is_int = c.startswith(('ds_','hs_')) or c in ['HE_hs','Guardias_ds','Dotación']
            mode = 'lines+markers+text' if c in p_v else 'none'
            if c in p_v:
                fig.add_trace(go.Scatter(x=df_plot['Período_fmt'], y=df_plot[c], name=c, mode=mode, text=[format_num(x, is_int) for x in df_plot[c]], textposition='top center'))
            else:
                fig.add_trace(go.Bar(x=df_plot['Período_fmt'], y=df_plot[c], name=c, yaxis='y2', opacity=0.6))
        
        fig.update_layout(template='plotly_white', barmode='group', yaxis2=dict(overlaying='y', side='right', showgrid=False), legend=dict(orientation='h', y=1.1))
        st.plotly_chart(fig, use_container_width=True)
        
        # Variación Mensual e Interanual
        st.markdown("---")
        m_col1, m_col2 = st.columns(2)
        with m_col1:
            st.subheader("Variación Mensual")
            v_m_val, v_m_pct = calc_variation(df_plot, total_sel, 'mensual')
            mode_m = st.radio("Formato:", ["Valores", "Porcentaje"], key=f"mode_m_{key_pfx}", horizontal=True)
            df_m = v_m_pct if mode_m == "Porcentaje" else v_m_val
            st.dataframe(df_m.drop(columns=['Período'], errors='ignore'), use_container_width=True)
        with m_col2:
            st.subheader("Variación Interanual")
            v_i_val, v_i_pct = calc_variation(df_plot, total_sel, 'interanual')
            mode_i = st.radio("Formato:", ["Valores", "Porcentaje"], key=f"mode_i_{key_pfx}", horizontal=True)
            df_i = v_i_pct if mode_i == "Porcentaje" else v_i_val
            # AQUÍ NO FILTRAMOS 2024
            st.dataframe(df_i.drop(columns=['Período'], errors='ignore'), use_container_width=True)

# ----------------- Main App -----------------

st.markdown("""<style>
    .metric-card { border-radius: 12px; padding: 15px; color: white; text-align: center; min-height: 120px; margin: 10px 0; }
    .metric-value { font-size: 1.5rem; font-weight: bold; }
    .metric-label { font-size: 0.9rem; text-transform: uppercase; opacity: 0.9; }
    .card-blue { background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); }
    .card-azure { background: linear-gradient(135deg, #2193b0 0%, #6dd5fa 100%); }
    .card-violet { background: linear-gradient(135deg, #4a00e0 0%, #8e2de2 100%); }
    .card-purple { background: linear-gradient(135deg, #834d9b 0%, #d04ed6 100%); }
    .card-indigo { background: linear-gradient(135deg, #4b6cb7 0%, #182848 100%); }
</style>""", unsafe_allow_html=True)

up = st.file_uploader("Cargue eficiencia.xlsx", type="xlsx")
if not up: st.info("Cargue un archivo."); st.stop()

df_ef, df_ind, k_cols, q_cols, yrs, m_map, k_i, q_i = load_data(up)

# Sidebar
st.sidebar.header("Filtros")
if st.sidebar.button("🔄 Resetear"):
    for k in st.session_state.keys(): del st.session_state[k]
    st.rerun()

sel_yrs = st.sidebar.multiselect("Años:", yrs, yrs)
f_mode = st.sidebar.radio("Filtrar por:", ["Mes", "Trimestre", "Semestre"], horizontal=True)

dff = df_ef[df_ef['Año'].isin(sel_yrs)].sort_values('Período')
dff_ind = df_ind[df_ind['Año'].isin(sel_yrs)].sort_values('Período') if not df_ind.empty else pd.DataFrame()

t1, t2, t3, t4 = st.tabs(["Costos", "Cantidades", "Relaciones", "Indicadores"])

with t1:
    show_kpi_cards(df_ef, ['$K_50%', '$K_100%', '$K_Total_HE', '$K_GTO', '$K_Total_Guardias'])
    show_data_block(dff, k_cols, "Costos ($K)", "cost")

with t2:
    show_kpi_cards(df_ef, ['hs_50%', 'hs_100%', 'hs_Total_HE', 'ds_GTO', 'ds_Total_Guardias'])
    show_data_block(dff, q_cols, "Cantidades (hs/ds)", "qty")

with t3:
    if not dff_ind.empty:
        show_data_block(dff_ind, k_i + q_i, "Relaciones (Masa Salarial)", "rel")

with t4:
    st.subheader("Ratios de Eficiencia")
    if not dff_ind.empty:
        opts = sorted(list(set(k_i + q_i)))
        c1, c2 = st.columns(2)
        num = c1.selectbox("Numerador:", opts)
        den = c2.selectbox("Denominador:", opts)
        if num and den:
            res = dff_ind[['Período_fmt']].copy()
            res['Ratio'] = dff_ind[num].astype(float) / dff_ind[den].astype(float)
            st.line_chart(res.set_index('Período_fmt'))
            st.dataframe(res, use_container_width=True)
