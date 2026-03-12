---
id: "TASK-2026-03-09__comparador-colonias"
title: "Comparador side-by-side de colonias/AGEBs"
status: "DONE"
phase: "Done"
scope_in:
  - "Seleccionar 2-3 colonias para comparar"
  - "Tabla comparativa con métricas demográficas y de uso de suelo"
  - "Mini-mapa resaltando las colonias seleccionadas"
  - "Gráfico de radar (spider chart) para perfil multidimensional"
  - "Ranking relativo: posición de cada colonia vs promedio municipal"
scope_out:
  - "Comparación temporal (requiere datos multi-año)"
  - "Comparación con otras alcaldías"
artifacts:
  card: card.md
plan_phase: 2
---

# Summary
- Objective: Permitir comparación directa entre zonas geográficas para toma de decisiones. "¿En qué se diferencia la colonia A de la B?"
- Constraints: Funciona con datos actuales. Nivel mínimo de comparación: colonia.

# Usuarios objetivo
- **Investigador:** Comparar AGEBs con perfil similar/diferente para estudios
- **Funcionario:** Justificar priorización de inversión pública ("la colonia X necesita más que Y porque...")
- **Ciudadano:** Entender cómo se compara su colonia con otras

# Métricas de comparación (iniciales)
- Población total y densidad
- % uso de suelo por categoría
- Número de manzanas
- Indicadores demográficos disponibles (población indígena, dependencia infantil, etc.)

# Dependencias
- **Requiere:** REFACTOR__unificar-apps-dash
- **Requiere:** Datos demográficos y edafológicos cargados
- **Bloquea:** Nada

# Updates
- 2026-03-09 - Created.
