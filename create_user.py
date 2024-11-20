from app import create_app, db
from app.models import User
import logging

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = create_app()
app.app_context().push()

def create_user(username, password):
    user = User(username=username)
    user.password = password  # Esto usa el setter para hashear la contraseña
    db.session.add(user)
    db.session.commit()
    logger.info(f'Usuario "{username}" creado exitosamente.')

if __name__ == '__main__':
    import sys
    if len(sys.argv) != 3:
        print("Uso: python create_user.py <username> <password>")
    else:
        _, username, password = sys.argv
        create_user(username, password)