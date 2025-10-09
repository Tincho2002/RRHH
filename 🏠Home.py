import streamlit as st
import base64
from pathlib import Path

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Portal de RRHH",
    page_icon="https://raw.githubusercontent.com/Tincho2002/RRHH/main/assets/logo_assa.jpg",
    layout="wide"
)

# --- FUNCIÓN PARA CODIFICAR IMÁGENES ---
def img_to_bytes(img_path):
    """Convierte una imagen local a bytes codificados en Base64."""
    try:
        img_bytes = Path(img_path).read_bytes()
        encoded = base64.b64encode(img_bytes).decode()
        return encoded
    except FileNotFoundError:
        # En caso de que el archivo no se encuentre, para evitar que la app se rompa.
        return None

# --- CSS PERSONALIZADO ---
st.markdown("""
<style>
    /* Estilos para el nuevo Encabezado (Header) */
    .header-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1rem 0;
    }

    .header-logo {
        width: 150px;
        height: auto;
    }

    .header-text {
        flex-grow: 1;
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

    /* Reglas para diseño responsivo en móviles */
    @media (max-width: 768px) {
        .card-container {
            flex-direction: column;
            align-items: center;
        }
        
        .header-container {
            flex-direction: column;
            gap: 15px;
        }
    }
</style>
""", unsafe_allow_html=True)


# --- ENCABEZADO RESPONSIVO ---
logo_path = "assets/logo_assa.jpg"
logo_base64 = img_to_bytes(logo_path)

# Solo muestra el encabezado si el logo se cargó correctamente
if logo_base64:
    logo_html = f'<img src="data:image/jpeg;base64,{logo_base64}" class="header-logo">'
    
    st.markdown(f"""
    <div class="header-container">
        {logo_html}
        <div class="header-text">
            <h1 style='text-align:center; color:#555;'>Bienvenido a la Aplicación de RRHH</h1>
            <h3 style='text-align:center; color:#555;'>Portal de Análisis de Capital Humano - Aguas Santafesinas S.A.</h3>
        </div>
        {logo_html}
    </div>
    """, unsafe_allow_html=True)
else:
    # Muestra un encabezado de texto simple si no se encuentra el logo
    st.error("No se pudo cargar el logo. Verifique la ruta: assets/logo_assa.jpg")
    st.markdown("<h1 style='text-align:center; color:#555;'>Bienvenido a la Aplicación de RRHH</h1>", unsafe_allow_html=True)

st.markdown("---")

# --- CONTENIDO DE INTRODUCCIÓN ---
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

# --- BARRA LATERAL ---
st.sidebar.success("Selecciona una aplicación arriba.")

