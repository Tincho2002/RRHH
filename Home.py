import streamlit as st
import requests
from streamlit_lottie import st_lottie

# --- Configuración Inicial ---
st.set_page_config(
    page_title="Aplicación Unificada Principal",
    page_icon="🏠",
    layout="wide"  # layout wide para mejor uso del espacio
)

# -----------------------------------------------------------------------
# --- CSS para la animación del logo (Fade-In y centrado de imagen) ---
# -----------------------------------------------------------------------
st.markdown("""
<style>
/* 1. ANIMACIÓN: Define el efecto de aparición */
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(-30px); }
    to { opacity: 1; transform: translateY(0); }
}

/* 2. APLICACIÓN DE LA ANIMACIÓN: Busca la imagen del logo y la anima */
/* El selector es más robusto si le damos un ID a la imagen con st.image(..., use_column_width=False, caption='animated-logo') */
/* Pero probaremos con el selector genérico más común para Streamlit */
.stImage img {
    animation: fadeIn 1.5s ease-out forwards;
    display: block; /* Necesario para que el margen funcione */
    margin-left: auto; /* Centra la imagen */
    margin-right: auto; /* Centra la imagen */
    margin-bottom: 20px;
}

/* 3. PEQUEÑA ANIMACIÓN ADICIONAL para que el título aparezca después */
@keyframes slideUp {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}
.st-emotion-cache-1jicfl2 { /* Selector para el st.title, puede variar */
    animation: slideUp 1s ease-out 1.5s forwards; /* 1.5s de retraso */
    opacity: 0; /* Empieza invisible */
}
</style>
""", unsafe_allow_html=True)


# --- Función para cargar la animación Lottie (mantener tu función aquí) ---
def load_lottieurl(url: str):
    """Carga una animación Lottie desde una URL."""
    try:
        r = requests.get(url)
        if r.status_code != 200:
            return None
        return r.json()
    except Exception:
        return None

# Reemplaza esta URL con el enlace JSON de la animación Lottie de tu elección.
LOTTIE_URL = "https://lottie.host/57a7051e-61c3-424a-939e-e3b8f15d97f5/9o5e4z08lI.json"
lottie_hr = load_lottieurl(LOTTIE_URL)


# -----------------------------------------------------------------------
# --- CONTENIDO DE LA PÁGINA DE INICIO ---
# -----------------------------------------------------------------------

# Centrar el logo y el título principal
logo_col, title_col = st.columns([1, 4])

with logo_col:
    # 1. Mostrar el Logo (animado por el CSS)
    # NOTA: Asegúrate de que la ruta sea correcta
    st.image("assets/logo_assa.jpg", width=150)

with title_col:
    # 2. Título principal (animado por el CSS)
    st.title("Bienvenido a la Aplicación de RRHH: Agua Potable S.A.")

# Separador visual
st.markdown("---")

# Re-introducir la distribución en columnas para el contenido y la animación Lottie
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
        st.balloons()

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
        st.info("Cargando animación Lottie...")

st.sidebar.success("Selecciona una aplicación arriba.")
