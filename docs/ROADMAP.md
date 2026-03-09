# Roadmap: Plataforma de Análisis Territorial de Coyoacán

## Visión

Transformar un visor de mapas en una **plataforma de inteligencia territorial** que permita a investigadores, funcionarios y ciudadanos entender, comparar y tomar decisiones basadas en evidencia geoespacial sobre Coyoacán.

## Usuarios objetivo

| Perfil | Necesita | Usa el proyecto para |
|--------|----------|---------------------|
| **Investigador** | Datos exportables, filtros avanzados, metodología transparente | Publicar análisis, validar hipótesis, cruzar variables |
| **Funcionario** | KPIs claros, semáforos, comparadores, índices compuestos | Priorizar inversión pública, justificar decisiones |
| **Ciudadano** | Simplicidad, narrativa visual, contexto interpretativo | Entender su colonia, comparar con otras, informarse |

---

## Fases

### Phase 1 — Foundation (Datos + Unificación)

> **Objetivo:** Tener una sola app funcional con todos los datos base cargados.

| Tarea | Tipo | Dependencia | Estado |
|-------|------|-------------|--------|
| Cargar datos demográficos INEGI 2020 | DATA | — | BACKLOG (ETL listo) |
| Cargar datos edafológicos SEDUVI 2017 | DATA | — | BACKLOG (ETL listo) |
| Unificar las dos apps Dash | REFACTOR | — | BACKLOG |
| Cargar datos DENUE (servicios) | DATA | — | BACKLOG |
| Cargar datos electorales INE | DATA | — | BACKLOG |

**Entregable:** App unificada Flask+Dash con 4+ rubros de datos en PostGIS.

### Phase 2 — Core Analysis (Features clave)

> **Objetivo:** Pasar de "visor de datos" a "plataforma de análisis" con features diferenciadores.

| Tarea | Tipo | Dependencia | Estado |
|-------|------|-------------|--------|
| Dashboard resumen ejecutivo (KPIs) | TASK | Phase 1 | BACKLOG |
| Comparador side-by-side de colonias | TASK | Phase 1 | BACKLOG |
| Índice de vulnerabilidad territorial | TASK | Phase 1 + DENUE | BACKLOG |
| Tooltips enriquecidos (ranking + contexto) | TASK | Phase 1 | BACKLOG |

**Entregable:** Dashboard con narrativa, indicadores compuestos, y herramienta de comparación.

### Phase 3 — Advanced Analysis (Análisis espacial real)

> **Objetivo:** Aprovechar PostGIS para análisis que no se pueden hacer en Excel.

| Tarea | Tipo | Dependencia | Estado |
|-------|------|-------------|--------|
| Análisis de accesibilidad (desiertos urbanos) | TASK | DENUE | BACKLOG |
| Visualización multi-capa con toggles | TASK | Phase 2 | BACKLOG |
| Series temporales (censo 2010 vs 2020) | TASK | ETL 2010 | BACKLOG |

**Entregable:** Mapas de desiertos urbanos, análisis temporal, capas superpuestas.

### Phase 4 — Impact (Diferenciación)

> **Objetivo:** Features que hacen al proyecto único y publicable.

| Tarea | Tipo | Dependencia | Estado |
|-------|------|-------------|--------|
| Detección de gentrificación | TASK | Phase 3 | BACKLOG |
| API REST de datos abiertos | TASK | Phase 2 | BACKLOG |

**Entregable:** Mapa de riesgo de gentrificación + API pública para multiplicar impacto.

---

## Diagrama de dependencias

```
Phase 1 (Foundation)
├── DATA: demograficos ──────────────────────┐
├── DATA: edafologicos ──────────────────────┤
├── DATA: DENUE ──────────────────┐          │
├── DATA: electorales ────────────┤          │
└── REFACTOR: unificar apps ──────┤──────────┤
                                  │          │
Phase 2 (Core Analysis)           │          │
├── TASK: resumen ejecutivo ◄─────┤──────────┘
├── TASK: comparador colonias ◄───┤
├── TASK: índice vulnerabilidad ◄─┘
└── TASK: tooltips enriquecidos
                    │
Phase 3 (Advanced)  │
├── TASK: accesibilidad ◄──── DENUE
├── TASK: capas superpuestas
└── TASK: series temporales ◄──── INEGI 2010
                    │
Phase 4 (Impact)    │
├── TASK: gentrificación ◄──── series temporales + DENUE
└── TASK: API datos abiertos
```

---

## Principios de desarrollo

1. **Datos primero** — No construir features sin datos reales cargados
2. **Una sola app** — Todo desarrollo nuevo va en la app unificada Flask+Dash
3. **Valor incremental** — Cada phase entrega valor por sí misma
4. **3 usuarios siempre** — Cada feature debe servir a al menos 2 de los 3 perfiles
5. **PostGIS como motor** — Aprovechar funciones espaciales, no solo almacenamiento
