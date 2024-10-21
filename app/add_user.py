from sqlalchemy import create_engine
from users import User, Base
from sqlalchemy.orm import sessionmaker
import os
from werkzeug.security import generate_password_hash

# Cargar variables de entorno
POSTGRES_USER = os.getenv('POSTGRES_USER')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
POSTGRES_DB = os.getenv('POSTGRES_DB')
DB_HOST = os.getenv('DB_HOST', 'localhost')
POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')

# Crear conexión a la base de datos
engine = create_engine(f'postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{DB_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

# Crear la tabla de usuarios si no existe
Base.metadata.create_all(engine)

# Función para agregar un usuario
def add_user(username, password):
    user = User(username=username)
    user.set_password(password)
    session.add(user)
    session.commit()
    print(f"Usuario {username} agregado correctamente.")

if __name__ == "__main__":
    username = input("Nombre de usuario: ")
    password = input("Contraseña: ")
    add_user(username, password)
