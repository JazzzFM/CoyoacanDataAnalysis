from dataclasses import dataclass
from typing import Dict
import logging
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import geopandas as gpd
from sqlalchemy import create_engine
from app import DashApp
from data_loader import DataLoader
from data_processor import DataProcessor
from logging_config import configure_logging

@dataclass
class DatabaseConfig:
    user: str
    password: str
    host: str
    port: int
    database: str

@dataclass
class AppConfig:
    db_config: 'DatabaseConfig'
    table_name: str

class Main:
    def __init__(self, config: AppConfig):
        self.config = config
        self.logger = configure_logging()
        self.data_loader = DataLoader(
            db_config=self.config.db_config,
            table_name=self.config.table_name,
            logger=self.logger
        )
        self.processor = DataProcessor(self.logger)
        self.app = DashApp(self.data_loader, self.processor, self.logger)

if __name__ == "__main__":
    logger = configure_logging()

    # Crear configuración como un objeto de clase
    app_config = AppConfig(
        db_config=DatabaseConfig(
            user="developer",
            password="MelonSK998",
            host="localhost",
            port=5432,
            database="Poligonos"
        ),
        table_name="datos_demograficos_coyoacan"
    )

    logger.info("Iniciando la aplicación principal.")
    try:
        main_app = Main(config=app_config)
        main_app.run()
    except Exception as e:
        logger.error(f"Error al ejecutar la aplicación: {e}")