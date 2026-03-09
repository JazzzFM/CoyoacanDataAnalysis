# Plan

## Objective
Migrar de Docker Compose (VPS) a Neon (PostGIS serverless) + Render (app hosting) con costo $0/mes.

## Scope
### In
- Crear proyecto y DB PostGIS en Neon
- Migrar datos (tablas de polígonos + datos temáticos)
- Adaptar código de conexión para Neon (SSL, pool)
- Configurar deploy en Render
- Documentar la nueva arquitectura

### Out
- Unificar las dos apps Dash
- CI/CD pipeline
- Migrar a plan pagado

## Phases

### Phase 1 — Neon: Crear DB y migrar datos
- [ ] Crear proyecto en Neon con extensión PostGIS
- [ ] Exportar datos de PostGIS local (pg_dump o ogr2ogr)
- [ ] Importar tablas: `poligonos_manzanas_agebs_colonias`, `datos_demograficos_particionada`, `datos_edafologicos_particionada`
- [ ] Verificar integridad: conteo de registros, geometrías válidas
- [ ] Aplicar `ST_Simplify` a geometrías para optimizar tamaño

#### Phase 1 Files
- Scripts SQL de exportación/importación
- Neon dashboard (consola web)

### Phase 2 — Adaptar código de conexión
- [ ] Modificar `dashboard/data_access/data_connection.py`: agregar `sslmode=require` al connection string
- [ ] Agregar `pool_pre_ping=True` al `create_engine()` para manejar scale-to-zero
- [ ] Mover credenciales hardcodeadas de `dashboard/app.py` a variables de entorno
- [ ] Modificar `config/default.py` para soportar Neon connection string
- [ ] Probar conexión local → Neon con el dashboard standalone

#### Phase 2 Files
- `dashboard/data_access/data_connection.py`
- `dashboard/app.py`
- `config/default.py`
- `.env` (nueva configuración)

### Phase 3 — Deploy en Render
- [ ] Crear `render.yaml` o configurar via dashboard de Render
- [ ] Configurar variables de entorno en Render (DATABASE_URI, SECRET_KEY)
- [ ] Adaptar `run.py` o crear `Procfile` para Gunicorn en Render
- [ ] Deploy inicial y verificar que el dashboard carga
- [ ] Configurar UptimeRobot para ping cada 14 min (evitar sleep)

#### Phase 3 Files
- `render.yaml` o `Procfile`
- `run.py`
- Render dashboard (consola web)

### Phase 4 — Documentación y limpieza
- [ ] Actualizar `docs/guias/setup-docker.md` con nota de deprecación
- [ ] Crear `docs/guias/setup-neon-render.md`
- [ ] Actualizar `CLAUDE.md` con nueva arquitectura
- [ ] Actualizar ADR: `docs/decisiones/20260308-migracion-neon-render.md`

#### Phase 4 Files
- `docs/guias/setup-neon-render.md`
- `docs/decisiones/20260308-migracion-neon-render.md`
- `CLAUDE.md`

## Validation Commands
```sql
-- En Neon: verificar PostGIS
SELECT PostGIS_version();

-- Verificar tablas migradas
SELECT COUNT(*) FROM poligonos_manzanas_agebs_colonias;
SELECT COUNT(*) FROM datos_demograficos_particionada;
SELECT COUNT(*) FROM datos_edafologicos_particionada;

-- Verificar geometrías válidas
SELECT COUNT(*), ST_IsValid("GEOM_MANZANA") FROM poligonos_manzanas_agebs_colonias GROUP BY 2;
```

```bash
# En Render: verificar app
curl -s https://<app-name>.onrender.com/ | head -20
```

## Success Criteria
- [ ] Dashboard accesible desde URL pública de Render
- [ ] Mapas coropléticos renderizan a 3 granularidades (manzana, ageb, colonia)
- [ ] Dropdown de métricas se puebla con datos de Neon
- [ ] Tiempo de wake-up < 60 segundos
- [ ] Storage en Neon < 0.5 GB (free tier)
- [ ] Costo mensual: $0
