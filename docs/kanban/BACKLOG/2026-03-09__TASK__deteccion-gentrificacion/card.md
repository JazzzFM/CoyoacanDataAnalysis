---
id: "TASK-2026-03-09__deteccion-gentrificacion"
title: "Mapa de riesgo de gentrificación y desplazamiento"
status: "BACKLOG"
phase: "Research"
scope_in:
  - "Cruzar cambio demográfico 2010→2020 con cambio de uso de suelo"
  - "Identificar zonas con: aumento de densidad + cambio uso habitacional→comercial"
  - "Crear índice de presión de gentrificación"
  - "Mapa de calor con zonas de riesgo de desplazamiento"
  - "Panel explicativo de factores contribuyentes"
scope_out:
  - "Datos de precios de suelo (no disponibles gratuitamente)"
  - "Predicción de gentrificación futura"
artifacts:
  card: card.md
plan_phase: 4
---

# Summary
- Objective: Identificar zonas de Coyoacán donde hay indicios de gentrificación o riesgo de desplazamiento poblacional, usando evidencia cuantitativa de cambio demográfico y urbano.
- Constraints: Sin datos de precios inmobiliarios. El análisis se basa en proxies: cambio de uso de suelo, cambio poblacional, densificación.

# Variables proxy de gentrificación
1. **Aumento de densidad poblacional** (censo 2020 vs 2010)
2. **Cambio de uso de suelo** (habitacional→comercial/mixto)
3. **Aumento de niveles de construcción** (verticalización)
4. **Diversificación comercial** (más negocios DENUE en la zona)
5. **Cambio en composición demográfica** (edad promedio, escolaridad)

# Dependencias
- **Requiere:** TASK__series-temporales (datos 2010+2020)
- **Requiere:** DATA__cargar-datos-denue
- **Bloquea:** Nada

# Updates
- 2026-03-09 - Created.
