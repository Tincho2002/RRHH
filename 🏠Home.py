import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Portal de RRHH",
    page_icon="https://raw.githubusercontent.com/Tincho2002/RRHH/main/assets/logo_assa.jpg",
    layout="wide"
)

# --------------------------------------------------------------------
# CSS
# --------------------------------------------------------------------
st.markdown("""
<style>
/* --- Splash Screen --- */
#splash-screen {
    position: fixed;
    top: 0; left: 0;
    width: 100vw; height: 100vh;
    background: linear-gradient(180deg, #005f73, #0a9396, #94d2bd);
    z-index: 9999;
    display: flex; flex-direction: column;
    justify-content: center; align-items: center;
    overflow: hidden;
    color: white;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    transition: opacity 1.5s ease-out;
}
#splash-screen.fade-out {
    opacity: 0;
}

/* --- Logo y título --- */
#splash-logo {
    width: 240px;
    opacity: 0;
    transform: scale(0.8);
    animation: fadeInScale 2s ease-out forwards;
}
#splash-title {
    font-size: 1.8em;
    opacity: 0;
    transform: translateY(20px);
    animation: fadeInSlide 2s 0.8s ease-out forwards;
}
@keyframes fadeInScale { to { opacity: 1; transform: scale(1); } }
@keyframes fadeInSlide { to { opacity: 1; transform: translateY(0); } }

/* --- Gotas --- */
.droplet {
    position: absolute;
    bottom: 100%;
    width: 2px;
    height: 50px;
    background: linear-gradient(to top, rgba(255,255,255,0.6), rgba(255,255,255,0.1));
    border-radius: 50%;
    animation: fall linear infinite;
    pointer-events: none;
}
@keyframes fall {
    0% { transform: translateY(0); opacity: 1; }
    100% { transform: translateY(110vh); opacity: 0; }
}

/* --- Contenido principal --- */
#main-content {
    opacity: 0;
    transition: opacity 1.2s ease-in;
}
#main-content.visible {
    opacity: 1;
}

/* --- Tarjetas --- */
.card-container {
    display: flex; gap: 20px;
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
}
.access-icon {
    font-size: 1.6em;
    color: #003366;
    transition: transform 0.3s ease;
}
.app-card:hover .access-icon { transform: scale(1.2); }
a.app-card, a.app-card:hover, a.app-card:visited, a.app-card:active {
    text-decoration: none !important;
    color: inherit;
}
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------------------------
# SPLASH (HTML + JS)
# --------------------------------------------------------------------
components.html("""
<div id="splash-screen">
    <img id="splash-logo" src="https://raw.githubusercontent.com/Tincho2002/RRHH/main/assets/logo_assa.jpg">
    <h1 id="splash-title">Portal de Análisis de RRHH</h1>
</div>

<script>
const splash = document.getElementById('splash-screen');

// Crear gotas dinámicamente
for (let i = 0; i < 45; i++) {
  const drop = document.createElement('div');
  drop.classList.add('droplet');
  drop.style.left = Math.random() * 100 + 'vw';
  drop.style.animationDuration = (0.5 + Math.random() * 0.7) + 's';
  drop.style.animationDelay = Math.random() * 3 + 's';
  splash.appendChild(drop);
}

// Ocultar splash después de 3 segundos
setTimeout(() => {
  splash.classList.add('fade-out');
  setTimeout(() => splash.remove(), 1800);
}, 3000);

// Mostrar contenido principal
window.addEventListener('load', () => {
  setTimeout(() => {
    const main = parent.document.querySelector('#main-content');
    if (main) main.classList.add('visible');
  }, 3100);
});
</script>
""", height=400)

# --------------------------------------------------------------------
# CONTENIDO PRINCIPAL
# --------------------------------------------------------------------
st.markdown('<div id="main-content">', unsafe_allow_html=True)

left_logo, center_text, right_logo = st.columns([1, 4, 1])
with left_logo:
    st.image("assets/logo_assa.jpg", width=200)
with center_text:
    st.title("Bienvenido a la Aplicación de RRHH")
    st.markdown("<h3 style='text-align:center; color:#555;'>Portal de Análisis de Capital Humano - Aguas Santafesinas S.A.</h3>", unsafe_allow_html=True)
with right_logo:
    st.image("assets/logo_assa.jpg", width=200)

st.markdown("---")

st.markdown("""
<div style="text-align: center;">
    <h2>Análisis Estratégico de Capital Humano</h2>
    <p>Esta es la página de inicio del sistema unificado de gestión de <strong>Recursos Humanos</strong>.</p>
    <p>Para acceder a cada módulo, haz clic directamente en la tarjeta o usa la barra lateral.</p>
</div>
""", unsafe_allow_html=True)

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

st.markdown("</div>", unsafe_allow_html=True)
st.sidebar.success("Selecciona una aplicación arriba.")
