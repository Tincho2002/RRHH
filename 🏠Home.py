import streamlit as st
import time

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Portal de RRHH",
    page_icon="https://raw.githubusercontent.com/Tincho2002/RRHH/main/assets/logo_assa.jpg",
    layout="wide" 
)

# --- CSS ÚNICO Y SEGURO PARA LA PÁGINA DE INICIO Y EFECTO DE CORTINA DE AGUA ---
st.markdown("""
<style>
    /* Estilos para el overlay de la animación de inicio */
    .water-curtain-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: linear-gradient(135deg, rgba(0, 150, 255, 0.8) 0%, rgba(0, 51, 102, 0.8) 100%); /* Efecto de agua/azul oscuro */
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        z-index: 9999; /* Asegura que esté por encima de todo */
        opacity: 1;
        animation: fadeOutCurtain 2s ease-out 2s forwards; /* Duración de la animación + delay */
        /* forwards mantiene el estado final de la animación */
    }

    /* Animación para el logo dentro de la cortina */
    .water-curtain-logo {
        opacity: 0;
        transform: translateY(20px);
        animation: fadeInLogo 1.5s ease-out 0.5s forwards; /* Aparece después de 0.5s */
        max-width: 300px; /* Ajusta el tamaño del logo */
        height: auto;
    }

    /* Keyframes para desvanecer la cortina */
    @keyframes fadeOutCurtain {
        to {
            opacity: 0;
            visibility: hidden; /* Oculta completamente una vez desvanecido */
        }
    }

    /* Keyframes para aparecer el logo */
    @keyframes fadeInLogo {
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    /* Corrección para que las tarjetas se apilen en móviles (pantallas angostas) */
    @media (max-width: 768px) {
        .card-container {
            flex-direction: column;
            align-items: center;
        }
    }

    /* Estilos de las Tarjetas (Flexbox y Responsivo) */
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

    .app-card:hover .access-icon { transform: scale(1.2); }
    
    a.app-card, a.app-card:visited, a.app-card:hover, a.app-card:active {
        text-decoration: none !important; 
        color: inherit;
    }

    /* Para asegurar que el resto del contenido no sea visible hasta que la animación termine */
    .content-hidden-until-animation {
        opacity: 0;
        animation: showContent 0.1s ease-out 4s forwards; /* Aparece después que la cortina haya terminado */
    }

    @keyframes showContent {
        to {
            opacity: 1;
        }
    }

    /* Ocultar elementos de Streamlit que podrían aparecer antes del efecto */
    #root > div:nth-child(1) > div > div > div > div {
        visibility: hidden;
    }
    .water-curtain-overlay ~ div {
        visibility: hidden;
    }
</style>
""", unsafe_allow_html=True)

# --- ANIMACIÓN DE INICIO: CORTINA DE AGUA Y LOGO ---
# Muestra la cortina con el logo. El CSS se encarga de la animación.
st.markdown(
    f"""
    <div class="water-curtain-overlay">
        <img src="https://raw.githubusercontent.com/Tincho2002/RRHH/main/assets/logo_assa.jpg" class="water-curtain-logo" alt="Logo ASSA">
    </div>
    """, 
    unsafe_allow_html=True
)

# Un pequeño delay para permitir que la animación CSS se complete antes de que el resto del contenido se cargue
# Esto es más para la sensación, el CSS ya maneja la visibilidad.
time.sleep(3.5) # Ajusta este tiempo si la animación es más larga o corta

# --- CONTENIDO PRINCIPAL DE LA PÁGINA ---
# Envuelve todo el contenido principal en un div que se hará visible después de la animación
st.markdown('<div class="content-hidden-until-animation">', unsafe_allow_html=True)

left_logo, center_text, right_logo = st.columns([1, 4, 1])

# Ahora los logos "normales" de la cabecera, sin el efecto de onda inicial
with left_logo:
    st.image("https://raw.githubusercontent.com/Tincho2002/RRHH/main/assets/logo_assa.jpg", width=200)
with center_text:
    st.title("Bienvenido a la Aplicación de RRHH")
    st.markdown("<h3 style='text-align:center; color:#555;'>Portal de Análisis de Capital Humano - Aguas Santafesinas S.A.</h3>", unsafe_allow_html=True)
with right_logo:
    st.image("https://raw.githubusercontent.com/Tincho2002/RRHH/main/assets/logo_assa.jpg", width=200)

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

# --- TARJETAS DE NAVEGACIÓN ---
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

# Cierra el div que envuelve el contenido principal
st.markdown('</div>', unsafe_allow_html=True)