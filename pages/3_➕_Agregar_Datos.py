"""Alta rápida de datos: un formulario por tipo de registro (ideal para tablet)."""
import os
from pathlib import Path
import streamlit as st

from src.auth import require_login
from src.db.connection import get_session
from src.db.crud import quick_add_proveedor
from src.db.models import Categoria, Cliente, Empleado, Producto, Proveedor
from src.ui import inject_css

st.set_page_config(page_title="Agregar datos - Ferretest", page_icon="➕", layout="wide")
require_login()
inject_css()
st.title("➕ Agregar datos")
st.caption("Alta de un registro por vez con soporte para fotos e imágenes. Para editar en lote usa 🗂️ Administrar Datos.")

# Directorio de almacenamiento de imágenes cargadas localmente
UPLOADS_DIR = Path(__file__).resolve().parents[1] / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)

tipo = st.selectbox(
    "¿Qué querés agregar?",
    ["📦 Producto", "🏷️ Categoría", "🚚 Proveedor", "👤 Cliente", "🧑‍💼 Empleado"],
)

if tipo == "📦 Producto":
    with get_session() as session:
        categorias = {c.nombre: c.id for c in session.query(Categoria).order_by(Categoria.nombre).all()}
        proveedores = {p.nombre: p.id for p in session.query(Proveedor).order_by(Proveedor.nombre).all()}

    quick_add_proveedor(key_prefix="agregar_producto")

    with st.form("alta_producto", clear_on_submit=True):
        sku = st.text_input("SKU *")
        nombre = st.text_input("Nombre *")
        descripcion = st.text_input("Descripción")
        c1, c2 = st.columns(2)
        categoria = c1.selectbox("Categoría", options=list(categorias.keys()) or ["(sin categorías)"])
        proveedor = c2.selectbox("Proveedor", options=list(proveedores.keys()) or ["(sin proveedores)"])
        c3, c4 = st.columns(2)
        precio_costo = c3.number_input("Precio costo (MXN)", min_value=0.0, step=100.0)
        precio_venta = c4.number_input("Precio venta (MXN)", min_value=0.0, step=100.0)
        c5, c6 = st.columns(2)
        stock_actual = c5.number_input("Stock actual", min_value=0, step=1)
        stock_minimo = c6.number_input("Stock mínimo", min_value=0, step=1)
        
        st.markdown("##### 📷 Imagen / Foto del Producto")
        foto_subida = st.file_uploader("Subir archivo de imagen (JPG, PNG, WEBP)", type=["jpg", "jpeg", "png", "webp"])
        imagen_url_externa = st.text_input("O pegar URL directa de imagen (opcional)", placeholder="https://ejemplo.com/foto.jpg")
        
        enviado = st.form_submit_button("💾 Guardar producto")

    if enviado:
        if not sku or not nombre:
            st.error("SKU y Nombre son obligatorios.")
        else:
            final_img_path = None
            if foto_subida is not None:
                # Guardar archivo subido localmente con nombre seguro basado en SKU
                ext = Path(foto_subida.name).suffix or ".jpg"
                clean_sku = "".join(c for c in sku if c.isalnum() or c in "-_")
                nombre_archivo = f"{clean_sku}{ext}"
                destino = UPLOADS_DIR / nombre_archivo
                with open(destino, "wb") as f:
                    f.write(foto_subida.getbuffer())
                final_img_path = str(destino)
            elif imagen_url_externa.strip():
                final_img_path = imagen_url_externa.strip()

            with get_session() as session:
                session.add(
                    Producto(
                        sku=sku,
                        nombre=nombre,
                        descripcion=descripcion or None,
                        categoria_id=categorias.get(categoria),
                        proveedor_id=proveedores.get(proveedor),
                        precio_costo=precio_costo,
                        precio_venta=precio_venta,
                        stock_actual=int(stock_actual),
                        stock_minimo=int(stock_minimo),
                        imagen_url=final_img_path,
                    )
                )
                session.commit()
            st.success(f"Producto '{nombre}' agregado correctamente con su imagen.")


elif tipo == "🏷️ Categoría":
    with st.form("alta_categoria", clear_on_submit=True):
        nombre = st.text_input("Nombre *")
        descripcion = st.text_input("Descripción")
        enviado = st.form_submit_button("💾 Guardar categoría")

    if enviado:
        if not nombre:
            st.error("El nombre es obligatorio.")
        else:
            with get_session() as session:
                session.add(Categoria(nombre=nombre, descripcion=descripcion or None))
                session.commit()
            st.success(f"Categoría '{nombre}' agregada correctamente.")

elif tipo == "🚚 Proveedor":
    with st.form("alta_proveedor", clear_on_submit=True):
        nombre = st.text_input("Nombre *")
        telefono = st.text_input("Teléfono")
        email = st.text_input("Email")
        enviado = st.form_submit_button("💾 Guardar proveedor")

    if enviado:
        if not nombre:
            st.error("El nombre es obligatorio.")
        else:
            with get_session() as session:
                session.add(Proveedor(nombre=nombre, telefono=telefono or None, email=email or None))
                session.commit()
            st.success(f"Proveedor '{nombre}' agregado correctamente.")

elif tipo == "👤 Cliente":
    with st.form("alta_cliente", clear_on_submit=True):
        nombre = st.text_input("Nombre *")
        telefono = st.text_input("Teléfono")
        email = st.text_input("Email")
        enviado = st.form_submit_button("💾 Guardar cliente")

    if enviado:
        if not nombre:
            st.error("El nombre es obligatorio.")
        else:
            with get_session() as session:
                session.add(Cliente(nombre=nombre, telefono=telefono or None, email=email or None))
                session.commit()
            st.success(f"Cliente '{nombre}' agregado correctamente.")

elif tipo == "🧑‍💼 Empleado":
    with st.form("alta_empleado", clear_on_submit=True):
        nombre = st.text_input("Nombre *")
        puesto = st.text_input("Puesto")
        enviado = st.form_submit_button("💾 Guardar empleado")

    if enviado:
        if not nombre:
            st.error("El nombre es obligatorio.")
        else:
            with get_session() as session:
                session.add(Empleado(nombre=nombre, puesto=puesto or None))
                session.commit()
            st.success(f"Empleado '{nombre}' agregado correctamente.")
