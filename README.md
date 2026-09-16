# Ferretest

Proyecto de práctica para aprender **análisis de datos** construyendo una interfaz web (usable desde una tableta Android vía navegador) para una ferretería ficticia. Conecta a **PostgreSQL** y usa **Streamlit + Pandas + SQLAlchemy**.

La base de datos parte **vacía**: iremos agregando tablas, datos y consultas a medida que aprendemos el vocabulario y las tareas típicas de un analista de datos.

## Stack

- **Python 3.11+**
- **Streamlit** – interfaz web (funciona en el navegador de la tableta apuntando a la IP de la PC en la red local)
- **Pandas** – manipulación y análisis de datos
- **SQLAlchemy** – ORM / acceso a la base de datos
- **PostgreSQL** – motor de base de datos
- **psycopg2-binary** – driver de PostgreSQL
- **python-dotenv** – manejo de variables de entorno
- **Plotly** – gráficos interactivos

## Estructura del proyecto

```
Ferretest/
├── app.py                  # App principal de Streamlit
├── requirements.txt
├── .env.example             # Variables de entorno de ejemplo (copiar a .env)
├── .streamlit/config.toml   # Configuración de Streamlit (tema, server)
├── scripts/
│   └── init_db.py           # Crea las tablas en PostgreSQL
└── src/
    └── db/
        ├── connection.py     # Conexión SQLAlchemy (engine, session)
        └── models.py         # Modelos ORM (esquema de la ferretería)
```

## Modelo de datos (inicial, vacío)

| Tabla                    | Descripción                                   |
|---------------------------|-----------------------------------------------|
| `categorias`              | Categorías de productos (herramientas, pintura, etc.) |
| `proveedores`              | Proveedores de la ferretería                   |
| `productos`                | Catálogo de productos (SKU, precios, stock)    |
| `clientes`                  | Clientes registrados                           |
| `empleados`                 | Empleados / vendedores                         |
| `ventas`                    | Cabecera de cada venta                         |
| `detalle_ventas`            | Ítems de cada venta                            |
| `movimientos_inventario`    | Entradas/salidas/ajustes de stock              |

Este esquema es un punto de partida: se puede modificar, ampliar o normalizar distinto a medida que avancemos.

## Puesta en marcha

1. **Instalar PostgreSQL** y crear la base de datos:
   ```sql
   CREATE DATABASE ferretest;
   ```
2. **Crear entorno virtual e instalar dependencias**
   ```powershell
   cd C:\Users\campo\Ferretest
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```
3. **Configurar variables de entorno**
   ```powershell
   copy .env.example .env
   # editar .env con usuario/contraseña reales de PostgreSQL
   ```
4. **Crear las tablas (base vacía)**
   ```powershell
   python scripts/init_db.py
   ```
5. **Cargar datos de prueba**
   ```powershell
   python scripts/seed_data.py
   ```
6. **Ejecutar la app**
   ```powershell
   streamlit run app.py
   ```
7. **Acceder desde la tableta Android**: con la PC y la tableta en la misma red WiFi, abrir en el navegador de la tableta `http://<IP-de-tu-PC>:8501` (Streamlit corre en el puerto 8501 por defecto). Podés obtener la IP con `ipconfig`.

## Vocabulario básico de analista de datos (a ir completando)

- **ETL**: Extract, Transform, Load — extraer datos de una fuente, transformarlos y cargarlos en otro destino.
- **Query / consulta SQL**: instrucción para leer o modificar datos en la base.
- **Dataset / dataframe**: conjunto de datos tabulares (filas y columnas), en Pandas se maneja como `DataFrame`.
- **KPI**: Key Performance Indicator, indicador clave de desempeño (ej: ventas del mes, ticket promedio).
- **Esquema (schema)**: estructura de tablas, columnas y relaciones de una base de datos.
- **Clave primaria / foránea (PK/FK)**: identificador único de una fila / referencia a otra tabla.
- **Normalización**: organizar tablas para evitar datos duplicados.
- **Join**: combinar filas de dos o más tablas según una relación.
- **Agregación**: operaciones como `SUM`, `COUNT`, `AVG` sobre grupos de datos (`GROUP BY`).
- **Dashboard**: panel visual con gráficos e indicadores para tomar decisiones.
- **Stock / inventario**: cantidad disponible de un producto.
- *(seguir agregando términos a medida que aparezcan)*

## Roadmap / tareas de aprendizaje

### Fase 0 – Entorno
- [x] Crear estructura del proyecto
- [x] Instalar PostgreSQL localmente y crear la base `ferretest`
- [x] Crear entorno virtual e instalar `requirements.txt`
- [x] Ejecutar `scripts/init_db.py` y verificar que las tablas se crean

### Fase 1 – Datos de prueba
- [x] Insertar categorías y proveedores de ejemplo
- [x] Insertar 15-20 productos de ferretería con precios y stock
- [x] Insertar algunos clientes y empleados
- [x] Generar ventas de ejemplo (`scripts/seed_data.py`, no requiere `Faker`)

### Fase 2 – Consultas SQL básicas
- [ ] Escribir consultas `SELECT` simples (todos los productos, productos con bajo stock)
- [ ] Practicar `WHERE`, `ORDER BY`, `LIMIT`
- [ ] Practicar `JOIN` entre `ventas`, `detalle_ventas` y `productos`
- [ ] Practicar `GROUP BY` + `SUM`/`COUNT` (ventas por categoría, por día)

### Fase 3 – Análisis con Pandas
- [ ] Leer tablas de PostgreSQL a un `DataFrame` con `pandas.read_sql`
- [ ] Calcular KPIs: ventas totales, ticket promedio, producto más vendido
- [ ] Detectar productos con stock bajo el mínimo
- [ ] Análisis de ventas por período (día/semana/mes)

### Fase 4 – Visualización en Streamlit
- [ ] Página de listado de productos con filtros (categoría, stock bajo)
- [ ] Página de ventas con gráfico de evolución (Plotly)
- [ ] Página de indicadores (KPIs) tipo dashboard
- [ ] Formulario para cargar nuevas ventas/productos desde la interfaz

### Fase 5 – Uso en tableta / mejoras
- [ ] Probar acceso desde la tableta Android en la red local
- [ ] Ajustar diseño para pantallas táctiles (botones grandes, columnas responsive)
- [ ] Agregar autenticación básica si se desea
- [ ] Explorar despliegue (Streamlit Community Cloud, Docker, etc.)

## Notas

- Este README y el esquema de datos se irán actualizando a medida que el proyecto evolucione; no hay datos reales, todo es un entorno de práctica.
