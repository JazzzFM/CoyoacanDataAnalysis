# Setup: Neon (PostGIS) + Render (Flask+Dash)

Guía para desplegar la app con costo $0/mes.

## Arquitectura

```
Usuario → Render (Flask+Dash, free tier) → Neon (PostGIS, free tier)
```

## 1. Neon (Base de datos)

La base ya está configurada:
- **Project ID:** `lucky-sun-44184647`
- **Host:** `ep-holy-queen-ak4xzy1t-pooler.c-3.us-west-2.aws.neon.tech`
- **DB:** `neondb`
- **PostGIS:** 3.5 habilitado

### Connection string
```
postgresql://neondb_owner:<password>@ep-holy-queen-ak4xzy1t-pooler.c-3.us-west-2.aws.neon.tech/neondb?sslmode=require
```

## 2. Render (Aplicación)

### Paso a paso

1. **Crear cuenta** en [render.com](https://render.com) (gratis, sin tarjeta)

2. **Nuevo Web Service:**
   - Conectar repositorio: `JazzzFM/CoyoacanDataAnalysis`
   - Branch: `main`
   - Runtime: `Python`

3. **Configurar build/start:**
   - Build Command: `./build.sh`
   - Start Command: `gunicorn --bind 0.0.0.0:$PORT --timeout 120 --workers 2 run:app`

4. **Variables de entorno** (en Render → Environment):

   | Variable | Valor |
   |----------|-------|
   | `DATABASE_URI` | `postgresql://neondb_owner:<password>@ep-holy-queen-ak4xzy1t-pooler.c-3.us-west-2.aws.neon.tech/neondb?sslmode=require` |
   | `SECRET_KEY` | (generar un string aleatorio largo) |
   | `PYTHON_VERSION` | `3.11.11` |

5. **Deploy** → Render clonará el repo, ejecutará `build.sh` y arrancará Gunicorn

### Verificar
```bash
# App responde
curl -I https://<app-name>.onrender.com/

# Dashboard carga
curl -s https://<app-name>.onrender.com/dashboard/ | grep -c "Coyoacán"
```

## 3. Anti-sleep (UptimeRobot)

Render free tier duerme la app tras 15 min de inactividad.

1. Crear cuenta en [uptimerobot.com](https://uptimerobot.com) (gratis)
2. Nuevo monitor HTTP(s) → URL de tu app en Render
3. Intervalo: **cada 5 minutos**

## 4. Login

- **Usuario:** `admin`
- **Password:** `admin2026`

Para cambiar la contraseña:
```bash
# Local
flask create-admin nueva_contraseña

# O directamente en Neon (generar hash con Python)
python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('nueva_contraseña'))"
```

## Limitaciones del free tier

| Servicio | Límite | Impacto |
|----------|--------|---------|
| Render | 512 MB RAM, sleep 15 min | Primer request lento (~30s wake-up) |
| Render | 750 horas/mes | Suficiente para 1 servicio 24/7 |
| Neon | 0.5 GB storage | Suficiente para datos actuales |
| Neon | Scale-to-zero | `pool_pre_ping=True` reconecta automáticamente |

## Archivos de deploy

- `Procfile` — Comando de arranque para Render
- `build.sh` — Instala GDAL/GEOS/PROJ + pip install
- `render.yaml` — Blueprint de infraestructura (alternativa a config manual)
- `requirements.txt` — Dependencias Python con versiones pinneadas
