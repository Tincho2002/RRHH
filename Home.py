import streamlit as st
# Eliminamos: from st_pages import ..., from streamlit_card import card, import base64

# --- Configuración Inicial ---
# Streamlit nativo usa el nombre de los archivos en 'pages/' para la navegación.
st.set_page_config(
    page_title="Aplicación Unificada Principal",
    page_icon="💧",
    layout="wide"
)

# -----------------------------------------------------------------------
# --- CSS: Animación del Logo y Estilos ---
# Mantenemos las animaciones y el estilo de los botones (aunque no los usemos)
st.markdown("""
<style>
/* 1. MOSTRAR LA BARRA LATERAL NATIVA (Necesaria para navegar sin st-pages) */
div[data-testid="stSidebar"] {
    display: block !important; 
}
/* El resto del CSS sigue siendo efectivo para el diseño */

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
/* El estilo de los botones/tarjetas ya no se usa, pero el resto se mantiene */
</style>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------
# --- CONTENIDO DE LA PÁGINA DE INICIO: EL PORTAL DE APLICACIONES ---
# -----------------------------------------------------------------------

# 1. Logo y Título (Centrados)
col_logo, col_title, _ = st.columns([1, 6, 1])

with col_logo:
    # Esta es la animación visible que sí funciona
    st.image("assets/logo_assa.jpg", width=100) 

with col_title:
    st.title("Bienvenido a la Aplicación de RRHH")
    st.markdown("<h2 style='text-align: center; color: #555;'>Portal de Análisis de Capital Humano - Aguas Potable S.A.</h2>", unsafe_allow_html=True)

st.markdown("---")


# 2. Contenido Principal e Instrucciones
main_col = st.columns([1, 4, 1])[1] 

with main_col:
    st.markdown("## Análisis Estratégico de Capital Humano")
    st.markdown(
        """
        Esta es la página de inicio del sistema unificado de gestión de **Recursos Humanos**.
        
        Hemos asegurado la estabilidad de la aplicación. Para navegar, utiliza la **barra lateral de la izquierda**, donde encontrarás las siguientes áreas de análisis:
        
        * **Dotación:** Consulta la estructura y distribución de personal.
        * **Horas Extras:** Analiza el impacto de horas adicionales.
        * **Masa Salarial:** Visualiza la composición y evolución de costos.
        """
    )
    
    # Botones simples (opcional, para invitar a usar la barra lateral)
    st.info("Por favor, selecciona una aplicación en la **barra lateral izquierda** para continuar.")


# Instrucción final para el usuario
st.sidebar.success("Selecciona una aplicación para continuar.")
