# Plan

## Objective
Reconstruir datos demográficos del censo 2020 y cargar a Neon PostGIS.

## Scope
### In
- Descarga de datos INEGI censo 2020 (AGEB nivel)
- ETL: limpieza, merge, cálculos de densidad
- Carga a tabla `datos_demograficos_particionada` en Neon

### Out
- Censos de otros años
- Datos económicos (DENUE) — tarea separada

## Phases

### Phase 1 — Obtener datos fuente
- [ ] Verificar si shapefiles del censo están disponibles en otra ubicación
- [ ] Si no: descargar de INEGI (Censo de Población y Vivienda 2020, nivel AGEB, CDMX)
- [ ] Colocar en `data/demografico/2020/`

#### Phase 1 Files
- `data/demografico/2020/hombres.shp`
- `data/demografico/2020/mujeres.shp`
- `data/demografico/2020/total.shp`

### Phase 2 — ETL (basado en notebook existente)
- [ ] Revisar `notebooks/EDADemografia.ipynb` para extraer lógica de ETL
- [ ] Crear script reproducible `scripts/etl_demograficos.py`
- [ ] Merge hombres + mujeres + total por `ageb`
- [ ] Clip a Coyoacán
- [ ] Calcular: area_km2, densidad_pob_total, densidad_hombres, densidad_mujeres
- [ ] Agregar columnas: anio=2020, territorio="coyoacan"
- [ ] Reproyectar a EPSG:4326

#### Phase 2 Files
- `notebooks/EDADemografia.ipynb` (referencia)
- `scripts/etl_demograficos.py` (nuevo)

### Phase 3 — Cargar a Neon
- [ ] Conectar a Neon con SQLAlchemy
- [ ] `gdf.to_postgis('datos_demograficos_particionada', engine, if_exists='replace')`
- [ ] Verificar conteo y columnas

## Validation Commands
```sql
SELECT COUNT(*) FROM datos_demograficos_particionada;
-- Esperado: ~154 AGEBs

SELECT DISTINCT anio FROM datos_demograficos_particionada;
-- Esperado: 2020

SELECT AVG(densidad_pob_total) FROM datos_demograficos_particionada WHERE densidad_pob_total > 0;
```

## Success Criteria
- [ ] ~154 registros cargados (AGEBs de Coyoacán)
- [ ] Columnas de población absoluta y tasas presentes
- [ ] Densidades calculadas correctamente
- [ ] Geometrías válidas en EPSG:4326
