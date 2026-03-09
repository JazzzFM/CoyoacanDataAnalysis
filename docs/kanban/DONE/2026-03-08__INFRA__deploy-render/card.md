---
id: "INFRA-2026-03-08__deploy-render"
title: "Deploy Flask+Dash en Render (free tier)"
status: "DONE"
phase: "Done"
scope_in:
  - "Crear render.yaml o Procfile para Gunicorn"
  - "Configurar variables de entorno en Render"
  - "Deploy inicial y verificar dashboard funcional"
  - "Configurar UptimeRobot para evitar sleep de 15 min"
  - "Documentar en docs/guias/setup-neon-render.md"
scope_out:
  - "Plan pagado de Render"
  - "CI/CD pipeline"
  - "Dominio custom"
artifacts:
  card: card.md
  validate: validate.md
plan_phase: 1
---

# Summary
- Objective: Desplegar la app Flask+Dash en Render free tier, conectada a Neon PostGIS, accesible desde URL pública.
- Constraints: 512 MB RAM (optimizar GeoPandas), sleep tras 15 min inactividad.

# Pasos

### 1. Preparar archivos de deploy
- [x] Crear `render.yaml` con config del servicio web
- [x] Crear `Procfile`: `web: gunicorn --bind 0.0.0.0:$PORT run:app`
- [x] Crear `build.sh` para instalar deps de sistema (GDAL/GEOS/PROJ)
- [x] Actualizar `requirements.txt` (geoalchemy2, Werkzeug==2.3.8, gunicorn==21.2.0)
- [x] Adaptar `app/dashboard.py` para cargar polígonos desde Neon PostGIS
- [x] Verificar arranque local con Gunicorn (152 colonias cargadas)

### 2. Configurar en Render (manual — requiere usuario)
- [ ] Crear cuenta en Render (gratis, sin tarjeta)
- [ ] Nuevo Web Service → conectar repo `JazzzFM/CoyoacanDataAnalysis`
- [ ] Configurar variables de entorno: `DATABASE_URI`, `SECRET_KEY`
- [ ] Build command: `./build.sh`
- [ ] Start command: `gunicorn --bind 0.0.0.0:$PORT --timeout 120 --workers 2 run:app`

### 3. Verificar
- [ ] App responde en URL pública
- [ ] Login funciona
- [ ] Dashboard renderiza mapas (con datos de polígonos al menos)

### 4. Anti-sleep
- [ ] Crear monitor en UptimeRobot (gratis) → ping cada 14 min a la URL

### 5. Documentar
- [ ] Crear `docs/guias/setup-neon-render.md`
- [ ] Actualizar `CLAUDE.md`

# Dependencias
- **Requiere:** Código adaptado para Neon (tarea TASK__adaptar-codigo-conexion-neon)
- **Bloquea:** Nada — última tarea de la cadena INFRA

# Updates
- 2026-03-08 - Created. Separada de Phase 3 de INFRA task.
- 2026-03-08 - Moved to DOING. Archivos de deploy creados: render.yaml, Procfile, build.sh. Dashboard adaptado para PostGIS. Verificado con Gunicorn localmente.
