# data_access/data_connection.py

"""
Maneja la conexión a la base de datos PostgreSQL,
usando dataclasses para credenciales y typing para Engine.
"""

import logging
from dataclasses import dataclass
from typing import Optional
from sqlalchemy.engine import Engine
from sqlalchemy import create_engine

logger = logging.getLogger(__name__)

@dataclass
class DatabaseCredentials:
    """
    Representa las credenciales y parámetros necesarios
    para conectarse a la base de datos PostgreSQL.
    """
    host: str
    port: int
    database: str
    user: str
    password: str

class DatabaseConnectionManager:
    """
    Maneja la creación de un Engine de SQLAlchemy para conectarse a PostgreSQL.
    Soporta credenciales individuales o DATABASE_URI directa.
    """

    def __init__(self, credentials: DatabaseCredentials = None, database_uri: str = None) -> None:
        self.credentials = credentials
        self.database_uri = database_uri
        self._engine: Optional[Engine] = None

    def get_engine(self) -> Engine:
        if not self._engine:
            try:
                logger.info("Creando nuevo Engine de SQLAlchemy...")
                if self.database_uri:
                    uri = self.database_uri
                else:
                    c = self.credentials
                    uri = (f"postgresql://{c.user}:{c.password}"
                           f"@{c.host}:{c.port}/{c.database}?sslmode=require")
                self._engine = create_engine(
                    uri, pool_pre_ping=True, pool_recycle=300
                )
            except Exception as ex:
                logger.error(f"Error creando el Engine de SQLAlchemy: {ex}")
                raise RuntimeError("No se pudo crear el Engine de SQLAlchemy.") from ex
        return self._engine