# Setup con Docker

Guía para levantar el proyecto completo usando Docker Compose.

---

## Prerequisitos

- Docker y Docker Compose instalados
- Puerto 5432 (PostgreSQL) y 8050 (app) disponibles

## 1. Configurar variables de entorno

Crear archivo `.env` en la raíz del proyecto:

```env
# Base de datos
POSTGRES_USER=developer
POSTGRES_PASSWORD=<tu_password>
POSTGRES_DB=Poligonos

# Aplicación Flask
DATABASE_URI=postgresql://developer:<tu_password>@db:5432/Poligonos
SECRET_KEY=<clave_secreta>
DASH_PORT=8050
```

**Nota:** El host de la DB es `db` (nombre del servicio en Docker Compose), no `localhost`.

## 2. Levantar los servicios

```bash
docker compose up --build
```

Esto levanta:
- **db:** PostgreSQL 14 con PostGIS 3.2 (imagen `postgis/postgis:14-3.2`)
- **app:** Python 3.9 con Gunicorn sirviendo la aplicación Flask+Dash

El servicio `app` espera a que la DB esté lista usando `wait-for-it.sh` antes de iniciar Gunicorn.

## 3. Crear usuario administrador

```bash
docker compose exec app flask create-admin <password>
```

## 4. Ejecutar migraciones

```bash
docker compose exec app flask db upgrade
```

Para generar una nueva migración después de cambiar modelos:

```bash
docker compose exec app flask db migrate -m "descripción del cambio"
docker compose exec app flask db upgrade
```

## 5. Cargar datos geoespaciales en PostGIS

Los shapefiles se cargan usando `ogr2ogr` o desde los notebooks de Jupyter.

Ejemplo con `ogr2ogr` desde fuera del contenedor:

```bash
ogr2ogr -f "PostgreSQL" \
  PG:"host=localhost port=5432 dbname=Poligonos user=developer password=<password>" \
  clean_data/poligonos/manzana/manzanas_coyoacan_clean.shp \
  -nln manzanas -lco GEOMETRY_NAME=geom
```

Desde los notebooks, los datos se limpian y cargan programáticamente (ver `notebooks/CleanDataPoligonos.ipynb` y `notebooks/NewTables.ipynb`).

## 6. Acceder a la aplicación

- **Dashboard Flask:** http://localhost:8050 (requiere login)
- **Dashboard Dash embebido:** http://localhost:8050/dashboard/ (requiere login previo)

## Arquitectura Docker

```
┌─────────────────────────────────────────┐
│            coyoacan_network             │
│                                         │
│  ┌──────────┐       ┌───────────────┐   │
│  │   app    │       │      db       │   │
│  │ :8050    │──────▶│ :5432         │   │
│  │ Gunicorn │       │ PostGIS 14    │   │
│  │ Flask+   │       │               │   │
│  │ Dash     │       │ Vol:          │   │
│  │          │       │ postgres_data │   │
│  └──────────┘       └───────────────┘   │
│   Vol: .:/app                           │
└─────────────────────────────────────────┘
```

## Troubleshooting

### La app no arranca y muestra errores de conexión a la DB
El script `wait-for-it.sh` espera a que el puerto 5432 esté disponible, pero PostGIS puede tardar unos segundos extra en inicializar la extensión. Si persiste, reiniciar:

```bash
docker compose restart app
```

### Error de Flask-Login con Werkzeug
El Dockerfile aplica un patch automático a Flask-Login (líneas 24-27 del Dockerfile) para resolver incompatibilidades con `werkzeug.urls`. Si se actualiza Flask-Login, verificar que el patch siga siendo necesario.

### Errores de permisos en wait-for-it.sh
```bash
chmod +x wait-for-it.sh
```

### Conectarse directamente a PostGIS

```bash
# Desde el host
psql -h localhost -p 5432 -U developer -d Poligonos

# Desde dentro del contenedor de la app
docker compose exec app psql -h db -U developer -d Poligonos

# Desde el contenedor de la DB
docker compose exec db psql -U developer -d Poligonos
```

### Verificar que PostGIS está habilitado

```sql
SELECT PostGIS_version();
```

### Reiniciar desde cero (elimina datos)

```bash
docker compose down -v
docker compose up --build
```
