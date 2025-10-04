import streamlit as st

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

/* 2. Animación de apertura para el logo (Zoom) */
@keyframes openingLogo {
    0% { transform: scale(3); opacity: 0; }
    100% { transform: scale(1); opacity: 1; }
}

/* 3. Aplica animación al logo */
.stImage img {
    animation: openingLogo 1.5s ease-out forwards;
    display: block; 
    margin-left: auto;
    margin-right: auto;
    margin-bottom: 20px;
}

/* 4. Estilo de los títulos */
h1 {
    text-align: center;
    font-size: 2.5em;
    color: #007bff;
}

/* 5. ESTILOS DE TARJETA HTML/CSS (La nueva solución de diseño) */
.card-container {
    display: flex; /* Alinea las tarjetas horizontalmente */
    gap: 20px;
    margin-top: 40px;
}
.app-card {
    flex: 1; /* Ocupa el mismo ancho */
    padding: 20px;
    border-radius: 12px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    transition: all 0.3s ease-in-out;
    text-align: center;
    cursor: pointer;
    text-decoration: none; /* Quitar subrayado del enlace */
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
    transform: translateY(-5px); /* Pequeño efecto de elevación */
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
col_logo, col_title, _ = st.columns([1, 6, 1])

with col_logo:
    st.image("assets/logo_assa.jpg", width=100) 

with col_title:
    st.title("Bienvenido a la Aplicación de RRHH")
    st.markdown("<h2 style='text-align: center; color: #555;'>Portal de Análisis de Capital Humano - Aguas Potable S.A.</h2>", unsafe_allow_html=True)

st.markdown("---")


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
                <p>Consulta la estructura, headcount y distribución de personal.</p>
                <b>(Clic para Acceder)</b>
            </a>
            <a href="/app_horas_extras" target="_self" class="app-card card-horas">
                <div class="card-title">⏰ Horas Extras</div>
                <p>Analiza el impacto de horas adicionales y gestiona los indicadores de ausentismo.</p>
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
