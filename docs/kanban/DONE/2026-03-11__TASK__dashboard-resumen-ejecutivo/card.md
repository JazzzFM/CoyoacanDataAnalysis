---
id: "TASK-2026-03-09__dashboard-resumen-ejecutivo"
title: "Dashboard de resumen ejecutivo con KPIs y estadísticas clave"
status: "DONE"
phase: "Done"
scope_in:
  - "Página Home con KPIs principales de Coyoacán"
  - "Cards con cifras clave: población total, colonias, AGEBs, manzanas"
  - "Mini-charts: distribución de uso de suelo (pie), top colonias por densidad (bar)"
  - "Mapa overview con todas las colonias coloreadas por métrica default"
  - "Diseño responsive para los 3 perfiles de usuario"
scope_out:
  - "Dashboards por rubro (son tareas separadas)"
  - "Análisis predictivo"
artifacts:
  card: card.md
plan_phase: 2
---

# Summary
- Objective: Que la página principal del dashboard cuente la historia de Coyoacán en 10 segundos. KPIs arriba, contexto visual abajo.
- Constraints: Debe funcionar con los datos actuales (demográficos + edafológicos + polígonos). Debe ser la primera impresión del proyecto.

# Diseño propuesto

```
┌─────────────────────────────────────────────────────────┐
│  COYOACÁN — Análisis Territorial                        │
├────────┬────────┬────────┬────────┬────────────────────┤
│ 452K   │ 153    │ 167    │ 4,813  │ 2 rubros activos  │
│ hab.   │ colon. │ AGEBs  │ mznas  │ de 6 planeados    │
├────────┴────────┴────────┴────────┴────────────────────┤
│                                                         │
│  ┌──────────────────────┐  ┌─────────────────────────┐ │
│  │  MAPA OVERVIEW       │  │  TOP 10 COLONIAS        │ │
│  │  (colonias por       │  │  por densidad           │ │
│  │   densidad)          │  │  [horizontal bar chart] │ │
│  │                      │  ├─────────────────────────┤ │
│  │                      │  │  USO DE SUELO           │ │
│  │                      │  │  [donut chart]          │ │
│  └──────────────────────┘  └─────────────────────────┘ │
├─────────────────────────────────────────────────────────┤
│  ⚡ Hallazgos clave:                                    │
│  • La colonia X tiene 3x más densidad que el promedio   │
│  • El 42% del territorio es uso habitacional            │
│  • 12 colonias no tienen datos de uso de suelo          │
└─────────────────────────────────────────────────────────┘
```

# Usuarios objetivo
- **Investigador:** Ve KPIs como punto de entrada, luego navega a rubros
- **Funcionario:** Obtiene snapshot ejecutivo para presentaciones
- **Ciudadano:** Entiende su alcaldía en números simples

# Dependencias
- **Requiere:** REFACTOR__unificar-apps-dash (para construir sobre app unificada)
- **Requiere:** Datos demográficos y edafológicos cargados
- **Bloquea:** Nada

# Updates
- 2026-03-09 - Created.
- 2026-03-11 - Implemented. KPIs dinámicos (620K hab, 153 colonias, 156 AGEBs, 4813 manzanas, 7 rubros), mapa overview por densidad, top 10 barras, donut uso suelo, 5 hallazgos auto-generados.
