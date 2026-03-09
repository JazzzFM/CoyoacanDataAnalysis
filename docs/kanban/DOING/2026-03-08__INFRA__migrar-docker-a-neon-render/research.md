# Research

## Questions
- ¿Neon o Supabase para PostGIS? → **Neon**
- ¿Dónde hospedar la app Flask+Dash gratis? → **Render**
- ¿512 MB de RAM alcanza para GeoPandas? → Sí, con optimizaciones

## Findings

### Neon vs Supabase

| Criterio | Neon | Supabase |
|----------|------|----------|
| PostGIS | Completo, sin fricciones | Completo, pero quirks de permisos en `spatial_ref_sys` |
| Free tier | 0.5 GB, 100 CU-hours/mes | 500 MB, 2 proyectos |
| Inactividad | Auto-wake ~1-2s | Pausa total tras 7 días (manual reactivar) |
| Conexiones | 100 directas, 10K pooled | 60 directas, ~200 pooled |
| Costo mínimo pagado | $5/mes | $25/mes |
| SQLAlchemy + GeoPandas | Directo con `create_engine()` | IPv4/IPv6 issues, puerto 6543 vs 5432 |
| ogr2ogr | Sin problemas | Errores de permisos en `spatial_ref_sys` |

### Render vs Koyeb para Flask+Dash

| Criterio | Render | Koyeb |
|----------|--------|-------|
| Gratis sin tarjeta | Sí | Sí |
| RAM | 512 MB | 512 MB |
| Sleep después de | 15 min | 60 min |
| Wake-up | 30-60 seg | Variable |
| Pagado | $7/mes always-on | Similar |

### Estrategias para RAM 512 MB
- `ST_Simplify(geometry, 0.001)` en queries PostGIS para reducir complejidad de polígonos
- `SELECT col1, col2, geometry FROM tabla` en vez de `SELECT *`
- Cachear GeoDataFrames procesados en memoria (evitar re-queries)
- Usar `chunksize` en `gpd.read_postgis()` para datasets grandes

### Cambios en código (mínimos)
1. `dashboard/data_access/data_connection.py`: agregar `?sslmode=require` y `pool_pre_ping=True`
2. Credenciales via variables de entorno (ya soportado parcialmente)
3. `requirements.txt`: sin cambios (mismas dependencias)

## References
- Neon PostGIS docs: neon.com/docs/extensions/postgis
- Neon SQLAlchemy guide: neon.com/docs/guides/sqlalchemy
- Render Python deploy docs: render.com/docs/deploy-flask
