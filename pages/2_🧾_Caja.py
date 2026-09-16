"""Caja: registrar ventas (con cola offline si se cae la conexión)."""
import pandas as pd
import streamlit as st

from src.auth import require_login
from src.db import offline_queue
from src.db.connection import get_session, is_db_available
from src.db.models import Cliente, DetalleVenta, Empleado, Producto, Venta
from src.ui import inject_css, format_mxn

st.set_page_config(page_title="Caja - Ferretest", page_icon="🧾", layout="wide")
require_login()
inject_css()
st.title("🧾 Caja - Registrar venta")

db_ok = is_db_available()
pendientes = offline_queue.count_pending()

col_a, col_b = st.columns([3, 1])
with col_a:
    if db_ok:
        st.success("Conectado a PostgreSQL")
    else:
        st.error("Sin conexión a PostgreSQL. Las ventas se guardarán localmente.")
with col_b:
    if pendientes:
        st.warning(f"{pendientes} venta(s) pendiente(s) de sincronizar")
        if db_ok and st.button("Sincronizar ahora"):
            ok, fallidas = offline_queue.sync_pending()
            st.toast(f"Sincronizadas: {ok} / Fallidas: {fallidas}")
            st.rerun()

if "carrito" not in st.session_state:
    st.session_state.carrito = []

try:
    with get_session() as session:
        productos_db = session.query(Producto).filter(Producto.activo.is_(True)).all()
        clientes_db = session.query(Cliente).all()
        empleados_db = session.query(Empleado).all()
        productos_opts = {f"{p.sku} - {p.nombre}": (p.id, float(p.precio_venta)) for p in productos_db}
        clientes_opts = {c.nombre: c.id for c in clientes_db}
        empleados_opts = {e.nombre: e.id for e in empleados_db}

    with st.form("agregar_item", clear_on_submit=True):
        c1, c2, c3 = st.columns([3, 1, 1])
        producto_sel = c1.selectbox("Producto", options=list(productos_opts.keys()) or ["(sin productos)"])
        cantidad = c2.number_input("Cantidad", min_value=1, value=1, step=1)
        agregar = c3.form_submit_button("➕ Agregar")
        if agregar and productos_opts:
            producto_id, precio = productos_opts[producto_sel]
            st.session_state.carrito.append(
                {"producto": producto_sel, "producto_id": producto_id, "cantidad": cantidad, "precio_unitario": precio}
            )

    if st.session_state.carrito:
        carrito_df = pd.DataFrame(st.session_state.carrito)
        carrito_df["subtotal"] = carrito_df["cantidad"] * carrito_df["precio_unitario"]
        st.dataframe(carrito_df[["producto", "cantidad", "precio_unitario", "subtotal"]], use_container_width=True)
        total = carrito_df["subtotal"].sum()
        st.metric("Total (MXN)", format_mxn(total))

        cliente_sel = st.selectbox("Cliente", options=list(clientes_opts.keys()) or ["Consumidor Final"])
        empleado_sel = st.selectbox("Empleado", options=list(empleados_opts.keys()) or ["(sin empleados)"])

        col_confirm, col_clear = st.columns(2)
        if col_confirm.button("✅ Confirmar venta", type="primary"):
            items = [
                {"producto_id": it["producto_id"], "cantidad": it["cantidad"], "precio_unitario": it["precio_unitario"]}
                for it in st.session_state.carrito
            ]
            cliente_id = clientes_opts.get(cliente_sel)
            empleado_id = empleados_opts.get(empleado_sel)
            try:
                if not is_db_available():
                    raise RuntimeError("DB no disponible")
                with get_session() as session:
                    venta = Venta(cliente_id=cliente_id, empleado_id=empleado_id, total=total)
                    session.add(venta)
                    session.flush()
                    for item in items:
                        session.add(DetalleVenta(venta_id=venta.id, **item))
                        prod = session.get(Producto, item["producto_id"])
                        if prod:
                            prod.stock_actual = max(0, prod.stock_actual - item["cantidad"])
                    session.commit()
                st.success("Venta guardada e inventario actualizado en PostgreSQL.")
            except Exception:
                offline_queue.enqueue_venta(cliente_id, empleado_id, items)
                st.warning("Sin conexión: la venta se guardó localmente y se sincronizará luego.")
            st.session_state.carrito = []
            st.rerun()
        if col_clear.button("🗑️ Vaciar carrito"):
            st.session_state.carrito = []
            st.rerun()
except Exception as e:
    st.error(f"No se pudo cargar el formulario de caja: {e}")
