import streamlit as st

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Portal de RRHH",
    page_icon="https://raw.githubusercontent.com/Tincho2002/RRHH/main/assets/logo_assa.jpg",
    layout="wide"
)

# --- FUNCIÓN: ANIMACIÓN DE INICIO ---
def show_animation():
    st.markdown("""
    <style>
        /* Ocultamos el menú y la barra superior mientras carga */
        [data-testid="stSidebar"], [data-testid="stHeader"] {
            visibility: hidden;
        }

        /* Overlay de la animación */
        .water-curtain-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background: linear-gradient(180deg, rgba(0, 102, 204, 0.95) 0%, rgba(0, 51, 102, 0.9) 100%);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 9999;
            animation: fadeOutCurtain 2s ease-out 2.5s forwards;
        }

        /* Logo animado */
        .water-curtain-logo {
            opacity: 0;
            transform: scale(0.6);
            border-radius: 20px;
            animation: fadeInLogo 1.5s ease-out 0.5s forwards;
            max-width: 250px;
            height: auto;
        }

        /* Contenido principal (oculto al principio) */
        .main-app-content {
            opacity: 0;
            animation: fadeInApp 1s ease-in 4.5s forwards;
        }

        /* Keyframes */
        @keyframes fadeOutCurtain {
            to { opacity: 0; visibility: hidden; }
        }
        @keyframes fadeInLogo {
            to { opacity: 1; transform: scale(1); }
        }
        @keyframes fadeInApp {
            to { opacity: 1; }
        }

        /* Tarjetas y estilo general */
        @media (max-width: 768px) {
            .card-container { flex-direction: column; align-items: center; }
        }
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
            cursor: pointer;
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
        .access-icon {
            font-size: 1.6em;
            color: #003366;
            transition: transform 0.3s ease;
        }
        .app-card:hover .access-icon {
            transform: scale(1.2);
        }
        a.app-card, a.app-card:visited, a.app-card:hover, a.app-card:active {
            text-decoration: none !important;
            color: inherit;
        }
    </style>
    """, unsafe_allow_html=True)

    # HTML de la animación
    st.markdown("""
    <div class="water-curtain-overlay">
        <img src="https://raw.githubusercontent.com/Tincho2002/RRHH/main/assets/logo_assa.jpg"
             class="water-curtain-logo" alt="Logo ASSA">
    </div>
    """, unsafe_allow_html=True)

    # Restaurar visibilidad tras la animación
    st.markdown("""
    <script>
        setTimeout(function() {
            const sidebar = document.querySelector('[data-testid="stSidebar"]');
            const header = document.querySelector('[data-testid="stHeader"]');
            if (sidebar) { sidebar.style.visibility = 'visible'; }
            if (header) { header.style.visibility = 'visible'; }
        }, 4500);
    </script>
    """, unsafe_allow_html=True)


# --- FUNCIÓN: CONTENIDO PRINCIPAL ---
def show_main_app():
    st.markdown('<div class="main-app-content">', unsafe_allow_html=True)

    left_logo, center_text, right_logo = st.columns([1, 4, 1])

    with left_logo:
        st.image("https://raw.githubusercontent.com/Tincho2002/RRHH/main/assets/logo_assa.jpg", width=200)
    with center_text:
        st.title("Bienvenido a la Aplicación de RRHH")
        st.markdown(
            "<h3 style='text-align:center; color:#555;'>Portal de Análisis de Capital Humano - Aguas Santafesinas S.A.</h3>",
            unsafe_allow_html=True
        )
    with right_logo:
        st.image("https://raw.githubusercontent.com/Tincho2002/RRHH/main/assets/logo_assa.jpg", width=200)

    st.markdown("---")

    # Banner (corregido: usa el logo existente en lugar de rrhh_banner.jpg)
    st.image("https://raw.githubusercontent.com/Tincho2002/RRHH/main/assets/logo_assa.jpg", use_container_width=True)

    st.markdown("""
    <div style="text-align: center;">
        <h2>Análisis Estratégico de Capital Humano</h2>
        <p>Esta es la página de inicio del sistema unificado de gestión de <strong>Recursos Humanos</strong>.</p>
        <p>Para acceder a cada módulo, haz clic directamente en la tarjeta de interés o usa la barra lateral.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="card-container">
        <a href="/Dotación" target="_self" class="app-card card-dotacion">
            <div class="card-title">👥 Dotación</div>
            <p>Consulta la estructura y distribución geográfica y por gerencia de personal.</p>
            <div class="access-icon">🔗</div>
        </a>
        <a href="/Horas_Extras" target="_self" class="app-card card-horas">
            <div class="card-title">⏰ Horas Extras</div>
            <p>Analiza el impacto de horas adicionales al 50% y al 100%.</p>
            <div class="access-icon">🔗</div>
        </a>
        <a href="/Masa_Salarial" target="_self" class="app-card card-masa">
            <div class="card-title">💵 Masa Salarial</div>
            <p>Visualiza la composición, evolución y proyecciones de costos salariales.</p>
            <div class="access-icon">🔗</div>
        </a>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.sidebar.success("Selecciona una aplicación arriba.")
    st.markdown('</div>', unsafe_allow_html=True)


# --- EJECUCIÓN ---
hide_menu_style = """
    <style>
        [data-testid="stSidebar"] {visibility: hidden;}
    </style>
"""
st.markdown(hide_menu_style, unsafe_allow_html=True)

# Mostrar animación
show_animation()

# Mostrar la app principal
show_main_app()
