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

/* 2. Animación de apertura para el logo principal (Zoom agresivo) */
@keyframes openingLogo {
    0% { transform: scale(3); opacity: 0; }
    100% { transform: scale(1); opacity: 1; }
}

/* 3. Animación de apertura para el logo repetido (Más sutil) */
@keyframes fade-in-scale {
    0% { transform: scale(0.9); opacity: 0; }
    100% { transform: scale(1); opacity: 1; }
}

/* 4. Selector para el PRIMER logo (usando el caption "main_logo") */
/* Centra la imagen dentro de su contenedor y aplica la animación. */
div[data-testid="stImage"] img[alt="main_logo"] { 
    animation: openingLogo 1.5s ease-out forwards;
    display: block; 
    margin: 0 auto; /* Centrado horizontal de la imagen */
}

/* 5. Selector para el SEGUNDO logo (usando el caption "secondary_logo") */
div[data-testid="stImage"] img[alt="secondary_logo"] {
    animation: fade-in-scale 1.5s ease-out 0.5s forwards; /* 0.5s de retraso */
    opacity: 0; /* Asegura que esté invisible al inicio */
    display: block;
    margin: 30px auto 20px auto; /* Centrado horizontal y margen */
    width: 200px; 
    max-width: 100%;
    border-radius: 8px;
    box-shadow: 0 0 10px rgba(0,0,0,0.1);
}

/* 6. Estilo de los títulos para Centrado */
h1, div[data-testid="stMarkdown"] h2 {
    text-align: center;
    width: 100%; 
}

h1 {
    font-size: 2.5em;
    color: #007bff;
}

/* 7. Centrado del Contenedor del Logo Principal */
/* Asegura que el logo y el título en la columna central estén juntos */
div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"] > div:first-child {
    display: flex;
    flex-direction: column;
    align-items: center; /* Centra el contenido verticalmente */
}

/* 8. ESTILOS DE TARJETA HTML/CSS */
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

# 1. Logo y Título (Centrado Perfecto usando columnas de ancho fijo)
# Usamos una columna central amplia para contener todo el encabezado
col_left, col_center, col_right = st.columns([1, 8, 1])

with col_center:
    # --- Logo Principal (Centrado por CSS) ---
    st.image("assets/logo_assa.jpg", width=100, caption="main_logo")
    
    # --- Títulos (Centrados por CSS) ---
    st.title("Bienvenido a la Aplicación de RRHH")
    st.markdown("<h2 style='color: #555;'>Portal de Análisis de Capital Humano - Aguas Santafesinas S.A.</h2>", unsafe_allow_html=True)
    
st.markdown("---")

# -----------------------------------------------------------------------
# --- SEGUNDO LOGO CON EFECTO (fade-in-scale) ---
# Usamos el contenedor st.container para asegurarnos de que la imagen quede
# en su propio bloque, centrado por el CSS del selector "secondary_logo"
# -----------------------------------------------------------------------
with st.container():
    st.image("assets/logo_assa.jpg", width=200, caption="secondary_logo")


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
