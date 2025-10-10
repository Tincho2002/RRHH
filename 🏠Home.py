import streamlit as st
from streamlit_option_menu import option_menu

# ----------------------------------------------------------------------------------
# --- CONFIGURACIÓN DE PÁGINA ---
# ----------------------------------------------------------------------------------
st.set_page_config(
    page_title="Portal de RRHH",
    page_icon="https://raw.githubusercontent.com/Tincho2002/RRHH/main/assets/logo_assa.jpg",
    layout="wide"
)

# ----------------------------------------------------------------------------------
# --- DEFINICIÓN DE LAS PÁGINAS COMO FUNCIONES ---
# ----------------------------------------------------------------------------------

def render_home_page():
    """Renderiza el contenido de la página de inicio."""
    # --- ENCABEZADO CON LOGOS Y TÍTULO ---
    left_logo, center_text, right_logo = st.columns([1, 4, 1])
    with left_logo:
        st.image("assets/logo_assa.jpg", width=300)
    with center_text:
        st.markdown("<h1 style='text-align:center; color:#555;'>Bienvenido a la Aplicación de RRHH</h1>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align:center; color:#555;'>Portal de Análisis de Capital Humano - Aguas Santafesinas S.A.</h3>", unsafe_allow_html=True)
    with right_logo:
        st.image("assets/logo_assa.jpg", width=300)

    st.markdown("---")

    # --- TEXTO INTRODUCTORIO ---
    st.markdown(
        """
        <div style="text-align: center;">
            <h2>Análisis Estratégico de Capital Humano</h2>
            <p>Esta es la página de inicio del sistema unificado de gestión de <strong>Recursos Humanos</strong>.</p>
            <p>Para acceder a cada módulo, usa la barra lateral de navegación.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # --- TARJETAS (AHORA SIN LINKS, SON SOLO INFORMATIVAS) ---
    st.markdown("""
    <div class="card-container">
        <div class="app-card card-dotacion">
            <div class="card-title">👥 Dotación</div>
            <p>Consulta la estructura y distribución geográfica y por gerencia de personal.</p>
        </div>
        <div class="app-card card-horas">
            <div class="card-title">⏰ Horas Extras</div>
            <p>Analiza el impacto de horas adicionales al 50% y al 100%.</p>
        </div>
        <div class="app-card card-masa">
            <div class="card-title">💵 Masa Salarial</div>
            <p>Visualiza la composición, evolución y proyecciones de costos salariales.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_dotacion_page(sub_selection):
    """
    Renderiza la página de Dotación según la sub-sección elegida.
    """
    # El título ahora se puede mostrar antes del if/elif
    # st.title(f"👥 Dotación: {sub_selection}")

    if sub_selection == "Resumen de Dotación":
        # Pega aquí el código correspondiente: gráficos, KPIs, etc.
        st.header("Resumen General de la Dotación")
        st.info("Aquí va el contenido de tu pestaña 'Resumen de Dotación'.")
        # Ejemplo: st.metric("Total de Empleados", "11.625")

    elif sub_selection == "Comparador de Mapas":
        st.header("Comparador de Mapas")
        st.info("Aquí va el contenido de tu pestaña 'Comparador de Mapas'.")

    elif sub_selection == "Mapa Geográfico":
        st.header("Mapa Geográfico")
        st.info("Aquí va el contenido de tu pestaña 'Mapa Geográfico'.")

    elif sub_selection == "Edad y Antigüedad":
        st.header("Análisis por Edad y Antigüedad")
        st.info("Aquí va el contenido de tu pestaña 'Edad y Antigüedad'.")

    elif sub_selection == "Desglose por Categoría":
        st.header("Desglose por Categoría")
        st.info("Aquí va el contenido de tu pestaña 'Desglose por Categoría'.")

    elif sub_selection == "Datos Brutos":
        st.header("Datos Brutos")
        st.info("Aquí va el contenido de tu pestaña 'Datos Brutos'.")

def render_horas_extras_page():
    """
    Renderiza la página de Horas Extras.
    """
    st.title("⏰ Horas Extras")
    st.info("Aquí va el contenido completo de tu aplicación de Horas Extras.")

def render_masa_salarial_page():
    """
    Renderiza la página de Masa Salarial.
    """
    st.title("💵 Masa Salarial")
    st.info("Aquí va el contenido completo de tu aplicación de Masa Salarial.")

# (Aquí iría todo tu CSS y el HTML del Splash Screen, lo omito para que la respuesta sea más corta,
# pero asegúrate de mantenerlo en tu archivo)
st.markdown("""<style> ... TU CSS AQUÍ ... </style>""", unsafe_allow_html=True)
st.html("""<div id="splash-screen"> ... TU HTML DEL SPLASH AQUÍ ... </div>""")


# -----------------------------------------------------------------------
# --- BARRA LATERAL Y LÓGICA DE NAVEGACIÓN ---
# -----------------------------------------------------------------------
with st.sidebar:
    selected = option_menu(
        menu_title="Menú Principal",
        options=["Home", "Dotación", "Horas Extras", "Masa Salarial"],
        icons=["house-door-fill", "people-fill", "alarm-fill", "cash-coin"],
        menu_icon="cast",
        default_index=0,
        # <-- CORRECCIÓN: Se elimina el parámetro 'submenu' que no existe.
    )

# -----------------------------------------------------------------------
# --- CONTENIDO PRINCIPAL (CONTROLADO POR LA SELECCIÓN DEL MENÚ) ---
# -----------------------------------------------------------------------
st.markdown('<div id="main-content">', unsafe_allow_html=True)

if selected == "Home":
    render_home_page()

elif selected == "Dotación":
    st.title("👥 Dotación") # Título principal de la sección

    # <-- NOVEDAD: Se crea un segundo menú horizontal para las pestañas.
    sub_selection = option_menu(
        menu_title=None, # No queremos título para este submenú
        options=[
            "Resumen de Dotación",
            "Comparador de Mapas",
            "Mapa Geográfico",
            "Edad y Antigüedad",
            "Desglose por Categoría",
            "Datos Brutos"
        ],
        # Íconos opcionales para cada pestaña
        icons=['card-list', 'map', 'geo-alt', 'person-badge', 'pie-chart', 'table'],
        orientation="horizontal",
        styles={ # Estilos para que parezca una barra de pestañas
            "container": {"padding": "0!important", "background-color": "#fafafa"},
            "icon": {"color": "orange", "font-size": "18px"},
            "nav-link": {"font-size": "14px", "text-align": "center", "margin":"0px", "--hover-color": "#eee"},
            "nav-link-selected": {"background-color": "#02ab21"},
        }
    )
    
    # Se llama a la función de renderizado con la pestaña seleccionada
    render_dotacion_page(sub_selection)

elif selected == "Horas Extras":
    render_horas_extras_page()

elif selected == "Masa Salarial":
    render_masa_salarial_page()

st.markdown('</div>', unsafe_allow_html=True)
