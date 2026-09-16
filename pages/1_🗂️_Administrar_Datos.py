"""Administración de datos: alta/baja/modificación sin necesidad de pgAdmin."""
import pandas as pd
import streamlit as st

from src.auth import require_login
from src.db.connection import get_session
from src.db.crud import quick_add_proveedor, render_simple_table
from src.db.models import Categoria, Cliente, Empleado, Producto, Proveedor
from src.ui import inject_css

st.set_page_config(page_title="Administrar datos - Ferretest", page_icon="🗂️", layout="wide")
require_login()
inject_css()
st.title("🗂️ Administrar datos")
st.caption("Edita, agrega o elimina filas y presiona 'Guardar cambios'. Se aplica directo en PostgreSQL.")

# Tamaño de imagen (px) por API externa (Lorem Picsum, placeholder hasta tener fotos reales)
_TAMANOS_VISTA = {"🔲 Iconos": 80, "🔳 Grande": 200, "⬛ Extra grande": 350}
_COLUMNAS_VISTA = {"🔲 Iconos": 8, "🔳 Grande": 4, "⬛ Extra grande": 2}

tab_prod, tab_cat, tab_prov, tab_cli, tab_emp = st.tabs(
    ["📦 Productos", "🏷️ Categorías", "🚚 Proveedores", "👤 Clientes", "🧑‍💼 Empleados"]
)

with tab_prod:
    quick_add_proveedor(key_prefix="admin_productos")

    with get_session() as session:
        categorias = {c.nombre: c.id for c in session.query(Categoria).order_by(Categoria.nombre).all()}
        proveedores = {p.nombre: p.id for p in session.query(Proveedor).order_by(Proveedor.nombre).all()}
        productos = session.query(Producto).order_by(Producto.sku).all()
        data = [
            {
                "id": p.id,
                "sku": p.sku,
                "nombre": p.nombre,
                "categoria": p.categoria.nombre if p.categoria else None,
                "proveedor": p.proveedor.nombre if p.proveedor else None,
                "precio_costo": float(p.precio_costo),
                "precio_venta": float(p.precio_venta),
                "stock_actual": p.stock_actual,
                "stock_minimo": p.stock_minimo,
                "imagen_url": p.imagen_url or "",
                "activo": p.activo,
            }
            for p in productos
        ]

    df = pd.DataFrame(
        data,
        columns=[
            "id", "sku", "nombre", "categoria", "proveedor",
            "precio_costo", "precio_venta", "stock_actual", "stock_minimo", "imagen_url", "activo",
        ],
    )

    vista = st.radio(
        "Vista",
        options=["📝 Tabla (editar)", *_TAMANOS_VISTA.keys()],
        horizontal=True,
        label_visibility="collapsed",
    )

    if vista != "📝 Tabla (editar)":
        tam = _TAMANOS_VISTA[vista]
        cols_por_fila = _COLUMNAS_VISTA[vista]
        cols = st.columns(cols_por_fila)
        for i, p in enumerate(data):
            with cols[i % cols_por_fila]:
                st.markdown('<div class="tuerca-card">', unsafe_allow_html=True)
                img_src = p["imagen_url"] if p["imagen_url"] else f"https://picsum.photos/seed/{p['sku']}/{tam}/{tam}"
                st.image(img_src, width=tam)
                st.caption(f"**{p['sku']}**  \n{p['nombre']}  \n$ {p['precio_venta']:,.2f} MXN · stock {p['stock_actual']}")
                st.markdown("</div>", unsafe_allow_html=True)
        st.caption("Los productos con foto personalizada mostrarán su imagen real; los demás usan el marcador provisorio.")
    else:
        edited = st.data_editor(
            df,
            num_rows="dynamic",
            use_container_width=True,
            disabled=["id"],
            column_config={
                "categoria": st.column_config.SelectboxColumn(options=list(categorias.keys())),
                "proveedor": st.column_config.SelectboxColumn(options=list(proveedores.keys())),
                "precio_costo": st.column_config.NumberColumn("Precio costo (MXN)", format="$ %.2f"),
                "precio_venta": st.column_config.NumberColumn("Precio venta (MXN)", format="$ %.2f"),
                "imagen_url": st.column_config.TextColumn("Ruta / URL Imagen"),
            },
            key="editor_productos",
        )

        if st.button("💾 Guardar cambios (Productos)"):
            with get_session() as session:
                ids_originales = set(df["id"].dropna().astype(int))
                ids_editados = set(edited["id"].dropna().astype(int))

                for eliminado_id in ids_originales - ids_editados:
                    obj = session.get(Producto, int(eliminado_id))
                    if obj:
                        session.delete(obj)

                for _, fila in edited.iterrows():
                    valores = {
                        "sku": fila["sku"],
                        "nombre": fila["nombre"],
                        "categoria_id": categorias.get(fila["categoria"]),
                        "proveedor_id": proveedores.get(fila["proveedor"]),
                        "precio_costo": fila["precio_costo"],
                        "precio_venta": fila["precio_venta"],
                        "stock_actual": int(fila["stock_actual"]) if pd.notna(fila["stock_actual"]) else 0,
                        "stock_minimo": int(fila["stock_minimo"]) if pd.notna(fila["stock_minimo"]) else 0,
                        "imagen_url": str(fila["imagen_url"]).strip() if pd.notna(fila["imagen_url"]) and str(fila["imagen_url"]).strip() else None,
                        "activo": bool(fila["activo"]),
                    }
                    if pd.isna(fila["id"]):
                        session.add(Producto(**valores))
                    else:
                        obj = session.get(Producto, int(fila["id"]))
                        if obj:
                            for c, v in valores.items():
                                setattr(obj, c, v)
                session.commit()
            st.success("Productos: cambios guardados en PostgreSQL.")
            st.rerun()

with tab_cat:
    render_simple_table(Categoria, "Categorías", ["nombre", "descripcion"])

with tab_prov:
    render_simple_table(Proveedor, "Proveedores", ["nombre", "telefono", "email"])

with tab_cli:
    render_simple_table(Cliente, "Clientes", ["nombre", "telefono", "email"])

with tab_emp:
    render_simple_table(Empleado, "Empleados", ["nombre", "puesto"])

st.divider()
if st.button("🔄 Refrescar datos"):
    st.rerun()
