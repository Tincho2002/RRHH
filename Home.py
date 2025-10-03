import streamlit as st
import json # Nuevo: Necesario para leer archivos Lottie locales

# --- Configuración Inicial ---
st.set_page_config(
    page_title="Aplicación Unificada Principal",
    page_icon="🏠",
    layout="wide"
)

# --- CSS para la animación del logo y título (Mejorada) ---
st.markdown("""
<style>
/* 1. ANIMACIÓN: Define el efecto de aparición (más lenta para ser perceptible) */
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(-30px); }
    to { opacity: 1; transform: translateY(0); }
}

/* 2. APLICACIÓN DE LA ANIMACIÓN: Logo (st.image) */
.stImage img {
    animation: fadeIn 2.5s ease-out forwards; /* 2.5s para que sea visible */
    display: block; 
    margin-left: auto;
    margin-right: auto;
    margin-bottom: 10px;
}

/* 3. ANIMACIÓN ADICIONAL para que el título aparezca después (slideUp) */
@keyframes slideUp {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}
/* Selector para el st.title (puede variar ligeramente) */
.st-emotion-cache-1jicfl2 { 
    animation: slideUp 1.5s ease-out 1.0s forwards; /* 1.0s de retraso */
    opacity: 0; 
}
</style>
""", unsafe_allow_html=True)


# --- Función para cargar la animación Lottie desde archivo ---
def load_lottiefile(filepath: str):
    """Carga una animación Lottie desde un archivo JSON local."""
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        # Retorna None si el archivo no se encuentra (mostrará el respaldo)
        return None

# Carga la animación desde el archivo local
# ¡Asegúrate de que este archivo exista en assets/!
lottie_hr = load_lottiefile("assets/hr_analysis.json")


# -----------------------------------------------------------------------
# --- CONTENIDO DE LA PÁGINA DE INICIO ---
# -----------------------------------------------------------------------

# 1. Logo y Título (Proporción 1:5 para reducir el logo)
logo_col, title_col = st.columns([1, 5]) 

with logo_col:
    # Logo más pequeño para proporción
    st.image("assets/logo_assa.jpg", width=300) 

with title_col:
    st.title("Bienvenido a la Aplicación de RRHH: Agua Potable S.A.")

# Separador visual
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
        # ¡Globos eliminados!
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
        # Mensaje de respaldo si el archivo Lottie no se encuentra.
        st.warning("No se pudo cargar la animación local (assets/hr_analysis.json).")

st.sidebar.success("Selecciona una aplicación arriba.")

