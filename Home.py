import streamlit as st
from streamlit_card import card
# Nota: No necesitamos importar st_pages aquí.

# --- Configuración Inicial ---
st.set_page_config(
    page_title="Aplicación Unificada Principal",
    page_icon="💧",
    layout="wide"
)

# --- CSS: Animación del Logo y Estilos de Tarjeta ---
st.markdown("""
<style>
/* 1. OCULTA LA BARRA LATERAL NATIVA para que solo usemos las tarjetas (¡CLAVE!) */
/* El selector puede variar ligeramente según la versión de Streamlit, pero este es el más común */
.st-emotion-cache-18ni7ap { 
    display: none; 
}
.st-emotion-cache-1y4p8ic { 
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

/* 4. Estilo del título */
h1 {
    text-align: center;
    font-size: 2.5em;
    color: #007bff; /* Color azul corporativo */
}

/* 5. Estilo para las tarjetas (Añade transición y sombra para el efecto visual) */
.stCard {
    box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2); 
    transition: 0.3s;
    border-radius: 10px;
}
.stCard:hover {
    box-shadow: 0 8px 16px 0 rgba(0,0,0,0.4); /* Sombra más fuerte al pasar el ratón */
    transform: scale(1.02); /* Pequeño zoom al pasar el ratón */
}
</style>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------
# --- CONTENIDO DE LA PÁGINA DE INICIO: EL PORTAL DE APLICACIONES ---
# -----------------------------------------------------------------------

# 1. Logo y Título (Centrados)
# Aumentamos la columna del título para compensar el tamaño del logo
col_logo, col_title, _ = st.columns([1, 6, 1])

with col_logo:
    # Asegúrate que la imagen se llame 'logo_assa.jpg' y esté en la carpeta 'assets/'
    st.image("assets/logo_assa.jpg", width=350) 

with col_title:
    st.title("Bienvenido a la Aplicación de RRHH")
    st.markdown("<h2 style='text-align: center; color: #555;'>Portal de Análisis de Capital Humano - Aguas Potable S.A.</h2>", unsafe_allow_html=True)

st.markdown("---")


# 2. Tarjetas Interactivas (El factor "Sorpresa" y Navegación)
st.markdown("<h3 style='text-align: center;'>Selecciona el área de análisis:</h3>", unsafe_allow_html=True)
st.empty() 

# Usa 3 columnas para alinear las tarjetas horizontalmente
col_dotacion, col_horas, col_masa = st.columns(3)


# --- TARJETA 1: Dotación ---
with col_dotacion:
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
        url="app_dotacion" # Corregido: SÓLO el nombre del archivo
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
        url="app_horas_extras" # Corregido: SÓLO el nombre del archivo
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
        url="app_masa_salarial" # Corregido: SÓLO el nombre del archivo
    )

st.markdown("---")
st.info("¡Las tarjetas son interactivas! Haz clic para navegar a cada aplicación.")
