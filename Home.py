import streamlit as st

st.set_page_config(
    page_title="Aplicación Unificada Principal",
    page_icon="🏠",
)

st.title("Bienvenido a la Aplicación Consolidada")
st.sidebar.success("Selecciona una aplicación arriba.")

st.markdown(
    """
    Esta es la página de inicio de tu nueva aplicación Streamlit multi-página.
    Usa el menú de la barra lateral para navegar a las aplicaciones A, B o C.
    """
)
