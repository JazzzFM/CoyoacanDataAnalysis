---
id: "TASK-2026-03-09__tooltips-enriquecidos"
title: "Tooltips enriquecidos con ranking, contexto y semáforo"
status: "DONE"
phase: "Done"
scope_in:
  - "Mostrar ranking de la zona en el tooltip ('Colonia #7 de 153')"
  - "Mostrar desviación vs promedio municipal ('+45% vs media')"
  - "Categorización semáforo visual (bajo/medio/alto) con colores"
  - "Tooltip adaptativo por rubro (diferentes métricas según contexto)"
scope_out:
  - "Tooltips clickeables con drill-down (eso es otra tarea)"
artifacts:
  card: card.md
plan_phase: 2
---

# Summary
- Objective: Que el hover sobre cualquier zona del mapa dé contexto inmediato, no solo el valor crudo. Un número sin contexto no dice nada.
- Constraints: Debe calcularse dinámicamente según la métrica seleccionada.

# Ejemplo de tooltip actual vs propuesto

**Actual:**
```
Colonia: Pedregal de Carrasco
densidad_pob_total: 18543.2
```

**Propuesto:**
```
📍 Pedregal de Carrasco
━━━━━━━━━━━━━━━━━━━━━
Densidad: 18,543 hab/km²  🔴 Muy alta
Ranking: #3 de 153 colonias
vs Promedio: +156% (media: 7,245)
━━━━━━━━━━━━━━━━━━━━━
Población: 28,412
Uso suelo: 78% Habitacional
```

# Dependencias
- **Requiere:** REFACTOR__unificar-apps-dash
- **Bloquea:** Nada (mejora incremental)

# Updates
- 2026-03-09 - Created.
- 2026-03-11 - Implemented. Ranking (#X de N), desviación vs promedio (+X%), semáforo por terciles (🟢🟡🔴), nombre de zona como header, tooltip adaptativo por rubro. Aplica a los 5 rubros numéricos.
