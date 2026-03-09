# Coyoacán Data Analysis - Kanban

> **Source of Truth**: Este directorio (`docs/kanban/`) es la fuente de verdad para el seguimiento de tareas del proyecto.

## Estructura de directorios

```
docs/kanban/
├── BACKLOG/               # Tareas pendientes de iniciar
├── DOING/                 # Tareas en progreso (máx 2)
├── DONE/                  # Tareas completadas
└── TEMPLATE_TASK_FOLDER/  # Plantilla para nuevas tareas
```

---

## Convenciones de nombrado

### Tareas (carpetas con documentación)

```
{YYYY-MM-DD}[-HHMM]__{TYPE}__{descripcion-corta}/
├── card.md      # Descripción principal, estado, actualizaciones
├── plan.md      # Plan de implementación (opcional en quick-fix)
├── research.md  # Investigación y hallazgos (opcional en quick-fix)
└── validate.md  # Criterios de validación y resultados
```

> **Justificación**: La fecha al inicio permite ordenamiento cronológico natural al listar directorios.

### Tipos de tareas

| Tipo | Uso | Ejemplo |
|------|-----|---------|
| `TASK` | Features, nuevos rubros, nuevas visualizaciones | Agregar rubro electoral al dashboard |
| `BUG` | Bugs en el dashboard o en la ingesta de datos | Mapa no renderiza a nivel colonia |
| `DATA` | Ingesta, limpieza, transformación de datos | Cargar censo 2020 a PostGIS |
| `INFRA` | Infraestructura, deploy, migraciones | Migrar de Docker a Neon + Render |
| `REFACTOR` | Refactorizaciones de código | Unificar las dos apps Dash |

### Ejemplos

```
2026-03-08__INFRA__migrar-postgis-a-neon/
2026-03-08__TASK__agregar-rubro-electoral/
2026-03-10__DATA__ingesta-censo-economia-2020/
2026-03-12__BUG__merge-edafologicos-colonia-duplicados/
2026-03-15__REFACTOR__unificar-dashboard-standalone-flask/
```

---

## Ciclo de vida de tareas

```
BACKLOG ──────► DOING ──────► DONE
                  │
      máx 2      │   requiere
      tareas     │   validación
                 └──────────────
```

### Reglas

1. **Máximo 2 tareas en DOING** — Evitar dispersión. Terminar antes de empezar.
2. **Mover carpeta completa** — Al cambiar estado, mover la carpeta de un directorio a otro.
3. **Actualizar card.md** — Al mover, actualizar el campo `status` y agregar entrada en `# Updates`.

---

## Fases dentro de DOING

Cada tarea en progreso pasa por fases documentadas en `card.md`:

1. **Research** — Investigación: entender el problema, explorar datos, revisar notebooks
2. **Plan** — Definir la solución y archivos a modificar
3. **Implement** — Desarrollo, código, queries
4. **Validate** — Verificar que funciona (datos correctos, mapa renderiza, etc.)

---

## Definición de Terminado (DoD)

Para mover cualquier tarea a **DONE**:

| Tipo | Requisitos para DONE |
|------|----------------------|
| `TASK` | Feature funcional + probada manualmente en el dashboard |
| `BUG` | Fix verificado + el mapa/dato se muestra correctamente |
| `DATA` | Datos cargados en PostGIS + verificados con query de control |
| `INFRA` | Servicio funcional + documentado en `docs/guias/` |
| `REFACTOR` | Funcionalidad existente sigue funcionando sin regresiones |

### Validación de datos (para tareas tipo `DATA`)

```sql
-- Query de control mínima en validate.md
SELECT COUNT(*), ST_IsValid(geometry) FROM tabla_nueva GROUP BY 2;
SELECT DISTINCT anio FROM tabla_nueva ORDER BY 1;
```

### Validación de dashboard (para tareas tipo `TASK` y `BUG`)

- [ ] El mapa renderiza a nivel manzana
- [ ] El mapa renderiza a nivel AGEB
- [ ] El mapa renderiza a nivel colonia
- [ ] El dropdown de métricas se puebla correctamente
- [ ] El hover muestra las columnas de tooltip esperadas

---

## Tareas Quick-Fix

Tareas con solo `card.md` cuando son:
- Cambios pequeños de configuración
- Bug fixes de una línea
- Ajustes de estilo en el dashboard

Se identifican con el sufijo `(quick-fix)` en el card.md.

---

## Guía de documentación

| Sección | Descripción | Obligatorio |
|---------|-------------|-------------|
| **Problema** | Descripción clara del problema o feature | Si |
| **Causa raíz** | Causa raíz técnica (solo bugs) | Solo bugs |
| **Solución** | Descripción de la solución implementada | Si |
| **Verificación** | Checklist de criterios validados | Si |
| **Datos afectados** | Tablas, columnas, o notebooks involucrados | Si aplica |
