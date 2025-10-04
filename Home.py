import streamlit as st
import json 
import requests # <--- Necesario de nuevo para cargar desde URL
from streamlit_lottie import st_lottie

# --- Configuración Inicial ---
st.set_page_config(
    page_title="Aplicación Unificada Principal",
    page_icon="🏠",
    layout="wide"
)

# ... (Mantén aquí todo el CSS para la animación del logo y título) ...

# --- Función para cargar la animación Lottie (Vuelve a URL) ---
def load_lottieurl(url: str):
    """Carga una animación Lottie desde una URL."""
    try:
        r = requests.get(url)
        if r.status_code != 200:
            return None
        return r.json()
    except Exception:
        return None

# URL LOTTIE ESTABLE: Animación de "Business Analysis"
LOTTIE_URL = "https://lottie.host/17e23118-2e0f-4886-9a2c-982464734898/Qd4qK02f08.json" 
lottie_hr = load_lottieurl(LOTTIE_URL)


# --- Función para cargar el archivo JSON local (ya no es necesaria, pero la dejamos vacía para evitar errores si la usas) ---
# def load_lottiefile(filepath: str):
#     return None 


# -----------------------------------------------------------------------
# --- CONTENIDO DE LA PÁGINA DE INICIO ---
# -----------------------------------------------------------------------

# 1. Logo y Título
logo_col, title_col = st.columns([1, 5]) 

with logo_col:
    st.image("assets/logo_assa.jpg", width=100) 

with title_col:
    st.title("Bienvenido a la Aplicación de RRHH: Agua Potable S.A.")

st.markdown("---")

# 2. Distribución del Contenido y Animación Lottie
col1, col2 = st.columns([1, 1])

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
    if st.button("Comenzar el Análisis"):
        st.success("¡Análisis iniciado! Selecciona una opción en la barra lateral.")

with col2:
    if lottie_hr:
        st_lottie(
            lottie_hr,
            speed=1,
            reverse=False,
            loop=True,
            quality='high',
            height=300,
            key="hr_animation"
        )
    else:
        # Mensaje de respaldo si el enlace remoto falla
        st.warning("No se pudo cargar la animación remota. La aplicación es funcional.")

st.sidebar.success("Selecciona una aplicación arriba.")
