# Análisis de correlaciones entre indicadores

**Type:** TASK
**Status:** DONE
**Date completed:** 2026-03-14
**Commit:** 6080a41

## Problema
No había forma de explorar relaciones entre indicadores (ej: ¿más densidad = menos área verde?).

## Solución
Nueva página /dashboard/correlaciones con:
- Scatter plot interactivo con selector X/Y/color
- Trendline OLS con coeficiente R
- Matriz de correlación heatmap de 16 métricas
- Color por tercera variable (opcional)

## Verificación
- [x] Scatter con trendline se genera correctamente
- [x] Matriz de correlación muestra 16×16 métricas
- [x] R se calcula y muestra en el título
