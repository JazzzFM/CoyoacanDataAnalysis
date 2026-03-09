---
id: "REFACTOR-2026-03-09__unificar-apps-dash"
title: "Unificar las dos apps Dash en una sola arquitectura"
status: "BACKLOG"
phase: "Research"
scope_in:
  - "Migrar arquitectura en capas de dashboard/ al app Flask+Dash integrado"
  - "Mantener autenticación Flask-Login del app/ actual"
  - "Usar la misma capa de datos (data_access/, services/) para ambas"
  - "Eliminar app/dashboard.py simple y reemplazar con el dashboard standalone mejorado"
  - "Un solo punto de entrada: run.py"
scope_out:
  - "Reescritura completa del frontend"
  - "Migración a otro framework (React, etc.)"
artifacts:
  card: card.md
plan_phase: 1
---

# Summary
- Objective: Tener una sola app Flask+Dash con la arquitectura limpia en capas del standalone pero con autenticación, para eliminar la divergencia entre las dos apps.
- Constraints: No romper funcionalidad existente. Mantener Flask-Login. Mantener compatibilidad con Render.

# Usuarios objetivo
- **Investigador**: Necesita filtros avanzados y exportación de datos
- **Funcionario**: Necesita indicadores claros y resúmenes ejecutivos
- **Ciudadano**: Necesita simplicidad y narrativa visual

# Estrategia
1. Mover `dashboard/data_access/`, `dashboard/services/`, `dashboard/domain/` a ubicación compartida
2. Reescribir `app/dashboard.py` usando `LayoutBuilder` y `CallbackRegister` del standalone
3. Integrar `FiguresGenerator` para mapas coropléticos con filtros
4. Mantener sidebar multi-rubro del standalone dentro de `/dashboard/` route de Flask
5. Eliminar dashboard/app.py standalone como punto de entrada separado

# Dependencias
- **Requiere:** Nada (puede iniciar ahora)
- **Bloquea:** Todas las tareas de nuevos features (deben ir en la app unificada)

# Updates
- 2026-03-09 - Created. Primera tarea de Phase 1 (Foundation).
