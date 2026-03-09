---
id: "INFRA-2026-03-08__deploy-render"
title: "Deploy Flask+Dash en Render (free tier)"
status: "BACKLOG"
phase: "Plan"
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
- [ ] Crear `render.yaml` con config del servicio web
- [ ] O crear `Procfile`: `web: gunicorn --bind 0.0.0.0:$PORT run:app`
- [ ] Verificar que `requirements.txt` esté actualizado (agregar `geoalchemy2`)
- [ ] Agregar `runtime.txt` con versión Python si es necesario

### 2. Configurar en Render
- [ ] Crear cuenta en Render (gratis, sin tarjeta)
- [ ] Nuevo Web Service → conectar repo GitHub
- [ ] Configurar variables de entorno: `DATABASE_URI`, `SECRET_KEY`, `DASH_PORT`
- [ ] Build command: `pip install -r requirements.txt`
- [ ] Start command: `gunicorn --bind 0.0.0.0:$PORT run:app`

### 3. Verificar
- [ ] App responde en URL pública
- [ ] Login funciona
- [ ] Dashboard renderiza mapas (con datos de polígonos al menos)

### 4. Anti-sleep
- [ ] Crear monitor en UptimeRobot (gratis) → ping cada 14 min a la URL

### 5. Documentar
- [ ] Crear `docs/guias/setup-neon-render.md`
- [ ] Actualizar `CLAUDE.md`
- [ ] Crear ADR `docs/decisiones/20260308-migracion-neon-render.md`

# Dependencias
- **Requiere:** Código adaptado para Neon (tarea TASK__adaptar-codigo-conexion-neon)
- **Bloquea:** Nada — última tarea de la cadena INFRA

# Updates
- 2026-03-08 - Created. Separada de Phase 3 de INFRA task.
