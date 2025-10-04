import streamlit as st
from streamlit_card import card
# Nota: La librería st-pages no necesita ser importada aquí,
# se usa en el archivo de configuración para definir el orden.

# --- Configuración Inicial ---
st.set_page_config(
    page_title="Aplicación Unificada Principal",
    page_icon="💧",
    layout="wide"
)

# --- CSS: Animación del Logo (Manteniendo la estética limpia) ---
st.markdown("""
<style>
/* Animación de apertura para el logo (Zoom) */
@keyframes openingLogo {
    0% { transform: scale(3); opacity: 0; }
    100% { transform: scale(1); opacity: 1; }
}

/* Aplica animación al logo */
.stImage img {
    animation: openingLogo 1.5s ease-out forwards;
    display: block; 
    margin-left: auto;
    margin-right: auto;
    margin-bottom: 20px;
}
/* Estilo del título */
h1 {
    text-align: center;
    font-size: 2.5em;
    color: #007bff; /* Color azul corporativo */
}
/* Estilo para las tarjetas */
.stCard {
    /* Sombra más suave para las tarjetas */
    box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2); 
    transition: 0.3s;
    border-radius: 5px;
}
.stCard:hover {
    box-shadow: 0 8px 16px 0 rgba(0,0,0,0.3);
}
</style>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------
# --- CONTENIDO DE LA PÁGINA DE INICIO: EL PORTAL DE APLICACIONES ---
# -----------------------------------------------------------------------

# 1. Logo y Título (Centrados)
col_logo, col_title, _ = st.columns([1, 4, 1])

with col_logo:
    # El logo sigue usando la animación CSS
    st.image("assets/logo_assa.jpg", width=300) 

with col_title:
    st.title("Bienvenido a la Aplicación de RRHH")
    st.markdown("<h2 style='text-align: center; color: #555;'>Portal de Análisis de Capital Humano - Aguas Potable S.A.</h2>", unsafe_allow_html=True)

st.markdown("---")


# 2. Tarjetas Interactivas (El factor "Sorpresa" y Navegación)
st.markdown("<h3 style='text-align: center;'>Selecciona el área de análisis:</h3>", unsafe_allow_html=True)
st.empty() # Espacio

# Usa 3 columnas para alinear las tarjetas horizontalmente
col_dotacion, col_horas, col_masa = st.columns(3)


# --- TARJETA 1: Dotación ---
with col_dotacion:
    # El 'url' aquí DEBE COINCIDIR con el nombre de archivo de tu app (ej: app_dotacion.py)
    card(
        title="Dotación",
        text="Consulta la estructura, headcount y distribución de personal por área y ubicación geográfica.",
        styles={
            "card": {
                "width": "100%", "height": "250px", "border-radius": "10px", 
                "background-color": "#e0f7fa" # Un color azul claro
            },
            "title": {"font-size": "24px"},
        },
        url="app_dotacion" # Streamlit usa el nombre del archivo sin la extensión .py
    )

# --- TARJETA 2: Horas Extras ---
with col_horas:
    card(
        title="Horas Extras",
        text="Analiza el impacto de horas adicionales y gestiona los indicadores de ausentismo.",
        styles={
            "card": {
                "width": "100%", "height": "250px", "border-radius": "10px", 
                "background-color": "#fffde7" # Un color amarillo claro
            },
            "title": {"font-size": "24px"},
        },
        url="app_horas_extras"
    )

# --- TARJETA 3: Masa Salarial ---
with col_masa:
    card(
        title="Masa Salarial y Costos",
        text="Visualiza la composición, evolución y proyecciones del gasto salarial total.",
        styles={
            "card": {
                "width": "100%", "height": "250px", "border-radius": "10px", 
                "background-color": "#f1f8e9" # Un color verde claro
            },
            "title": {"font-size": "24px"},
        },
        url="app_masa_salarial"
    )

st.markdown("---")
st.info("Para navegar a las aplicaciones, haz clic directamente en las tarjetas de arriba.")


