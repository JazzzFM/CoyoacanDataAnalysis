# config/default.py

import os

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'default_secret_key')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URI', 'sqlite:///default.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DASH_PORT = int(os.getenv('DASH_PORT', 8050))
    # Agrega otras configuraciones según sea necesario

