import streamlit as st
import pandas as pd
# Importaciones de otras páginas (necesarias si esta fuera la app principal)
# import app_dotacion # Simulación de importación
# import app_horas_extras # Simulación de importación


# --- Configuración Inicial ---
st.set_page_config(
    page_title="Aplicación Unificada Principal",
    page_icon="💧",
    layout="wide"
)

# --- CSS: Animación del Logo y Estilos ---
st.markdown("""
<style>
/* 1. MOSTRAR LA BARRA LATERAL NATIVA (Necesaria para navegar) */
div[data-testid="stSidebar"] {
    display: block !important; 
}

/* 2. Animación de apertura para el primer logo (Zoom agresivo, usado en el primer logo) */
@keyframes openingLogo {
    0% { transform: scale(3); opacity: 0; }
    100% { transform: scale(1); opacity: 1; }
}

/* 3. Animación de apertura para el logo repetido (Más sutil) */
@keyframes fade-in-scale {
    0% { transform: scale(0.9); opacity: 0; }
    100% { transform: scale(1); opacity: 1; }
}

/* 4. Aplica animación al PRIMER logo de la página */
/* Se aplica a la imagen dentro de la primera columna, asumiendo es el primer st.image */
div.st-emotion-cache-1r6i7h4 > div[data-testid="stImage"] img, 
div.st-emotion-cache-1r6i7h4 > div[data-testid="stImage"] { 
    animation: openingLogo 1.5s ease-out forwards;
}


/* --- CLASE PARA EL SEGUNDO LOGO (CONTENEDOR) --- */
/* Esta clase se aplicará al contenedor (st.container) y anima la imagen dentro */
.secondary-logo-container div[data-testid="stImage"] img {
    animation: fade-in-scale 1.5s ease-out 0.5s forwards !important; /* 0.5s de retraso */
    opacity: 0 !important; /* Asegura que esté invisible al inicio */
    display: block !important;
    margin: 30px auto 20px auto !important;
    width: 200px; 
    max-width: 100%;
    border-radius: 8px;
    box-shadow: 0 0 10px rgba(0,0,0,0.1);
}

/* 6. Estilo de los títulos */
h1 {
    text-align: center;
    font-size: 2.5em;
    color: #007bff;
}

/* 7. ESTILOS DE TARJETA HTML/CSS */
.card-container {
    display: flex;
    gap: 20px;
    margin-top: 40px;
}
.app-card {
    flex: 1;
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
.card-dotacion { background-color: #e0f7fa; } /* Azul claro */
.card-horas { background-color: #fffde7; }  /* Amarillo claro */
.card-masa { background-color: #f1f8e9; }   /* Verde claro */

.app-card:hover {
    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.2);
    transform: translateY(-5px);
}

.card-title {
    font-size: 1.5em;
    font-weight: bold;
    color: #007bff;
    margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------
# --- CONTENIDO DE LA PÁGINA DE INICIO: EL PORTAL DE APLICACIONES ---
# -----------------------------------------------------------------------

# 1. Logo y Título (Centrados)
# El logo en esta columna tendrá la animación "openingLogo"
col_logo, col_title, _ = st.columns([1, 6, 1])

with col_logo:
    st.image("assets/logo_assa.jpg", width=300) 

with col_title:
    st.title("Bienvenido a la Aplicación de RRHH")
    st.markdown("<h2 style='text-align: center; color: #555;'>Portal de Análisis de Capital Humano - Aguas Santafesinas S.A.</h2>", unsafe_allow_html=True)
    
st.markdown("---")

# -----------------------------------------------------------------------
# --- SEGUNDO LOGO CON EFECTO (fade-in-scale) ---
# Se utiliza un st.container con la clase CSS para asegurar que la ruta sea correcta
# y el CSS pueda apuntar a la imagen de forma precisa.
# -----------------------------------------------------------------------
st.markdown('<div class="secondary-logo-container">', unsafe_allow_html=True)
# El logo aparecerá en el centro gracias al "margin: auto" en el CSS de la clase.
st.image("assets/logo_assa.jpg", width=200, caption="Segundo Logo Animado de ASSA")
st.markdown('</div>', unsafe_allow_html=True) 
# -----------------------------------------------------------------------
# --- CONTINUACIÓN DEL DASHBOARD (FALTA LA NAVEGACIÓN REAL) ---
# -----------------------------------------------------------------------

# 2. Contenido Principal y Tarjetas (Usando HTML/CSS para el diseño)
main_col = st.columns([1, 10, 1])[1] 

with main_col:
    st.markdown("## Análisis Estratégico de Capital Humano")
    st.markdown(
        """
        Esta es la página de inicio del sistema unificado de gestión de **Recursos Humanos**.
        
        Para acceder a cada módulo, haz clic directamente en la tarjeta de interés o usa la barra lateral.
        """
    )
    
    # --- INYECCIÓN DE HTML PARA LAS TARJETAS (Navegación Estable) ---
    st.markdown(
        f"""
        <div class="card-container">
            <a href="/app_dotacion" target="_self" class="app-card card-dotacion">
                <div class="card-title">👥 Dotación</div>
                <p>Consulta la estructura y distribución geográfica y por gerencia de personal.</p>
                <b>(Clic para Acceder)</b>
            </a>
            <a href="/app_horas_extras" target="_self" class="app-card card-horas">
                <div class="card-title">⏰ Horas Extras</div>
                <p>Analiza el impacto de horas adicionales al 50% y al 100%.</p>
                <b>(Clic para Acceder)</b>
            </a>
            <a href="/app_masa_salarial" target="_self" class="app-card card-masa">
                <div class="card-title">💵 Masa Salarial</div>
                <p>Visualiza la composición, evolución y proyecciones de costos salariales.</p>
                <b>(Clic para Acceder)</b>
            </a>
        </div>
        """, unsafe_allow_html=True
    )
    # --- FIN DE LAS TARJETAS HTML ---
    
    st.markdown("---")


# Instrucción final para el usuario
st.sidebar.success("Selecciona una aplicación para continuar.")


