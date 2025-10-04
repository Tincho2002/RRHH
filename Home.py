import streamlit as st

# --- Configuración Inicial ---
st.set_page_config(
    page_title="Aplicación Unificada Principal",
    page_icon="🏠",
    layout="wide"
)

# ----------------------------------------------------------------------------------
# --- CÓDIGO CSS: ANIMACIÓN DE APERTURA NOTORIA (ZOOM Y FADE) ---
# ----------------------------------------------------------------------------------
st.markdown("""
<style>
@keyframes openingLogo {
    0% { transform: scale(3); opacity: 0; }
    50% { transform: scale(1.1); opacity: 1; }
    100% { transform: scale(1); opacity: 1; }
}

@keyframes slideUp {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}

.stImage img {
    animation: openingLogo 2s ease-out forwards;
    display: block; 
    margin-left: auto;
    margin-right: auto;
    margin-bottom: 10px;
}

.st-emotion-cache-1jicfl2 { 
    animation: slideUp 1s ease-out 1.5s forwards;
    opacity: 0; 
}
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------
# --- CONTENIDO DE LA PÁGINA DE INICIO ---
# -----------------------------------------------------------------------

# 1. Logos y Título centrados horizontalmente
left_logo, center_text, right_logo = st.columns([1, 4, 1])

with left_logo:
    st.image("assets/logo_assa.jpg", width=200)

with center_text:
    st.title("Bienvenido a la Aplicación de RRHH")
    st.markdown("### Portal de Análisis de Capital Humano - Aguas Santafesinas S.A.")

with right_logo:
    st.image("assets/logo_assa.jpg", width=200)

st.markdown("---")

# 2. Contenido principal centrado
main_col = st.columns([1, 4, 1])[1]

with main_col:
    st.markdown("## Análisis Estratégico de Capital Humano")
    st.markdown(
        """
        Esta es la página de inicio de la aplicación consolidada para la gestión de **Recursos Humanos**.
        Usa el menú de la barra lateral para navegar a las siguientes áreas clave:

        * **Dotación:** Consulta la distribución de personal.
        * **Horas Extras:** Analiza y gestiona las horas de trabajo adicionales.
        * **Masa Salarial:** Visualiza la composición y evolución del gasto salarial.
        """
    )
    if st.button("Comenzar el Análisis"):
        st.success("¡Análisis iniciado! Selecciona una opción en la barra lateral.")

# Mensaje de navegación
st.sidebar.success("Selecciona una aplicación arriba.")
