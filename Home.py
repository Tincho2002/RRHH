import streamlit as st
import requests
from streamlit_lottie import st_lottie

# --- Configuración Inicial ---
st.set_page_config(
    page_title="Aplicación Unificada Principal",
    page_icon="🏠",
    layout="wide" # Usa layout wide para una mejor visualización de la animación
)

# --- Función para cargar la animación Lottie ---
def load_lottieurl(url: str):
    """Carga una animación Lottie desde una URL."""
    try:
        r = requests.get(url)
        if r.status_code != 200:
            return None
        return r.json()
    except Exception as e:
        st.error(f"Error al cargar la animación Lottie: {e}")
        return None

# Reemplaza esta URL con el enlace JSON de la animación Lottie de tu elección.
# Busca algo relacionado con RRHH, Negocios o Análisis de Datos.
LOTTIE_URL = "https://lottie.host/57a7051e-61c3-424a-939e-e3b8f15d97f5/9o5e4z08lI.json"  # Ejemplo de RRHH

lottie_hr = load_lottieurl(LOTTIE_URL)

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
