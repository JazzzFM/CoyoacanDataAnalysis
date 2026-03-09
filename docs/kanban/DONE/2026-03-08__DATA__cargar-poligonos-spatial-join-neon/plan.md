# Plan

## Objective
Recrear spatial join de los 3 niveles geográficos y cargar a Neon.

## Scope
### In
- Leer shapefiles de `clean_data/poligonos/`
- Spatial join: manzana → AGEB (within), manzana → colonia (within)
- Renombrar columnas al esquema esperado por el dashboard
- Cargar a Neon via `to_postgis()`

### Out
- Datos temáticos
- Optimización de geometrías

## Phases

### Phase 1 — Spatial join local
- [ ] Leer los 3 shapefiles con GeoPandas
- [ ] `gpd.sjoin(manzanas, agebs, predicate='within')` → asociar ID_AGEB a cada manzana
- [ ] `gpd.sjoin(resultado, colonias, predicate='within')` → asociar ID_COLONIA + NOMBRE_COLONIA
- [ ] Renombrar columnas: `id_manzana` → `ID_MANZANA`, `geometry` → `GEOM_MANZANA`, etc.
- [ ] Preservar las 3 geometrías como columnas separadas (GEOM_MANZANA, GEOM_AGEB, GEOM_COLONIA)

#### Phase 1 Files
- `clean_data/poligonos/manzana/manzanas_coyoacan_clean.shp`
- `clean_data/poligonos/ageb/ageb_coyoacan_clean.shp`
- `clean_data/poligonos/colonia/colonias_coyoacan_clean.shp`

### Phase 2 — Cargar a Neon
- [ ] Conectar a Neon con SQLAlchemy (sslmode=require)
- [ ] `gdf.to_postgis('poligonos_manzanas_agebs_colonias', engine, if_exists='replace')`
- [ ] Verificar conteo de registros
- [ ] Verificar geometrías válidas

#### Phase 2 Files
- Script Python o notebook para la carga

## Validation Commands
```sql
SELECT COUNT(*) FROM poligonos_manzanas_agebs_colonias;
-- Esperado: ~4,400-4,813

SELECT COUNT(DISTINCT "ID_AGEB") FROM poligonos_manzanas_agebs_colonias;
-- Esperado: ~167

SELECT COUNT(DISTINCT "ID_COLONIA") FROM poligonos_manzanas_agebs_colonias;
-- Esperado: ~153
```

## Success Criteria
- [ ] Tabla cargada con ~4,400+ registros
- [ ] Las 3 columnas de geometría presentes y válidas
- [ ] Todos los AGEBs y colonias representados
