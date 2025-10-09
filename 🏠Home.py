import streamlit as st
import time
from streamlit_lottie import st_lottie
import json
from pathlib import Path

# -------------------------------
# Configuración inicial de la app
# -------------------------------
st.set_page_config(
    page_title="Panel RRHH",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# -------------------------------
# Función para cargar animaciones Lottie
# -------------------------------
def load_lottie_file(filepath: str):
    with open(filepath, "r") as f:
        return json.load(f)

# -------------------------------
# Animación inicial
# -------------------------------
def show_animation():
    animation_path = Path("assets/animation.json")

    # Si existe el archivo, lo cargamos
    if animation_path.exists():
        lottie_animation = load_lottie_file(str(animation_path))
    else:
        st.error("No se encontró el archivo de animación.")
        return

    # Centrar animación y logo
    st.markdown(
        """
        <style>
        .center {
            display: flex;
            justify-content: center;
            align-items: center;
            height: 90vh;
            flex-direction: column;
        }
        .logo {
            width: 160px;
            border-radius: 50%;
            margin-bottom: 20px;
            box-shadow: 0px 4px 15px rgba(0,0,0,0.3);
            animation: fadeIn 2s ease-in-out;
        }
        @keyframes fadeIn {
            from {opacity: 0;}
            to {opacity: 1;}
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    with st.container():
        st.markdown('<div class="center">', unsafe_allow_html=True)
        st.image("assets/logo.png", class_="logo")
        st_lottie(lottie_animation, height=250, key="logo")
        st.markdown("</div>", unsafe_allow_html=True)

    # Espera antes de mostrar la app principal
    time.sleep(3)

# -------------------------------
# Contenido principal de la app
# -------------------------------
def show_main_app():
    # Mostramos el menú lateral nuevamente
    show_menu_style = """
        <style>
            [data-testid="stSidebar"] {visibility: visible;}
        </style>
    """
    st.markdown(show_menu_style, unsafe_allow_html=True)

    # -------------------------------
    # Menú lateral
    # -------------------------------
    st.sidebar.title("📂 Menú Principal")
    st.sidebar.markdown("---")
    menu = st.sidebar.radio(
        "Navegación",
        ["🏠 Inicio", "📊 Dashboard", "👥 Empleados", "⚙️ Configuración"]
    )

    # -------------------------------
    # Contenido según opción seleccionada
    # -------------------------------
    if menu == "🏠 Inicio":
        st.title("🏠 Bienvenida al Panel de RRHH")
        st.write("Usá el menú de la izquierda para navegar por las secciones.")
        st.image("assets/rrhh_banner.jpg", use_container_width=True)

    elif menu == "📊 Dashboard":
        st.title("📊 Dashboard de Indicadores")
        st.write("Visualizá los indicadores clave del área de RRHH.")
        st.metric("Empleados activos", 248)
        st.metric("Promedio de edad", "37 años")
        st.metric("Rotación anual", "8.2%")

    elif menu == "👥 Empleados":
        st.title("👥 Gestión de Empleados")
        st.write("Aquí podrás consultar y administrar la información de los empleados.")
        st.dataframe({
            "Nombre": ["Ana López", "Carlos Pérez", "María Gómez"],
            "Puesto": ["Analista", "Jefe de Área", "Administrativo"],
            "Estado": ["Activo", "Activo", "Licencia"]
        })

    elif menu == "⚙️ Configuración":
        st.title("⚙️ Configuración del Sistema")
        st.write("Ajustes generales y preferencias del panel.")

# -------------------------------
# Flujo principal
# -------------------------------

# Ocultamos el menú lateral mientras se muestra la animación
hide_menu_style = """
    <style>
        [data-testid="stSidebar"] {visibility: hidden;}
    </style>
"""
st.markdown(hide_menu_style, unsafe_allow_html=True)

# Mostramos la animación inicial
show_animation()

# Mostramos el contenido principal de la app
show_main_app()
