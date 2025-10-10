import streamlit as st
from streamlit_option_menu import option_menu

# ----------------------------------------------------------------------------------
# --- CONFIGURACIÓN DE PÁGINA ---
# ----------------------------------------------------------------------------------
st.set_page_config(
    page_title="Portal de RRHH",
    page_icon="https://raw.githubusercontent.com/Tincho2002/RRHH/main/assets/logo_assa.jpg",
    layout="wide"
)

# ----------------------------------------------------------------------------------
# --- DEFINICIÓN DE LAS PÁGINAS COMO FUNCIONES ---
# ----------------------------------------------------------------------------------

def render_home_page():
    """Renderiza el contenido de la página de inicio."""
    # --- ENCABEZADO CON LOGOS Y TÍTULO ---
    left_logo, center_text, right_logo = st.columns([1, 4, 1])
    with left_logo:
        st.image("assets/logo_assa.jpg", width=300)
    with center_text:
        st.markdown("<h1 style='text-align:center; color:#555;'>Bienvenido a la Aplicación de RRHH</h1>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align:center; color:#555;'>Portal de Análisis de Capital Humano - Aguas Santafesinas S.A.</h3>", unsafe_allow_html=True)
    with right_logo:
        st.image("assets/logo_assa.jpg", width=300)

    st.markdown("---")

    # --- TEXTO INTRODUCTORIO ---
    st.markdown(
        """
        <div style="text-align: center;">
            <h2>Análisis Estratégico de Capital Humano</h2>
            <p>Esta es la página de inicio del sistema unificado de gestión de <strong>Recursos Humanos</strong>.</p>
            <p>Para acceder a cada módulo, usa la barra lateral de navegación.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # --- TARJETAS (AHORA SIN LINKS, SON SOLO INFORMATIVAS) ---
    st.markdown("""
    <div class="card-container">
        <div class="app-card card-dotacion">
            <div class="card-title">👥 Dotación</div>
            <p>Consulta la estructura y distribución geográfica y por gerencia de personal.</p>
        </div>
        <div class="app-card card-horas">
            <div class="card-title">⏰ Horas Extras</div>
            <p>Analiza el impacto de horas adicionales al 50% y al 100%.</p>
        </div>
        <div class="app-card card-masa">
            <div class="card-title">💵 Masa Salarial</div>
            <p>Visualiza la composición, evolución y proyecciones de costos salariales.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_dotacion_page(sub_selection):
    """
    Renderiza la página de Dotación según la sub-sección elegida.
    
    ❗️ IMPORTANTE: Pega aquí todo el código de tu anterior archivo 'Dotacion.py',
    y organízalo dentro de los if/elif según la variable 'sub_selection'.
    """
    st.title(f"👥 Dotación: {sub_selection}")

    if sub_selection == "Resumen de Dotación":
        st.header("Resumen General de la Dotación")
        st.info("Aquí va el contenido de tu pestaña 'Resumen de Dotación'.")
        # Pega aquí el código correspondiente: gráficos, KPIs, etc.
        # Ejemplo: st.metric("Total de Empleados", "11.625")

    elif sub_selection == "Comparador de Mapas":
        st.header("Comparador de Mapas")
        st.info("Aquí va el contenido de tu pestaña 'Comparador de Mapas'.")
        # Pega aquí el código correspondiente

    elif sub_selection == "Mapa Geográfico":
        st.header("Mapa Geográfico")
        st.info("Aquí va el contenido de tu pestaña 'Mapa Geográfico'.")
        # Pega aquí el código correspondiente

    elif sub_selection == "Edad y Antigüedad":
        st.header("Análisis por Edad y Antigüedad")
        st.info("Aquí va el contenido de tu pestaña 'Edad y Antigüedad'.")
        # Pega aquí el código correspondiente

    elif sub_selection == "Desglose por Categoría":
        st.header("Desglose por Categoría")
        st.info("Aquí va el contenido de tu pestaña 'Desglose por Categoría'.")
        # Pega aquí el código correspondiente

    elif sub_selection == "Datos Brutos":
        st.header("Datos Brutos")
        st.info("Aquí va el contenido de tu pestaña 'Datos Brutos'.")
        # Pega aquí el código correspondiente a la tabla de datos.

def render_horas_extras_page():
    """
    Renderiza la página de Horas Extras.
    
    ❗️ IMPORTANTE: Pega aquí todo el código de tu anterior archivo 'Horas_Extras.py'.
    """
    st.title("⏰ Horas Extras")
    st.info("Aquí va el contenido completo de tu aplicación de Horas Extras.")
    # Pega tu código aquí

def render_masa_salarial_page():
    """
    Renderiza la página de Masa Salarial.
    
    ❗️ IMPORTANTE: Pega aquí todo el código de tu anterior archivo 'Masa_Salarial.py'.
    """
    st.title("💵 Masa Salarial")
    st.info("Aquí va el contenido completo de tu aplicación de Masa Salarial.")
    # Pega tu código aquí

# ----------------------------------------------------------------------------------
# --- CSS (SE MANTIENE IGUAL) ---
# ----------------------------------------------------------------------------------
# (Omitido por brevedad, es el mismo CSS que ya tenías para el splash screen y las tarjetas)
st.markdown("""
<style>
/* ... TU CSS VA AQUÍ ... */
/* --- Pantalla de Carga (Splash Screen) --- */
#splash-screen {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background: linear-gradient(180deg, #005A7A, #00A7C4);
    z-index: 1000;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    color: white;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    animation: hideSplash 1.5s ease-out 3.5s forwards;
}

#splash-logo {
    border-radius: 25px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
    animation: fadeInScale 1.5s 0.5s ease-out forwards;
}

#splash-title {
    animation: fadeInSlide 1.5s 1s ease-out forwards;
}

@keyframes hideSplash {
    from { opacity: 1; }
    to { opacity: 0; visibility: hidden; }
}

@keyframes fadeInScale { 
    from { opacity: 0; transform: scale(0.8); }
    to { opacity: 1; transform: scale(1); }
}
@keyframes fadeInSlide { 
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}

/* --- Animación de Gotas --- */
.droplet {
    position: absolute;
    bottom: 100%;
    width: 2px;
    height: 50px;
    background: linear-gradient(to top, rgba(255, 255, 255, 0.6), rgba(255, 255, 255, 0.1));
    border-radius: 50%;
    animation: fall linear infinite;
}

@keyframes fall { to { transform: translateY(100vh); } }

/* --- Estilos del Contenido Principal --- */
#main-content {
    opacity: 0; /* Inicia oculto */
    animation: showContent 1.5s ease-in 3.5s forwards;
}

@keyframes showContent {
    from { opacity: 0; }
    to { opacity: 1; }
}

/* 👇 CORRECCIÓN: Animación para la UI (Barra Lateral y Cabecera) */
[data-testid="stSidebar"],
[data-testid="stHeader"] {
    opacity: 0; /* Inician ocultos */
    transform: translateY(-20px); /* Un pequeño efecto de deslizamiento hacia abajo */
    animation: showUI 0.75s ease-out 3.5s forwards;
}

@keyframes showUI {
    to {
        opacity: 1;
        transform: translateY(0);
    }
}


/* ---------- TARJETAS (CARDS) DE NAVEGACIÓN ---------- */
.card-container {
    display: flex;
    gap: 20px;
    margin-top: 40px;
    flex-wrap: wrap;
    justify-content: center;
}

.app-card {
    flex: 1;
    min-width: 260px;
    max-width: 350px;
    padding: 20px;
    border-radius: 12px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    transition: all 0.3s ease-in-out;
    text-align: center;
    /* cursor: pointer; */ /* Se quita el cursor de link */
    text-decoration: none;
    color: #333;
    min-height: 180px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}

.card-dotacion { background-color: #e0f7fa; }
.card-horas { background-color: #fffde7; }
.card-masa { background-color: #f1f8e9; }

.app-card:hover {
    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.2);
    transform: translateY(-5px);
}

.card-title {
    font-size: 1.5em;
    font-weight: bold;
    color: #003366;
    margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------
# --- PANTALLA DE CARGA (SE MANTIENE IGUAL) ---
# -----------------------------------------------------------------------
st.html("""
<div id="splash-screen">
    <script>
        const splash = document.getElementById('splash-screen');
        for (let i = 0; i < 50; i++) {
            const droplet = document.createElement('div');
            droplet.className = 'droplet';
            droplet.style.left = `${Math.random() * 100}vw`;
            droplet.style.animationDuration = `${0.5 + Math.random() * 0.5}s`;
            droplet.style.animationDelay = `${Math.random() * 4}s`;
            splash.appendChild(droplet);
        }
    </script>
    <img id="splash-logo" src="https://raw.githubusercontent.com/Tincho2002/RRHH/main/assets/logo_assa.jpg" width="500">
    <h1 id="splash-title">Portal de Análisis de RRHH</h1>
</div>
""")

# -----------------------------------------------------------------------
# --- BARRA LATERAL Y LÓGICA DE NAVEGACIÓN ---
# -----------------------------------------------------------------------
with st.sidebar:
    selected = option_menu(
        menu_title="Menú Principal",
        options=["Home", "Dotación", "Horas Extras", "Masa Salarial"],
        icons=["house-door-fill", "people-fill", "alarm-fill", "cash-coin"],
        menu_icon="cast",
        default_index=0,
        # AÑADIMOS EL SUBMENÚ BASADO EN TU CAPTURA DE PANTALLA
        submenu={
            "Dotación": [
                "Resumen de Dotación", 
                "Comparador de Mapas", 
                "Mapa Geográfico", 
                "Edad y Antigüedad", 
                "Desglose por Categoría", 
                "Datos Brutos"
            ]
        }
    )

# -----------------------------------------------------------------------
# --- CONTENIDO PRINCIPAL (CONTROLADO POR LA SELECCIÓN DEL MENÚ) ---
# -----------------------------------------------------------------------
st.markdown('<div id="main-content">', unsafe_allow_html=True)

if selected == "Home":
    render_home_page()
elif selected == "Dotación":
    # Obtenemos la sub-selección del estado de la sesión
    sub_selection = st.session_state.get("submenu_Dotación")
    render_dotacion_page(sub_selection)
elif selected == "Horas Extras":
    render_horas_extras_page()
elif selected == "Masa Salarial":
    render_masa_salarial_page()

st.markdown('</div>', unsafe_allow_html=True)
