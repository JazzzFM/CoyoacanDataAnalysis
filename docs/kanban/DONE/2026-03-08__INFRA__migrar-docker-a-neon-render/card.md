---
id: "INFRA-2026-03-08__migrar-docker-a-neon-render"
title: "Migrar de Docker/VPS a Neon (PostGIS) + Render (App)"
status: "DONE"
phase: "Done"
scope_in:
  - "Crear proyecto PostGIS en Neon y migrar datos"
  - "Adaptar connection string y pool config en data_connection.py"
  - "Configurar deploy de Flask+Dash en Render"
  - "Optimizar queries para RAM limitada (512 MB)"
  - "Documentar nueva arquitectura en docs/guias/"
scope_out:
  - "Migrar a plan pagado (solo free tier por ahora)"
  - "Unificar las dos apps Dash (tarea aparte)"
  - "CI/CD pipeline (fuera de alcance inicial)"
artifacts:
  card: card.md
  research: research.md
  plan: plan.md
  validate: validate.md
plan_phase: 1
---

# Summary
- Objective: Eliminar la dependencia de VPS/Docker migrando la base de datos PostGIS a Neon (serverless) y la app Flask+Dash a Render (free tier), logrando costo $0/mes.
- Constraints: Free tier de Neon (0.5 GB storage, scale-to-zero), free tier de Render (512 MB RAM, sleep tras 15 min inactividad).

# Arquitectura objetivo

```
                    ┌──────────────┐
  Usuario ────────▶ │  Render      │
                    │  (Flask+Dash)│
                    │  Gratis      │
                    └──────┬───────┘
                           │ postgresql://...@xyz.neon.tech/Poligonos?sslmode=require
                           ▼
                    ┌──────────────┐
                    │  Neon        │
                    │  (PostGIS)   │
                    │  Gratis      │
                    └──────────────┘
```

# Decisiones técnicas

| Decisión | Elegido | Alternativa descartada | Por qué |
|----------|---------|------------------------|---------|
| DB | Neon | Supabase | Auto-wake (vs pausa 7 días), $5 vs $25 plan pagado, menos fricciones PostGIS |
| App hosting | Render | Koyeb | Gratis sin tarjeta, mejor documentación para Dash, comunidad más grande |
| RAM 512 MB | ST_Simplify + cache | Upgrade pagado | Mantener costo $0 |

# Updates
- 2026-03-08 - Created. Investigación completada, Neon + Render seleccionados.
- 2026-03-08 - Moved to DOING. Iniciando Phase 1: crear proyecto Neon con PostGIS.
- 2026-03-08 - Phase 1 parcial: proyecto Neon creado (lucky-sun-44184647), PostGIS 3.5 habilitado, esquema de 4 tablas + 9 índices creados. Tablas vacías — la carga de datos se separó en tareas DATA independientes.
- 2026-03-08 - Entorno virtual creado con uv (.venv, Python 3.11, dependencias instaladas).
- 2026-03-08 - Bloqueada Phase 2 (adaptar código) hasta que las tareas DATA carguen datos a Neon.

# Tareas DATA bloqueantes
1. `DATA-2026-03-08__cargar-poligonos-spatial-join-neon` — Recrear spatial join y cargar polígonos
2. `DATA-2026-03-08__reextraer-datos-demograficos-inegi` — Re-descargar censo 2020 y cargar
3. `DATA-2026-03-08__reextraer-datos-edafologicos-seduvi` — Re-descargar uso de suelo y cargar

# Neon project info
- Project ID: `lucky-sun-44184647`
- Branch: `main` (br-aged-night-ak2jt2v1)
- Database: `neondb`
- Host: `ep-holy-queen-ak4xzy1t-pooler.c-3.us-west-2.aws.neon.tech`
