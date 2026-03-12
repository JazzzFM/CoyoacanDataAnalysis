---
id: "TASK-2026-03-09__capas-superpuestas"
title: "Visualización multi-capa con toggle de rubros"
status: "DONE"
phase: "Done"
scope_in:
  - "Toggle de capas tipo Google Maps: activar/desactivar rubros sobre el mapa"
  - "Capa base: polígonos coropléticos (demografía o uso de suelo)"
  - "Capas overlay: puntos de servicios (DENUE), secciones electorales"
  - "Control de opacidad por capa"
  - "Leyenda dinámica según capas activas"
scope_out:
  - "Más de 3 capas simultáneas (rendimiento)"
  - "Análisis de intersección automática"
artifacts:
  card: card.md
plan_phase: 3
---

# Summary
- Objective: Permitir al usuario ver correlaciones espaciales activando múltiples capas. Ejemplo: ver densidad poblacional + puntos de salud para detectar zonas densas sin servicios.
- Constraints: Plotly soporta múltiples traces en un mapa. Máximo 2-3 capas activas para no saturar la visualización.

# Implementación técnica
- Usar `dcc.Checklist` para toggles de capas
- Cada capa es un trace separado en el mapa Plotly (choropleth + scattermapbox)
- Callback actualiza `figure.data` según capas seleccionadas
- Opacidad configurable con `dcc.Slider`

# Dependencias
- **Requiere:** REFACTOR__unificar-apps-dash, al menos 2 rubros con datos
- **Bloquea:** Nada

# Updates
- 2026-03-09 - Created.
- 2026-03-11 - Implemented. Página /dashboard/capas con RadioItems para capa base (5 métricas de indicadores_colonia), slider opacidad, checklists para 13 subcategorías infraestructura y 3 categorías recursos naturales. Reutiliza generar_mapa_categorico para overlays.
