"""Cola local (offline-first) para ventas cuando Postgres no está disponible.

Cada dispositivo guarda sus ventas pendientes en un SQLite local
(data/offline_queue.sqlite3). Cuando vuelve la conexión, `sync_pending()`
las inserta en PostgreSQL en el mismo orden en que se generaron y las
marca como sincronizadas. Sirve para casos de corte de luz/red durante
el cobro en el comercio.
"""
import json
import sqlite3
from datetime import datetime
from pathlib import Path

from src.db.connection import SessionLocal, is_db_available
from src.db.models import DetalleVenta, Venta

QUEUE_DIR = Path(__file__).resolve().parents[2] / "data"
QUEUE_PATH = QUEUE_DIR / "offline_queue.sqlite3"


def _get_conn() -> sqlite3.Connection:
    QUEUE_DIR.mkdir(exist_ok=True)
    conn = sqlite3.connect(QUEUE_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS ventas_pendientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            payload TEXT NOT NULL,
            creado_en TEXT NOT NULL,
            sincronizado INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    return conn


def enqueue_venta(cliente_id, empleado_id, items: list[dict], fecha=None) -> int:
    """Guarda una venta localmente. `items` es una lista de
    {"producto_id": int, "cantidad": int, "precio_unitario": float}."""
    payload = {
        "cliente_id": cliente_id,
        "empleado_id": empleado_id,
        "items": items,
        "fecha": (fecha or datetime.now()).isoformat(),
    }
    conn = _get_conn()
    try:
        cur = conn.execute(
            "INSERT INTO ventas_pendientes (payload, creado_en) VALUES (?, ?)",
            (json.dumps(payload), datetime.now().isoformat()),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def count_pending() -> int:
    conn = _get_conn()
    try:
        row = conn.execute(
            "SELECT COUNT(*) FROM ventas_pendientes WHERE sincronizado = 0"
        ).fetchone()
        return row[0] if row else 0
    finally:
        conn.close()


def sync_pending() -> tuple[int, int]:
    """Intenta insertar en PostgreSQL todas las ventas pendientes.

    Devuelve (sincronizadas, fallidas).
    """
    if not is_db_available():
        return 0, count_pending()

    conn = _get_conn()
    try:
        pendientes = conn.execute(
            "SELECT id, payload FROM ventas_pendientes WHERE sincronizado = 0 ORDER BY id"
        ).fetchall()
    finally:
        conn.close()

    ok, fallidas = 0, 0
    with SessionLocal() as session:
        for row_id, payload_json in pendientes:
            payload = json.loads(payload_json)
            try:
                venta = Venta(
                    fecha=datetime.fromisoformat(payload["fecha"]),
                    cliente_id=payload["cliente_id"],
                    empleado_id=payload["empleado_id"],
                    total=sum(i["cantidad"] * i["precio_unitario"] for i in payload["items"]),
                )
                session.add(venta)
                session.flush()
                for item in payload["items"]:
                    session.add(
                        DetalleVenta(
                            venta_id=venta.id,
                            producto_id=item["producto_id"],
                            cantidad=item["cantidad"],
                            precio_unitario=item["precio_unitario"],
                        )
                    )
                    prod = session.get(Producto, item["producto_id"])
                    if prod:
                        prod.stock_actual = max(0, prod.stock_actual - item["cantidad"])
                session.commit()
                _mark_synced(row_id)
                ok += 1
            except Exception:
                session.rollback()
                fallidas += 1

    return ok, fallidas


def _mark_synced(row_id: int) -> None:
    conn = _get_conn()
    try:
        conn.execute(
            "UPDATE ventas_pendientes SET sincronizado = 1 WHERE id = ?", (row_id,)
        )
        conn.commit()
    finally:
        conn.close()
