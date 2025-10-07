import streamlit as st
import time

st.set_page_config(
    page_title="Portal de RRHH",
    page_icon="https://raw.githubusercontent.com/Tincho2002/RRHH/main/assets/logo_assa.jpg",
    layout="wide" 
)

# --- Splash Screen Aislado (se ejecuta solo una vez) ---
if 'splash_run' not in st.session_state:
    # Este CSS y HTML SÓLO se aplican a la pantalla de carga. Es 100% autónomo.
    st.html("""
        <style>
            #splash-screen {
                position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
                background: linear-gradient(180deg, #005f73, #0a9396, #94d2bd);
                z-index: 1000; display: flex; flex-direction: column;
                justify-content: center; align-items: center; color: white;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                opacity: 1;
                transition: opacity 1.5s ease-out;
            }
            #splash-screen.hidden { opacity: 0; visibility: hidden; }
            #splash-logo {
                border-radius: 25px; box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
                animation: fadeInScale 1.5s 0.5s ease-out forwards;
            }
            #splash-title { animation: fadeInSlide 1.5s 1s ease-out forwards; }
            @keyframes fadeInScale { 
                from { opacity: 0; transform: scale(0.8); }
                to { opacity: 1; transform: scale(1); }
            }
            @keyframes fadeInSlide { 
                from { opacity: 0; transform: translateY(20px); }
                to { opacity: 1; transform: translateY(0); }
            }
        </style>
        <div id="splash-screen">
            <img id="splash-logo" src="https://raw.githubusercontent.com/Tincho2002/RRHH/main/assets/logo_assa.jpg" width="250">
            <h1 id="splash-title">Portal de Análisis de RRHH</h1>
        </div>
        <script>
            setTimeout(function() {
                var splash = document.getElementById('splash-screen');
                if (splash) {
                    splash.classList.add('hidden');
                }
            }, 3000);
        </script>
    """)
    st.session_state.splash_run = True
    time.sleep(3.2) # Pausa el script de Python para dar tiempo a la animación a terminar


# --- CSS Principal de la Página (Seguro y No Condicional) ---
st.markdown("""
<style>
    /* Corrección para que las tarjetas se apilen en móviles */
    @media (max-width: 768px) {
        .card-container {
            flex-direction: column;
            align-items: center;
        }
    }

    /* Estilos de las Tarjetas (Flexbox y Responsivo) */
    .card-container {
        display: flex; gap: 20px; margin-top: 40px;
        flex-wrap: wrap; justify-content: center;
    }
    .app-card {
        flex: 1; min-width: 260px; max-width: 350px; padding: 20px;
        border-radius: 12px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease-in-out; text-align: center; cursor: pointer;
        text-decoration: none; color: #333; min-height: 180px;
        display: flex; flex-direction: column; justify-content: space-between;
    }
    .card-dotacion { background-color: #e0f7fa; }
    .card-horas { background-color: #fffde7; }
    .card-masa { background-color: #f1f8e9; }
    .app-card:hover {
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.2);
        transform: translateY(-5px);
    }
    .card-title {
        font-size: 1.5em; font-weight: bold; color: #003366; margin-bottom: 10px;
    }
    .access-icon {
        font-size: 1.6em; color: #003366; transition: transform 0.3s ease;
    }
    .app-card:hover .access-icon { transform: scale(1.2); }
    a.app-card, a.app-card:visited, a.app-card:hover, a.app-card:active {
        text-decoration: none !important; color: inherit;
    }
</style>
""", unsafe_allow_html=True)


# --- CONTENIDO PRINCIPAL COMPLETO DE LA APP ---
left_logo, center_text, right_logo = st.columns([1, 4, 1])
with left_logo:
    st.image("assets/logo_assa.jpg", width=200)
with center_text:
    st.title("Bienvenido a la Aplicación de RRHH")
    st.markdown("<h3 style='text-align:center; color:#555;'>Portal de Análisis de Capital Humano - Aguas Santafesinas S.A.</h3>", unsafe_allow_html=True)
with right_logo:
    st.image("assets/logo_assa.jpg", width=200)

st.markdown("---")
st.markdown(
    """
    <div style="text-align: center;">
        <h2>Análisis Estratégico de Capital Humano</h2>
        <p>Esta es la página de inicio del sistema unificado de gestión de <strong>Recursos Humanos</strong>.</p>
        <p>Para acceder a cada módulo, haz clic directamente en la tarjeta de interés o usa la barra lateral.</p>
    </div>
    """,
    unsafe_allow_html=True
)
st.markdown("""
<div class="card-container">
    <a href="/Dotacion" target="_self" class="app-card card-dotacion">
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
