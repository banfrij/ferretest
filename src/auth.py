"""Autenticación simple por sesión para proteger la app (login obligatorio)."""
import hashlib
import hmac

import streamlit as st


def _hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def require_login() -> None:
    """Muestra un formulario de login y detiene la ejecución hasta autenticar.

    Mientras no haya sesión, oculta por completo la barra lateral (nav incluida)
    para que no se puedan ver ni recorrer las páginas sin loguearse.
    """
    if st.session_state.get("authenticated"):
        with st.sidebar:
            st.caption(f"👤 Sesión: {st.session_state.get('auth_user', '')}")
            if st.button("🚪 Cerrar sesión"):
                st.session_state.authenticated = False
                st.session_state.pop("auth_user", None)
                st.rerun()
        return

    st.markdown(
        """
        <style>
            [data-testid="stSidebar"] { display: none; }
            [data-testid="collapsedControl"] { display: none; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title("🔒 Ferretest - Iniciar sesión")
    with st.form("login_form"):
        username = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        submitted = st.form_submit_button("Ingresar")

    if submitted:
        expected_user = st.secrets["auth"]["username"]
        expected_hash = st.secrets["auth"]["password_hash"]
        if username == expected_user and hmac.compare_digest(_hash(password), expected_hash):
            st.session_state.authenticated = True
            st.session_state.auth_user = username
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos.")

    st.stop()
