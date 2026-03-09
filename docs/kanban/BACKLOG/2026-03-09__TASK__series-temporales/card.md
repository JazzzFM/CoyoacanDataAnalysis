---
id: "TASK-2026-03-09__series-temporales"
title: "Series temporales y comparación intercensal 2010 vs 2020"
status: "BACKLOG"
phase: "Research"
scope_in:
  - "Descargar datos censo INEGI 2010 a nivel AGEB para Coyoacán"
  - "Cargar a tabla datos_demograficos_particionada con anio=2010"
  - "Crear vista de cambio porcentual por AGEB: ((2020 - 2010) / 2010) * 100"
  - "Mapa animado o slider temporal 2010 → 2020"
  - "Gráficos de línea para métricas clave a nivel alcaldía"
scope_out:
  - "Proyecciones futuras (regresión, forecasting)"
  - "Datos anteriores a 2010"
artifacts:
  card: card.md
plan_phase: 3
---

# Summary
- Objective: Agregar dimensión temporal al análisis. Detectar tendencias de crecimiento/decrecimiento, gentrificación, y cambio demográfico en 10 años.
- Constraints: Datos censales solo cada 10 años. Los AGEBs pueden cambiar entre censos (requiere reconciliación espacial).

# Análisis habilitados
- Crecimiento poblacional por AGEB/colonia
- Cambio en composición demográfica (envejecimiento, migración)
- Detección de gentrificación (cambio de perfil + uso de suelo)
- Slider temporal en el mapa

# Dependencias
- **Requiere:** Datos INEGI 2010 (descarga de gaia.inegi.org.mx/scince2010)
- **Requiere:** ETL adaptado para 2010
- **Bloquea:** TASK__deteccion-gentrificacion

# Updates
- 2026-03-09 - Created.
