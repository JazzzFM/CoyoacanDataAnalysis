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
    SRP: única responsabilidad: crear y mantener la conexión a la base de datos.
    """

    def __init__(self, credentials: DatabaseCredentials) -> None:
        """
        :param credentials: Datos de host, port, db, user, password
        """
        self.credentials: DatabaseCredentials = credentials
        self._engine: Optional[Engine] = None

    def get_engine(self) -> Engine:
        """
        Retorna un Engine de SQLAlchemy. Si ya existe, lo reutiliza.
        
        :raises RuntimeError: Si no se puede crear el engine.
        """
        if not self._engine:
            try:
                logger.info("Creando nuevo Engine de SQLAlchemy...")
                self._engine = create_engine(
                    f"postgresql://{self.credentials.user}:{self.credentials.password}"
                    f"@{self.credentials.host}:{self.credentials.port}/{self.credentials.database}"
                )
            except Exception as ex:
                logger.error(f"Error creando el Engine de SQLAlchemy: {ex}")
                raise RuntimeError("No se pudo crear el Engine de SQLAlchemy.") from ex

        return self._engine