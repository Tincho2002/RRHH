import streamlit as st
import requests
from streamlit_lottie import st_lottie

st.set_page_config(
    page_title="Aplicación Unificada Principal",
    page_icon="🏠",
    layout="wide"
)

# --- CSS para la animación del logo ---
st.markdown("""
<style>
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(-20px); }
    to { opacity: 1; transform: translateY(0); }
}
.animated-logo {
    animation: fadeIn 1.5s ease-out forwards;
    margin-bottom: 20px; /* Espacio debajo del logo */
}
</style>
""", unsafe_allow_html=True)

# --- Contenido de la Página de Inicio ---

# Mostrar el logo animado
st.markdown(f'<div class="animated-logo"><img src="data:image/png;base64,{base64.b64encode(open("assets/logo.png", "rb").read()).decode()}" width="200"></div>', unsafe_allow_html=True)

st.title("Bienvenido a la Aplicación de RRHH: Agua Potable S.A. 💧")
st.sidebar.success("Selecciona una aplicación arriba.")
# ... (resto del código)
# --- Contenido de la Página de Inicio ---

# Título y Barra Lateral
st.title("Bienvenido a la Aplicación de RRHH: Agua Potable S.A. 💧")
st.sidebar.success("Selecciona una aplicación arriba.")

# Creación de Columnas para centrar la animación y el texto
col1, col2 = st.columns([1, 2]) # Ajusta la proporción según el tamaño que desees

with col1:
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
    # Puedes añadir un botón o elemento que te guste para la apertura
    if st.button("Comenzar el Análisis"):
        st.balloons() # Pequeño efecto al iniciar

with col2:
    if lottie_hr:
        st_lottie(
            lottie_hr,
            speed=1,
            reverse=False,
            loop=True,
            quality='high', # 'low', 'medium', or 'high'
            height=300, # Altura del elemento
            width=None,
            key="hr_animation"
        )
    else:
        st.info("Cargando animación o contenido estático de respaldo...")


