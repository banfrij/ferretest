"""Punto de entrada de la app Streamlit - Ferretest (Home / Dashboard)."""
from datetime import date, timedelta
import time
import pandas as pd
from sqlalchemy import func
import streamlit as st

from src.auth import require_login
from src.db import offline_queue
from src.db.connection import get_session, is_db_available
from src.db.models import Producto, Venta
from src.ui import inject_css, format_mxn

st.set_page_config(page_title="Ferretest", page_icon="🛠️", layout="wide")
require_login()
inject_css()

st.title("🛠️ Ferretest - Panel de Ferretería")
st.caption("Proyecto de práctica: análisis de datos con Streamlit + PostgreSQL")
st.info("Usa el menú de la izquierda: **📊 Panel de Control** (gráficas y alertas), **🗂️ Administrar Datos**, **➕ Agregar Datos** o **🧾 Caja**.")

st.divider()

# --- Consultas de ventas: Hoy, Ayer, Antier e Histórico ---
hoy = date.today()
ayer = hoy - timedelta(days=1)
antier = hoy - timedelta(days=2)

ventas_hoy_total = 0.0
ventas_hoy_cant = 0
ventas_ayer_total = 0.0
ventas_ayer_cant = 0
ventas_antier_total = 0.0
ventas_antier_cant = 0
total_historico = 0.0
n_productos = 0
stock_bajo = 0
n_ventas_total = 0

try:
    with get_session() as session:
        n_productos = session.query(Producto).count()
        stock_bajo = session.query(Producto).filter(Producto.stock_actual <= Producto.stock_minimo).count()
        n_ventas_total = session.query(Venta).count()
        
        # Agrupación de ventas por día
        ventas_por_fecha = (
            session.query(
                func.date(Venta.fecha),
                func.count(Venta.id),
                func.sum(Venta.total)
            )
            .group_by(func.date(Venta.fecha))
            .all()
        )
        
        for f_date, cant, suma in ventas_por_fecha:
            monto = float(suma or 0)
            if f_date == hoy:
                ventas_hoy_total = monto
                ventas_hoy_cant = cant
            elif f_date == ayer:
                ventas_ayer_total = monto
                ventas_ayer_cant = cant
            elif f_date == antier:
                ventas_antier_total = monto
                ventas_antier_cant = cant
            total_historico += monto

except Exception as e:
    st.error(f"No se pudo conectar a la base de datos: {e}")
    st.info("Revisa tu archivo .env y que PostgreSQL esté corriendo.")

# --- Definición de Ventana Modal (Dialog) ---
@st.dialog("📋 Resumen Ejecutivo Inicial", width="large")
def mostrar_modal_resumen():
    st.markdown("#### 🔩 Estado Rápido de la Ferretería")
    st.caption("Esta ventana emergente muestra los datos clave al ingresar. Puedes cerrarla con la 'X' o el botón inferior.")
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Ventas Hoy", format_mxn(ventas_hoy_total), help=f"{ventas_hoy_cant} ventas registradas hoy")
    m2.metric("Ventas Ayer", format_mxn(ventas_ayer_total), help=f"{ventas_ayer_cant} ventas registradas ayer")
    m3.metric("Ventas Antier", format_mxn(ventas_antier_total), help=f"{ventas_antier_cant} ventas registradas antier")
    
    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    c1.metric("📦 Productos Activos", n_productos)
    c2.metric("🚨 Stock Bajo", stock_bajo)
    c3.metric("💰 Total Histórico", format_mxn(total_historico))
    
    if st.button("Cerrar Resumen", type="primary", use_container_width=True):
        st.rerun()

# Abrir el modal solo 1 vez al iniciar sesión en un periodo de 1 hora (3600 seg)
ahora = time.time()
ultimo_despliegue = st.session_state.get("modal_ultimo_despliegue", 0)
if ahora - ultimo_despliegue >= 3600:
    st.session_state.modal_ultimo_despliegue = ahora
    mostrar_modal_resumen()

st.subheader("💵 Balance de Ventas Recientes")

# Métricas en el cuerpo del Home
col_hoy, col_ayer, col_antier, col_tot = st.columns(4)
col_hoy.metric(
    "📅 Ventas Hoy",
    format_mxn(ventas_hoy_total),
    delta="0 ventas" if ventas_hoy_cant == 0 else f"{ventas_hoy_cant} ventas",
    delta_color="off"
)
col_ayer.metric(
    "⏮️ Ventas Ayer",
    format_mxn(ventas_ayer_total),
    delta=f"{ventas_ayer_cant} ventas",
    delta_color="off"
)
col_antier.metric(
    "⏪ Ventas Antier",
    format_mxn(ventas_antier_total),
    delta=f"{ventas_antier_cant} ventas",
    delta_color="off"
)
col_tot.metric(
    "🏛️ Total Histórico",
    format_mxn(total_historico),
    delta=f"{n_ventas_total} ventas",
    delta_color="off"
)

st.divider()
st.subheader("📦 Catálogo de Productos")
try:
    with get_session() as session:
        productos = session.query(Producto).all()
        df = pd.DataFrame(
            [
                {
                    "SKU": p.sku,
                    "Nombre": p.nombre,
                    "Categoría": p.categoria.nombre if p.categoria else None,
                    "Stock": p.stock_actual,
                    "Precio venta (MXN)": float(p.precio_venta),
                }
                for p in productos
            ]
        )
    if df.empty:
        st.info("La base de datos está vacía. Ejecuta scripts/init_db.py y carga datos de prueba.")
    else:
        st.dataframe(df, use_container_width=True)
except Exception as e:
    st.error(f"No se pudo conectar a la base de datos: {e}")
    st.info("Revisa tu archivo .env y que PostgreSQL esté corriendo.")

# --- Sección de Conocimiento: Glosario de Estadística Industrial & Manual por Estación ---
st.divider()
with st.expander("📖 Glosario de Estadística Industrial & Guía Técnica de Estaciones", expanded=False):
    tab_glo, tab_est = st.tabs(["📚 Glosario de Estadística Industrial", "⚙️ Guía de Comandos por Estación"])
    
    with tab_glo:
        st.markdown(
            """
            #### 📊 Vocabulario y Métricas Clave de Analítica Industrial & Retail
            - **KPI (Key Performance Indicator):** Indicador cuantitativo de desempeño para evaluar el rendimiento operativo y comercial del negocio.
            - **Stock de Seguridad (Safety Stock - $SS$):** Nivel de amortiguación de inventario para absorber variaciones imprevistas en la demanda o retrasos de proveedores.
            - **Punto de Reorden (ROP - Reorder Point):** Umbral de inventario ($ROP = \text{Demanda Promedio} \times \text{Lead Time} + SS$) que dispara una orden de reposición antes de llegar al desabastecimiento.
            - **Tasa de Desabastecimiento (Stockout Rate):** Porcentaje de transacciones o SKUs que no pudieron ser surtidos por falta de disponibilidad.
            - **Rotación de Inventario (Inventory Turnover):** Veces que el inventario se renueva en un período determinado ($\frac{\text{Costo de Mercancías Vendidas}}{\text{Inventario Promedio}}$).
            - **Margen de Contribución Unitario:** Ganancia directa generada por cada unidad vendida ($\text{Precio de Venta} - \text{Precio de Costo}$).
            - **Clasificación ABC (Principio de Pareto 80/20):** Segmentación del catálogo donde los productos tipo **A** (~20% de los SKUs) concentran el ~80% de los ingresos.
            - **ETL (Extract, Transform, Load):** Flujo de extracción de datos transaccionales, transformación estructurada (vía Pandas) y carga en dashboards analíticos.
            """
        )
    
    with tab_est:
        st.markdown(
            """
            #### 🔩 Arquitectura y Comandos Ejecutados por Estación
            
            1. **🏠 Estación Principal (`app.py`):**
               - *Función:* Balance temporalizado (Ventas Hoy, Ayer, Antier e Histórico), catálogo general y control de conectividad.
               - *Comando SQL / ORM:*
                 ```sql
                 SELECT DATE(fecha), COUNT(id), SUM(total) FROM ventas GROUP BY DATE(fecha);
                 ```
            
            2. **📊 Estación Panel de Control (`pages/0_📊_Panel_de_Control.py`):**
               - *Función:* Semáforo de advertencias tintilantes en CSS, gráficas de dispersión temporal y Pareto de productos críticos con tooltips interactivos.
               - *Comando SQL / ORM:*
                 ```sql
                 SELECT p.sku, p.nombre, p.stock_actual, p.stock_minimo, SUM(d.cantidad) AS vendidos
                 FROM productos p JOIN detalle_ventas d ON d.producto_id = p.id
                 GROUP BY p.id;
                 ```
            
            3. **🗂️ Estación Administrar Datos (`pages/1_🗂️_Administrar_Datos.py`):**
               - *Función:* CRUD bidireccional en lote (`st.data_editor`) y galería de imágenes por tamaño de visualización (Iconos, Grande, Extra grande).
               - *Comando SQL / ORM:*
                 ```python
                 session.query(Producto).order_by(Producto.sku).all()
                 session.delete(obj) / session.commit()
                 ```
            
            4. **🧾 Estación Caja / Punto de Venta (`pages/2_🧾_Caja.py`):**
               - *Función:* Carrito de cobro con deducción de stock atómica y cola de contingencia local en SQLite (`offline_queue.py`) ante cortes de red/luz.
               - *Comando SQL / ORM:*
                 ```sql
                 BEGIN;
                 INSERT INTO ventas (cliente_id, empleado_id, total) VALUES (...);
                 INSERT INTO detalle_ventas (venta_id, producto_id, cantidad, precio_unitario) VALUES (...);
                 UPDATE productos SET stock_actual = stock_actual - :cantidad WHERE id = :producto_id;
                 COMMIT;
                 ```
            
            5. **➕ Estación Agregar Datos (`pages/3_➕_Agregar_Datos.py`):**
               - *Función:* Alta modular de registros individuales con soporte para subida de fotos locales (`uploads/`) o URLs externas.
               - *Comando SQL / ORM:*
                 ```sql
                 INSERT INTO productos (sku, nombre, precio_costo, precio_venta, stock_actual, stock_minimo, imagen_url, categoria_id, proveedor_id) VALUES (...);
                 ```
            """
        )

# --- Pie de página: Estado de conexión y sincronización ---
st.divider()
db_ok = is_db_available()
pendientes = offline_queue.count_pending()
col_pie_a, col_pie_b = st.columns([3, 1])
with col_pie_a:
    if db_ok:
        st.success("Conectado a PostgreSQL")
    else:
        st.error("Sin conexión a PostgreSQL. Las ventas se guardarán localmente.")
with col_pie_b:
    if pendientes:
        st.warning(f"{pendientes} venta(s) pendiente(s) de sincronizar")
        if db_ok and st.button("Sincronizar ahora"):
            ok, fallidas = offline_queue.sync_pending()
            st.toast(f"Sincronizadas: {ok} / Fallidas: {fallidas}")
            st.rerun()



