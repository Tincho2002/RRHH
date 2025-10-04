import streamlit as st
from st_pages import show_pages, Page, hide_pages
import base64 # Importado para la función de navegación

# --- Configuración Inicial ---
st.set_page_config(
    page_title="Aplicación Unificada Principal",
    page_icon="💧",
    layout="wide"
)

# -----------------------------------------------------------------------
# --- CONFIGURACIÓN DE PÁGINAS (Necesario para st-pages) ---
# Ocultamos la barra lateral inmediatamente para que solo se vea el Home Portal
show_pages(
    [
        Page("Home.py", "Inicio", "🏠"),
        Page("pages/app_dotacion.py", "Dotación", "👥"),
        Page("pages/app_horas_extras.py", "Horas Extras", "⏰"),
        Page("pages/app_masa_salarial.py", "Masa Salarial", "💵"),
    ]
)
hide_pages(["Dotación", "Horas Extras", "Masa Salarial"]) # Ocultamos para forzar el uso del portal


# --- Función de Navegación (Truco para moverte entre páginas) ---
def navigate_to(page_name):
    """Genera y ejecuta un script JS para forzar la navegación."""
    # El nombre de la página debe coincidir con el path configurado por st-pages
    script = f"""
        <script>
            window.parent.postMessage({{
                type: 'streamlit:nav_to',
                url: '{page_name}'
            }}, '*')
        </script>
    """
    st.components.v1.html(script, height=0)

# --- CSS: Animación del Logo y Estilos de Botones ---
st.markdown("""
<style>
/* 1. OCULTA LA BARRA LATERAL NATIVA (Ahora solo la ocultamos visualmente) */
div[data-testid="stSidebar"] {
    display: none;
}

/* 2. Animación de apertura para el logo (Zoom) */
@keyframes openingLogo {
    0% { transform: scale(3); opacity: 0; }
    100% { transform: scale(1); opacity: 1; }
}

/* 3. Aplica animación al logo */
.stImage img {
    animation: openingLogo 1.5s ease-out forwards;
    display: block; 
    margin-left: auto;
    margin-right: auto;
    margin-bottom: 20px;
}

/* 4. Estilo de los títulos */
h1 {
    text-align: center;
    font-size: 2.5em;
    color: #007bff;
}

/* 5. Estilo de los botones nativos para que parezcan tarjetas */
.stButton>button {
    width: 100%;
    height: 150px; /* Tamaño fijo para la tarjeta */
    font-size: 1.2em;
    font-weight: bold;
    border-radius: 10px;
    box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2); 
    transition: 0.3s;
    border: none;
    color: #333;
}
.stButton>button:hover {
    box-shadow: 0 8px 16px 0 rgba(0,0,0,0.4);
    transform: scale(1.02); /* Pequeño zoom al pasar el ratón */
    background-color: #f0f2f6; /* Cambio de color sutil */
}

/* 6. Estilos de color para botones específicos (por si quieres usarlos) */
#dotacion-button button { background-color: #e0f7fa; } /* Azul claro */
#horas-button button { background-color: #fffde7; } /* Amarillo claro */
#masa-button button { background-color: #f1f8e9; } /* Verde claro */

</style>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------
# --- CONTENIDO DE LA PÁGINA DE INICIO: EL PORTAL DE APLICACIONES ---
# -----------------------------------------------------------------------

# 1. Logo y Título (Centrados)
col_logo, col_title, _ = st.columns([1, 6, 1])

with col_logo:
    st.image("assets/logo_assa.jpg", width=100) 

with col_title:
    st.title("Bienvenido a la Aplicación de RRHH")
    st.markdown("<h2 style='text-align: center; color: #555;'>Portal de Análisis de Capital Humano - Aguas Potable S.A.</h2>", unsafe_allow_html=True)

st.markdown("---")


# 2. Botones Nativos como Tarjetas (La Solución Funcional)
st.markdown("<h3 style='text-align: center;'>Selecciona el área de análisis:</h3>", unsafe_allow_html=True)
st.empty() 

col_dotacion, col_horas, col_masa = st.columns(3)


# --- BOTÓN 1: Dotación ---
with col_dotacion:
    st.markdown('<div id="dotacion-button">', unsafe_allow_html=True)
    if st.button("👥 **Dotación** \n\n Consulta la estructura y distribución de personal.", key="btn_dotacion"):
        navigate_to("Dotación") 
    st.markdown('</div>', unsafe_allow_html=True)

# --- BOTÓN 2: Horas Extras ---
with col_horas:
    st.markdown('<div id="horas-button">', unsafe_allow_html=True)
    if st.button("⏰ **Horas Extras** \n\n Analiza el impacto de horas adicionales y ausentismo.", key="btn_horas"):
        navigate_to("Horas Extras")
    st.markdown('</div>', unsafe_allow_html=True)

# --- BOTÓN 3: Masa Salarial ---
with col_masa:
    st.markdown('<div id="masa-button">', unsafe_allow_html=True)
    if st.button("💵 **Masa Salarial** \n\n Visualiza la composición, evolución y proyecciones de costos.", key="btn_masa"):
        navigate_to("Masa Salarial")
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")
st.info("Haz clic en una de las tarjetas para acceder al área de análisis. La navegación ahora es estable.")
