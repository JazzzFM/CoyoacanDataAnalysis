# app/commands.py

import click
from flask import current_app
from flask.cli import with_appcontext
from app import db
from app.models import User

@click.command('create-admin')
@click.argument('password')
@with_appcontext
def create_admin(password):
    """Crear o actualizar el usuario administrador con la contraseña proporcionada."""
    admin = User.query.filter_by(username='admin').first()
    if admin:
        admin.set_password(password)
        click.echo("Contraseña del administrador actualizada correctamente.")
    else:
        admin = User(username='admin')
        admin.set_password(password)
        db.session.add(admin)
        click.echo("Usuario administrador creado correctamente.")
    db.session.commit()

def register_commands(app):
    app.cli.add_command(create_admin)

