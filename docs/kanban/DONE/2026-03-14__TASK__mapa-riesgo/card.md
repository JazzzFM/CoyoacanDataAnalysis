# Mapa de riesgo territorial multi-amenaza

**Type:** TASK
**Status:** DONE
**Date completed:** 2026-03-14
**Commit:** 6080a41

## Problema
Los datos de riesgo (inundaciones, accidentes, convergencia) estaban dispersos en el rubro de infraestructura sin un análisis integrado.

## Solución
Nueva página /dashboard/riesgo con:
- Score compuesto por colonia via spatial join (gpd.sjoin)
- 4 componentes seleccionables: inundaciones, accidentes peatonales, convergencia de riesgos, vulnerabilidad territorial
- Mapa coroplético YlOrRd
- Ranking top 20 con conteos por tipo de amenaza
- Normalización por componente, pesos iguales

## Verificación
- [x] Spatial joins ejecutan en <5 segundos
- [x] Conteos de inundaciones/accidentes coinciden con datos fuente
- [x] Mapa y tabla se generan sin errores
