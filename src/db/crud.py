"""Utilidades reutilizables para editar tablas desde Streamlit (reemplazo liviano de pgAdmin)."""
import pandas as pd
import streamlit as st

from src.db.connection import get_session
from src.db.models import Proveedor


def quick_add_proveedor(key_prefix: str) -> None:
    """Expander para dar de alta un proveedor nuevo sin salir del formulario actual."""
    with st.expander("➕ Agregar proveedor nuevo"):
        with st.form(f"{key_prefix}_alta_proveedor_rapida", clear_on_submit=True):
            nombre = st.text_input("Nombre *", key=f"{key_prefix}_prov_nombre")
            telefono = st.text_input("Teléfono", key=f"{key_prefix}_prov_tel")
            email = st.text_input("Email", key=f"{key_prefix}_prov_email")
            enviado = st.form_submit_button("💾 Guardar proveedor")
        if enviado:
            if not nombre:
                st.error("El nombre es obligatorio.")
            else:
                with get_session() as session:
                    session.add(Proveedor(nombre=nombre, telefono=telefono or None, email=email or None))
                    session.commit()
                st.success(f"Proveedor '{nombre}' agregado. Volvé a abrir el selector para usarlo.")
                st.rerun()


def render_simple_table(model, label: str, columns: list[str]):
    """Editor genérico (alta/baja/modificación) para modelos simples sin FKs."""
    with get_session() as session:
        rows = session.query(model).order_by(model.id).all()
        data = [{"id": r.id, **{c: getattr(r, c) for c in columns}} for r in rows]

    df = pd.DataFrame(data, columns=["id", *columns])
    edited = st.data_editor(
        df,
        num_rows="dynamic",
        use_container_width=True,
        disabled=["id"],
        key=f"editor_{model.__tablename__}",
    )

    if st.button(f"💾 Guardar cambios ({label})", key=f"save_{model.__tablename__}"):
        with get_session() as session:
            ids_originales = set(df["id"].dropna().astype(int))
            ids_editados = set(edited["id"].dropna().astype(int))

            for eliminado_id in ids_originales - ids_editados:
                obj = session.get(model, int(eliminado_id))
                if obj:
                    session.delete(obj)

            for _, fila in edited.iterrows():
                valores = {c: (fila[c] if pd.notna(fila[c]) else None) for c in columns}
                if pd.isna(fila["id"]):
                    session.add(model(**valores))
                else:
                    obj = session.get(model, int(fila["id"]))
                    if obj:
                        for c, v in valores.items():
                            setattr(obj, c, v)
            session.commit()
        st.success(f"{label}: cambios guardados en PostgreSQL.")
        st.rerun()
