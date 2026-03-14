# Resumen ejecutivo v2 — KPIs enriquecidos

**Type:** TASK
**Status:** DONE
**Date completed:** 2026-03-14
**Commit:** 4d937e3

## Problema
El home page solo mostraba 5 KPIs genéricos (población, colonias, AGEBs, manzanas, rubros) y 2 charts (densidad + uso suelo). No reflejaba la riqueza de datos disponibles.

## Solución
- 5 → 10 KPIs en 2 filas (+internet, temp nocturna, infra, viv desocupadas, vulnerabilidad media)
- +2 charts extra: top 10 vulnerabilidad + top 10 área verde
- 5 → 7 hallazgos dinámicos cruzando múltiples dimensiones (correlación densidad-verde, colonia más vulnerable, brecha digital)

## Verificación
- [x] 10 KPIs se calculan sin NaN
- [x] Charts extra se generan correctamente
- [x] Hallazgos son dinámicos (cambian si cambian los datos)
