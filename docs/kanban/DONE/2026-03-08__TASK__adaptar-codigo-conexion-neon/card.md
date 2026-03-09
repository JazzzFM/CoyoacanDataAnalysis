---
id: "TASK-2026-03-08__adaptar-codigo-conexion-neon"
title: "Adaptar código de conexión para Neon PostGIS"
status: "BACKLOG"
phase: "Plan"
scope_in:
  - "Agregar sslmode=require y pool_pre_ping al engine SQLAlchemy"
  - "Mover credenciales hardcodeadas a variables de entorno"
  - "Probar conexión local → Neon con dashboard standalone"
scope_out:
  - "Deploy a Render (tarea separada)"
  - "Unificar las dos apps Dash"
artifacts:
  card: card.md
  validate: validate.md
plan_phase: 1
---

# Summary
- Objective: Adaptar el código de conexión a BD para que funcione con Neon (SSL requerido, scale-to-zero, credenciales via env vars) en lugar de PostgreSQL local.
- Constraints: Cambios mínimos — solo connection string y pool config.

# Archivos a modificar

| Archivo | Cambio |
|---|---|
| `dashboard/data_access/data_connection.py` | Agregar `?sslmode=require` al connection string, `pool_pre_ping=True` y `pool_recycle=300` al engine |
| `dashboard/app.py` | Mover credenciales hardcodeadas a `os.getenv()` |
| `config/default.py` | Asegurar que `SQLALCHEMY_DATABASE_URI` soporte Neon connection string |
| `.env.example` | Crear template con variables necesarias para Neon |

# Neon connection info
- Host: `ep-holy-queen-ak4xzy1t-pooler.c-3.us-west-2.aws.neon.tech`
- Database: `neondb`
- User: `neondb_owner`
- SSL: required

# Dependencias
- **Requiere:** Polígonos cargados en Neon ✅ (completado)
- **Bloquea:** Deploy en Render

# Updates
- 2026-03-08 - Created. Separada de Phase 2 de INFRA task.
