import streamlit as st

# --- Configuración Inicial ---
st.set_page_config(
    page_title="Aplicación Unificada Principal",
    page_icon="🏠",
    layout="wide"
)

# ----------------------------------------------------------------------------------
# --- CSS: ANIMACIÓN, LOGOS Y TARJETAS ---
# ----------------------------------------------------------------------------------
st.markdown("""
<style>
@keyframes openingLogo {
    0% { transform: scale(3); opacity: 0; }
    50% { transform: scale(1.1); opacity: 1; }
    100% { transform: scale(1); opacity: 1; }
}

@keyframes slideUp {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}

.stImage img {
    animation: openingLogo 2s ease-out forwards;
    display: block; 
    margin-left: auto;
    margin-right: auto;
    margin-bottom: 10px;
}

.st-emotion-cache-1jicfl2 { 
    animation: slideUp 1s ease-out 1.5s forwards;
    opacity: 0; 
}

/* ---------- TARJETAS (CARDS) ---------- */
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
.card-horas { background-color: #fffde7; }    /* Amarillo claro */
.card-masa { background-color: #f1f8e9; }     /* Verde claro */

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
# --- ENCABEZADO CON LOGOS Y TÍTULO ---
# -----------------------------------------------------------------------
left_logo, center_text, right_logo = st.columns([1, 4, 1])

with left_logo:
    st.image("assets/logo_assa.jpg", width=200)

with center_text:
    st.title("Bienvenido a la Aplicación de RRHH")
    st.markdown("<h3 style='text-align:center; color:#555;'>Portal de Análisis de Capital Humano - Aguas Santafesinas S.A.</h3>", unsafe_allow_html=True)

with right_logo:
    st.image("assets/logo_assa.jpg", width=200)

st.markdown("---")

# -----------------------------------------------------------------------
# --- CONTENIDO PRINCIPAL Y TARJETAS ---
# -----------------------------------------------------------------------
main_col = st.columns([1, 10, 1])[1]

with main_col:
    st.markdown("## Análisis Estratégico de Capital Humano")
    st.markdown(
        """
        Esta es la página de inicio del sistema unificado de gestión de **Recursos Humanos**.
        
        Para acceder a cada módulo, haz clic directamente en la tarjeta de interés o usa la barra lateral.
        """
    )

    # Tarjetas interactivas
    st.markdown(
        """
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

    st.markdown("---")

# Mensaje lateral
st.sidebar.success("Selecciona una aplicación arriba.")
