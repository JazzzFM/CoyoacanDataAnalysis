# Fortalecimiento del índice de vulnerabilidad territorial

**Type:** TASK
**Status:** DONE
**Date completed:** 2026-03-14
**Commit:** 895916a

## Problema
El índice de vulnerabilidad solo usaba 7 componentes, dejando sin aprovechar métricas ya cargadas en la BD como temperatura nocturna, internet, consumo de agua, rezago de espacio público y escuelas básicas.

## Solución
- Índice ampliado de 7 → 12 componentes con pesos redistribuidos (suma = 1.0)
- Nuevos componentes: isla de calor, brecha digital, presión hídrica, rezago espacio público, acceso educación
- Comparador radar: 7 → 10 ejes; tabla: 9 → 14 filas
- Capas base: 5 → 9 métricas seleccionables
- Panel de sliders scrollable para 12 componentes
- ETL infraestructura: +trolebús (101 paradas, 3 líneas)
- ETL datos abiertos: +concentración equipamiento (101/153 colonias)

## Verificación
- [x] App arranca sin errores
- [x] Pesos suman 1.0
- [x] Todas las columnas existen en la BD
- [x] Páginas vulnerabilidad, comparador, capas responden 200
