# Estética Coyoacán + paneles de interpretación analítica

**Type:** TASK
**Status:** DONE
**Date completed:** 2026-03-14
**Commit:** 1b838bf

## Problema
El dashboard usaba Bootstrap default sin identidad visual. Las páginas analíticas no tenían contexto narrativo — los datos se mostraban sin interpretación.

## Solución
**Estética:**
- CSS custom con paleta verde Coyoacán (#1a3c34 → #40916c)
- Sidebar con gradiente oscuro y 3 secciones: DATOS / ANÁLISIS / HERRAMIENTAS
- Cards con sombras, hover, tablas con header verde
- Panel .insight-panel con borde verde y fondo degradado

**Interpretaciones en 6 páginas:**
- Home: Coyoacán en contexto (segregación norte-sur, OMS y área verde)
- Vulnerabilidad: 12 componentes y patrón sur-oriente
- Accesibilidad: desiertos urbanos y nearest-neighbor
- Riesgo: multi-amenaza, Churubusco/Insurgentes
- Correlaciones: densidad-verde, segregación por valor suelo
- Perfil: cómo interpretar semáforos y rankings

## Verificación
- [x] CSS se carga (/dashboard/assets/custom.css → 200)
- [x] Todas las páginas renderizan con nuevo estilo
- [x] Paneles insight visibles en las 6 páginas
