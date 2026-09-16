"""Panel de Control: gráficas interactivas con tooltips detallados, paleta azul petróleo y alertas tintilantes."""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import func
import streamlit as st

from src.auth import require_login
from src.db.connection import get_session
from src.db.models import Categoria, Cliente, DetalleVenta, Empleado, Producto, Venta
from src.ui import inject_css, format_mxn

st.set_page_config(page_title="Panel de Control - Ferretest", page_icon="📊", layout="wide")
require_login()
inject_css()

st.title("📊 Panel de Control & Analítica")
st.caption("Visualización de métricas en tiempo real con paleta oscura azul petróleo, alertas y tooltips interactivos.")

# -------------------------------------------------------------------------
# 1. CARGA DE DATOS DESDE POSTGRESQL
# -------------------------------------------------------------------------
with get_session() as session:
    productos_query = session.query(Producto).all()
    productos_data = [
        {
            "id": p.id,
            "sku": p.sku,
            "nombre": p.nombre,
            "categoria": p.categoria.nombre if p.categoria else "(sin categoría)",
            "stock_actual": p.stock_actual,
            "stock_minimo": p.stock_minimo,
            "precio_costo": float(p.precio_costo),
            "precio_venta": float(p.precio_venta),
            "margen": p.stock_actual - p.stock_minimo,
            "estado": (
                "🔴 CRÍTICO" if (p.stock_actual - p.stock_minimo) <= 0
                else "🟡 ADVERTENCIA" if (p.stock_actual - p.stock_minimo) <= 3
                else "🟢 NORMAL"
            ),
        }
        for p in productos_query
    ]

    ventas_query = (
        session.query(Venta.fecha, Venta.total, Cliente.nombre.label("cliente"))
        .outerjoin(Cliente, Cliente.id == Venta.cliente_id)
        .order_by(Venta.fecha)
        .all()
    )
    ventas_data = [
        {"fecha": v.fecha, "total": float(v.total), "cliente": v.cliente or "Consumidor Final"}
        for v in ventas_query
    ]

    top_prod_query = (
        session.query(
            Producto.sku,
            Producto.nombre,
            Producto.stock_actual,
            Producto.stock_minimo,
            func.sum(DetalleVenta.cantidad).label("unidades_vendidas"),
            func.sum(DetalleVenta.cantidad * DetalleVenta.precio_unitario).label("recaudado"),
        )
        .join(DetalleVenta, DetalleVenta.producto_id == Producto.id)
        .group_by(Producto.id, Producto.sku, Producto.nombre, Producto.stock_actual, Producto.stock_minimo)
        .all()
    )
    top_prod_data = [
        {
            "sku": tp.sku,
            "nombre": tp.nombre,
            "stock_actual": tp.stock_actual,
            "stock_minimo": tp.stock_minimo,
            "unidades_vendidas": int(tp.unidades_vendidas or 0),
            "recaudado": float(tp.recaudado or 0),
            "estado": (
                "🔴 CRÍTICO" if (tp.stock_actual - tp.stock_minimo) <= 0
                else "🟡 ADVERTENCIA" if (tp.stock_actual - tp.stock_minimo) <= 3
                else "🟢 NORMAL"
            ),
        }
        for tp in top_prod_query
    ]

df_prod = pd.DataFrame(productos_data)
df_ventas = pd.DataFrame(ventas_data)
df_top = pd.DataFrame(top_prod_data)

# -------------------------------------------------------------------------
# 2. SECCIÓN DE ALERTAS TINTILANTES / PULSANTES DE STOCK MÍNIMO
# -------------------------------------------------------------------------
st.subheader("🚨 Semáforo de Inventario & Alertas")

if not df_prod.empty:
    criticos = df_prod[df_prod["margen"] <= 0]
    cercanos = df_prod[(df_prod["margen"] > 0) & (df_prod["margen"] <= 3)]

    col_s1, col_s2, col_s3 = st.columns(3)
    col_s1.metric("🔴 En/Bajo el Mínimo", len(criticos))
    col_s2.metric("🟡 Próximos a Agotarse (≤3 u)", len(cercanos))
    col_s3.metric("📦 Total Productos en Catálogo", len(df_prod))

    # Banner animado tintilante para estado crítico
    if not criticos.empty:
        items_criticos_str = ", ".join([f"<b>{row['nombre']}</b> (Stock: {row['stock_actual']} / Min: {row['stock_minimo']})" for _, row in criticos.iterrows()])
        st.markdown(
            f"""
            <div class="alerta-pulsante-roja">
                <span style="font-size: 1.1rem; font-weight: bold; color: #FCA5A5;">⚠️ ALERTA CRÍTICA: PRODUCTOS EN O BAJO EL MÍNIMO</span><br>
                <span style="color: #FEE2E2;">Se requiere reabastecimiento urgente para: {items_criticos_str}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Banner animado tintilante para estado de advertencia
    if not cercanos.empty:
        items_cercanos_str = ", ".join([f"<b>{row['nombre']}</b> (Stock: {row['stock_actual']} / Min: {row['stock_minimo']})" for _, row in cercanos.iterrows()])
        st.markdown(
            f"""
            <div class="alerta-pulsante-amarilla">
                <span style="font-size: 1.05rem; font-weight: bold; color: #FDE047;">⚡ ADVERTENCIA: STOCK CERCANO AL MÍNIMO (Margen ≤ 3)</span><br>
                <span style="color: #FEF9C3;">Vigilar niveles para: {items_cercanos_str}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.divider()

# -------------------------------------------------------------------------
# 3. GRÁFICAS INTERACTIVAS (PLOTLY) CON PALETA AZUL PETRÓLEO Y TOOLTIPS
# -------------------------------------------------------------------------
st.subheader("📈 Gráficas Analíticas (Haz clic o pasa el cursor sobre las barras)")

# Configuración base de tema visual oscuro/azul petróleo para Plotly
_PLOTLY_THEME = dict(
    paper_bgcolor="#011A24",
    plot_bgcolor="#032B3A",
    font=dict(color="#F1F5F9", family="JetBrains Mono, Roboto Mono, monospace", size=12),
    xaxis=dict(gridcolor="#0B4F6C", zerolinecolor="#0B4F6C", tickfont=dict(color="#CBD5E1")),
    yaxis=dict(gridcolor="#0B4F6C", zerolinecolor="#0B4F6C", tickfont=dict(color="#CBD5E1")),
    margin=dict(l=40, r=30, t=50, b=40),
)

col_g1, col_g2 = st.columns(2)

# --- GRÁFICA 1: STOCK POR CATEGORÍA ---
with col_g1:
    st.markdown("##### 📦 Stock Disponible por Categoría")
    if not df_prod.empty:
        stock_cat = (
            df_prod.groupby("categoria", as_index=False)
            .agg(
                stock_total=("stock_actual", "sum"),
                cant_productos=("id", "count"),
                alertas_criticas=("margen", lambda m: (m <= 0).sum()),
            )
            .sort_values("stock_total", ascending=False)
        )

        # Gráfico de barras con tooltips enriquecidos
        fig_cat = go.Figure(
            data=[
                go.Bar(
                    x=stock_cat["categoria"],
                    y=stock_cat["stock_total"],
                    marker=dict(
                        color=stock_cat["stock_total"],
                        colorscale=[[0, "#0284C7"], [0.5, "#00D2FF"], [1, "#38BDF8"]],
                        line=dict(color="#00E5FF", width=1.5),
                    ),
                    # Tooltip personalizado al pasar el cursor (Hovertemplate)
                    hovertemplate=(
                        "<b>🏷️ Categoría: %{x}</b><br>"
                        "📊 Stock Total: <b>%{y} unidades</b><br>"
                        "📦 Variedad de Productos: %{customdata[0]} items<br>"
                        "⚠️ Alertas Críticas: %{customdata[1]} productos<br>"
                        "<extra></extra>"
                    ),
                    customdata=stock_cat[["cant_productos", "alertas_criticas"]].values,
                )
            ]
        )
        fig_cat.update_layout(**_PLOTLY_THEME)
        fig_cat.update_layout(xaxis_title="Categoría", yaxis_title="Unidades en Inventario")
        st.plotly_chart(fig_cat, use_container_width=True, key="chart_categorias")
    else:
        st.info("Sin datos de inventario.")

# --- GRÁFICA 2: EVOLUCIÓN TEMPORAL DE VENTAS ---
with col_g2:
    st.markdown("##### 💵 Evolución de Ventas por Día (MXN)")
    if not df_ventas.empty:
        df_ventas["dia"] = pd.to_datetime(df_ventas["fecha"]).dt.date
        ventas_dia = (
            df_ventas.groupby("dia", as_index=False)
            .agg(
                total_dia=("total", "sum"),
                n_ventas=("total", "count"),
            )
            .sort_values("dia")
        )

        fig_ventas = go.Figure(
            data=[
                go.Scatter(
                    x=ventas_dia["dia"],
                    y=ventas_dia["total_dia"],
                    mode="lines+markers",
                    line=dict(color="#00E5FF", width=3),
                    marker=dict(size=9, color="#FFFFFF", line=dict(color="#00D2FF", width=2)),
                    # Tooltip personalizado para la curva de ventas
                    hovertemplate=(
                        "<b>📅 Fecha: %{x}</b><br>"
                        "💰 Recaudación: <b>$ %{y:,.2f} MXN</b><br>"
                        "🧾 Tickets emitidos: %{customdata[0]} ventas<br>"
                        "<extra></extra>"
                    ),
                    customdata=ventas_dia[["n_ventas"]].values,
                )
            ]
        )
        fig_ventas.update_layout(**_PLOTLY_THEME)
        fig_ventas.update_layout(xaxis_title="Fecha", yaxis_title="Monto Vendido (MXN)")
        st.plotly_chart(fig_ventas, use_container_width=True, key="chart_ventas")
    else:
        st.info("Sin ventas registradas.")

# -------------------------------------------------------------------------
# 4. GRÁFICA 3: TOP PRODUCTOS CON DETALLE POR SELECCIÓN / CLIC
# -------------------------------------------------------------------------
st.markdown("##### 🏆 Top Productos Más Vendidos & Estado de Stock")
st.caption("Las barras rojas indican productos de alta rotación con stock crítico o al límite.")

if not df_top.empty:
    df_top_sorted = df_top.sort_values("unidades_vendidas", ascending=True).tail(10)
    
    # Asignar colores según nivel de criticidad
    colores_barra = [
        "#EF4444" if est == "🔴 CRÍTICO" else "#EAB308" if est == "🟡 ADVERTENCIA" else "#00D2FF"
        for est in df_top_sorted["estado"]
    ]

    fig_top = go.Figure(
        data=[
            go.Bar(
                y=df_top_sorted["nombre"],
                x=df_top_sorted["unidades_vendidas"],
                orientation="h",
                marker=dict(
                    color=colores_barra,
                    line=dict(color="#FFFFFF", width=1),
                ),
                # Tooltip con desglose completo del producto
                hovertemplate=(
                    "<b>🛠️ Producto: %{y}</b><br>"
                    "📦 SKU: %{customdata[0]}<br>"
                    "🔥 Unidades Vendidas: <b>%{x}</b><br>"
                    "💵 Total Recaudado: <b>$ %{customdata[1]:,.2f} MXN</b><br>"
                    "📊 Stock Actual: <b>%{customdata[2]}</b> (Mínimo: %{customdata[3]})<br>"
                    "🚦 Estado: <b>%{customdata[4]}</b><br>"
                    "<extra></extra>"
                ),
                customdata=df_top_sorted[["sku", "recaudado", "stock_actual", "stock_minimo", "estado"]].values,
            )
        ]
    )
    fig_top.update_layout(**_PLOTLY_THEME)
    fig_top.update_layout(xaxis_title="Unidades Vendidas", yaxis_title="Producto")
    st.plotly_chart(fig_top, use_container_width=True, key="chart_top_productos")

    # Selector interactivo para inspección detallada de un producto
    st.markdown("###### 🔍 Ficha de Detalle por Producto Seleccionado")
    prod_sel_nombre = st.selectbox(
        "Selecciona un producto para consultar su ficha técnica y niveles de advertencia:",
        options=df_top_sorted["nombre"].tolist()[::-1],
    )
    
    if prod_sel_nombre:
        info_sel = df_top[df_top["nombre"] == prod_sel_nombre].iloc[0]
        c_i1, c_i2, c_i3, c_i4 = st.columns(4)
        c_i1.metric("SKU", info_sel["sku"])
        c_i2.metric("Unidades Vendidas", info_sel["unidades_vendidas"])
        c_i3.metric("Stock Actual / Mínimo", f"{info_sel['stock_actual']} / {info_sel['stock_minimo']}")
        c_i4.metric("Estado", info_sel["estado"])
        
        if info_sel["stock_actual"] <= info_sel["stock_minimo"]:
            st.error(f"⚠️ **Atención:** `{info_sel['nombre']}` tiene alta demanda pero solo quedan **{info_sel['stock_actual']} unidades** (mínimo establecido: {info_sel['stock_minimo']}). Se sugiere emitir orden de compra inmediata.")

