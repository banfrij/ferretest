"""Carga datos de prueba en la base de datos (Fase 1 del roadmap)."""
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.db.connection import SessionLocal
from src.db.models import (
    Categoria,
    Cliente,
    DetalleVenta,
    Empleado,
    Producto,
    Proveedor,
    Venta,
)

CATEGORIAS = ["Herramientas manuales", "Herramientas eléctricas", "Pintura", "Plomería", "Electricidad", "Ferretería general"]

PROVEEDORES = [
    ("Distribuidora Norte", "011-4444-1111", "ventas@norte.com"),
    ("Bosch Argentina", "011-4444-2222", "contacto@bosch.com.ar"),
    ("Sherwin Williams", "011-4444-3333", "pedidos@sherwin.com"),
]

PRODUCTOS = [
    ("HM-001", "Martillo carpintero 16oz", "Herramientas manuales", 3500, 6500, 40, 5),
    ("HM-002", "Destornillador Phillips", "Herramientas manuales", 800, 1600, 60, 10),
    ("HM-003", "Llave inglesa 10\"", "Herramientas manuales", 2500, 4800, 30, 5),
    ("HM-004", "Pinza universal 8\"", "Herramientas manuales", 2200, 4200, 25, 5),
    ("HE-001", "Taladro percutor 650W", "Herramientas eléctricas", 35000, 62000, 15, 3),
    ("HE-002", "Amoladora angular 4.5\"", "Herramientas eléctricas", 28000, 49000, 12, 3),
    ("HE-003", "Sierra circular 7 1/4\"", "Herramientas eléctricas", 45000, 78000, 8, 2),
    ("PT-001", "Pintura látex interior 20L", "Pintura", 30000, 52000, 20, 4),
    ("PT-002", "Esmalte sintético 1L", "Pintura", 4500, 8500, 35, 5),
    ("PT-003", "Rodillo + bandeja", "Pintura", 2200, 4200, 40, 8),
    ("PL-001", "Caño PVC 1/2\" x 3m", "Plomería", 1800, 3200, 50, 10),
    ("PL-002", "Llave de paso 1/2\"", "Plomería", 3200, 6000, 25, 5),
    ("PL-003", "Cinta teflón", "Plomería", 300, 700, 100, 20),
    ("EL-001", "Cable unipolar 2.5mm x 10m", "Electricidad", 4000, 7500, 40, 8),
    ("EL-002", "Toma corriente doble", "Electricidad", 900, 1900, 60, 10),
    ("EL-003", "Disyuntor diferencial 25A", "Electricidad", 8500, 15500, 15, 3),
    ("FG-001", "Cinta métrica 5m", "Ferretería general", 1500, 3000, 45, 8),
    ("FG-002", "Guantes de trabajo", "Ferretería general", 1200, 2500, 60, 10),
    ("FG-003", "Candado 40mm", "Ferretería general", 2800, 5200, 30, 5),
]

CLIENTES = [
    ("Juan Pérez", "011-5555-1111", "juan.perez@mail.com"),
    ("María González", "011-5555-2222", "maria.gonzalez@mail.com"),
    ("Carlos Rodríguez", "011-5555-3333", "carlos.rodriguez@mail.com"),
    ("Ana Fernández", "011-5555-4444", "ana.fernandez@mail.com"),
    ("Consumidor Final", None, None),
]

EMPLEADOS = [
    ("Lucía Martínez", "Vendedora"),
    ("Diego Sosa", "Vendedor"),
    ("Roberto Díaz", "Encargado"),
]


def seed():
    session = SessionLocal()
    try:
        if session.query(Categoria).count() > 0:
            print("La base ya tiene datos. No se insertó nada (evita duplicados).")
            return

        categorias = {nombre: Categoria(nombre=nombre) for nombre in CATEGORIAS}
        session.add_all(categorias.values())

        proveedores = [Proveedor(nombre=n, telefono=t, email=e) for n, t, e in PROVEEDORES]
        session.add_all(proveedores)
        session.flush()

        productos = []
        for sku, nombre, cat_nombre, costo, venta, stock, minimo in PRODUCTOS:
            productos.append(
                Producto(
                    sku=sku,
                    nombre=nombre,
                    categoria=categorias[cat_nombre],
                    proveedor=random.choice(proveedores),
                    precio_costo=costo,
                    precio_venta=venta,
                    stock_actual=stock,
                    stock_minimo=minimo,
                )
            )
        session.add_all(productos)

        clientes = [Cliente(nombre=n, telefono=t, email=e) for n, t, e in CLIENTES]
        session.add_all(clientes)

        empleados = [Empleado(nombre=n, puesto=p) for n, p in EMPLEADOS]
        session.add_all(empleados)
        session.flush()

        # Generar ventas de ejemplo de los últimos 30 días
        hoy = datetime.utcnow()
        for i in range(25):
            fecha = hoy - timedelta(days=random.randint(0, 30), hours=random.randint(0, 23))
            venta = Venta(
                fecha=fecha,
                total=0,
                cliente=random.choice(clientes),
                empleado=random.choice(empleados),
            )
            session.add(venta)
            session.flush()

            total = 0
            n_items = random.randint(1, 4)
            elegidos = random.sample(productos, n_items)
            for producto in elegidos:
                cantidad = random.randint(1, 5)
                precio_unitario = float(producto.precio_venta)
                total += cantidad * precio_unitario
                session.add(
                    DetalleVenta(
                        venta=venta,
                        producto=producto,
                        cantidad=cantidad,
                        precio_unitario=precio_unitario,
                    )
                )
            venta.total = total

        session.commit()
        print("Datos de prueba insertados correctamente.")
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    seed()
