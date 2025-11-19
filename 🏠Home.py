import streamlit as st

# --- Configuración de la página ---
st.set_page_config(
    page_title="Portal de RRHH",
    page_icon="https://cdn.jsdelivr.net/gh/Tincho2002/RRHH@main/assets/logo_assa.jpg",
    layout="wide"
)

# ----------------------------------------------------------------------------------
# --- CSS: PANTALLA DE CARGA, ANIMACIONES Y NUEVAS TARJETAS ---
# ----------------------------------------------------------------------------------
st.markdown("""
<style>
    /* Importar fuente moderna */
    @import url('https://fonts.googleapis.com/css2?family=Source+Sans+Pro:wght@400;600;700&display=swap');

    /* =========================================
       1. ESTILOS DE ANIMACIÓN (SPLASH & UI)
       ========================================= */
    
    /* Pantalla de Carga (Splash Screen) */
    #splash-screen {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background: linear-gradient(180deg, #005A7A, #00A7C4);
        z-index: 9999; /* Z-index alto para tapar todo */
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        color: white;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        
        /* Animación de salida: se va hacia arriba */
        animation: slideUpSplash 1s ease-out 2.5s forwards;
    }

    #splash-logo {
        border-radius: 25px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
        animation: fadeInScale 1.5s 0.5s ease-out forwards;
    }

    #splash-title {
        margin-top: 20px;
        animation: fadeInSlide 1.5s 1s ease-out forwards;
    }

    /* Keyframes Animaciones */
    @keyframes slideUpSplash {
        from { transform: translateY(0); }
        to { transform: translateY(-100vh); visibility: hidden; }
    }

    @keyframes fadeInScale {
        from { opacity: 0; transform: scale(0.8); }
        to { opacity: 1; transform: scale(1); }
    }
    @keyframes fadeInSlide {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }

    /* Animación de Gotas */
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

    /* --- Estilos del Contenido Principal (Fade In) --- */
    #main-content {
        opacity: 0; 
        animation: showContent 1.5s ease-in 2.5s forwards;
    }
    @keyframes showContent {
        from { opacity: 0; }
        to { opacity: 1; }
    }

    /* Animación para la UI (Barra Lateral y Cabecera) */
    [data-testid="stSidebar"],
    [data-testid="stHeader"] {
        opacity: 0; 
        transform: translateY(-20px); 
        animation: showUI 0.75s ease-out 2.5s forwards;
    }
    @keyframes showUI {
        to { opacity: 1; transform: translateY(0); }
    }


    /* =========================================
       2. ESTILOS DE LAS TARJETAS (NUEVO DISEÑO)
       ========================================= */
    
    /* Grid Flexbox Responsivo */
    .cards-grid {
        display: flex;
        flex-wrap: wrap;
        gap: 25px;
        justify-content: center;
        perspective: 1000px;
        padding: 20px 0;
        font-family: 'Source Sans Pro', sans-serif;
    }

    /* Tarjeta Base */
    .nav-card {
        background: white;
        border-radius: 16px;
        padding: 30px 25px;
        width: 280px; 
        text-decoration: none !important;
        color: #333;
        box-shadow: 0 10px 30px rgba(0,0,0,0.08);
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
        border: 1px solid rgba(255,255,255,0.6);
        position: relative;
        overflow: hidden;
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
        flex-grow: 1; 
        max-width: 350px;
        cursor: pointer;
    }

    /* Efecto Hover */
    .nav-card:hover {
        transform: translateY(-10px);
        box-shadow: 0 20px 40px rgba(0,0,0,0.15);
    }

    /* --- PALETA DE COLORES (Gama Azul/Violeta) --- */
    
    /* Dotación (Cyan) */
    .card-cyan { background: linear-gradient(145deg, #ffffff 0%, #e0f7fa 100%); border-top: 6px solid #00bcd4; }
    .card-cyan .card-icon { color: #00bcd4; }
    .card-cyan:hover .go-btn { background-color: #00bcd4; color: white; }

    /* Horas Extras (Indigo) */
    .card-indigo { background: linear-gradient(145deg, #ffffff 0%, #e8eaf6 100%); border-top: 6px solid #3f51b5; }
    .card-indigo .card-icon { color: #3f51b5; }
    .card-indigo:hover .go-btn { background-color: #3f51b5; color: white; }

    /* Masa Salarial (Violeta) */
    .card-violet { background: linear-gradient(145deg, #ffffff 0%, #f3e5f5 100%); border-top: 6px solid #9c27b0; }
    .card-violet .card-icon { color: #9c27b0; }
    .card-violet:hover .go-btn { background-color: #9c27b0; color: white; }

    /* Planta de Cargos (Slate) */
    .card-slate { background: linear-gradient(145deg, #ffffff 0%, #eceff1 100%); border-top: 6px solid #607d8b; }
    .card-slate .card-icon { color: #607d8b; }
    .card-slate:hover .go-btn { background-color: #607d8b; color: white; }

    /* Indicadores (Azul) */
    .card-blue { background: linear-gradient(145deg, #ffffff 0%, #e3f2fd 100%); border-top: 6px solid #2196f3; }
    .card-blue .card-icon { color: #2196f3; }
    .card-blue:hover .go-btn { background-color: #2196f3; color: white; }

    /* Elementos Internos */
    .card-icon {
        font-size: 3.5rem;
        margin-bottom: 20px;
        transition: transform 0.4s ease;
        filter: drop-shadow(0 4px 4px rgba(0,0,0,0.1));
    }
    .nav-card:hover .card-icon {
        transform: scale(1.15) rotate(8deg);
    }

    .card-title {
        font-size: 1.3rem;
        font-weight: 700;
        margin-bottom: 12px;
        color: #1e293b;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .card-desc {
        font-size: 0.95rem;
        color: #64748b;
        margin-bottom: 25px;
        line-height: 1.5;
        flex-grow: 1; 
    }

    .go-btn {
        background-color: #fff;
        border-radius: 50%;
        width: 45px;
        height: 45px;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 4px 10px rgba(0,0,0,0.08);
        font-size: 1.2rem;
        color: #cbd5e1;
        transition: all 0.3s ease;
        align-self: center;
        margin-top: auto;
    }
    .nav-card:hover .go-btn {
        box-shadow: 0 8px 15px rgba(0,0,0,0.2);
        transform: scale(1.1);
    }
    
    /* Header Responsive */
    .header-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 20px;
    }
    .header-text { text-align: center; flex-grow: 1; }
    .header-logo { width: 200px; flex-shrink: 0; height: auto; border-radius: 15px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }

    @media (max-width: 768px) {
        .header-container { flex-direction: column; justify-content: center; }
        .header-logo { width: 180px; }
        .cards-grid { flex-direction: column; align-items: center; }
        .nav-card { width: 100%; max-width: 100%; }
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------
# --- PANTALLA DE CARGA (HTML) ---
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
    
    <img id="splash-logo" src="https://cdn.jsdelivr.net/gh/Tincho2002/RRHH@main/assets/logo_assa.jpg" width="500">
    <h1 id="splash-title" style="margin-top:20px;">Portal de Análisis de RRHH</h1>
</div>
""")

# -----------------------------------------------------------------------
# --- CONTENIDO PRINCIPAL ---
# -----------------------------------------------------------------------

# Envolvemos todo en un div 'main-content' para aplicar la animación de entrada
st.markdown('<div id="main-content">', unsafe_allow_html=True)

# --- CABECERA ---
logo_url = "https://cdn.jsdelivr.net/gh/Tincho2002/RRHH@main/assets/logo_assa.jpg"

st.markdown(f"""
<div class="header-container">
    <img src="{logo_url}" class="header-logo logo-left">
    <div class="header-text">
        <h1 style='color:#555; font-size: 2.5rem; margin:0;'>Bienvenido a la Aplicación de RRHH</h1>
        <h3 style='color:#555; margin:5px 0;'>Portal de Análisis de Capital Humano</h3>
        <h3 style='color:#555; margin:0;'>Aguas Santafesinas S.A.</h3>
    </div>
    <img src="{logo_url}" class="header-logo logo-right">
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# --- TEXTO INTRODUCTORIO ---
st.markdown(
    """
    <div style="text-align: center; margin-bottom: 40px;">
        <h2 style="color: #1e293b;">Análisis Estratégico de Capital Humano</h2>
        <p style="color: #64748b; font-size: 1.1rem;">Esta es la página de inicio del sistema unificado de gestión de <strong>Recursos Humanos</strong>.</p>
        <p style="color: #64748b; font-size: 1.1rem;">Para acceder a cada módulo, haz clic directamente en la tarjeta de interés o usa la barra lateral.</p>
    </div>
    """,
    unsafe_allow_html=True
)

# --- NUEVAS TARJETAS NAVEGABLES (HTML CORREGIDO) ---
# Usamos la estructura 'cards-grid' y 'nav-card' definidas en el CSS de arriba.
cards_html = """
<div class="cards-grid">
    
    <!-- 1. Dotación -->
    <a href="Dotacion" target="_self" class="nav-card card-cyan">
        <div class="card-icon">👥</div>
        <div class="card-title">Dotación</div>
        <div class="card-desc">
            Consulta la estructura y distribución geográfica y por gerencia de personal.
        </div>
        <div class="go-btn">📎</div>
    </a>

    <!-- 2. Horas Extras -->
    <a href="Horas_Extras" target="_self" class="nav-card card-indigo">
        <div class="card-icon">⏰</div>
        <div class="card-title">Horas Extras</div>
        <div class="card-desc">
            Analiza el impacto de horas adicionales al 50% y al 100%.
        </div>
        <div class="go-btn">📎</div>
    </a>

    <!-- 3. Masa Salarial -->
    <a href="Masa_Salarial" target="_self" class="nav-card card-violet">
        <div class="card-icon">💸</div>
        <div class="card-title">Masa Salarial</div>
        <div class="card-desc">
            Visualiza la composición, evolución y proyecciones de costos salariales.
        </div>
        <div class="go-btn">📎</div>
    </a>

    <!-- 4. Planta de Cargos -->
    <a href="Planta_de_Cargos" target="_self" class="nav-card card-slate">
        <div class="card-icon">📊</div>
        <div class="card-title">Planta de Cargos</div>
        <div class="card-desc">
            Analiza la dinámica de ingresos y egresos, y la composición detallada.
        </div>
        <div class="go-btn">📎</div>
    </a>

    <!-- 5. Indicadores de Eficiencia -->
    <a href="Indicadores_de_Eficiencia" target="_self" class="nav-card card-blue">
        <div class="card-icon">🎯</div>
        <div class="card-title">Indicadores de Eficiencia</div>
        <div class="card-desc">
            Mide el rendimiento y la productividad a través de KPIs clave.
        </div>
        <div class="go-btn">📎</div>
    </a>

</div>
"""

st.markdown(cards_html, unsafe_allow_html=True)

st.markdown("---")
st.markdown('</div>', unsafe_allow_html=True) # Cierre del main-content

# Mensaje lateral
st.sidebar.success("Selecciona una aplicación arriba.")