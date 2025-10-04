import streamlit as st

# No necesitamos 'json', 'requests' o 'streamlit_lottie'
# porque usamos CSS para animar el logo.

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
/* 1. ANIMACIÓN DE APERTURA: Hace que el logo aparezca grande y se encoja */
@keyframes openingLogo {
    0% { transform: scale(3); opacity: 0; }        /* Inicia muy grande e invisible */
    50% { transform: scale(1.1); opacity: 1; }     /* Se acerca al tamaño final (ligero rebote) */
    100% { transform: scale(1); opacity: 1; }      /* Se asienta en el tamaño final */
}

/* 2. ANIMACIÓN DE APARICIÓN PARA EL TÍTULO (Aparece después) */
@keyframes slideUp {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}

/* 3. APLICACIÓN DE LA ANIMACIÓN: Logo (st.image) */
.stImage img {
    animation: openingLogo 2s ease-out forwards; /* 2 segundos de duración */
    display: block; 
    margin-left: auto;
    margin-right: auto;
    margin-bottom: 10px;
}

/* 4. APLICACIÓN DE LA ANIMACIÓN: Título */
/* El selector puede variar, pero este es el más común para st.title */
.st-emotion-cache-1jicfl2 { 
    animation: slideUp 1s ease-out 1.5s forwards; /* 1.5 segundos de retraso */
    opacity: 0; 
}
</style>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------
# --- CONTENIDO DE LA PÁGINA DE INICIO ---
# -----------------------------------------------------------------------

# 1. Logo y Título (Usa columnas para poner el logo al lado del título)
logo_col, title_col = st.columns([1, 5]) 

with logo_col:
    # Esta imagen hereda la animación CSS 'openingLogo'
    # Asegúrate de que la ruta sea correcta: assets/logo.jpg
    st.image("assets/logo_assa.jpg", width=500) 

with title_col:
    # Este título hereda la animación CSS 'slideUp'
    st.title("Bienvenido a la Aplicación de RRHH: Aguas Santafesinas S.A.")

st.markdown("---")

# 2. Distribución del Contenido y Área de Enfoque (Análisis)
# Quitamos la columna de Lottie y centramos el contenido importante
main_col = st.columns([1, 4, 1])[1] # Usa una columna central ancha

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
        # Se quitó st.balloons()
        st.success("¡Análisis iniciado! Selecciona una opción en la barra lateral.")

# Mensaje de navegación
st.sidebar.success("Selecciona una aplicación arriba.")
