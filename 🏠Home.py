import streamlit as st


# Esta es la configuración que debes agregar o modificar
st.set_page_config(
    page_title="Portal de RRHH",
    page_icon="🏠"  # Puedes usar cualquier emoji o la URL a una imagen .ico
)

# ----------------------------------------------------------------------------------
# --- CSS: ANIMACIÓN, LOGOS Y TARJETAS MEJORADAS ---
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
@keyframes pulse {
    0% { transform: scale(1); }
    50% { transform: scale(1.25); }
    100% { transform: scale(1); }
}
.app-card:hover .access-icon {
    animation: pulse 0.8s ease-in-out infinite;
    transform: translateY(-5px);
    box-shadow: 0 0 25px rgba(0, 51, 102, 0.25); /* halo azul oscuro */
}
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(30px); }
    to { opacity: 1; transform: translateY(0); }
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
    animation: fadeInUp 1s ease both;
}

.app-card:nth-child(1) { animation-delay: 0.3s; }
.app-card:nth-child(2) { animation-delay: 0.6s; }
.app-card:nth-child(3) { animation-delay: 0.9s; }

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

/* Ícono de acceso */
.access-icon {
    font-size: 1.6em;
    color: #003366;
    transition: transform 0.3s ease;
}
.app-card:hover .access-icon {
    transform: scale(1.2);
}

/* Elimina subrayado de todos los enlaces */
a.app-card, a.app-card:visited, a.app-card:hover, a.app-card:active {
    text-decoration: none !important;
    color: inherit;
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

    st.markdown("""
    <div class="card-container">
        <a href="/1_👥_Dotación" target="_self" class="app-card card-dotacion">
            <div class="card-title">👥 Dotación</div>
            <p>Consulta la estructura y distribución geográfica y por gerencia de personal.</p>
            <div class="access-icon">🔗</div>
        </a>
        <a href="/2_🕒_Horas_Extras" target="_self" class="app-card card-horas">
            <div class="card-title">⏰ Horas Extras</div>
            <p>Analiza el impacto de horas adicionales al 50% y al 100%.</p>
            <div class="access-icon">🔗</div>
        </a>
        <a href="/3_💵_Masa_Salarial" target="_self" class="app-card card-masa">
            <div class="card-title">💵 Masa Salarial</div>
            <p>Visualiza la composición, evolución y proyecciones de costos salariales.</p>
            <div class="access-icon">🔗</div>
        </a>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

# Mensaje lateral
st.sidebar.success("Selecciona una aplicación arriba.")




