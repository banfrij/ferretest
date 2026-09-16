"""Crea las tablas en PostgreSQL a partir de los modelos (base vacía)."""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.db.connection import engine
from src.db.models import Base

if __name__ == "__main__":
    Base.metadata.create_all(engine)
    print("Tablas creadas correctamente en la base de datos 'ferretest'.")
