# Perfil de colonia — Ficha técnica individual

**Type:** TASK
**Status:** DONE
**Date completed:** 2026-03-14
**Commit:** 6080a41

## Problema
No había forma de ver todos los indicadores de una colonia específica en un solo lugar. El usuario tenía que navegar entre múltiples rubros para entender el estado de su zona.

## Solución
Nueva página /dashboard/perfil con:
- Dropdown para seleccionar colonia
- 4 KPIs con ranking (#X de 153)
- Radar chart individual (10 ejes normalizados)
- Categorías: urbanismo social, calidad vivienda, concentración equipamiento, zona sísmica
- Semáforo por 4 dimensiones (Densidad, Vivienda, Medio Ambiente, Servicios) con 3-4 indicadores cada una

## Verificación
- [x] Callback responde OK para cualquier colonia
- [x] Rankings calculados correctamente
- [x] Semáforos por terciles funcionan
